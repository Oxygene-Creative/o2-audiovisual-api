from pydantic import BaseModel
import json
from typing import Optional
from app.core.redis import redis_router as queue_router
from datetime import datetime
class Upload(BaseModel):
    stream_id: str
    stream_name: str
    stream_type: str
    bucket: str
    blob: str
    timestamp_str: Optional[str]

@queue_router.post("/enqueue")
async def priority_queue_handler(upload: Upload):
    timestamp = (
        datetime.strptime(upload.timestamp_str, "%Y-%m-%dT%H:%M:%S")
        if upload.timestamp_str
        else datetime.now()
    )

    upload = {
        "stream_id": upload.stream_id,
        "stream_name": upload.stream_name,
        "timestamp": upload.timestamp_str,
        "gcp_bucket": upload.get("bucket"),
        "gcp_blob": upload.get("blob"),
    }

    # Add to redis sorted list
    await queue_router.broker.redis.zadd("av:priority_queue", {json.dumps(upload): timestamp})

    return
