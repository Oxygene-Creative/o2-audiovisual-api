from app.core.redis import redis_router as audience_broker
from faststream.redis import StreamSub, Pipeline
from faststream.redis.annotations import RedisMessage, Redis
import os
import logging
import httpx

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
        # extract gcp_blob paths from data
        payload = [item.get("gcp_blob", None) for item in data]

        logger.info(f"Sending batch request to {SEGMENTATION_GPU_URL}/audience/batch for voice activity detection")
        
        # Make async POST request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SEGMENTATION_GPU_URL}/vad/batch",
                json=payload
            )        
        response.raise_for_status()
        
        # transform voice activity
        for idx, result in enumerate(response.json()):            
            data[idx]["audience"] = [
                { "label": "male", "score": result.get("male", 0.0) },
                { "label": "female", "score": result.get("female", 0.0) }
            ]
            logger.info(f"audience analysis for {data[idx]["source"]["name"]}: {data[idx]["audience"]}")

        return data

    except httpx.RequestError as e:
        logger.error(f"Request error during batch audience: {e}")
        raise
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during audience: {e}")
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
        results = await _process_audience(data)
        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                result,
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
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
        results = await _process_audience(data)
        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                result,
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
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
        results = await _process_audience(data)
        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await audience_broker.publish(
                result,
                stream="audiovisual:asr_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()