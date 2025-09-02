from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os

# Initialize the Elasticsearch client
es_client = Elasticsearch(
    hosts=[os.getenv('ELASTIC_CLOUD_URL')],
    api_key=os.getenv('ELASTIC_API_KEY')
)

def save(index: str, doc):
    es_client.index(index=index, document=doc)
    
def save_bulk(actions):
    bulk(es_client, actions)
    
def search(index, query):
    results = es_client.search(index=index, body=query)
    return results

async def fetch_stream_data(data: list[dict]):
    response = es_client.mget(body={"docs": data})
    results = [
        {
            "_index": doc["_index"],
            "_id": doc["_id"],
            "_source": doc["_source"] if doc["found"] else None,
        }
        for doc in response["docs"]
    ]
    return results

async def update_stream_data(data: list[dict], status: dict):
    actions = []

    for doc in data:
        doc["_updates"]["status"] = status
        actions.append({
            "_op_type": "update",
            "_index": doc.get("_index"),
            "_id": doc.get("_id"),
            "doc": doc.get("_updates", {})
        })

    save_bulk(actions)

    return actions
