import asyncio
import time
from app.analyzers.embeddings import embed_text
from app.analyzers.emotion import analyze_emotions
from app.analyzers.nlp import categorize_text
from app.analyzers.sentiment import sentiment_analysis
from app.analyzers.topics import analyze_topics
from app.analyzers.transcription import remove_timestamps_and_format
from app.core.graphql import fetch_industries, get_tags
from app.core.redis import redis_router as nlp_router
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

async def _process_nlp(data: list[dict]):
    try:
        # Start timing
        start_time = time.time() 
        data = await fetch_stream_data(data)

        tv_categories = await get_tags("Tv")
        radio_categories = await get_tags("Radio")
        industry_sectors = await fetch_industries()

        batch_payloads = [
            remove_timestamps_and_format(item.get("_source", {}).get("raw_text", "")) 
            for item in data
        ]

        batch_tag_payloads = []
        batch_industry_payloads = []

        # payloads for category analysis
        for item in data:
            batch_industry_payloads.append({ 
                "text": remove_timestamps_and_format(item.get("_source", {}).get("raw_text", "")),
                "categories":  industry_sectors,
                "multi_label": True
            })
            if item.get("_index", "").startsWith("radio"):
                batch_tag_payloads.append({ 
                    "text": remove_timestamps_and_format(item.get("_source", {}).get("raw_text", "")),
                    "categories":  radio_categories,
                    "multi_label": True
                })
            elif item.get("_index", "").startsWith("tv"):
                batch_tag_payloads.append({ 
                    "text": remove_timestamps_and_format(item.get("_source", {}).get("raw_text", "")),
                    "categories":  tv_categories,
                    "multi_label": True
                })

        tags, topics, emotions, sentiments, embeddings, industries  = await asyncio.gather(
            categorize_text(data=batch_tag_payloads),
            analyze_topics(data=batch_payloads),
            analyze_emotions(data=batch_payloads),
            sentiment_analysis(data=batch_payloads),
            embed_text(data=batch_payloads),
            categorize_text(data=batch_industry_payloads)
        )

        # populate updates
        for idx, item in enumerate(data): 
            item["_updates"]["tags"]= tags[idx]
            item["_updates"]["embeddings"]= embeddings[idx]
            item["_updates"]["sentiment"]= sentiments[idx]
            item["_updates"]["emotions"]= emotions[idx]
            item["_updates"]["topics"]= topics[idx]
            item["_updates"]["industries"]= industries[idx]

            end_time = time.time()
            time_taken = end_time - start_time

            logger.info(f"nlp analysis for {item["_source"]["source"]["name"]} completed in {time_taken}s")

        return data
    
    except Exception as e:
        logger.error(f"An unexpected error occurred during nlp analysis: {e}")
        raise

@nlp_router.subscriber(stream=StreamSub(
        "audiovisual:nlp_stream",
        group="audiovisual:nlp_group",
        consumer="nlp_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_nlp_worker_1(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        nlp_results = await _process_nlp(data)
        # update stream data in database 
        results = await update_stream_data(
            data=nlp_results, 
            status={"complete": False, "step": "LLM" })

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await nlp_router.broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:llm_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()

@nlp_router.subscriber(stream=StreamSub(
        "audiovisual:nlp_stream",
        group="audiovisual:nlp_group",
        consumer="nlp_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_nlp_worker_2(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        nlp_results = await _process_nlp(data)
        # update stream data in database 
        results = await update_stream_data(
            data=nlp_results, 
            status={"complete": False, "step": "LLM" })

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await nlp_router.broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:llm_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()

@nlp_router.subscriber(stream=StreamSub(
        "audiovisual:nlp_stream",
        group="audiovisual:nlp_group",
        consumer="nlp_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_nlp_worker_3(data: list[dict], msg: RedisMessage, redis: Redis, pipe: Pipeline,):
    try:
        nlp_results = await _process_nlp(data)
        # update stream data in database 
        results = await update_stream_data(
            data=nlp_results, 
            status={"complete": False, "step": "LLM" })

        await msg.ack(redis)

        # batch publish to next stage
        for result in results:
            await nlp_router.broker.publish(
                { "_index": result.get("_index"), "_id": result.get("_id") },
                stream="audiovisual:llm_stream",
                pipeline=pipe,
            )

        await pipe.execute() 
    except Exception as e:
        await msg.nack()