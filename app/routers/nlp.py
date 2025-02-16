from fastapi import APIRouter
from app.analyzers.nlp import analyze_sentiment_transformers, categorize_text_with_embeddings, match_keywords_with_fuzzy_matching

router = APIRouter()

@router.get("/sentiment")
def sentiment_analysis( text: str ):
    result = analyze_sentiment_transformers(text)
    return result

@router.get("/categorization")
def categorization( text: str, categories: list[str], threshold: float = 0.3  ):
    result = categorize_text_with_embeddings(text, categories, threshold)
    return result

@router.get("/keywords")
def categorization( text: str, categories: list[str] ):
    result = match_keywords_with_fuzzy_matching(text, categories)
    return result

