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

def categorize_text(text: str, categories: List[str], threshold=0.3):
    # Check if text is empty, None, or whitespace
    if not text or text.isspace():
        return []

    # Check if keywords is empty or None
    if not categories or not isinstance(categories, list):
        return []
    
    results = classifier(text, categories, multi_label=True)
    tags = [
        {"label": label, "score": score} 
        for label, score in zip(results['labels'], results['scores'])
    ]
    
    tag_objects = [TagAnalysis(label=t['label'], score=t['score']) for t in tags]
    
    return tag_objects 

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

def lda_topic_modeling(texts, num_topics=5, passes=10):
    # Create a dictionary representation of the documents
    dictionary = corpora.Dictionary(texts)
    
    # Filter extremes with less strict parameters
    dictionary.filter_extremes(
        no_below=1,      # Appear in at least 1 document
        no_above=1.0,    # Can appear in 100% of documents
        keep_n=None      # Don't limit vocabulary size
    )

    # Create a bag-of-words corpus
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # Remove empty documents from corpus
    corpus = [doc for doc in corpus if doc]
    
    # Check if the corpus is empty (no terms left)
    if len(corpus) == 0:
        raise ValueError("Cannot compute LDA over an empty collection (no terms).")
    
    # Train LDA model    
    lda_model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=min(num_topics, len(dictionary)),
        passes=passes,
        alpha=0.1,       # Set a low alpha for more distinct topics
        eta=0.01,        # Set a low eta for more distinct topics
        random_state=42,
        iterations=100,  # Increase iterations
        chunksize=2000,
        eval_every=10    # Evaluate model every 10 iterations
    )
    
    return lda_model, corpus, dictionary

def topic_modelling(text: str, num_topics=3):
    # split text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", " "]
    )
    docs = text_splitter.split_text(text)
    # Fit and transform
    processed_texts = preprocess_text(docs)
    # Check if preprocessing resulted in empty texts
    if not processed_texts:
        return []
    
    lda_model, corpus, dictionary = lda_topic_modeling(processed_texts, num_topics=num_topics)
    
    topic_word_dist = lda_model.state.get_lambda()
    topics = []
    
    for idx, topic_dist in enumerate(topic_word_dist):
        # Get top words and their probabilities
        topic_words = [(lda_model.id2word[id], prob) 
                      for id, prob in enumerate(topic_dist)]
        
        # Sort by probability
        topic_words = sorted(topic_words, key=lambda x: x[1], reverse=True)
        
        # Get top N words with their probabilities
        top_words = topic_words[:5]
        topics.append(top_words)

    prompt = ChatPromptTemplate.from_messages(
        [("user", "I have a topic that is described by the following words: {keywords} Please give a single label to define the topic. The label has to be one or two words maximum")],
    )
    
    chain = prompt | llm | StrOutputParser()
    
    final_topics = []
    
    for topic_words in topics:
        # Create simpler keyword string for labeling
        simple_keywords = ", ".join(word for word, _ in topic_words)
        
        # Get label from chain
        label = chain.invoke({"keywords": simple_keywords})
        
        # Create dictionary with label and words+scores
        final_topics.append({
            "label": label,
            "words": [{
                "word": word,
                "score": float(score)
            } for word, score in topic_words]
        })

    return final_topics



    