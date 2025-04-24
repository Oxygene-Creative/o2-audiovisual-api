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
