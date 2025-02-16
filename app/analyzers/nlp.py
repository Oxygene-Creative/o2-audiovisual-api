from transformers import pipeline
from fuzzywuzzy import process
from app.analyzers.embeddings import embed_text, embedding_model
from bertopic import BERTopic
from app.core.llm import llm
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import torch
import re

# Load a pre-trained sentiment analysis pipeline
classifier = pipeline("sentiment-analysis")

# Load BERTopic
topic_model = BERTopic(embedding_model=embedding_model)

def sentiment_analysis(text):
    result = classifier(text)[0]  # Returns a dictionary with label and score
    label = result['label']
    if label == "POSITIVE":
        return "Positive"
    elif label == "NEGATIVE":
        return "Negative"
    else:
        return "Neutral"

def match_keywords(text, keywords):
    """
    Match words in the text to categories using fuzzy matching.
    """
    # Extract only alphanumeric words and convert to lowercase
    text_words = re.findall(r'\b\w+\b', text.lower())
    matched_keywords = set()

    for word in text_words:
        # Find closest category matches to the word
        match, score = process.extractOne(word, keywords)
        print(f"Word: {word}, Match: {match}, Score: {score}")
        if score > 95:  # Threshold to accept a match
            matched_keywords.add(match)

    return list(matched_keywords) if matched_keywords else []

def categorize_text(text, categories, threshold=0.3):
    """
    Categorize text based on semantic similarity to category names.
    """
    # Encode the text and category names
    text_embedding = embed_text(text)
    category_embeddings = embed_text(categories)

    # Compute similarity scores
    similarities = embedding_model.similarity(text_embedding, category_embeddings)[0]
    scores, indices = torch.topk(similarities, k=len(categories))
    
    matched_categories = []
    
    for score, idx in zip(scores, indices):
        if score > threshold:
            matched_categories.append(categories[idx])
    
    return matched_categories 

def topic_modelling(text: list[str]):
    # Fit and transform
    topics, probs = topic_model.fit_transform(text)
    prompt = ChatPromptTemplate.from_messages(
        [("user", "I have a topic that is described by the following keywords: {keywords} Please give a single label to define the topic.")],
    )
    
    chain = prompt | llm | StrOutputParser()
    
    final_topics = []
    
    # Get all topics and their words
    for topic_id in set(topics):  # Use 'set' to ensure unique topic IDs
        if topic_id == -1:  # Skip outlier topic
            continue

        # Fetch the words for the given topic
        words = topic_model.get_topic(topic_id)

        # Convert words to a comma-separated string
        keyword_string = ", ".join([word for word, score in words])
        
        # create human readable labe for the topic
        label = chain.invoke({"keywords": keyword_string })
        
        final_topics.append({ "label": label, "words": words })
        
    return final_topics
    