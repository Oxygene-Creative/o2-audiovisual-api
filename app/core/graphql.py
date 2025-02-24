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
        "X-API-Key": f"{GRAPHQL_API_KEY}"
    }
    try:
        response = requests.post(
            url=GRAPHQL_URI, 
            json={"query": query, "variables": variables },
            headers=headers)
        response.raise_for_status()
        response_json = response.json()
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
    response = fetch_data(query, variables)
    return response['findUniqueTerms']

def get_tags(stream_type: str) -> List[str]:
    query = """
    query ($query: FindTagInput!){
        findTags(query: $query){
            values
        }
    }
    """
    variables = { "query": { "name": stream_type } }
    response = fetch_data(query, variables)
    tags = []
    for res in response['findTags']:
        tags.extend(res['values'])
    return tags

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
    response = fetch_data(query, variables)
    
    return response['findConfigs']
