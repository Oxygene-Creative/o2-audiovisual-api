import asyncio
import uuid
from app.core.es import save_bulk
from app.core.files import calc_file_size, delete_file, extract_file_name, subfolder_check
from app.core.gcp import delete_blob, download_file, upload
from app.core.media_processing import extract_audio_from_video, slice_audio
from app.core.redis import redis_broker as segmentation_broker
from faststream.redis import StreamSub, Pipeline
from faststream.redis.annotations import RedisMessage, Redis
import logging
import httpx
import os

# Configure the logger
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Create logger instance
logger = logging.getLogger(__name__)

SEGMENTATION_GPU_URL = os.getenv("SEGMENTATION_GPU_URL", "").strip()

def replace_mp4_with_mp3(blob_path: str) -> str:
    if blob_path.endswith(".mp4"):
        # Replace the extension
        return blob_path.rsplit(".", 1)[0] + ".mp3"
    else:
        raise ValueError("The given blob path does not have an .mp4 extension")

async def _process_segmet(data: dict, segments: list, asset_file_path: str) -> list:
    processed_segments = []
    
    stream_type = data.pop("stream_type", None)
    if stream_type.lower() == "audio":
        # Slice audio file based on speech segments
        speech_segment_files = await asyncio.to_thread(
            slice_audio, segments, asset_file_path
        )
    elif stream_type.lower() == "video":
        # Slice video file based on speech segments
        speech_segment_files = await asyncio.to_thread(
            slice_audio, segments, asset_file_path
        )

    # Upload segment files to gcp and create data dict
    for segment in speech_segment_files:  
        local_file_path = segment["audio_file"]
        file_name = extract_file_name(local_file_path)
        file_size = calc_file_size(local_file_path)
        
        # Destination file path construction
        recording_date = data.get("timestamp")
        dest_file_path = (
            f"tv/{data.get('source').get('name')}/{recording_date}/{file_name}" 
            if stream_type.lower() == "video" 
            else f"radio/{data.get('source').get('name')}/{recording_date}/{file_name}"          
        )
        # Upload to GCP
        await asyncio.to_thread(upload, data.get("gcp_bucket"), local_file_path, dest_file_path)
        
        if stream_type == "video":
            # Extract sound track of video segment and upload to GCS
            soundtrack_file_path = await asyncio.to_thread(extract_audio_from_video, asset_file_path)
            soundtrack_file_name = extract_file_name(soundtrack_file_path)
            soundtrack_dest_file_path = f"tv/{data.get('source').get('name')}/{recording_date}/{soundtrack_file_name}"          
            await asyncio.to_thread(upload, data.get("gcp_bucket"), soundtrack_file_path, soundtrack_dest_file_path)
            await asyncio.to_thread(delete_file, soundtrack_file_path)

        # Delete master file
        await asyncio.to_thread(delete_file, local_file_path)
        
        # Delete master blob
        await asyncio.to_thread(delete_blob, data.get("gcp_bucket"), data.get("gcp_blob"))
        
        # Create elastic search data
        data.pop("stream_id")
        index = data.pop("_index", None)
        data["duration"] = segment["duration"]
        data["gcp_blob"] = dest_file_path
        data["file_size"] = file_size

        processed_segments.append({ "_index": index, "data": data})
    
    return processed_segments
    
async def _segment_media(data: list[dict]):
    try:
        # extract gcp_blob paths from data
        payload = [
            item.get("gcp_blob")
            if item.get("stream_type", "").lower() == "audio"
            else replace_mp4_with_mp3(item.get("gcp_blob"))
            for item in data
        ]

        logger.info(f"Sending batch request to {SEGMENTATION_GPU_URL}/vad/batch for speech and music segmentation")
        
        # Make async POST request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SEGMENTATION_GPU_URL}/vad/batch",
                json=payload
            )        
        response.raise_for_status()

        subfolder_check(f"{os.getcwd()}/o2-files")
        results = []

        for idx, result in enumerate(response.json()):
            # download master file
            file_name = extract_file_name(data[idx].get("gcp_blob"))
            asset_file_path = f"{os.getcwd()}/o2-files/{file_name}"
            await asyncio.to_thread(download_file, data[idx].get("gcp_bucket"), data[idx].get("gcp_blob"), asset_file_path)

            processed_segments = await _process_segmet(
                data=data[idx],
                segments=result.get("speech"),
                asset_file_path=asset_file_path
            )
            
            results.extend(processed_segments)
            logger.info(f'segment analysis for {data[idx]["source"]["name"]}: {processed_segments}')

        return results

    except httpx.RequestError as e:
        logger.error(f"Request error during batch audience: {e}")
        raise
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during audience: {e}")
        raise

async def _save_segments(segments: list[dict]):
    actions = [
        {
            "_op_type": "index",
            "_index": segment.get("_index"),
            "_id": str(uuid.uuid4()),
            "doc": segment.get("data")
        }
        for segment in segments
    ]
    save_bulk(actions)

    return actions

@segmentation_broker.subscriber(stream=StreamSub(
        "audiovisual:segmentation_stream",
        group="audiovisual:segmentation_group",
        consumer="segmentation_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_segmentation_worker_1(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        segments = await _segment_media(data=data)
        results = await _save_segments(segments=segments)

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await segmentation_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:audience_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()

@segmentation_broker.subscriber(stream=StreamSub(
        "audiovisual:segmentation_stream",
        group="audiovisual:segmentation_group",
        consumer="segmentation_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_segmentation_worker_2(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        segments = await _segment_media(data=data)
        results = await _save_segments(segments=segments)

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await segmentation_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:audience_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()

@segmentation_broker.subscriber(stream=StreamSub(
        "audiovisual:segmentation_stream",
        group="audiovisual:segmentation_group",
        consumer="segmentation_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_segmentation_worker_3(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        segments = await _segment_media(data=data)
        results = await _save_segments(segments=segments)

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await segmentation_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:audience_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()