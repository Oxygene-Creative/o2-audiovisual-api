import httpx
from httpx import DigestAuth
import sys
import os
import asyncio
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TVH_URL = os.getenv("TVHEADEND_URI")
USERNAME = os.getenv("TVHEADEND_USER")
PASSWORD = os.getenv("TVHEADEND_PASS")
GRAPHQL_URI = os.environ['GRAPHQL_URI']
GRAPHQL_API_KEY = os.environ['GRAPHQL_API_KEY']

auth = DigestAuth(USERNAME, PASSWORD)

async def get_finished_recordings(client):
    r = await client.get(
        f"{TVH_URL}/api/dvr/entry/grid_finished", 
        params={"start": 0, "limit": 9999},
        auth=auth)
    r.raise_for_status()
    return r.json().get("entries", [])

async def delete_recording(client, uuid):
    r = await client.post(
        f"{TVH_URL}/api/dvr/entry/remove", 
        json={"uuid": uuid},
        auth=auth)
    r.raise_for_status()
    print(f"Deleted recording {uuid}")

async def upload_recording(
    file_path: str,
    stream_id: str,
    stream_name: str,
    timestamp: str,
    api_url: str = "http://monitorapi.oxygenehosting.com/api/av/uploads-from-pi"
):
    file_name = Path(file_path).name

    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            files = {
                "file": (file_name, f, "video/MP2T"),
            }
            data = {
                "stream_id": stream_id,
                "stream_name": stream_name,
                "timestamp": timestamp,
            }
            response = await client.post(api_url, files=files, data=data)
            response.raise_for_status()
            print("✅ Uploaded successfully:", response.json())
            return response.json()

async def get_tv_stream(stream_name: str):
    query = """
    query ($filter: FindTvStreamsInput!){
        findTvStreams(filter: $filter){
            id
            tv_stream_name
            streaming_link
            format
        }
    }
    """
    variables = { "filter": { "status": "active" } }
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": GRAPHQL_API_KEY
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GRAPHQL_URI,
            json={"query": query, "variables": variables},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        streams = data["data"]["findTvStreams"]
        return streams

async def process_and_upload(recording_path: str):
    from datetime import datetime

    # Example: extract name + time from filename
    # E.g. "1pm news Citizen TV-2025-06-26.ts"
    filename = Path(recording_path).stem
    parts = filename.rsplit("-", 1)
    stream_name = parts[0].rsplit(" ", 1)[-1].strip()
    timestamp = parts[1] + "T13:00"  # Or extract from metadata

    # Step 1: Match with GraphQL
    stream = await get_tv_stream(stream_name)
    stream_id = stream["id"]

    # Step 2: Upload
    await upload_recording(
        file_path=recording_path,
        stream_id=stream_id,
        stream_name=stream_name,
        timestamp=timestamp
    )


def match_video_with_platform():
    return

# Run the async function
import asyncio
entries = asyncio.run(get_finished_recordings())
len(entries)

# Regular expression to extract the date, time, and TV stream name
pattern = r"-([A-Za-z0-9\s]+)-(\d{4}-\d{2}-\d{2})-(\d{2}-\d{2})-"
match = re.search(pattern, entries[0].get('filename'))

if match:
    tv_stream_name = match.group(1)
    date = match.group(2)
    time = match.group(3).replace('-', ':')  # Format time as 'HH:MM'
    
    print(f"TV Stream Name: {tv_stream_name.strip()}")
    print(f"Date: {date}")
    print(f"Time: {time}")
else:
    print("Data not found in the file name.")


