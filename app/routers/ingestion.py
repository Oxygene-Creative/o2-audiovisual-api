import hashlib
import asyncio
from pydantic import BaseModel
import json
from typing import Optional
import logging
import os
from app.core.es import search
from app.core.redis import redis_client
from app.core.gcp import get_blob_metadata
from app.core.redis_keys import (
    ASR_STREAM,
    AUDIENCE_STREAM,
    LLM_STREAM,
    NLP_STREAM,
    PRIORITY_QUEUE,
    SEGMENTATION_STREAM,
)
from datetime import datetime
from fastapi import APIRouter, HTTPException
from google.api_core.exceptions import NotFound
from app.core.redis import redis_broker as _broker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
INGESTION_VALIDATE_GCS_BLOB = os.getenv("INGESTION_VALIDATE_GCS_BLOB", "1") == "1"
INGESTION_VALIDATE_GCS_BLOB_STRICT = (
    os.getenv("INGESTION_VALIDATE_GCS_BLOB_STRICT", "0") == "1"
)

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

    doc_id = hashlib.sha256(upload.blob.encode("utf-8")).hexdigest()
    logger.info(
        "Ingestion request received: doc_id=%s stream_id=%s type=%s blob=%s",
        doc_id,
        upload.stream_id,
        upload.media_type,
        upload.blob,
    )

    data = {
        "doc_id": doc_id,
        "_index": index,
        "stream_id": upload.stream_id,
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

    if INGESTION_VALIDATE_GCS_BLOB:
        try:
            source_blob_metadata = await _blob_metadata_async(
                upload.bucket,
                upload.blob,
            )
            if not source_blob_metadata:
                logger.warning(
                    "Ingestion rejected missing blob: doc_id=%s bucket=%s blob=%s",
                    doc_id,
                    upload.bucket,
                    upload.blob,
                )
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "blob_not_found",
                        "doc_id": doc_id,
                        "bucket": upload.bucket,
                        "blob": upload.blob,
                    },
                )
            data["source_blob_generation"] = source_blob_metadata.get("generation")
            data["source_blob_etag"] = source_blob_metadata.get("etag")
            data["source_blob_size"] = source_blob_metadata.get("size")
            data["source_blob_updated"] = source_blob_metadata.get("updated")
        except HTTPException:
            raise
        except Exception as check_error:
            if INGESTION_VALIDATE_GCS_BLOB_STRICT:
                logger.error(
                    "Ingestion blob validation strict reject: doc_id=%s bucket=%s blob=%s error=%s",
                    doc_id,
                    upload.bucket,
                    upload.blob,
                    check_error,
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "blob_validation_failed",
                        "doc_id": doc_id,
                        "bucket": upload.bucket,
                        "blob": upload.blob,
                    },
                )
            logger.warning(
                "Ingestion blob validation failed-open: doc_id=%s bucket=%s blob=%s error=%s",
                doc_id,
                upload.bucket,
                upload.blob,
                check_error,
            )

    # Add to redis sorted list
    await redis_client.zadd(
        PRIORITY_QUEUE,
        {json.dumps(data): timestamp.timestamp()})

    logger.info(
        "Ingestion enqueued: doc_id=%s "
        "queue=%s score=%s",
        doc_id,
        PRIORITY_QUEUE,
        timestamp.timestamp(),
    )

    return data


async def _blob_metadata_async(bucket: str, blob: str):
    try:
        return await asyncio.to_thread(get_blob_metadata, bucket, blob)
    except NotFound:
        return None


@ingestion_router.post("/reingestion")
async def reingestion_handler():
    # find docs that status is not complete
    query = {
        "_source": ["status", "gcp_blob"],
        "query": {
            "term": {
                "status.complete": False
            }
        }
    }
    response = search(index="radio_*,tv_*", query=query)

    # post to the appropriate stream
    hits = response["hits"]["hits"]
    logger.info("Reingestion fetched incomplete docs: count=%s", len(hits))
    for hit in hits:
        step = hit.get("_source", {}).get("status", {}).get("step", "")

        if step == "INGESTION":
            await _broker.publish(
                {"_index": hit["_index"], "_id": hit["_id"]},
                stream=SEGMENTATION_STREAM,
            )
            logger.info(
                "Reingestion publish: index=%s id=%s step=%s stream=%s",
                hit["_index"],
                hit["_id"],
                step,
                SEGMENTATION_STREAM,
            )

        elif step == "AUDIENCE":
            await _broker.publish(
                {"_index": hit["_index"], "_id": hit["_id"]},
                stream=AUDIENCE_STREAM,
            )
            logger.info(
                "Reingestion publish: index=%s id=%s step=%s stream=%s",
                hit["_index"],
                hit["_id"],
                step,
                AUDIENCE_STREAM,
            )

        elif step == "ASR":
            await _broker.publish(
                {"_index": hit["_index"], "_id": hit["_id"]},
                stream=ASR_STREAM,
            )
            logger.info(
                "Reingestion publish: index=%s id=%s step=%s stream=%s",
                hit["_index"],
                hit["_id"],
                step,
                ASR_STREAM,
            )

        elif step == "NLP":
            await _broker.publish(
                {"_index": hit["_index"], "_id": hit["_id"]},
                stream=NLP_STREAM,
            )
            logger.info(
                "Reingestion publish: index=%s id=%s step=%s stream=%s",
                hit["_index"],
                hit["_id"],
                step,
                NLP_STREAM,
            )

        elif step == "LLM":
            await _broker.publish(
                {"_index": hit["_index"], "_id": hit["_id"]},
                stream=LLM_STREAM,
            )
            logger.info(
                "Reingestion publish: index=%s id=%s step=%s stream=%s",
                hit["_index"],
                hit["_id"],
                step,
                LLM_STREAM,
            )

        else:
            logger.warning(
                "Reingestion skipped unknown step: index=%s id=%s step=%s",
                hit.get("_index"),
                hit.get("_id"),
                step,
            )

    # return list of items posted to stream
    return hits
