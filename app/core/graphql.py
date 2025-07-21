import requests
from typing import List, Any
import os
from dotenv import load_dotenv

from app.models.graphql import Config

load_dotenv()

GRAPHQL_URI = os.environ['GRAPHQL_URI']
GRAPHQL_API_KEY = os.environ['GRAPHQL_API_KEY']

def fetch_data(query: str, variables: Any):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": f"{GRAPHQL_API_KEY}"
    }
    try:
        response = requests.post(
            url=GRAPHQL_URI, 
            json={"query": query, "variables": variables },
            headers=headers,
            verify=False)
        response.raise_for_status()
        response_json = response.json()

        # Check for errors in response
        if "errors" in response_json:
            error_message = response_json["errors"]
            raise Exception(f"GraphQL error: {error_message}")

        return response_json['data']
    
    except requests.exceptions.RequestException as e:
        # Handle specific exceptions or log the error as needed
        print(f"Request failed: {e}")
        return None

def get_all_terms() -> List[str]:
    query = """
    query {
        findUniqueTerms
    }
    """
    variables = { }
    try:
        response = fetch_data(query, variables)
        return response['findUniqueTerms']
    except Exception as e:
        print(f"Error fetching terms: {e}")  # Optional: log the error

async def get_tags(stream_type: str) -> List[str]:
    query = """
    query ($query: FindTagInput!){
        findTags(query: $query){
            values
        }
    }
    """
    variables = { "query": { "name": stream_type } }
    try:
        response = fetch_data(query, variables)
        tags = []
        
        for res in response['findTags']:
            tags.extend(res['values'])
        return tags
    except Exception as e:
        print(f"Error fetching terms: {e}")  # Optional: log the error
        return ["sports", "news", "lifestyle", "education", "energy"]

def get_configs() -> List[Config]:
    query = """ 
    query ($query: FindConfigInput!){
        findConfigs(query: $query){
            key
            value
        }
    }
    """
    variables = { "query": {} }
    try:
        response = fetch_data(query, variables)
        return response['findConfigs']
    except Exception as e:
        print(f"Error fetching terms: {e}")  # Optional: log the error
        return None

def add_tv_stream_upload(
    tv_stream_id: str,
    file_path: str,
    file_name: str,
    file_size: float,
    timestamp: str,
    male: float,
    female: float,
    music: float,
    noise: float,
    noEnergy: float,
    recording_id: str,
    duration: float
) -> dict:
    query = """
    mutation ($data: AddTvStreamUploadInput!) {
        addTvStreamUpload(data: $data) {
            id
        }
    }
    """
    variables = {
        "data": {
            "tv_stream_id": tv_stream_id,
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "timestamp": timestamp,
            "male": male,
            "female": female,
            "music": music,
            "noise": noise,
            "noEnergy": noEnergy,
            "recording_id": recording_id,
            "duration": duration
        }
    }
    try:
        response = fetch_data(query, variables)
        if "errors" in response:
            print(f"GraphQL errors in adding TV stream upload: {response['errors']}")
            return None
        return response["addTvStreamUpload"]
    except Exception as e:
        print(f"Error adding TV stream upload: {e}")
        return None

def add_radio_stream_upload(
    radio_stream_id: str,
    file_path: str,
    file_name: str,
    file_size: float,
    timestamp: str,
    male: float,
    female: float,
    music: float,
    noise: float,
    noEnergy: float,
    recording_id: str,
    duration: float
) -> dict:
    query = """
    mutation ($data: AddRadioStreamUploadInput!) {
        addRadioStreamUpload(data: $data) {
            id
        }
    }
    """
    variables = {
        "data": {
            "radio_stream_id": radio_stream_id,
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "timestamp": timestamp,
            "male": male,
            "female": female,
            "music": music,
            "noise": noise,
            "noEnergy": noEnergy,
            "recording_id": recording_id,
            "duration": duration
        }
    }
    try:
        response = fetch_data(query, variables)
        if "errors" in response:
            print(f"GraphQL errors in adding radio stream upload: {response['errors']}")
            return None
        return response["addRadioStreamUpload"]
    except Exception as e:
        print(f"Error adding Radio stream upload: {e}")
        return None
    
async def fetch_industries():
    query = """
    query ($query: FindIndustryInput!){
    findIndustries(query: $query){
        name
        value
    }
    }
    """
    variables = { "query": {}}
    try:
        response = fetch_data(query, variables)
        if "errors" in response:
            print(f"GraphQL errors in fetching industries: {response['errors']}")
            return None
        data = response["findIndustries"]
    
        all_sub_sectors = []
        for item in data:
            sub_sectors = [s.strip() for s in item["value"].split(",")]
            all_sub_sectors.extend(sub_sectors)

        return all_sub_sectors
    except Exception as e:
        print(f"Error  in fetching industries: {e}")
        return None