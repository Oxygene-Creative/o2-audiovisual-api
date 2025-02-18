from fastapi import FastAPI
from faststream.redis import RedisRouter
from app.models.analytics import AnalysisModel
from datetime import datetime
from app.core.gcp import download_file
from app.core.files import extract_file_name, subfolder_check
import os
from app.core.media_processing import extract_audio_from_video

video_router = RedisRouter()

@video_router.post("/upload/video")
async def start_video(stream_id: str, bucket: str, blob: str, timestamp_str: str):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
    
    # download video
    file_name = extract_file_name(blob)
    subfolder_check(f"{os.getcwd()}/o2-files")
    video_file_path = f"{os.getcwd()}/o2-files/{file_name}"
    download_file(bucket, blob, video_file_path)
    
    # extract audio from video
    audio_file_path = extract_audio_from_video(video_file_path)
    
    analysis = AnalysisModel(
        stream_id=stream_id,
        video_path=video_file_path,
        audio_path=audio_file_path,
        type="video",
        timestamp=timestamp
    )
    await video_router.broker.publish(analysis, "audio_seg")
    return "Video file is downloaded and analysis is ongoing!"





