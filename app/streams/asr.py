import asyncio
import time

from fastapi import Depends
from app.analyzers.transcription import post_process_transcription, transcribe
from app.core.gcp import delete_blob
from app.core.redis import redis_broker as asr_broker
from faststream.redis import StreamSub, Pipeline
from faststream.redis.annotations import RedisMessage, Redis
from app.core.es import fetch_stream_data, update_stream_data
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
            if item.get("_index", "").startswith == "tv":
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

        # populate updates
        for idx, result in enumerate(response):   
            if not result.get("success"):
                data[idx]["_updates"]["raw_text"] = ""
                data[idx]["_updates"]["language"] = ""
                data[idx]["_updates"]["language_score"] = 0.0
                continue

            raw_text = result.get("transcription").get("raw_text","")
            if len(raw_text.split()) > 10:
                processed_transcript = await post_process_transcription(raw_text.split())
            else:
                processed_transcript = raw_text

            data[idx]["_updates"]["raw_text"] = processed_transcript
            data[idx]["_updates"]["language"] = result.get("transcription").get("language","")
            data[idx]["_updates"]["language_score"] = result.get("transcription").get("language_score",0.0)

            end_time = time.time()
            time_taken = end_time - start_time

            logger.info(f'asr analysis for {data[idx]["_source"].get("source", {}).get("name")} completed in {time_taken}s')

        # cleanup gcs: delete soundtrack of video
        for item in data:
            if item.get("_index", "").startswith == "tv":
                await asyncio.to_thread(
                    delete_blob, 
                    item.get("_source").get("gcp_bucket"), 
                    item.get("_source", {}).get("gcp_blob").rsplit('.', 1)[0] + ".mp3"
                )

        return data

    except Exception as e:
        logger.error(f"An unexpected error occurred during asr analysis: {e}")
        raise

@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="audiovisual:asr_group",
        consumer="asr_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_1(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        asr_results = await _process_asr(data)
        # update stream data in database 
        results = await update_stream_data(
            data=asr_results, 
            status={"complete": False, "step": "NLP" })

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await asr_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:nlp_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()

@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="audiovisual:asr_group",
        consumer="asr_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_2(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        asr_results = await _process_asr(data)
        # update stream data in database 
        results = await update_stream_data(
            data=asr_results, 
            status={"complete": False, "step": "NLP" })

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await asr_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:nlp_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()

@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="audiovisual:asr_group",
        consumer="asr_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_3(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        asr_results = await _process_asr(data)
        # update stream data in database 
        results = await update_stream_data(
            data=asr_results, 
            status={"complete": False, "step": "NLP" })

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await asr_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:nlp_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()