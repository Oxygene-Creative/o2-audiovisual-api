import asyncio
import json
import time
from app.analyzers.llm import llm_transcript_analysis
from app.core.redis import redis_broker as llm_broker
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

async def _process_llm(data: list[dict]):
    try:
        # Start timing
        start_time = time.time() 
        data = await fetch_stream_data(data)

        # create tasks for threading
        tasks = [
            llm_transcript_analysis(item.get("_source", {}).get("raw_text", "")) 
            for item in data
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)

        for idx, item in enumerate(results):

            if item is None:
                continue
            
            llm_analysis_json = item.model_dump_json()
            llm_analysis_dict = json.loads(llm_analysis_json)
            data[idx]["_updates"].update(llm_analysis_dict)
            data[idx]["_updates"]["creator"] = llm_analysis_dict.get("show_metadata", {}).get("host", "")
            data[idx]["_updates"]["title"] = llm_analysis_dict.get("show_metadata", {}).get("program_name", "")

            # End timing
            end_time = time.time()
            time_taken = end_time - start_time

            logger.info(f'llm analysis for {data[idx]["_source"]["source"]["name"]} completed in {time_taken}s')
    
        return data
    
    except Exception as e:
        logger.error(f"An unexpected error occurred during llm analysis: {e}")
        raise

async def _worker_handler(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    try:
        results = await _process_llm(data)

        # update stream data in database 
        await update_stream_data(
            data=results, 
            status={"complete": True, "step": None })

        await msg.ack(redis)
 
    except Exception as e:
        await msg.nack()

@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="audiovisual:llm_group",
        consumer="llm_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_1(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)

@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="audiovisual:llm_group",
        consumer="llm_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_2(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)

@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="audiovisual:llm_group",
        consumer="llm_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_3(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)

@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="audiovisual:llm_group",
        consumer="llm_worker_4",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_4(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)

@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="audiovisual:llm_group",
        consumer="llm_worker_5",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_5(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)

@llm_broker.subscriber(stream=StreamSub(
        "audiovisual:llm_stream",
        group="audiovisual:llm_group",
        consumer="llm_worker_6",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_llm_worker_6(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline):
    await _worker_handler(data=data, msg=msg, redis=redis, pipe=pipe)
