from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from utils.media_processing import convert_video_format, extract_audio_from_video
import tempfile
import os
from pathlib import Path
from utils.gcp import upload
import asyncio
from datetime import datetime
import httpx
from fastapi import BackgroundTasks
from streams.segmentation import replace_mp4_with_mp3
import subprocess
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
    if not file.filename.endswith('.ts'):
        raise HTTPException(status_code=400, detail="File must be a .ts file")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ts') as temp_ts:
        content = await file.read()
        temp_ts.write(content)
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