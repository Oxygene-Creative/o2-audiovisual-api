import asyncio
import time

from fastapi import Depends
from app.analyzers.transcription import post_process_transcription, transcribe
from app.core.gcp import delete_blob
from app.core.redis import redis_broker as asr_broker
from faststream.redis import StreamSub, Pipeline
from faststream.redis.annotations import RedisMessage, Redis
from app.core.es import fetch_stream_data, update_stream_data
from app.core.redis_keys import ASR_GROUP, ASR_STREAM, NLP_STREAM
import logging

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Create logger instance
logger = logging.getLogger(__name__)


async def _process_asr(data: list[dict]):
    try:
        # Start timing
        start_time = time.time()
        data = await fetch_stream_data(data)

        batch_payloads = []
        for item in data:
            if item.get("_index", "").startswith("tv_"):
                # use video's sound track
                batch_payloads.append({
                    "bucket": item.get("_source", {}).get("gcp_bucket", None),
                    "blob": item.get("_source", {}).get("gcp_blob").rsplit('.', 1)[0] + ".mp3"
                })
            else:
                batch_payloads.append({
                    "bucket": item.get("_source", {}).get("gcp_bucket", None),
                    "blob": item.get("_source", {}).get("gcp_blob", None)
                })
        response = await transcribe(data=batch_payloads)

        if isinstance(response, dict):
            logger.error("ASR batch returned error payload: %s", response)
            response = [response for _ in data]
        elif not isinstance(response, list):
            logger.error(
                "ASR batch returned unexpected response type: %s",
                type(response).__name__,
            )
            response = []

        if len(response) < len(data):
            logger.warning(
                "ASR response/data size mismatch: response=%s data=%s",
                len(response),
                len(data),
            )
            response = response + [{} for _ in range(len(data) - len(response))]

        # populate updates
        for idx, _ in enumerate(data):
            result = response[idx] if idx < len(response) else {}
            if not isinstance(result, dict):
                logger.warning(
                    "ASR item response type invalid at idx=%s type=%s",
                    idx,
                    type(result).__name__,
                )
                result = {}

            if not result.get("success"):
                data[idx]["_updates"]["raw_text"] = ""
                data[idx]["_updates"]["language"] = ""
                data[idx]["_updates"]["language_score"] = 0.0
                continue

            transcription = result.get("transcription")
            if not isinstance(transcription, dict):
                logger.warning(
                    "ASR transcription payload invalid at idx=%s type=%s",
                    idx,
                    type(transcription).__name__,
                )
                transcription = {}

            raw_text = transcription.get("raw_text", "")
            if len(raw_text.split()) > 10:
                processed_transcript = await post_process_transcription(raw_text)
            else:
                processed_transcript = raw_text

            data[idx]["_updates"]["raw_text"] = processed_transcript
            data[idx]["_updates"]["language"] = transcription.get("language", "")
            data[idx]["_updates"]["language_score"] = transcription.get(
                "language_score",
                0.0,
            )

            end_time = time.time()
            time_taken = end_time - start_time

            logger.info(
                f'asr analysis for {data[idx]["_source"].get("source", {}).get("name")} completed in {time_taken}s')

        # cleanup gcs: delete soundtrack of video
        for item in data:
            if item.get("_index", "").startswith("tv_"):
                await asyncio.to_thread(
                    delete_blob,
                    item.get("_source").get("gcp_bucket"),
                    item.get("_source", {}).get(
                        "gcp_blob").rsplit('.', 1)[0] + ".mp3"
                )

        return data

    except Exception as e:
        logger.error(f"An unexpected error occurred during asr analysis: {e}")
        raise


async def _worker_handler(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    success = False
    try:
        asr_results = await _process_asr(data)
        # update stream data in database
        results = await update_stream_data(
            data=asr_results,
            status={"complete": False, "step": "NLP"})

        # batch publish to next stage
        for result in results:
            await asr_broker.publish(
                {"_index": result.get("_index"), "_id": result.get("_id")},
                stream=NLP_STREAM,
                pipeline=pipe,
            )

        await pipe.execute()
        success = True
    except Exception:
        logger.exception("ASR worker failed; message will be nacked")
    finally:
        if success:
            await msg.ack(redis)
        else:
            await msg.nack()


@asr_broker.subscriber(stream=StreamSub(
    ASR_STREAM,
    group=ASR_GROUP,
    consumer="asr_worker_1",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_asr_worker_1(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)


@asr_broker.subscriber(stream=StreamSub(
    ASR_STREAM,
    group=ASR_GROUP,
    consumer="asr_worker_2",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_asr_worker_2(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)


@asr_broker.subscriber(stream=StreamSub(
    ASR_STREAM,
    group=ASR_GROUP,
    consumer="asr_worker_3",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_asr_worker_3(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)


@asr_broker.subscriber(stream=StreamSub(
    ASR_STREAM,
    group=ASR_GROUP,
    consumer="asr_worker_4",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_asr_worker_4(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)


@asr_broker.subscriber(stream=StreamSub(
    ASR_STREAM,
    group=ASR_GROUP,
    consumer="asr_worker_5",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_asr_worker_5(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)


@asr_broker.subscriber(stream=StreamSub(
    ASR_STREAM,
    group=ASR_GROUP,
    consumer="asr_worker_6",
    batch=True,
    max_records=10,
    polling_interval=100,
)
)
async def process_asr_worker_6(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)
