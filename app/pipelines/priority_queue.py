from pydantic import BaseModel
import json
from typing import Optional
from app.core.redis import redis_router as queue_router, audio_queue_busy_lock, video_queue_busy_lock, redis_client
from datetime import datetime
import uuid
import asyncio

class Upload(BaseModel):
    stream_id: str
    stream_name: str
    media_type: str
    bucket: str
    blob: str
    timestamp_str: Optional[str]

@queue_router.post("/enqueue")
async def enqueue_handler(upload: Upload):
    timestamp = (
        datetime.strptime(upload.timestamp_str, "%Y-%m-%dT%H:%M:%S")
        if upload.timestamp_str
        else datetime.now()
    ).timestamp()

    upload = {
        "id": str(uuid.uuid4()),
        "stream_id": upload.stream_id,
        "media_type": upload.media_type,
        "stream_name": upload.stream_name,
        "timestamp": upload.timestamp_str,
        "gcp_bucket": upload.bucket,
        "gcp_blob": upload.blob,
    }

    # Add to redis sorted list
    await redis_client.zadd("av:priority_queue", {json.dumps(upload): timestamp})

    return upload["id"]


async def queue_processor():
    print("🔄 Queue processor started")
    while True:
        if not audio_queue_busy_lock.locked() or not video_queue_busy_lock.locked():
            # retrieve the next item in the queue
            result = await redis_client.zpopmax("av:priority_queue", count=1)
            
            if result:
                data_json, score = result[0]
                result_json = json.loads(data_json)

                if result_json.get("media_type", "").lower() == "video":
                    # post to video analysis
                    await queue_router.broker.publish(
                        json.dumps(result_json), "av:video_segmentation"
                    )
                elif result_json.get("media_type", "").lower() == "audio":
                    # post to audio analysis
                    await queue_router.broker.publish(
                        json.dumps(result_json), "av:audio_segmentation"
                    )
        else:
            print("🔁 AV Queue Still busy...")
        await asyncio.sleep(0.5)