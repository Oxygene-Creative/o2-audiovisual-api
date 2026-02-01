from fastapi import APIRouter, File, UploadFile, HTTPException, Form
import tempfile
from datetime import datetime
import os
from utils.redis import redis_client
import json

uploads_router = APIRouter()


@uploads_router.post("/uploads-from-pi")
async def upload_videos_from_pi(
    file: UploadFile = File(...),
    stream_id: str = Form(...),
    stream_name: str = Form(...),
    timestamp: str = Form(...)
):
    filename = file.filename or ""
    if not (filename.endswith('.ts') or filename.endswith('.mp4')):
        raise HTTPException(
            status_code=400,
            detail="File must be a .ts or .mp4 file",
        )

    suffix = '.mp4' if filename.endswith('.mp4') else '.ts'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_ts:
        while True:
            chunk = await file.read(4 * 1024 * 1024)
            if not chunk:
                break
            temp_ts.write(chunk)
        temp_ts_path = temp_ts.name

    timestamp_dt = (
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        if timestamp
        else datetime.now()
    )

    payload = {
        "path": temp_ts_path,
        "stream_id": stream_id,
        "stream_name": stream_name,
        "timestamp": timestamp
    }

    # Add to redis sorted list
    await redis_client.zadd(
        "media_srv:priority_queue",
        {json.dumps(payload): timestamp_dt.timestamp()})

    return {
        "success": True,
        "message": "Vide file uploaded and queued for processing."
    }
