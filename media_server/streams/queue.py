import json
from utils.redis import redis_broker as queue_broker, worker_1_busy_lock, worker_2_busy_lock, worker_3_busy_lock, redis_client
import asyncio

async def queue_processor():
     while True:
        if not worker_1_busy_lock.locked() or not worker_2_busy_lock.locked() or not worker_3_busy_lock.locked():
            # retrieve the next 10 items in the queue
            result = await redis_client.zpopmax("media_srv:priority_queue", count=1)

            if result:
                data_json, score = result[0]
                result_json = json.loads(data_json)
            
                # post to media analysis
                await queue_broker.publish(
                    result_json, 
                    stream="media_srv:media_processing"
                )   
        # else:
        #     print("🔁 AudioVisual Queue Still busy...")
        await asyncio.sleep(0.5)