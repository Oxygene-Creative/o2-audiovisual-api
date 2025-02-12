from sentence_transformers import SentenceTransformer
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

model = SentenceTransformer("all-MiniLM-L6-v2")

BaseOptions = mp.tasks.BaseOptions
ImageEmbedder = mp.tasks.vision.ImageEmbedder
ImageEmbedderOptions = mp.tasks.vision.ImageEmbedderOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = ImageEmbedderOptions(
    base_options=BaseOptions(model_asset_path='/path/to/model.tflite'),
    quantize=True,
    running_mode=VisionRunningMode.IMAGE)

def embed_text(sentences):
    embeddings = model.encode(sentences)
    return embeddings

def embed_images(image_url: str):
    mp_image = mp.Image.create_from_file(image_url)
    
    with ImageEmbedder.create_from_options(options) as embedder:
        embedding_result = embedder.embed(mp_image)
        return embedding_result.embeddings[0]
