from transformers import pipeline
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

# Download NLTK resources
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('stopwords')
stop_words = stopwords.words('english')

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

    # Filter extremes to remove very rare and overly common words
    dictionary.filter_extremes(no_below=1, no_above=0.8)

    # Create a bag-of-words corpus
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # Check if the corpus is empty (no terms left)
    if len(corpus) == 0:
        raise ValueError("Cannot compute LDA over an empty collection (no terms).")

    # Train LDA model
    lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, passes=passes)

    return lda_model, corpus, dictionary

def topic_modelling(text: str):
    # Fit and transform
    processed_texts = preprocess_text(text)
    # Check if preprocessing resulted in empty texts
    if not processed_texts:
        return []
    
    lda_model, corpus, dictionary = lda_topic_modeling(processed_texts, num_topics=3)
    topics = []
    for idx in range(lda_model.num_topics):
        # Get the top words for the topic
        topic = lda_model.show_topic(idx, topn=5)
        words = [word for word, _ in topic]
        topics.append(words)
    
    prompt = ChatPromptTemplate.from_messages(
        [("user", "I have a topic that is described by the following keywords: {keywords} Please give a single label to define the topic.")],
    )
    
    chain = prompt | llm | StrOutputParser()
    
    final_topics = []
    
    # Get all topics and their words
    for words in topics:
        keyword_string = ", ".join(words)
        # create human readable labe for the topic
        label = chain.invoke({"keywords": keyword_string })
        final_topics.append({ "label": label, "words": words })
        
    return final_topics



    