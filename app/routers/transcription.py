from typing import List
from app.analyzers.transcription import transcribe
from fastapi import APIRouter
from pydantic import BaseModel
import json

from app.core.es import search

transcribe_router = APIRouter()

class TranscribeRequest(BaseModel):
    audio_url: str
    queries: List[str]
    
class TranscriptionRequest(BaseModel):
    indexes: str
    
@transcribe_router.post("/transcribe")
def transcribe(request: TranscribeRequest):
    transcript = transcribe(request.audio_url)
    json_data = json.loads(transcript)
    return json_data

@transcribe_router.post("/transcription")
def get_transcription(request: TranscriptionRequest):
    
    # Search query
    query = {
        "query": {
            "match_all": {}
        },
        "size": 10000
    }

    # Execute search
    result = search(index=request.indexes, query=query)
    all_records = []
    # Print results
    for hit in result['hits']['hits']:
        all_records.append(hit['_source'])
        
    return json.dumps(all_records, indent=2, ensure_ascii=False, default=str)

