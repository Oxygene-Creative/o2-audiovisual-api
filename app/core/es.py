from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os

# Initialize the Elasticsearch client
es_client = Elasticsearch(
    hosts=[os.environ['ES_URI']],
    api_key=os.environ['ES_API_KEY']
    # http_auth=(os.environ['ES_USERNAME'], os.environ['ES_PASSWORD']),
)

def save(index: str, doc):
    es_client.index(index=index, document=doc)
    
def save_bulk(actions):
    bulk(es_client, actions)
    
def search(index, query):
    results = es_client.search(index=index, body=query)
    return results