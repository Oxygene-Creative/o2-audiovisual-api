import mediapipe as mp
import os
import torch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Check if a GPU is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    device = device.type)

ImageEmbedder = mp.tasks.vision.ImageEmbedder
    
def image_embedding_model_options():
    BaseOptions = mp.tasks.BaseOptions
    ImageEmbedderOptions = mp.tasks.vision.ImageEmbedderOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    IMAGE_EMBEDDER_MODEL_PATH = f"{os.getcwd()}/app/models/mobilenet_v3_small_075_224_embedder.tflite"

    options = ImageEmbedderOptions(
        base_options=BaseOptions(model_asset_path=IMAGE_EMBEDDER_MODEL_PATH),
        quantize=True,
        running_mode=VisionRunningMode.IMAGE)

    return options

def embed_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    docs = text_splitter.split_text(text)
    embeddings = embedding_model.encode(docs)
    return embeddings

def embed_images(image_url: str):
    mp_image = mp.Image.create_from_file(image_url)
    options = image_embedding_model_options()
   
    with ImageEmbedder.create_from_options(options) as embedder:
        embedding_result = embedder.embed(mp_image)
        return embedding_result.embeddings[0]
