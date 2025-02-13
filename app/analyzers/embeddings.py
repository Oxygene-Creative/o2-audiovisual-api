from sentence_transformers import SentenceTransformer
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import torch

# Check if a GPU is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device=device)

BaseOptions = mp.tasks.BaseOptions
ImageEmbedder = mp.tasks.vision.ImageEmbedder
ImageEmbedderOptions = mp.tasks.vision.ImageEmbedderOptions
VisionRunningMode = mp.tasks.vision.RunningMode

IMAGE_EMBEDDER_MODEL_PATH = f"{os.getcwd()}/app/models/mobilenet_v3_small_075_224_embedder.tflite"

options = ImageEmbedderOptions(
    base_options=BaseOptions(model_asset_path=IMAGE_EMBEDDER_MODEL_PATH),
    quantize=True,
    running_mode=VisionRunningMode.IMAGE)

def embed_text(sentences):
    embeddings = embedding_model.encode(sentences)
    return embeddings

def embed_images(image_url: str):
    mp_image = mp.Image.create_from_file(image_url)
    
    with ImageEmbedder.create_from_options(options) as embedder:
        embedding_result = embedder.embed(mp_image)
        return embedding_result.embeddings[0]
