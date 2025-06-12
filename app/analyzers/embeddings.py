import mediapipe as mp
import os
from app.analyzers.ai_api_client import APIClient

AI_API_URL = os.getenv("AI_API_URL", "https://ai-api-350748994585.us-central1.run.app")
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

async def embed_text(text: str):
    try:
        client = APIClient(base_url=AI_API_URL)    
        # Emotions example
        embeddings_result = await client.get_embeddings(text=text)
        return embeddings_result
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close()

def embed_images(image_url: str):
    mp_image = mp.Image.create_from_file(image_url)
    options = image_embedding_model_options()
   
    with ImageEmbedder.create_from_options(options) as embedder:
        embedding_result = embedder.embed(mp_image)
        return embedding_result.embeddings[0]
