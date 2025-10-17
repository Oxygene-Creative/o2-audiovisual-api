from utils.gcp import upload
from utils.media_processing import convert_video_format
from utils.redis import redis_broker as media_processing_broker, worker_1_busy_lock, worker_2_busy_lock, worker_3_busy_lock
from faststream.redis import StreamSub, Pipeline
from faststream.redis.annotations import RedisMessage, Redis
import logging
import httpx
import os
from datetime import datetime
import time
import subprocess

# Configure the logger
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Create logger instance
logger = logging.getLogger(__name__)

AUDIOVISUAL_API_URI = os.getenv("AUDIOVISUAL_API_URI", "https://monitorapi.oxygenehosting.com/api/av")

async def _is_video_corrupted(file_path):
    try:
        # Run FFmpeg on the file and check for integrity
        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", file_path, "-f", "null", "-"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        return "Error" in result.stderr.decode("utf-8")
    except Exception as e:
        print(f"Error checking file '{file_path}': {e}")
        return True

async def _ingest_video(upload: dict):
    try:        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{AUDIOVISUAL_API_URI}/ingestion", json=upload)
            
            # Check response status code
            if response.status_code == 200:
                # Parse JSON response if needed
                print("video ingested")
                return response.json()
            else:
                raise Exception(f"Failed to start video analysis: {response.status_code} - {response.text}")
                
    except httpx.RequestError as e:
        raise Exception(f"Error ingesting video to data streams: {str(e)}")

async def _process_media(data: dict):
    try:
        # Start timing
        start_time = time.time() 

        path = data.get("path", None)
        stream_name = data.get("stream_name", "")
        stream_id = data.get("stream_id", "")
        timestamp = data.get("timestamp")

        # check if video recording is legit
        if await _is_video_corrupted(path):
            print("corrupt file")
            if os.path.exists(path):
                os.unlink(path)
            return

        # Use the new function for conversion
        output_path = convert_video_format(path, "ts", "mp4")
        print("video converted")
        
        # Parse into datetime object
        dt = datetime.strptime(data.get("timestamp", ""), "%Y-%m-%dT%H:%M:%S")

        # Format outputs
        recording_date = dt.strftime("%Y-%m-%d")
        datetime_str = dt.strftime("%Y%m%d_%H%M")        
        
        gcp_path = f'tv/{stream_name}/{recording_date}/{stream_name}_{datetime_str}.mp4'

        # Upload to GCP
        bucket_name = "audiovisual-streams"
        upload(bucket_name, output_path, gcp_path)
        print("video uploaded to gcp")

        upload_file_info = {
            "stream_id": stream_id,
            "stream_name": stream_name,
            "bucket": bucket_name,
            "blob": gcp_path,
            "media_type": "video",
            "timestamp_str": timestamp
        }

        # Start video analysis
        await _ingest_video(upload=upload_file_info)

        end_time = time.time()
        time_taken = end_time - start_time
        logger.info(f'Media processing for {stream_name} ar {timestamp} done in {time_taken}s')
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during media processing: {e}")
        raise

    finally:
        # Clean up files
        if os.path.exists(data.get("path", None)):
            os.unlink(data.get("path", None))

        if os.path.exists(output_path):
            os.unlink(output_path)

async def _worker_handler(data: dict, msg: RedisMessage, redis: Redis, pipe: Pipeline):
    try:
        await _process_media(data=data)
        # acknowledge message
        await msg.ack(redis)
    except Exception as e:
        logger.error(f"nack called, error: {e}")
        await msg.nack()

@media_processing_broker.subscriber(stream=StreamSub(
        "media_srv:media_processing",
        group="media_srv:media_processing_group",
        consumer="media_processing_1",
        polling_interval=100,
    )
)
async def process_media_worker_1(data: dict, msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    async with worker_1_busy_lock:
        await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)

@media_processing_broker.subscriber(stream=StreamSub(
        "media_srv:media_processing",
        group="media_srv:media_processing_group",
        consumer="media_processing_2",
        polling_interval=100,
    )
)
async def process_media_worker_2(data: dict, msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    async with worker_2_busy_lock:
        await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)

@media_processing_broker.subscriber(stream=StreamSub(
        "media_srv:media_processing",
        group="media_srv:media_processing_group",
        consumer="media_processing_3",
        polling_interval=100,
    )
)
async def process_media_worker_3(data: dict, msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    async with worker_3_busy_lock:
        await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)
