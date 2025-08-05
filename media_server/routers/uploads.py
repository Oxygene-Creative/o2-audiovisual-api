from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from utils.media_processing import convert_video_format
import tempfile
import os
from pathlib import Path
from utils.gcp import upload
import asyncio
from datetime import datetime
import httpx

uploads_router = APIRouter()
AUDIOVISUAL_API_URI = os.getenv("AUDIOVISUAL_API_URI", "https://monitorapi.oxygenehosting.com/api/av")

async def handle_start_video_analysis(upload: dict):
    try:        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{AUDIOVISUAL_API_URI}/", json=upload)
            
            # Check response status code
            if response.status_code == 200:
                # Parse JSON response if needed
                return response.json().get("analysis_id")
            else:
                raise Exception(f"Failed to start video analysis: {response.status_code} - {response.text}")
                
    except httpx.RequestError as e:
        raise Exception(f"Error communicating with video analysis endpoint: {str(e)}")

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
    
    try:
        output_path = convert_video_format(temp_ts_path, "ts", "mp4")
        
        # Parse into datetime object
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")

        # Format outputs
        recording_date = dt.strftime("%Y-%m-%d")
        datetime_str = dt.strftime("%Y%m%d_%H%M")

        gcp_path = f'tv/{stream_name}/{recording_date}/{stream_name}_{datetime_str}.mp4'

        await asyncio.to_thread(upload, "audiovisual-streams", output_path, gcp_path)

        uploadFile = {
            "stream_id": stream_id,
            "stream_name": stream_name,
            "bucket": "audiovisual-streams",
            "blob": gcp_path,
            "timestamp_str": timestamp  
        }
        
        analysis_id = await handle_start_video_analysis(upload=uploadFile)

        return {
            "success": True,
            "analysis_id": analysis_id,
            "gcp_path": gcp_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_ts_path):
            os.unlink(temp_ts_path)

        if os.path.exists(output_path):
            os.unlink(output_path)
        