from typing import List
from app.analyzers.transcription import transcribe
from fastapi import APIRouter
from pydantic import BaseModel
import json

transcribe_router = APIRouter()

class TranscribeRequest(BaseModel):
    audio_url: str
    queries: List[str]
    
@transcribe_router.post("/transcribe")
def transcribe(request: TranscribeRequest):
    transcript = transcribe(request.audio_url)
    json_data = json.loads(transcript)
    return json_data

