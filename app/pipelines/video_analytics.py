from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from faststream.redis import fastapi
from app.models.analytics import AnalysisModel
from datetime import datetime
from app.core.gcp import delete_blob, download_file, upload
from app.core.files import calc_file_size, delete_file, extract_file_name, subfolder_check
import os
from app.core.media_processing import extract_audio_from_video, slice_video
import time 
import uuid
from app.core.redis import redis_router as video_router
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

class Upload(BaseModel):
    stream_id: str
    stream_name: str
    bucket: str
    blob: str
    timestamp_str: Optional[str]


async def handle_start_video_analysis(upload: Upload):
    try:
        timestamp = datetime.strptime(upload.timestamp_str, "%Y-%m-%dT%H:%M:%S")
    except (ValueError, AttributeError):
        timestamp = datetime.now()
    
    # download video
    file_name = extract_file_name(upload.blob)
    subfolder_check(f"{os.getcwd()}/o2-files")
    video_file_path = f"{os.getcwd()}/o2-files/{file_name}"

    # Use asyncio.to_thread to avoid blocking the event loop
    await asyncio.to_thread(download_file, upload.bucket, upload.blob, video_file_path)
    
    # extract audio from video
    audio_file_path = await asyncio.to_thread(extract_audio_from_video, video_file_path)
    
    analysis_id = uuid.uuid4()
    analysis = {
        "id": str(analysis_id),
        "stream_id": upload.stream_id,
        "stream_name": upload.stream_name,
        "audio_path": audio_file_path,
        "video_path": video_file_path,
        "type": "video",
        "timestamp": timestamp.isoformat(),
        "gcp_bucket": upload.bucket,
        "gcp_blob": upload.blob,
    }
    await video_router.broker.publish(json.dumps(analysis), "av:audio_seg")
    return analysis_id

async def handle_video_upload(msg: str):
    
    try:
        data = json.loads(msg)

        try:
            timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")

        # Start timing
        start_time = time.time()

        for index, segment in enumerate(data["segments"]):
            # slice video segment
            local_file_path = await asyncio.to_thread(slice_video, data['video_path'], segment['start'], segment['stop'])
            
            file_name = extract_file_name(local_file_path)
            file_size = calc_file_size(local_file_path)
            
            # dest file path construction
            recording_date = timestamp.date().isoformat()
            dest_file_path = f"tv/{data['stream_name']}/{recording_date}/{file_name}"
            
            # upload to gcp
            await asyncio.to_thread(upload, data['gcp_bucket'], local_file_path, dest_file_path)
            
            # delete local file
            await asyncio.to_thread(delete_file, local_file_path)
            await asyncio.to_thread(delete_file, segment['audio_file'])

            # update segment
            data['segments'][index]['file_size'] = file_size
            data['segments'][index]['gcp_path'] = dest_file_path
        
        # delete the master files
        await asyncio.to_thread(delete_file, data['video_path'])
        await asyncio.to_thread(delete_file, data['audio_path'])
        await asyncio.to_thread(delete_blob, data['gcp_bucket'], data['gcp_blob'])

        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to upload video files to gcp: {time_taken:.2f} seconds.")
        
        return json.dumps(data)
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

@video_router.post("/analysis/video")
async def start_video_analysis(upload: Upload):
    return await handle_start_video_analysis(upload)
    
@video_router.subscriber("av:upload_video_gcp")
@video_router.publisher("av:save_analysis_es")
async def upload_video_gcp(msg: str):
    return await handle_video_upload(msg)
    


