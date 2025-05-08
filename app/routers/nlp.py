from typing import List, Optional
from app.analyzers.transcription import remove_timestamps_and_format
from fastapi import APIRouter
from app.analyzers.nlp import match_keywords, categorize_text
from app.analyzers.topics import analyze_topics
from app.analyzers.sentiment import sentiment_analysis
from pydantic import BaseModel
import json

nlp_router = APIRouter()

class TextRequest(BaseModel):
    text: str

class CategorizeRequest(BaseModel):
    text: str
    tags: List[str]
    threshold: Optional[float] = 0.3
    
class KeywordsRequest(BaseModel):
    text: str
    queries: List[str]
    
class TopicsRequest(BaseModel):
    text: str
    num_topics: int = 3

@nlp_router.post("/sentiment")
def analyze_sentiment( request: TextRequest ):
    result = sentiment_analysis(request.text)
    return result

@nlp_router.post("/categorization")
async def analyze_categories( request: CategorizeRequest  ):
    result = await categorize_text(request.text, request.tags, request.threshold)
    return result

@nlp_router.post("/keywords")
def analyze_keywords( request: KeywordsRequest ):
    result = match_keywords(request.text, request.queries)
    return result

@nlp_router.post("/topics")
def analyze_topics( request: TopicsRequest ):
    clean_transcript = remove_timestamps_and_format(request.text)
    result = analyze_topics(clean_transcript, num_topics=request.num_topics)
    return result

