from fastapi import FastAPI
from faststream.redis import RedisRouter
from app.models.analytics import AnalysisModel, Segment
from datetime import datetime
from app.core.files import extract_file_name, subfolder_check
from app.core.gcp import download_file
import os
import time
from app.analyzers.segmentation import gender_music_segmentation
from app.core.media_processing import slice_audio

audio_router = RedisRouter()

@audio_router.post("/upload/audio")
async def start_audio(stream_id: str, bucket: str, blob: str, timestamp_str: str):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

    # download audio
    file_name = extract_file_name(blob)
    subfolder_check(f"{os.getcwd()}/o2-files")
    audio_file_path = f"{os.getcwd()}/o2-files/{file_name}"
    download_file(bucket, blob, audio_file_path)
    
    analysis = AnalysisModel(
        stream_id=stream_id,
        audio_path=audio_file_path,
        type="video",
        timestamp=timestamp
    )
    await audio_router.broker.publish(analysis, "audio_seg")
    return "Audio file is downloaded and analysis is ongoing!"


@audio_router.subscriber("audio_seg")
@audio_router.publish("audio_transcribe")
async def audio_seg(data: AnalysisModel):
    # Start timing
    start_time = time.time()
    activity_segments, speech_segments = gender_music_segmentation(data.audio_file)

    # End timing
    end_time = time.time()
    
    # Calculate time taken
    time_taken = end_time - start_time
    print(f"Time taken for audio segmentation: {time_taken:.2f} seconds.")
    
    # transform activity segments and add to analysis object
    data.activity = {item["labels"]: item["duration"] for item in activity_segments}
    
    # slice audio file based on speech segments
    speech_segment_files = slice_audio(speech_segments, data.audio_path)
    for segment in speech_segment_files:
        new_segment = Segment(
            start=segment['start'],
            stop=segment['stop'],
            duration= segment["duration"],
            audio_file=segment['audio_file']
        )
        data.segments.append(new_segment)
    
    return data

