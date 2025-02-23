from fastapi import APIRouter
from app.analyzers.nlp import match_keywords, categorize_text, topic_modelling
from app.analyzers.sentiment import sentiment_analysis

router = APIRouter()

@router.get("/sentiment")
def sentiment_analysis( text: str ):
    result = sentiment_analysis(text)
    return result

@router.get("/categorize")
def categorization( text: str, categories: list[str], threshold: float = 0.3  ):
    result = categorize_text(text, categories, threshold)
    return result

@router.get("/keywords")
def categorization( text: str, tags: list[str] ):
    result = match_keywords(text, tags)
    return result

@router.get("/topics")
def topic_models( text: str ):
    result = topic_modelling(text)
    return result

