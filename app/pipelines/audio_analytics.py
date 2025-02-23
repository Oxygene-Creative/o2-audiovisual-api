from typing import Optional
from fastapi import FastAPI
from faststream.redis import fastapi
from app.models.analytics import AnalysisModel, Segment, Activity
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
    
audio_router = fastapi.RedisRouter()

@audio_router.post("/analysis/audio")
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
    
    analysis_id = uuid.uuid4()
    analysis = AnalysisModel(
        id=str(analysis_id),
        stream_id=upload.stream_id,
        stream_name=upload.stream_name,
        audio_path=audio_file_path,
        type="audio",
        timestamp=timestamp,
        gcp_bucket=upload.bucket,
        gcp_blob=upload.blob
    )
    await audio_router.broker.publish(analysis.model_dump_json(), "av:audio_seg")
    return analysis_id

@audio_router.subscriber("av:audio_seg")
@audio_router.publisher("av:audio_transcribe")
async def audio_seg(msg: str):
    data = AnalysisModel.model_validate_json(msg)
    # Start timing
    start_time = time.time()
    activity_segments, speech_segments = gender_music_segmentation(data.audio_path)

    # End timing
    end_time = time.time()
    
    # Calculate time taken
    time_taken = end_time - start_time
    print(f"Time taken for audio segmentation: {time_taken:.2f} seconds.")
    
    # transform activity segments and add to analysis object
    activity = {item["labels"]: item["duration"] for item in activity_segments}
    
    data.activity = Activity(
        male = activity["male"] or 0.0,
        female = activity["female"] or 0.0,
        music = activity["music"] or 0.0,
        noEnergy = activity["noEnergy"] or 0.0
    )
    
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
    
    return data.model_dump_json()

@audio_router.subscriber("av:upload_audio_gcp")
@audio_router.publisher("av:save_analysis_es")
async def upload_audio_gcp(msg: str):
    data = AnalysisModel.model_validate_json(msg)
    try:        
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
        
        return data.model_dump_json()
    except Exception as e:
        print(f"Unexpected error: {e}")
        await audio_router.broker.publish(data.model_dump_json(), "av:save_analysis_es")
    

