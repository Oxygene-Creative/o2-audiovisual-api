import logging
import os
import tempfile
from datetime import datetime

import asyncio
import ffmpeg
from fastapi import APIRouter, File, UploadFile, HTTPException, Form

from app.core.gcp import upload
from app.core.media_processing import check_media_integrity, validate_file_size

uploads_router = APIRouter()
logger = logging.getLogger(__name__)


@uploads_router.post("/uploads-from-pi")
async def upload_videos_from_pi(
    file: UploadFile = File(...),
    stream_id: str = Form(...),
    stream_name: str = Form(...),
    timestamp: str = Form(...)
):
    # Example: enforce .ts uploads only
    # if not file.filename.endswith(".ts"):
    #     raise HTTPException(status_code=400, detail="Only .ts uploads")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.ts') as temp_ts:
        content = await file.read()
        temp_ts.write(content)
        temp_ts_path = temp_ts.name
    logger.info(
        "Saved upload '%s' to temp path %s (%d bytes)",
        file.filename,
        temp_ts_path,
        os.path.getsize(temp_ts_path),
    )

    output_path = None  # Initialize to None to avoid UnboundLocalError

    try:
        # Validate file size first (quick check)
        # At least 1KB
        if not await validate_file_size(temp_ts_path, min_size_bytes=1024):
            raise HTTPException(
                status_code=400, detail="Uploaded file is too small or empty")
        logger.info("%s passed size validation", temp_ts_path)

        # Check for corruption using ffprobe
        logger.info("Checking media integrity for %s", temp_ts_path)
        integrity_ok = await check_media_integrity(temp_ts_path)
        logger.info(
            "Integrity check result for %s: %s",
            temp_ts_path,
            integrity_ok,
        )
        if not integrity_ok:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded media file appears to be corrupted or invalid"
                ),
            )

        logger.info("Media file %s passed integrity checks", file.filename)

        output_path = temp_ts_path.replace('.ts', '.mp4')

        # Convert using ffmpeg-python
        logger.info(
            "Starting ffmpeg conversion temp=%s output=%s",
            temp_ts_path,
            output_path,
        )
        stdout, stderr = (
            ffmpeg
            .input(temp_ts_path)
            .output(output_path, vcodec='libx264', acodec='aac', preset='fast')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        if stdout:
            logger.debug(
                "ffmpeg stdout for %s: %s",
                file.filename,
                stdout.decode('utf-8', errors='ignore'),
            )
        if stderr:
            logger.debug(
                "ffmpeg stderr for %s: %s",
                file.filename,
                stderr.decode('utf-8', errors='ignore'),
            )
        logger.info("ffmpeg conversion completed for %s", file.filename)

        # Parse into datetime object
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            logger.info(
                "Falling back to minute-level timestamp parse for %s",
                timestamp,
            )
            dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")

        # Format outputs
        recording_date = dt.strftime("%Y-%m-%d")
        datetime_str = dt.strftime("%Y%m%d_%H%M")

        gcp_path = (
            f"tv/{stream_name}/{recording_date}/"
            f"{stream_name}_{datetime_str}.mp4"
        )

        await asyncio.to_thread(
            upload,
            "audiovisual-streams",
            output_path,
            gcp_path,
        )

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
