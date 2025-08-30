import json
from app.core.redis import redis_router as queue_router, audio_queue_busy_lock, video_queue_busy_lock, redis_client
import asyncio

async def queue_processor():
     while True:
        if not audio_queue_busy_lock.locked() or not video_queue_busy_lock.locked():
            # retrieve the next item in the queue
            result = await redis_client.zpopmax("audiovisual:priority_queue", count=1)
            
            if result:
                data_json, score = result[0]
                result_json = json.loads(data_json)

                # post to media analysis
                await queue_router.broker.publish(
                    json.dumps(result_json), "audiovisual:audience_stream"
                )
                    
        else:
            print("🔁 AudioVisual Queue Still busy...")
        await asyncio.sleep(0.5)