import asyncio
import uuid
from app.core.es import save_bulk
from app.core.files import calc_file_size, delete_file, extract_file_name, subfolder_check
from app.core.gcp import blob_exists, download_file, upload
from app.core.media_processing import extract_audio_from_video, slice_audio, slice_video
from app.core.replay_log import write_replay_candidate
from app.core.redis import redis_broker as segmentation_broker, worker_1_busy_lock, worker_2_busy_lock, worker_3_busy_lock
from faststream.redis import StreamSub, Pipeline
from faststream.redis.annotations import RedisMessage, Redis
import logging
import httpx
import os
from datetime import datetime
import time
from google.api_core.exceptions import NotFound, PreconditionFailed
from app.core.redis_keys import (
    AUDIENCE_STREAM,
    SEGMENTATION_GROUP,
    SEGMENTATION_STREAM,
)

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Create logger instance
logger = logging.getLogger(__name__)

SEGMENTATION_GPU_URL = os.getenv("SEGMENTATION_GPU_URL", "").strip()
SEGMENTATION_PREP_TIMEOUT_SECONDS = int(os.getenv("SEGMENTATION_PREP_TIMEOUT_SECONDS", "300"))
SEGMENTATION_ITEM_TIMEOUT_SECONDS = int(os.getenv("SEGMENTATION_ITEM_TIMEOUT_SECONDS", "900"))


def replace_mp4_with_mp3(blob_path: str) -> str:
    if blob_path and blob_path.endswith(".mp4"):
        # Replace the extension
        return blob_path.rsplit(".", 1)[0] + ".mp3"
    else:
        raise ValueError("The given blob path does not have an .mp4 extension")


async def ensure_audio_blob(
    bucket: str,
    video_blob: str,
    source_generation: str | None = None,
) -> str:
    audio_blob = replace_mp4_with_mp3(video_blob)
    if blob_exists(bucket, audio_blob):
        return audio_blob

    file_name = extract_file_name(video_blob)
    local_video_path = f"{os.getcwd()}/o2-files/{file_name}"
    await asyncio.to_thread(
        download_file,
        bucket,
        video_blob,
        local_video_path,
        source_generation,
    )

    audio_path = await extract_audio_from_video(local_video_path)
    await asyncio.to_thread(upload, bucket, audio_path, audio_blob)

    await asyncio.to_thread(delete_file, audio_path)
    await asyncio.to_thread(delete_file, local_video_path)

    return audio_blob


async def _process_segmet(data: dict, segments: list, asset_file_path: str) -> list:
    processed_segments = []
    segment_cleanup_paths = []
    audio_cleanup_paths = []
    speech_segment_files = []

    stream_type = data.pop("stream_type", None)
    if stream_type and stream_type.lower() == "audio":
        # Slice audio file based on speech segments
        speech_segment_files = await slice_audio(segments, asset_file_path)

    elif stream_type and stream_type.lower() == "video":
        # Slice video file based on speech segments
        video_tasks = [
            slice_video(asset_file_path, segment['start'], segment['stop']) for segment in segments
        ]
        speech_segment_files = await asyncio.gather(*video_tasks)
    else:
        logger.warning("Skipping segment processing due to unsupported stream_type=%s", stream_type)
        await asyncio.to_thread(delete_file, asset_file_path)
        return []

    # Upload segment files to gcp and create data dict
    for ix, segment in enumerate(speech_segment_files):
        # create local copy
        segment_data = data.copy()
        local_file_path = segment["file_path"]
        file_name = extract_file_name(local_file_path)
        file_size = calc_file_size(local_file_path)
        if not os.path.exists(local_file_path):
            logger.warning(
                "Segment file missing before upload: %s", local_file_path)
            continue

        # Destination file path construction
        recording_date = datetime.fromisoformat(
            segment_data.get("timestamp")).strftime("%Y-%m-%d")

        dest_file_path = (
            f"tv/{segment_data.get('source').get('name')}/{recording_date}/{file_name}"
            if stream_type.lower() == "video"
            else f"radio/{segment_data.get('source').get('name')}/{recording_date}/{file_name}"
        )
        # Upload to GCP
        await asyncio.to_thread(upload, segment_data.get("gcp_bucket"), local_file_path, dest_file_path)

        if stream_type == "video":
            # Extract sound track of video segment and upload to GCS
            soundtrack_file_path = await extract_audio_from_video(local_file_path)
            soundtrack_file_name = extract_file_name(soundtrack_file_path)
            soundtrack_dest_file_path = f"tv/{data.get('source').get('name')}/{recording_date}/{soundtrack_file_name}"
            await asyncio.to_thread(upload, data.get("gcp_bucket"), soundtrack_file_path, soundtrack_dest_file_path)
            audio_cleanup_paths.append(soundtrack_file_path)

        segment_cleanup_paths.append(local_file_path)

        # Create elastic search data
        segment_data["duration"] = segment["duration"]
        segment_data["gcp_blob"] = dest_file_path
        segment_data["file_size"] = file_size

        processed_segments.append(
            {"_index": segment_data.get('_index'), "data": segment_data})

    for audio_path in audio_cleanup_paths:
        await asyncio.to_thread(delete_file, audio_path)

    for segment_path in segment_cleanup_paths:
        await asyncio.to_thread(delete_file, segment_path)

    # Delete local master file
    await asyncio.to_thread(delete_file, asset_file_path)

    return processed_segments


async def _segment_media(data: list[dict]):
    try:
        # Start timing
        start_time = time.time()
        logger.info(
            "Segmentation batch received: size=%s ids=%s",
            len(data),
            [item.get("doc_id") for item in data],
        )
        # Build payload and keep item mapping aligned with VAD response.
        prepared_items = []
        for item in data:
            if item.get("stream_type", "").lower() == "audio":
                if not blob_exists(item.get("gcp_bucket"), item.get("gcp_blob")):
                    replay_log_path = write_replay_candidate(
                        {
                            "reason": "missing_source_audio_blob",
                            "doc_id": item.get("doc_id"),
                            "bucket": item.get("gcp_bucket"),
                            "blob": item.get("gcp_blob"),
                            "stream_type": item.get("stream_type"),
                        }
                    )
                    logger.warning(
                        "Skipping doc_id=%s: source audio blob missing bucket=%s blob=%s replay_log=%s",
                        item.get("doc_id"),
                        item.get("gcp_bucket"),
                        item.get("gcp_blob"),
                        replay_log_path,
                    )
                    continue
                prepared_items.append(
                    {
                        "item": item,
                        "payload": {
                            "bucket": item.get("gcp_bucket"),
                            "blob": item.get("gcp_blob"),
                        },
                    }
                )
                continue

            if item.get("stream_type", "").lower() == "video":
                try:
                    audio_blob = await asyncio.wait_for(
                        ensure_audio_blob(
                            item.get("gcp_bucket"),
                            item.get("gcp_blob"),
                            item.get("source_blob_generation"),
                        ),
                        timeout=SEGMENTATION_PREP_TIMEOUT_SECONDS,
                    )
                except NotFound as not_found_error:
                    replay_log_path = write_replay_candidate(
                        {
                            "reason": "missing_source_video_blob",
                            "doc_id": item.get("doc_id"),
                            "bucket": item.get("gcp_bucket"),
                            "blob": item.get("gcp_blob"),
                            "stream_type": item.get("stream_type"),
                            "error": str(not_found_error),
                            "source_blob_generation": item.get("source_blob_generation"),
                        }
                    )
                    logger.warning(
                        "Skipping doc_id=%s: source video blob missing during prep. bucket=%s blob=%s error=%s replay_log=%s",
                        item.get("doc_id"),
                        item.get("gcp_bucket"),
                        item.get("gcp_blob"),
                        not_found_error,
                        replay_log_path,
                    )
                    continue
                except PreconditionFailed as precondition_error:
                    replay_log_path = write_replay_candidate(
                        {
                            "reason": "source_blob_generation_mismatch",
                            "doc_id": item.get("doc_id"),
                            "bucket": item.get("gcp_bucket"),
                            "blob": item.get("gcp_blob"),
                            "stream_type": item.get("stream_type"),
                            "error": str(precondition_error),
                            "source_blob_generation": item.get("source_blob_generation"),
                        }
                    )
                    logger.warning(
                        "Skipping doc_id=%s: source generation mismatch during prep. bucket=%s blob=%s generation=%s error=%s replay_log=%s",
                        item.get("doc_id"),
                        item.get("gcp_bucket"),
                        item.get("gcp_blob"),
                        item.get("source_blob_generation"),
                        precondition_error,
                        replay_log_path,
                    )
                    continue
                except Exception as prep_error:
                    logger.exception(
                        "Skipping doc_id=%s during payload prep. bucket=%s blob=%s error=%s",
                        item.get("doc_id"),
                        item.get("gcp_bucket"),
                        item.get("gcp_blob"),
                        prep_error,
                    )
                    continue

                prepared_items.append(
                    {
                        "item": item,
                        "payload": {
                            "bucket": item.get("gcp_bucket"),
                            "blob": audio_blob,
                        },
                    }
                )

        payload = [entry["payload"] for entry in prepared_items]

        if not payload:
            logger.warning("Segmentation batch skipped: no valid payload items after preparation")
            return []

        logger.info(
            "Segmentation payload prepared: size=%s payload=%s",
            len(payload),
            payload,
        )

        logger.info(
            f"Sending batch request to {SEGMENTATION_GPU_URL}/vad/batch for speech and music segmentation")

        # Make async POST request using httpx
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{SEGMENTATION_GPU_URL}/vad/batch",
                json=payload
            )
        response.raise_for_status()
        vad_results = response.json()
        if not isinstance(vad_results, list):
            logger.error(
                "Unexpected VAD response shape. Expected list, got %s payload=%s",
                type(vad_results).__name__,
                vad_results,
            )
            raise ValueError("Invalid VAD batch response shape")
        logger.info(
            "VAD response received: items=%s status_code=%s",
            len(vad_results) if isinstance(vad_results, list) else 0,
            response.status_code,
        )
        subfolder_check(f"{os.getcwd()}/o2-files")
        results = []

        for idx, result in enumerate(vad_results):
            if idx >= len(prepared_items):
                logger.warning(
                    "VAD result/prepared_items size mismatch at idx=%s: prepared_size=%s",
                    idx,
                    len(prepared_items),
                )
                break

            current_item = prepared_items[idx]["item"]
            current_payload = prepared_items[idx]["payload"]

            if not isinstance(result, dict):
                logger.warning(
                    "Skipping item idx=%s doc_id=%s: invalid result type=%s",
                    idx,
                    current_item.get("doc_id"),
                    type(result).__name__,
                )
                continue

            if not result.get("success", False):
                logger.warning(
                    "Skipping item idx=%s doc_id=%s: success flag false. "
                    "bucket=%s blob=%s error=%s result_keys=%s",
                    idx,
                    current_item.get("doc_id"),
                    current_payload.get("bucket"),
                    current_payload.get("blob"),
                    result.get("error"),
                    list(result.keys()) if isinstance(result, dict) else type(result),
                )
                continue

            # only speech stuff
            activity_list = result.get("activity") or []
            speech_segments = result.get("speech") or []
            activity = {item["labels"]: item["duration"]
                        for item in activity_list if isinstance(item, dict)}

            logger.info(
                "VAD item summary idx=%s doc_id=%s success=%s speech_segments=%s activity=%s",
                idx,
                current_item.get("doc_id"),
                result.get("success", False),
                len(speech_segments),
                activity,
            )

            if activity.get("male") in [0, None] and activity.get("female") in [0, None]:
                logger.warning(
                    "Skipping item idx=%s doc_id=%s: male and female durations are empty/zero",
                    idx,
                    current_item.get("doc_id"),
                )
                continue

            if not speech_segments:
                logger.warning(
                    "Skipping item idx=%s doc_id=%s: no speech segments returned by VAD",
                    idx,
                    current_item.get("doc_id"),
                )
                continue

            # download master file
            file_name = extract_file_name(current_item.get("gcp_blob"))
            asset_file_path = f"{os.getcwd()}/o2-files/{file_name}"
            try:
                await asyncio.to_thread(
                    download_file,
                    current_item.get("gcp_bucket"),
                    current_item.get("gcp_blob"),
                    asset_file_path,
                    current_item.get("source_blob_generation"),
                )

                processed_segments = await asyncio.wait_for(
                    _process_segmet(
                        data=current_item,
                        segments=speech_segments,
                        asset_file_path=asset_file_path,
                    ),
                    timeout=SEGMENTATION_ITEM_TIMEOUT_SECONDS,
                )
            except (NotFound, PreconditionFailed) as download_error:
                replay_log_path = write_replay_candidate(
                    {
                        "reason": "source_master_download_failed",
                        "doc_id": current_item.get("doc_id"),
                        "bucket": current_item.get("gcp_bucket"),
                        "blob": current_item.get("gcp_blob"),
                        "stream_type": current_item.get("stream_type"),
                        "error": str(download_error),
                        "source_blob_generation": current_item.get("source_blob_generation"),
                    }
                )
                logger.warning(
                    "Skipping doc_id=%s: source download failed bucket=%s blob=%s generation=%s error=%s replay_log=%s",
                    current_item.get("doc_id"),
                    current_item.get("gcp_bucket"),
                    current_item.get("gcp_blob"),
                    current_item.get("source_blob_generation"),
                    download_error,
                    replay_log_path,
                )
                continue
            except Exception as process_error:
                replay_log_path = write_replay_candidate(
                    {
                        "reason": "segmentation_item_processing_failed",
                        "doc_id": current_item.get("doc_id"),
                        "bucket": current_item.get("gcp_bucket"),
                        "blob": current_item.get("gcp_blob"),
                        "stream_type": current_item.get("stream_type"),
                        "error": str(process_error),
                    }
                )
                logger.exception(
                    "Skipping failed segmentation item idx=%s doc_id=%s error=%s replay_log=%s",
                    idx,
                    current_item.get("doc_id"),
                    process_error,
                    replay_log_path,
                )
                await asyncio.to_thread(delete_file, asset_file_path)
                continue

            if not processed_segments:
                logger.warning(
                    "No processed segments created for idx=%s doc_id=%s",
                    idx,
                    current_item.get("doc_id"),
                )

            end_time = time.time()
            time_taken = end_time - start_time
            results.extend(processed_segments)
            logger.info(
                f'segment analysis for {current_item["source"]["name"]} done in {time_taken}s')

        logger.info("Segmentation batch complete: total_segment_docs=%s", len(results))

        return results

    except httpx.RequestError as e:
        logger.error(f"Request error during batch segmentation: {e}")
        raise

    except Exception as e:
        logger.error(f"An unexpected error occurred during segmentation: {e}")
        raise


async def _save_segments(segments: list[dict]):
    actions = []
    for segment in segments:
        action = {
            "_op_type": "index",
            "_index": segment.get("_index"),
            "_id": str(uuid.uuid4()),
        }

        action.update(segment.get("data"))
        action.update({"status": {"step": "AUDIENCE", "complete": False}})
        actions.append(action)

    if not actions:
        logger.warning("No segment actions to write to Elasticsearch")
        return actions

    save_bulk(actions)
    logger.info("Elasticsearch bulk index complete: actions=%s", len(actions))

    # Create Recording in Graphql

    return actions


async def _worker_handler(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    try:
        logger.info(
            "Segmentation worker handling batch: size=%s ids=%s",
            len(data),
            [item.get("doc_id") for item in data],
        )
        segments = await _segment_media(data=data)
        results = await _save_segments(segments=segments)
        logger.info(
            "Segmentation worker stage output: segments=%s es_actions=%s",
            len(segments),
            len(results),
        )

        # batch publish to next stage
        for result in results:
            await segmentation_broker.publish(
                {"_index": result.get("_index"), "_id": result.get("_id")},
                stream=AUDIENCE_STREAM,
                pipeline=pipe,
            )

        await pipe.execute()
        logger.info("Published to audience stream: count=%s", len(results))
        # acknowledge message
        await msg.ack(redis)
        logger.info("Segmentation batch acked successfully")
    except Exception as e:
        logger.error(f"nack called, error: {e}")
        await msg.nack()


@segmentation_broker.subscriber(stream=StreamSub(
    SEGMENTATION_STREAM,
    group=SEGMENTATION_GROUP,
    consumer="segmentation_worker_1",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_segmentation_worker_1(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    async with worker_1_busy_lock:
        await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)


@segmentation_broker.subscriber(stream=StreamSub(
    SEGMENTATION_STREAM,
    group=SEGMENTATION_GROUP,
    consumer="segmentation_worker_2",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_segmentation_worker_2(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    async with worker_2_busy_lock:
        await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)


@segmentation_broker.subscriber(stream=StreamSub(
    SEGMENTATION_STREAM,
    group=SEGMENTATION_GROUP,
    consumer="segmentation_worker_3",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_segmentation_worker_3(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    async with worker_3_busy_lock:
        await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)
