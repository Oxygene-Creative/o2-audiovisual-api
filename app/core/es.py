from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Initialize the Elasticsearch client
es = Elasticsearch(
    hosts=["http://localhost:9200"],  # Replace with your Elasticsearch host and port
    http_auth=("username", "password"),  # Optional for authenticated clusters
)

def save(index: str, doc):
    es.index(index=index, document=doc)
    
def save_bulk(actions):
    bulk(es, actions)