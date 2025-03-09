from app.analyzers.llm import llm_transcript_analysis
from fastapi import APIRouter
from pydantic import BaseModel
import json

ads_router = APIRouter()

class TextRequest(BaseModel):
    text: str
    
@ads_router.post("/ads-and-engagement")
def ads_and_engagement(request: TextRequest):
    data = llm_transcript_analysis(request.text)
    json_data = json.loads(data.model_dump_json())
    return json_data

