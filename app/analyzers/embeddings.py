from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_sentences(sentences):
    embeddings = model.encode(sentences)
    return embeddings

def embed_images(image):
    return