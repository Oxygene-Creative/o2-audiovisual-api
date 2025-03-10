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

mapping = {
    "mappings": {
        "properties": {
            "ads": {
                "type": "nested",
                "properties": {
                    "brand": {"type": "text"},
                    "product": {"type": "text"}
                }
            }
        }
    }
}

# Create index with mapping
# es_client.indices.create(index="radio_075d8278-9977-40ba-a0c2-189b4bdd10fa", body=mapping)
# es_client.indices.create(index="radio_204a6953-5e8a-4a8d-b60f-51fb97d0a566", body=mapping)
# es_client.indices.create(index="radio_34aa475f-74dd-4737-a4f4-e5cb06de1e27", body=mapping)
# es_client.indices.create(index="radio_3571c245-ff27-4a8f-b096-1df857d78021", body=mapping)
# es_client.indices.create(index="radio_72e7e42e-1450-42db-aa1d-990f3c8f915a", body=mapping)
# es_client.indices.create(index="radio_ea2f4b20-b21d-410a-ab98-082fa5a05a6d", body=mapping)