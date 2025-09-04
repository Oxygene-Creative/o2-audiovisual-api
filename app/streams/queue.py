import json
from app.core.redis import redis_broker as queue_broker, queue_busy_lock, redis_client
import asyncio

async def queue_processor():
     while True:
        if not queue_busy_lock.locked():
            # retrieve the next item in the queue
            result = await redis_client.zpopmax("audiovisual:priority_queue", count=1)
            
            if result:
                data_json, score = result[0]
                result_json = json.loads(data_json)

                # post to media analysis
                await queue_broker.publish(
                    result_json, stream="audiovisual:segmentation_stream"
                )
                    
        else:
            print("🔁 AudioVisual Queue Still busy...")
        await asyncio.sleep(0.5)