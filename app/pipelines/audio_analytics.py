from typing import Optional
from fastapi import FastAPI
from faststream.redis import RedisRouter
from app.models.analytics import AnalysisModel, Segment
from datetime import datetime
from app.core.files import calc_file_size, delete_file, extract_file_name, subfolder_check
from app.core.gcp import delete_blob, download_file, upload
import os
import time
from app.analyzers.segmentation import gender_music_segmentation
from app.core.media_processing import slice_audio
from pydantic import BaseModel
import uuid

class Upload(BaseModel):
    stream_id: str
    stream_name: str
    bucket: str
    blob: str
    timestamp_str: Optional[str]
    
audio_router = RedisRouter()

@audio_router.get("/analysis/audio")
async def start_audio_analysis(upload: Upload):
    try:
        timestamp = datetime.strptime(upload.timestamp_str, "%Y-%m-%dT%H:%M:%S")
    except (ValueError, AttributeError):
        timestamp = datetime.now()
    
    # download audio
    file_name = extract_file_name(upload.blob)
    subfolder_check(f"{os.getcwd()}/o2-files")
    audio_file_path = f"{os.getcwd()}/o2-files/{file_name}"
    download_file(upload.bucket, upload.blob, audio_file_path)
    
    analysis = AnalysisModel(
        id=uuid.uuid4(),
        stream_id=upload.stream_id,
        stream_name=upload.stream_name,
        audio_path=audio_file_path,
        type="audio",
        timestamp=timestamp
    )
    await audio_router.broker.publish(analysis, "av:audio_seg")
    return "Audio file is downloaded and analysis is ongoing!"

@audio_router.subscriber("av:audio_seg")
@audio_router.publish("av:audio_transcribe")
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

@audio_router.subscriber("av:upload_audio_gcp")
@audio_router.publish("av:save_analysis_es")
async def upload_audio_gcp(data: AnalysisModel):
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        # file details
        local_file_path = segment.audio_file
        file_name = extract_file_name(local_file_path)
        file_size = calc_file_size(local_file_path)
        
        # dest file path construction
        recording_date = data.timestamp.date().isoformat()
        dest_file_path = f"audio/{data.stream_name}/{recording_date}/{file_name}"
        
        # upload to gcp
        upload(data.gcp_bucket, local_file_path, dest_file_path)
        
        # delete local file
        delete_file(local_file_path)
        
        # update segment
        data.segments[index].file_size = file_size
        data.segments[index].gcp_path = dest_file_path
    
    # delete the master audio files
    delete_file(data.audio_path)
    delete_blob(data.gcp_bucket, data.gcp_blob)
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to upload audio files to gcp: {time_taken:.2f} seconds.")
    
    return data
    

