from pydantic import BaseModel
import json
from typing import Optional
from app.core.redis import redis_router as queue_router, redis_client
from datetime import datetime
import uuid

class Upload(BaseModel):
    stream_id: str
    stream_name: str
    media_type: str
    bucket: str
    blob: str
    timestamp_str: Optional[str]

@queue_router.post("/ingestion")
async def ingestion_handler(upload: Upload):
    timestamp = (
        datetime.strptime(upload.timestamp_str, "%Y-%m-%dT%H:%M:%S")
        if upload.timestamp_str
        else datetime.now()
    ).timestamp()

    upload = {
        "id": uuid.uuid4(),
        "stream_id": upload.stream_id,
        "media_type": upload.media_type,
        "stream_name": upload.stream_name,
        "timestamp": upload.timestamp_str,
        "gcp_bucket": upload.get("bucket"),
        "gcp_blob": upload.get("blob"),
    }

    # Add to redis sorted list
    await redis_client.zadd("audiovisual:priority_queue", {json.dumps(upload): timestamp})

    return upload["analysis_id"]

