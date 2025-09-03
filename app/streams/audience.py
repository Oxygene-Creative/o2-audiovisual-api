import time
from app.core.redis import redis_broker as audience_broker
from app.streams.segmentation import replace_mp4_with_mp3
from faststream.redis import StreamSub, Pipeline
from faststream.redis.annotations import RedisMessage, Redis
import os
import logging
import httpx
from app.core.es import fetch_stream_data, update_stream_data


# Configure the logger
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Create logger instance
logger = logging.getLogger(__name__)

SEGMENTATION_GPU_URL = os.getenv("SEGMENTATION_GPU_URL", "").strip()

async def _process_audience(data: list[dict]):
    try:
        # Start timing
        start_time = time.time()
        data = await fetch_stream_data(data)
        # extract gcp_blob paths from data
        payload = [
            { "bucket": item.get("_source", {}).get("gcp_bucket"), "blob": item.get("_source", {}).get("gcp_blob") }
            if item.get("_index", "").startswith("radio_")
            else { "bucket": item.get("_source", {}).get("gcp_bucket"), "blob": replace_mp4_with_mp3(item.get("_source", {}).get("gcp_blob")) }
            for item in data
        ]

        logger.info(f"Sending batch request to {SEGMENTATION_GPU_URL}/vad/batch for audience analysis")
        
        # Make async POST request using httpx
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{SEGMENTATION_GPU_URL}/vad/batch",
                json=payload
            )        
        response.raise_for_status()
        
        # transform voice activity
        for idx, result in enumerate(response.json()):
            activity = {item["labels"]: item["duration"] for item in result.get("activity")}   

            data[idx]["_updates"]["audience"] = [
                { "label": "male", "score": activity.get("male", 0.0) },
                { "label": "female", "score": activity.get("female", 0.0) }
            ]

            end_time = time.time()
            time_taken = end_time - start_time
            logger.info(f'audience analysis for {data[idx]["_source"]["source"]["name"]} completed in {time_taken}s')

        return data

    except httpx.RequestError as e:
        logger.error(f"Request error during batch audience analysis: {e}")
        raise
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during audience analysis: {e}")
        raise

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_1(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)
        
        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )
        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_2(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_3(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_4",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_4(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)
        
        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )
        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_5",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_5(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_6",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_6(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_7",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_7(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)
        
        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )
        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_8",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_8(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_9",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_9(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_10",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_10(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_11",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_11(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)
        
        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )
        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_12",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_12(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

@audience_broker.subscriber(stream=StreamSub(
        "audiovisual:audience_stream",
        group="audiovisual:audience_group",
        consumer="audience_worker_12",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_audience_worker_12(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        audience_results = await _process_audience(data)

        # update stream data in database and 
        results = await update_stream_data(
            data=audience_results, 
            status={"complete": False, "step": "ASR" })

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 

        await msg.ack(redis)
    except Exception as e:
        await msg.nack()

