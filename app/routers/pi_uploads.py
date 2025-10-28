from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from app.core.media_processing import check_media_integrity, validate_file_size
import ffmpeg
import tempfile
import os
from pathlib import Path
from app.core.gcp import upload
import asyncio
from datetime import datetime

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

    output_path = None  # Initialize to None to avoid UnboundLocalError

    try:
        # Validate file size first (quick check)
        # At least 1KB
        if not await validate_file_size(temp_ts_path, min_size_bytes=1024):
            raise HTTPException(
                status_code=400, detail="Uploaded file is too small or empty")

        # Check for corruption using ffprobe
        print(f"Checking integrity of {file.filename}...")
        if not await check_media_integrity(temp_ts_path):
            raise HTTPException(
                status_code=400, detail="Uploaded media file appears to be corrupted or invalid")

        print(f"Media file {file.filename} passed integrity checks")

        output_path = temp_ts_path.replace('.ts', '.mp4')

        # Convert using ffmpeg-python
        (
            ffmpeg
            .input(temp_ts_path)
            .output(output_path, vcodec='libx264', acodec='aac', preset='fast')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # Parse into datetime object
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")

        # Format outputs
        recording_date = dt.strftime("%Y-%m-%d")
        datetime_str = dt.strftime("%Y%m%d_%H%M")

        gcp_path = f'tv/{stream_name}/{recording_date}/{stream_name}_{datetime_str}.mp4'

        await asyncio.to_thread(upload, "audiovisual-streams", output_path, gcp_path)

        # uploadFile = Upload(
        #     stream_id=stream_id,
        #     stream_name=stream_name,
        #     bucket="audiovisual-streams",
        #     blob=gcp_path,
        #     timestamp_str=timestamp
        # )

        # analysis_id = await handle_start_video_analysis(upload=uploadFile)

        return {
            "success": True,
            # "analysis_id": analysis_id,
            "gcp_path": gcp_path
        }

    except ffmpeg.Error as e:
        print("stdout:", e.stdout.decode('utf8', errors='ignore'))
        print("stderr:", e.stderr.decode('utf8', errors='ignore'))
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")

    finally:
        if os.path.exists(temp_ts_path):
            os.unlink(temp_ts_path)

        if output_path and os.path.exists(output_path):
            os.unlink(output_path)
