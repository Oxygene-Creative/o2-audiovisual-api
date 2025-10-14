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

uploads_router = APIRouter()
AUDIOVISUAL_API_URI = os.getenv("AUDIOVISUAL_API_URI", "https://monitorapi.oxygenehosting.com/api/av")

async def handle_start_video_analysis(upload: dict):
    try:        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{AUDIOVISUAL_API_URI}/ingestion", json=upload)
            
            # Check response status code
            if response.status_code == 200:
                # Parse JSON response if needed
                return response.json()
            else:
                raise Exception(f"Failed to start video analysis: {response.status_code} - {response.text}")
                
    except httpx.RequestError as e:
        raise Exception(f"Error communicating with video analysis endpoint: {str(e)}")

def background_task_conversion_and_analysis(
    temp_ts_path: str, 
    stream_id: str, 
    stream_name: str, 
    timestamp: str
):
    try:
        # Use the new function for conversion
        output_path = convert_video_format(temp_ts_path, "ts", "mp4")
        
        # Parse into datetime object
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")
        
        # Format outputs
        recording_date = dt.strftime("%Y-%m-%d")
        datetime_str = dt.strftime("%Y%m%d_%H%M")
        
        gcp_path = f'tv/{stream_name}/{recording_date}/{stream_name}_{datetime_str}.mp4'

        # Upload to GCP
        bucket_name = "audiovisual-streams"
        upload(bucket_name, output_path, gcp_path)

        upload_file_info = {
            "stream_id": stream_id,
            "stream_name": stream_name,
            "bucket": bucket_name,
            "blob": gcp_path,
            "media_type": "video",
            "timestamp_str": timestamp
        }

        # # extract audio from video
        # soundtrack_file_path = asyncio.run(extract_audio_from_video(output_path))
        # # upload audio file
        # sound_track_dest = replace_mp4_with_mp3(gcp_path)
        # upload(bucket_name, soundtrack_file_path, sound_track_dest)

        # Start video analysis
        asyncio.run(handle_start_video_analysis(upload=upload_file_info))

    except Exception as e:
        print(f"Error in background task: {e}")

    finally:
        # Clean up files
        if os.path.exists(temp_ts_path):
            os.unlink(temp_ts_path)

        if os.path.exists(output_path):
            os.unlink(output_path)

@uploads_router.post("/uploads-from-pi")
async def upload_videos_from_pi(
    background_tasks: BackgroundTasks,
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
    
    # Start background tasks
    background_tasks.add_task(
        background_task_conversion_and_analysis,
        temp_ts_path, stream_id, stream_name, timestamp
    )

    return {
        "success": True,
        "message": "Upload and processing started in the background."
    }