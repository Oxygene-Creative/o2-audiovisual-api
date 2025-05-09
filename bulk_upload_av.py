from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
load_dotenv()
import os
import requests
from datetime import datetime
import time

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


folder_to_station_map = [
    {"folder": "radio/Radio Jambo", "station": {"id": "72e7e42e-1450-42db-aa1d-990f3c8f915a", "radio_stream_name": "Radio Jambo"}},
    {"folder": "radio/Spice FM", "station": {"id": "204a6953-5e8a-4a8d-b60f-51fb97d0a566", "radio_stream_name": "Spice FM"}},
    {"folder": "radio/Ghetto Radio", "station": {"id": "ea2f4b20-b21d-410a-ab98-082fa5a05a6d", "radio_stream_name": "Ghetto Radio"}},
    {"folder": "radio/Classic FM", "station": {"id": "34aa475f-74dd-4737-a4f4-e5cb06de1e27", "radio_stream_name": "Classic 105"}},
    {"folder": "radio/capitalfm", "station": {"id": "3571c245-ff27-4a8f-b096-1df857d78021", "radio_stream_name": "Capital FM"}},  
    {"folder": "radio/classicfm", "station": {"id": "34aa475f-74dd-4737-a4f4-e5cb06de1e27", "radio_stream_name": "Classic 105"}},  
    {"folder": "radio/radiojambo", "station": {"id": "72e7e42e-1450-42db-aa1d-990f3c8f915a", "radio_stream_name": "Radio Jambo"}}, 
    {"folder": "radio/Capital FM", "station": {"id": "3571c245-ff27-4a8f-b096-1df857d78021", "radio_stream_name": "Capital FM"}},
    {"folder": "radio/Classic 105", "station": {"id": "34aa475f-74dd-4737-a4f4-e5cb06de1e27", "radio_stream_name": "Classic 105"}},
    {"folder": "radio/Radio Citizen", "station": {"id": "075d8278-9977-40ba-a0c2-189b4bdd10fa", "radio_stream_name": "Radio Citizen"}},
]


def post_audio_analysis(api_url, stream_id, stream_name, bucket, blob, timestamp_str):
    # Request payload
    payload = {
        "stream_id": stream_id,
        "stream_name": stream_name,
        "bucket": bucket,
        "blob": blob,
        "timestamp_str": timestamp_str
    }

    # Perform the POST request
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

        # Return the JSON response
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting audio analysis data: {e}")
        return None
    

def list_mp3_files_in_folder(bucket_name, folder_name):
    # Initialize the GCS client
    bucket = storage_client.bucket(bucket_name)

    # Add trailing slash to folder name if missing
    if not folder_name.endswith("/"):
        folder_name += "/"

    # Retrieve all objects with the given prefix
    blobs = bucket.list_blobs(prefix=folder_name)
    mp3_files = [
        blob.name for blob in blobs
        if blob.name.startswith(folder_name) and "/" not in blob.name[len(folder_name):] and blob.name.endswith(".mp3")
    ]

    return mp3_files


if __name__ == "__main__":
    api_url = "http://20.55.28.126:8000/analysis/audio"
    bucket_name = "audiovisual-streams" 

    overall_recordings = []
    total_files_count = 0

    # Loop through the folder mappings and calculate total files
    for mapping in folder_to_station_map:
        folder_name = mapping["folder"]  # Get folder name
        station = mapping["station"]

        # Call the function to list all mp3 files in the folder
        mp3_files = list_mp3_files_in_folder(bucket_name, folder_name)

        # Select up to 40 recordings (use slicing to limit)
        selected_recordings = mp3_files[:20]

        # Add the count of mp3 files to the total
        total_files_count += len(mp3_files)

        # Add selected recordings to the overall list and log the count
        overall_recordings.extend([{"blob": file, "station": station} for file in selected_recordings])

     # Print the overall total files count
    print(f"Total mp3 files in root directories across all folders: {total_files_count}")

    print("Posting data to the API...")
    batch_size = 6
    batch_timeout = 12 * 60

    for i in range(0, len(overall_recordings), batch_size):
        # Slice the overall recordings into batches of 6
        batch = overall_recordings[i:i + batch_size]
        
        for recording in batch:
            blob = recording["blob"]
            station = recording["station"]

            try:
                filename = os.path.basename(blob)
                timestamp_raw = filename.split("_")[-2] + "_" + filename.split("_")[-1].replace(".mp3", "")    # Extract "20241120_171643"
                timestamp_dt = datetime.strptime(timestamp_raw, "%Y%m%d_%H%M%S")  # Parse it
                timestamp_str = timestamp_dt.strftime("%Y-%m-%dT%H:%M:%S")  # Format to ISO-8601
            except ValueError:
                print(f"Skipping file with invalid timestamp format: {blob}")
                continue

            response = post_audio_analysis(
                api_url=api_url,
                stream_id=station["id"],
                stream_name=station["radio_stream_name"],
                bucket=bucket_name,
                blob=blob,
                timestamp_str=timestamp_str
            )

            # Log API response
            if response:
                print(f"Successfully posted: {blob}")
                print(f"Response: {response}")
            else:
                print(f"Failed to post: {blob}")

        if i + batch_size < len(overall_recordings):
            time.sleep(batch_timeout)