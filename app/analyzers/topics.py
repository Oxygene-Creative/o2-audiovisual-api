from app.agents.prompts import TOPIC_NAME_PROMPT
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from langchain.prompts import PromptTemplate
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.llm import llm
from langchain_core.output_parsers import StrOutputParser

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight embedding model

def get_top_keywords(documents, num_keywords=5):
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    keywords_per_cluster = []
    for i in range(X.shape[0]):
        tfidf_scores = zip(feature_names, X[i, :].toarray()[0])
        sorted_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)[:num_keywords]
        keywords_per_cluster.append([word for word, _ in sorted_keywords])
    return keywords_per_cluster

def analyze_topics(text: str, chunk_size=300):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_text(text)
    embeddings = embedding_model.encode(texts)

    # Cluster Embeddings (KMeans for simplicity)
    n_clusters = 3  # Choose number of clusters (topics)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    # Group texts into clusters
    clustered_texts = {}
    for idx, label in enumerate(labels):
        clustered_texts.setdefault(label, []).append(texts[idx])

    # Extract Keywords per Cluster (Using TF-IDF)
    cluster_keywords = {}
    for cluster, texts_in_cluster in clustered_texts.items():
        cluster_keywords[cluster] = get_top_keywords(texts_in_cluster)


    prompt_template = PromptTemplate(
        input_variables=["keywords"],
        template=TOPIC_NAME_PROMPT
    )

    topic_names = []
    for cluster, keywords in cluster_keywords.items():
        keywords_str = ", ".join(sum(keywords, [])) 
        prompt = prompt_template.format(keywords=keywords_str)
        ai_message  = llm.invoke(prompt)
        topic_name = ai_message.content.strip()

        topic_names.append({
            "label": topic_name,
            "keywords": keywords_str
        })

    return topic_names