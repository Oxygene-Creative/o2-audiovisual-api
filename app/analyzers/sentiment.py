from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

model_name="distilbert-base-uncased-finetuned-sst-2-english"
# Initialize model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def sentiment_analysis(text, chunk_size=300):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)

    # Process each chunk
    chunk_sentiments = []

    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            sentiment_score = probs[0][1].item()  # Assuming positive is index 1
            chunk_sentiments.append(sentiment_score)

    # Calculate average sentiment
    avg_sentiment = np.mean(chunk_sentiments)

    # Classify based on average sentiment
    if avg_sentiment > 0.6:
        return 'positive'
    elif avg_sentiment < 0.4:
        return 'negative'
    else:
        return 'neutral'