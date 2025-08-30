import asyncio
import time
from app.analyzers.transcription import post_process_transcription, transcribe
from app.core.gcp import delete_blob
from app.core.redis import redis_router as asr_broker
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
        data = fetch_stream_data(data)

        batch_payloads = []
        for item in data:
            if item.get("_index", "").startswith == "tv":
                # use video's sound track
                soundtrack = item.get("_source", {}).get("gcp_blob").rsplit('.', 1)[0] + ".mp3"
                batch_payloads.append(soundtrack)
            else:
                batch_payloads.append(item.get("_source", {}).get("gcp_blob"))

        batch_payloads = [item.get("_source", {}).get("gcp_blob", None) for item in data]
        response = await transcribe(gcs_blobs=batch_payloads)

        # populate updates
        for idx, result in enumerate(response):   
            await asyncio.sleep(0.5)     

            raw_text = result.get("raw_text","")
            word_count = len(raw_text.split())
            if raw_text.strip() and word_count > 5:
                processed_transcript = await post_process_transcription(raw_text)
            else:
                processed_transcript = raw_text

            data[idx]["_updates"]["raw_text"] = processed_transcript
            data[idx]["_updates"]["language"] = result.get("language","")
            data[idx]["_updates"]["language_score"] = result.get("language_score",0.0)

            end_time = time.time()
            time_taken = end_time - start_time

            logger.info(f"asr analysis for {data[idx]["_source"]["source"]["name"]} completed in {time_taken}s")

        
        # cleanup gcs, delete soundtrack of video
        for item in data:
            if item.get("_index", "").startswith == "tv":
                await asyncio.to_thread(
                    delete_blob, 
                    item.get("_source").get("gcp_bucket"), 
                    item.get("_source").get("gcp_blob")
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