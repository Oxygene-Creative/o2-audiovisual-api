from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse
import ffmpeg
import tempfile
import os
from pathlib import Path
from app.core.gcp import upload

uploads_router = APIRouter()

@uploads_router.post("/uploads-from-pi")
async def upload_videos_from_pi(file: UploadFile = File(...),  gcp_path: str = Query(...)):
    if not file.filename.endswith('.ts'):
        raise HTTPException(status_code=400, detail="File must be a .ts file")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ts') as temp_ts:
        content = await file.read()
        temp_ts.write(content)
        temp_ts_path = temp_ts.name
    
    output_path = temp_ts_path.replace('.ts', '.mp4')
    
    try:
        # Convert using ffmpeg-python
        (
            ffmpeg
            .input(temp_ts_path)
            .output(output_path, vcodec='libx264', acodec='aac', preset='fast')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        return FileResponse(
            output_path,
            media_type='video/mp4',
            filename=f"{Path(file.filename).stem}.mp4"
        )
        
    except ffmpeg.Error as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
    
    finally:
        if os.path.exists(temp_ts_path):
            os.unlink(temp_ts_path)
        
        upload("audiovisual-streams", output_path, gcp_path)

        if os.path.exists(output_path):
            os.unlink(output_path)
        