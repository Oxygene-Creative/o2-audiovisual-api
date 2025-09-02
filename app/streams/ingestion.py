import uuid
from pydantic import BaseModel
import json
from typing import Optional
from app.core.redis import redis_router as queue_router, redis_client
from datetime import datetime

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
    )

    if upload.media_type.lower() == "audio":
        source_type = "Radio Station"
        index = f"radio_{upload.stream_id}"
    elif upload.media_type.lower() == "video":
        source_type = "TV Station"
        index = f"tv_{upload.stream_id}"
    else:
        source_type = "UNKNOWN"
        index = None

    data = {
        "doc_id": str(uuid.uuid4()),
        "_index": index,
        "stream_type": upload.media_type,
        "source": {
            "type": source_type,
            "name": upload.stream_name
        },
        "timestamp": timestamp.isoformat(),
        "gcp_bucket": upload.get("bucket"),
        "gcp_blob": upload.get("blob"),
        "status": {
            "complete": False,
            "step": "INGESTION"
        }
    }

    # Add to redis sorted list
    await redis_client.zadd(
        "audiovisual:priority_queue", 
        {data: timestamp.timestamp()})

    return True

