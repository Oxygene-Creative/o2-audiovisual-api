from fastapi import APIRouter, HTTPException
from typing import List, Dict, Union
from transformers import pipeline
from datetime import datetime
from collections import Counter
from langchain_text_splitters import RecursiveCharacterTextSplitter

router = APIRouter()

# Initialize emotion classifier
emotion_classifier = pipeline(
    "text-classification", 
    model="j-hartmann/emotion-english-distilroberta-base", 
    return_all_scores=True
)

def analyze_emotions(text, chunk_size=300) -> Dict:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)

    emotion_scores = {}
    for chunk in chunks:
        predictions = emotion_classifier(chunk)[0]
        for score in predictions:
            emotion = score['label']
            confidence = score['score']
            if emotion not in emotion_scores:
                emotion_scores[emotion] = 0.0
            emotion_scores[emotion] += confidence  # Sum scores across chunks
    
    # Convert aggregated scores into a list of dicts
    results = [{"label": emotion, "score": score} for emotion, score in emotion_scores.items()]
    return results
    """Check if the emotion analysis service is healthy"""
    try:
        # Test text for health check
        test_text = "I am very happy today!"
        
        # Try to get the classifier
        classifier = get_emotion_classifier()
        
        # Try a test prediction
        predictions = classifier(test_text)[0]
        
        # If we get here, everything is working
        return {
            "status": "healthy",
            "model": "j-hartmann/emotion-english-distilroberta-base",
            "last_checked": datetime.now().isoformat(),
            "test_prediction": {
                "text": test_text,
                "dominant_emotion": max(predictions, key=lambda x: x['score'])['label']
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )