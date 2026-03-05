import json
import asyncio
import logging
from redis.exceptions import RedisError
from app.core import redis as redis_state
from app.core.redis import (
    redis_broker as queue_broker,
    worker_1_busy_lock,
    worker_2_busy_lock,
    worker_3_busy_lock,
)
from app.core.redis_keys import PRIORITY_QUEUE, SEGMENTATION_STREAM


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def queue_processor():
    while True:
        try:
            if (
                not worker_1_busy_lock.locked()
                or not worker_2_busy_lock.locked()
                or not worker_3_busy_lock.locked()
            ):
                # retrieve the next 10 items in the queue
                result = await redis_state.redis_client.zpopmax(
                    PRIORITY_QUEUE,
                    count=1,
                )

                if result:
                    data_json, score = result[0]
                    result_json = json.loads(data_json)
                    doc_id = result_json.get("doc_id")

                    logger.info(
                        "Queue dequeue: doc_id=%s score=%s "
                        "stream_id=%s type=%s",
                        doc_id,
                        score,
                        result_json.get("stream_id"),
                        result_json.get("stream_type"),
                    )

                    await queue_broker.publish(
                        result_json,
                        stream=SEGMENTATION_STREAM,
                    )
                    logger.info(
                        "Queue publish success: doc_id=%s "
                        "to=%s",
                        doc_id,
                        SEGMENTATION_STREAM,
                    )
        except (RedisError, OSError, ValueError) as exc:
            logger.error("Queue processor Redis error: %s", exc)
            try:
                redis_state.load_redis_client()
            except (RedisError, OSError, ValueError) as reload_exc:
                logger.error(
                    "Queue processor Redis client reload failed: %s",
                    reload_exc,
                )
            await asyncio.sleep(2)
        # else:
        #     print("🔁 AudioVisual Queue Still busy...")
        await asyncio.sleep(0.5)
