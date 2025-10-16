import httpx
from httpx import DigestAuth
import sys
import os
import asyncio
import re
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from difflib import get_close_matches
import os
import stat

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TVH_URL = os.getenv("TVHEADEND_URI")
USERNAME = os.getenv("TVHEADEND_USER")
PASSWORD = os.getenv("TVHEADEND_PASS")
GRAPHQL_URI = os.environ['GRAPHQL_URI']
GRAPHQL_API_KEY = os.environ['GRAPHQL_API_KEY']
MEDIASERVER_URI = os.environ["MEDIASERVER_URI"]

auth = DigestAuth(USERNAME, PASSWORD)

async def get_finished_recordings():
    timeout = httpx.Timeout(10800)
    async with httpx.AsyncClient(timeout=timeout) as client:  # Create client locally
        r = await client.get(
            f"{TVH_URL}/api/dvr/entry/grid_finished", 
            params={"start": 0, "limit": 9999},
            auth=auth
        )
        r.raise_for_status()
        all_entries = r.json().get("entries", [])
        sorted_entries = sorted(all_entries, key=lambda x: x.get("start", 0), reverse=True)
        return sorted_entries

async def delete_recording(uuid):
    timeout = httpx.Timeout(30)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(
                f"{TVH_URL}/api/dvr/entry/remove", 
                params={"uuid": uuid },
                auth=auth
            )
            r.raise_for_status()
            print(f"Deleted recording {uuid}")
    except httpx.HTTPError as e:
        print(f"Failed to delete recording {uuid}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Execution completed for deleting the recording.")

async def upload_recording(
    file_path: str,
    stream_id: str,
    stream_name: str,
    timestamp: str
):
    file_name = Path(file_path).name
    timeout = httpx.Timeout(10800)

    async with httpx.AsyncClient(timeout=timeout) as client:
        with open(file_path, "rb") as f:
            files = {
                "file": (file_name, f, "video/MP2T"),
            }
            data = {
                "stream_id": stream_id,
                "stream_name": stream_name,
                "timestamp": timestamp,
            }

            try:
                response = await client.post(
                    f"{MEDIASERVER_URI}/uploads-from-pi", 
                    files=files, 
                    data=data
                )
                response.raise_for_status()
                print("✅ Uploaded successfully:", response.json())
                return response.json()
            except httpx.ConnectError as e:
                print(f"Connection error occurred while trying to reach {GRAPHQL_URI}: {e}")
                return []
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred with status code {e.response.status_code}: {e.response.text}")
                return []
            except httpx.RequestError as e:
                print(f"An error occurred while handling your request: {e}")
                return []
            

async def get_tv_streams():
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
    variables = { "filter": { } }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": GRAPHQL_API_KEY
    }

    timeout = httpx.Timeout(10800)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(
                GRAPHQL_URI,
                json={"query": query, "variables": variables},
                headers=headers
            )
            r.raise_for_status()
            data = r.json()
            streams = data["data"]["findTvStreams"]
            return streams
        except httpx.ConnectError as e:
            print(f"Connection error occurred while trying to reach {GRAPHQL_URI}: {e}")
            return []
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred with status code {e.response.status_code}: {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"An error occurred while handling your request: {e}")
            return []
    
async def process_and_upload(streams: list, recording_path: str, uuid: str):
    # Extract relevant details from filename
    filename = Path(recording_path).stem
    # pattern = r"[-_](Signet [A-Za-z0-9\s]+)[-_]?(\d{4}-\d{2}-\d{2})[-_]?(\d{2}[:\-]?\d{2})"
    pattern = r"[-_](Signet [A-Za-z0-9\s]+)[-_](\d{4}-\d{2}-\d{2})[-_](\d{2}[-_]\d{2})[-_]?"
    match = re.search(pattern, filename)

    if not match:
        print(f"Invalid filename format: {filename}")
        # raise ValueError(f"Invalid filename format: {filename}")
        return
    
    # Extract TV station, date, and time
    tv_station_name = match.group(1)
    tv_station_name = tv_station_name.replace("Signet", "").strip()
    date = match.group(2)
    timestamp = match.group(3).replace("-", ":")  # Format time as 'HH:MM'

    # Step 1: Match with GraphQL
    stream_names = [stream["tv_stream_name"] for stream in streams]
    best_match = get_close_matches(tv_station_name, stream_names, n=1, cutoff=0.6)  # Adjust cutoff as needed

    if not best_match:
        raise ValueError(f"No matching stream found for: {tv_station_name}")
    
    best_match_name = best_match[0]
    matched_stream = next(stream for stream in streams if stream["tv_stream_name"] == best_match_name)
    stream_id = matched_stream["id"]
    stream_name = matched_stream["tv_stream_name"]

    # Step 2: Upload
    await upload_recording(
        file_path=recording_path,
        stream_id=stream_id,
        stream_name=stream_name,
        timestamp=f"{date}T{timestamp}"
    )

    # Step 3: Remove recording
    await delete_recording(uuid)

async def main():
    # Run the async function
    entries = await get_finished_recordings()
    streams = await get_tv_streams()

    for entry in entries:
        try:
            await process_and_upload(streams, entry.get("filename"), entry.get("uuid"))
        except Exception as e:
            print(e)
            print(f"Stream is not uploaded: {entry.get('uuid')}")

if __name__ == "__main__":
    asyncio.run(main())




