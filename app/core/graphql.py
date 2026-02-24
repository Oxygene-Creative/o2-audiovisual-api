import logging
import os
from typing import Any, List, Optional

import requests
from dotenv import load_dotenv

from app.models.graphql import Config

load_dotenv()

logger = logging.getLogger(__name__)

GRAPHQL_URI = os.environ["GRAPHQL_URI"]
GRAPHQL_API_KEY = os.environ["GRAPHQL_API_KEY"]


def _summarize_query(query: str) -> str:
    if not query:
        return "<empty>"
    for line in query.splitlines():
        stripped = line.strip()
        if stripped.startswith("query") or stripped.startswith("mutation"):
            return stripped
    return query.strip().splitlines()[0]


def fetch_data(query: str, variables: Optional[Any]):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": f"{GRAPHQL_API_KEY}"
    }
    try:
        response = requests.post(
            url=GRAPHQL_URI,
            json={"query": query, "variables": variables},
            headers=headers,
            verify=False)
        response.raise_for_status()
        response_json = response.json()

        # Check for errors in response
        if "errors" in response_json:
            logger.error(
                "GraphQL errors for %s: %s",
                _summarize_query(query),
                response_json["errors"],
            )
            return None

        return response_json['data']

    except requests.exceptions.RequestException as e:
        logger.error(
            "GraphQL request failed for %s: %s",
            _summarize_query(query),
            e,
        )
        try:
            logger.error(
                "GraphQL response status=%s body=%s",
                response.status_code,
                response.text,
            )
        except Exception:
            logger.debug("GraphQL response details unavailable", exc_info=True)
        return None


async def get_all_terms():
    query = """
    query {
        findUniqueTerms
    }
    """
    variables = {}
    try:
        response = fetch_data(query, variables)
        return response['findUniqueTerms']
    except Exception as e:
        logger.error("Error fetching terms: %s", e, exc_info=True)


async def get_tags(stream_type: str) -> List[str]:
    query = """
    query ($query: FindTagInput!){
        findTags(query: $query){
            values
        }
    }
    """
    variables = {"query": {"name": stream_type}}
    try:
        response = fetch_data(query, variables)
        tags = []

        for res in response['findTags']:
            tags.extend(res['values'])
        return tags
    except Exception as e:
        logger.error("Error fetching tags: %s", e, exc_info=True)
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
    variables = {"query": {}}
    try:
        response = fetch_data(query, variables)
        return response['findConfigs']
    except Exception as e:
        logger.error("Error fetching configs: %s", e, exc_info=True)
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
        if not response:
            return None
        return response["addTvStreamUpload"]
    except Exception as e:
        logger.error("Error adding TV stream upload: %s", e, exc_info=True)
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
        if not response:
            return None
        return response["addRadioStreamUpload"]
    except Exception as e:
        logger.error("Error adding radio stream upload: %s", e, exc_info=True)
        return None


async def fetch_industries():
    query = """
    query {
        findIndustries(query: {}){
            name
            value
        }
    }
    """
    variables = None
    try:
        response = fetch_data(query, variables)
        if not response:
            return []
        data = response.get("findIndustries")
        if not data:
            logger.warning("GraphQL findIndustries returned empty data")
            return []

        all_sub_sectors = []
        for item in data:
            value = item.get("value") if isinstance(item, dict) else None
            if not value:
                continue
            sub_sectors = [s.strip() for s in value.split(",")]
            all_sub_sectors.extend(sub_sectors)

        return all_sub_sectors
    except Exception as e:
        logger.error("Error in fetching industries: %s", e, exc_info=True)
        return []


async def update_last_seen(stream_type: str, stream_id: str, timestamp: str):
    mutation = """
    mutation ($id: String!, $stream: String!, $timestamp: String!){
        updateLastSeen(id: $id, stream: $stream, timestamp: $timestamp)
    }
    """
    variables = {"id": stream_id,
                 "stream": stream_type, "timestamp": timestamp}
    try:
        response = fetch_data(mutation, variables)
        if not response:
            return None
        data = response["updateLastSeen"]

        return data
    except Exception as e:
        logger.error("Error updating last seen: %s", e, exc_info=True)
        return None
