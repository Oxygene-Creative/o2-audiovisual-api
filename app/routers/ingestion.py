import uuid
from pydantic import BaseModel
import json
from typing import Optional
from app.core.es import search
from app.core.redis import redis_client
from datetime import datetime
from fastapi import APIRouter
from app.core.redis import redis_broker as _broker

ingestion_router = APIRouter()

class Upload(BaseModel):
    stream_id: str
    stream_name: str
    media_type: str
    bucket: str
    blob: str
    timestamp_str: Optional[str]

@ingestion_router.post("/ingestion")
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
        "gcp_bucket": upload.bucket,
        "gcp_blob": upload.blob,
        "status": {
            "complete": False,
            "step": "INGESTION"
        }
    }

    # Add to redis sorted list
    await redis_client.zadd(
        "audiovisual:priority_queue", 
        {json.dumps(data): timestamp.timestamp()})

    return data

@ingestion_router.post("/reingestion")
async def reingestion_handler():
    # find docs that status is not complete
    query = {
        "query": {
            "term": {
                "status.complete": False
            }
        }
    }
    response= search(index="radio_*,tv_*", query=query)

    # post to the appropriate stream
    hits = response["hits"]["hits"]
    for hit in hits:
        step = hit.get("_source", {}).get("status", {}).get("step", "")

        # if step == "INGESTION":
        #     await _broker.publish(
        #         { "_index": hit["_index"], "_id": hit["_id" ]}, 
        #         stream="audiovisual:segmentation_stream"
        #     )

        # elif step == "AUDIENCE":
        #     await _broker.publish(
        #         { "_index": hit["_index"], "_id": hit["_id" ]}, 
        #         stream="audiovisual:audience_stream"
        #     )

        # elif step == "ASR":
        #     await _broker.publish(
        #         { "_index": hit["_index"], "_id": hit["_id" ]}, 
        #         stream="audiovisual:asr_stream"
        #     )

        # elif step == "NLP":
        #     await _broker.publish(
        #         { "_index": hit["_index"], "_id": hit["_id" ]}, 
        #         stream="audiovisual:nlp_stream"
        #     )

        # elif step == "LLM":
        #     await _broker.publish(
        #         { "_index": hit["_index"], "_id": hit["_id" ]}, 
        #         stream="audiovisual:llm_stream"
        #     )



    # return list of items posted to stream
    return hits