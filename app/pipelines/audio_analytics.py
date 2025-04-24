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
from dotenv import load_dotenv
from app.core.redis import redis_router as audio_router
import asyncio
from concurrent.futures import ProcessPoolExecutor
import requests
import json
load_dotenv()

# Create a global executor for process-based parallelism
executor = ProcessPoolExecutor()

GPU_ACTIVATED = os.getenv("GPU_ACTIVATED", "false").lower() == "true"
SEGMENTATION_GPU_URL = os.getenv("SEGMENTATION_GPU_URL", "").strip()

# Create a global executor for process-based parallelism
executor = ProcessPoolExecutor()

GPU_ACTIVATED = os.getenv("GPU_ACTIVATED", "false").lower() == "true"
SEGMENTATION_GPU_URL = os.getenv("SEGMENTATION_GPU_URL", "").strip()

class Upload(BaseModel):
    stream_id: str
    stream_name: str
    bucket: str
    blob: str
    timestamp_str: Optional[str]

async def async_gender_music_segmentation(audio_path):
    if GPU_ACTIVATED and SEGMENTATION_GPU_URL:
        try:
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_path), audio_file, "audio/mpeg")
                }
                print(f"Sending request to {SEGMENTATION_GPU_URL}/segment-audio with audio file: {audio_path}")
                response = requests.post(f"{SEGMENTATION_GPU_URL}/segment-audio", files=files)
                response.raise_for_status()  # Raise exception if HTTP status is an error
                response_data = response.json()
                return response_data["activity"], response_data["speech"]
        except requests.RequestException as e:
            print(f"Request error during GPU segmentation: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, gender_music_segmentation, audio_path)

async def handle_start_audio_analysis(upload: Upload):
    try:
        timestamp = (
            datetime.strptime(upload.timestamp_str, "%Y-%m-%dT%H:%M:%S")
            if upload.timestamp_str
            else datetime.now()
        )

        # download audio
        file_name = extract_file_name(upload.blob)
        subfolder_check(f"{os.getcwd()}/o2-files")
        audio_file_path = f"{os.getcwd()}/o2-files/{file_name}"

        await asyncio.to_thread(download_file, upload.bucket, upload.blob, audio_file_path)
        # download_file(upload.bucket, upload.blob, audio_file_path)
        
        analysis_id = uuid.uuid4()
        analysis = {
            "id": str(analysis_id),
            "stream_id": upload["stream_id"],
            "stream_name": upload["stream_name"],
            "audio_path": audio_file_path,
            "type": "audio",
            "timestamp": timestamp.isoformat(),
            "gcp_bucket": upload["bucket"],
            "gcp_blob": upload["blob"],
        }

        # Publish analysis object
        await audio_router.broker.publish(json.dumps(analysis), "av:audio_seg")
        return analysis_id
        
    except Exception as e:
        print(f"Error during audio analysis start: {e}")
        raise

async def handle_audio_segmentation(msg: str):
    try:
        data = json.loads(msg)

        # Start timing
        start_time = time.time()

        # Use the process pool executor for CPU-heavy segmentation
        activity_segments, speech_segments = await async_gender_music_segmentation(data['audio_path'])

        # Calculate time taken
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken for audio segmentation: {time_taken:.2f} seconds.")

        # Transform activity segments and add to analysis object
        activity = {item["labels"]: item["duration"] for item in activity_segments}
        data["activity"] = {
            "male": activity.get("male", 0.0),
            "female": activity.get("female", 0.0),
            "music": activity.get("music", 0.0),
            "noEnergy": activity.get("noEnergy", 0.0),
            "noise": activity.get("noise", 0.0),
        }

        # Slice audio file based on speech segments
        speech_segment_files = await asyncio.to_thread(
            slice_audio, speech_segments, data["audio_path"]
        )

        data["segments"] = []
        for segment in speech_segment_files:            
            data["segments"].append({
                "start": segment["start"],
                "stop": segment["stop"],
                "duration": segment["duration"],
                "audio_file": segment["audio_file"],
            })

        return json.dumps(data)

    except Exception as e:
        print(f"Error during audio segmentation: {e}")
        raise
    
async def handle_audio_upload_gcp(msg: str):
    try:
        data = json.loads(msg)

        timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S")

        # Start timing
        start_time = time.time()

        for index, segment in enumerate(data["segments"]):
            local_file_path = segment["audio_file"]
            file_name = extract_file_name(local_file_path)
            file_size = calc_file_size(local_file_path)

            # Destination file path construction
            recording_date = timestamp.date().isoformat()
            dest_file_path = f"radio/{data['stream_name']}/{recording_date}/{file_name}"

            # Upload to GCP (wrapped in asyncio.to_thread for non-blocking behavior)
            await asyncio.to_thread(upload, data["gcp_bucket"], local_file_path, dest_file_path)

            # Delete local file
            await asyncio.to_thread(delete_file, local_file_path)

            # Update segment metadata
            data["segments"][index]["file_size"] = file_size
            data["segments"][index]["gcp_path"] = dest_file_path

        # Delete the master audio file and GCP blob
        await asyncio.to_thread(delete_file, data["audio_path"])
        await asyncio.to_thread(delete_blob, data["gcp_bucket"], data["gcp_blob"])

        # Calculate time taken
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to upload audio files to GCP: {time_taken:.2f} seconds.")

        return json.dumps(data)

    except Exception as e:
        print(f"Error during audio upload to GCP: {e}")
        raise

@audio_router.post("/analysis/audio")
async def start_audio_analysis(upload: Upload):
    return await handle_start_audio_analysis(upload)

@audio_router.subscriber("av:audio_seg")
@audio_router.publisher("av:audio_transcribe")
async def audio_seg(msg: str):
    return await handle_audio_segmentation(msg)

@audio_router.subscriber("av:upload_audio_gcp")
@audio_router.publisher("av:save_analysis_es")
async def upload_audio_gcp(msg: str):
    return await handle_audio_upload_gcp(msg)