from google.cloud import storage
from datetime import datetime


def list_audio_files_in_folder(bucket_name, folder):
    client = storage.Client()
    blobs = client.list_blobs(bucket_name, prefix=folder)

    audio_files = []
    for blob in blobs:
        if blob.name.endswith((".mp3", ".wav", ".aac")):  # Adjust extensions based on your audio formats.
            audio_files.append({
                "blob": blob.name,  # Full path of the audio file in the bucket.
                "timestamp_str": extract_timestamp_from_blob(blob.name),  # Extract timestamp from filename.
            })
    return audio_files


def extract_timestamp_from_blob(blob_name):
    try:
        filename = blob_name.split("/")[-1]  # Extract just the filename.
        timestamp_part = filename.split("_")[-1].split(".")[0]  # e.g., '20241112_161944' or '2025-03-05T16:20:34'
        if len(timestamp_part) == 14:  # Format: YYYYMMDD_HHmmss
            timestamp = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
        else:  # Handle other common timestamp formats like ISO.
            timestamp = datetime.fromisoformat(timestamp_part)
        return timestamp.isoformat()  # Return in ISO format.
    except Exception as e:
        print(f"Error extracting timestamp from blob ({blob_name}): {e}")
        return None


def create_analysis_requests(radio_mapping, bucket_name):
    """
    Generate request objects for analysis based on `radio_mapping` and audio files in the corresponding folders.

    :param radio_mapping: List of dictionaries representing radio mappings (stream_name, stream_id, folders).
    :param bucket_name: Name of the GCP bucket.
    :return: List of request objects for audio analysis.
    """
    requests = []

    for station in radio_mapping:
        stream_name = station["stream_name"]
        stream_id = station["stream_id"]
        folders = station["folders"]

        for folder in folders:
            audio_files = list_audio_files_in_folder(bucket_name, folder)
            for audio_file in audio_files:
                request = {
                    "stream_id": stream_id,
                    "stream_name": stream_name,
                    "bucket": bucket_name,
                    "blob": audio_file["blob"],
                    "timestamp_str": audio_file["timestamp_str"],
                }
                requests.append(request)

    return requests


# Example usage:
def main():
    # Define the mapping of streams to folders.
    radio_mapping = [
        {
            "stream_name": "Radio Jambo",
            "stream_id": "72e7e42e-1450-42db-aa1d-990f3c8f915a",
            "folders": ["radio/Radio Jambo/Folder1", "radio/Radio Jambo/Folder2"]  # Replace with actual folder paths.
        },
        # Add more stations/folder mappings as necessary.
    ]

    # Define your GCP bucket name here.
    bucket_name = "audiovisual-streams"

    # Generate the request objects for analysis.
    requests = create_analysis_requests(radio_mapping, bucket_name)

    # Display the total count of request objects.
    total_requests = len(requests)
    print(f"Total request objects created: {total_requests}")


    # Process each request and display the current object being processed.
    for idx, request in enumerate(requests, start=1):
        print(f"Processing request {idx}/{total_requests}: {request}")
    


if __name__ == "__main__":
    main()