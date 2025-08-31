from typing import List
from fuzzywuzzy import process
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from app.analyzers.ai_api_client import APIClient
import os

AI_API_URL = os.getenv("AI_API_URL", "https://ai-api2-350748994585.us-central1.run.app")

# Download NLTK resources
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('stopwords')
stop_words = stopwords.words('english')

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

async def categorize_text(data: List):
    try:
        client = APIClient(base_url=AI_API_URL)  
        categories_result = await client.get_categories(data=data)
        return categories_result
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close() 

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



    