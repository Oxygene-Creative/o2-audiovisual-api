from typing import List
from transformers import pipeline
from app.models.analytics import TagAnalysis
from fuzzywuzzy import process
from app.analyzers.embeddings import embed_text, embedding_model
from app.core.llm import llm
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import torch
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from gensim import corpora
from gensim.models import LdaModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
import asyncio

# Download NLTK resources
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('stopwords')
stop_words = stopwords.words('english')

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def match_keywords(text: str, keywords: List[str]):
    """
    Match words in the text to categories using fuzzy matching.
    """
    # Check if text is empty, None, or whitespace
    if not text or text.isspace():
        return []

    # Check if keywords is empty or None
    if not keywords or not isinstance(keywords, list):
        return []
    # Extract only alphanumeric words and convert to lowercase
    text_words = re.findall(r'\b\w+\b', text.lower())
    matched_keywords = set()

    for word in text_words:
        # Find closest category matches to the word
        match, score = process.extractOne(word, keywords)
        if score > 95:  # Threshold to accept a match
            matched_keywords.add(match)

    return list(matched_keywords) if matched_keywords else []

async def categorize_text(text: str, categories: List[str], threshold=0.3):
    # Check if text is empty, None, or whitespace
    if not text or text.isspace():
        return []

    # Check if keywords is empty or None
    if not categories or not isinstance(categories, list):
        return []
    
    # results = classifier(text, categories, multi_label=True)
    # Offload pipeline execution to a background thread to prevent event loop blocking
    results = await asyncio.to_thread(classifier, text, categories, multi_label=True)

    tags = [
        {"label": label, "score": score} 
        for label, score in zip(results['labels'], results['scores'])
    ]

    return tags 

def preprocess_text(texts):
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    
    processed_texts = []
    
    for text in texts:
        # Remove non-alphanumeric chars and lowercase
        text = re.sub(r'[^\w\s]', '', text).lower()
    
        # Tokenize words
        words = nltk.word_tokenize(text)
        
        # Remove stopwords and lemmatize words
        processed = [lemmatizer.lemmatize(word) 
                     for word in words 
                     if word not in stop_words and len(word) > 1]
        
        if processed:
            processed_texts.append(processed)
    
    return processed_texts



    