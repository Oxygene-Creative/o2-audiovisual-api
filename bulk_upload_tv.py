from google.cloud import storage
from datetime import datetime, timedelta
import re
import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import requests
import uuid
import asyncio

from app.core.gcp import download_file, upload
from app.core.media_processing import extract_audio_from_video
from app.streams.segmentation import replace_mp4_with_mp3
load_dotenv()

credentials_dict = {
    'type': 'service_account',
    'client_id': os.environ['GCP_CLIENT_ID'],
    'client_email': os.environ['GCP_CLIENT_EMAIL'],
    'private_key_id': os.environ['GCP_PRIVATE_KEY_ID'],
    'private_key': os.environ['GCP_PRIVATE_KEY'],
    "token_uri": "https://oauth2.googleapis.com/token",
}

credentials = service_account.Credentials.from_service_account_info(
    credentials_dict
)

storage_client = storage.Client(credentials = credentials, project=os.environ['GCP_PROJECT_ID'])

def list_mp4_recordings(bucket_name, tv_stations, start_date, end_date):

    bucket = storage_client.bucket(bucket_name)
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    results = []
    
    for station in tv_stations:
        tv_id = station["tv_id"]
        tv_name = station["tv_name"]
        
        current_date = start
        while current_date <= end:
            folder = f"tv/{tv_name}/{current_date.isoformat()}"
            blobs = bucket.list_blobs(prefix=folder)
            
            for blob in blobs:
                filename = blob.name.split("/")[-1]
                
                match = re.match(rf"{tv_name}_(\d{{8}}_\d{{4}})\.mp4", filename)
                if match:
                    ts_str = match.group(1)
                    timestamp = datetime.strptime(ts_str, "%Y%m%d_%H%M")
                    
                    results.append({
                        "stream_id": tv_id,
                        "stream_name": tv_name,
                        "bucket": bucket_name,
                        "blob": blob.name,
                        "media_type": "video",
                        "timestamp_str": timestamp.isoformat()
                    })
            current_date += timedelta(days=1)
    
    return results

def post_video_analysis(api_url, payload):
    # Perform the POST request
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

        # Return the JSON response
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting video analysis data: {e}")
        return None


if __name__ == "__main__":
    tv_stations = [
        {"tv_id": "467b7ea3-f99c-4da3-a8b1-57972f039dfd", "tv_name": "KBC"},
        {"tv_id": "832f9552-8639-4a92-b403-9df812b1f6e9", "tv_name": "NTV"},
        {"tv_id": "3c435889-6b8c-4b77-b9d5-c73e6a5d16f3", "tv_name": "Citizen TV"},
        {"tv_id": "3571a9ff-4970-4cc9-8e1c-85eb1a5e8990", "tv_name": "KTN"},
        {"tv_id": "ad33d8b1-4d5b-42a1-b52e-f3b0dc72c2b9", "tv_name": "K24"},
        {"tv_id": "827ebb1f-7d32-4b12-bae6-3005b26a4ba4", "tv_name": "TV47"}
    ]
    api_url = "http://localhost:8000/ingestion"
    bucket_name = "audiovisual-streams" 

    results = list_mp4_recordings(
        bucket_name=bucket_name,
        tv_stations=tv_stations,
        start_date="2025-09-25",
        end_date="2025-09-25"
    )

    for r in results:
        # download video file
        video_file = f"./o2-files/{str(uuid.uuid4())}.mp4"
        download_file(bucket_name, r.get("blob"), video_file)
        # extract audio from video
        soundtrack_file_path = asyncio.run(extract_audio_from_video(video_file))
        # upload audio file
        sound_track_dest = replace_mp4_with_mp3(r.get("blob"))
        upload(bucket_name, soundtrack_file_path, sound_track_dest)
        post_video_analysis(api_url=api_url, payload=r)

    print(len(results))