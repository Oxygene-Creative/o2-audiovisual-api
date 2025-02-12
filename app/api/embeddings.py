from fastapi import APIRouter
from app.analyzers.embeddings import embed_images, embed_text
from app.core.gcp import download_file, delete_file
import uuid

router = APIRouter()

@router.get("/text")
def create_text_embeddings(text: list[str]):
    embeddings = embed_text(text)
    return { "embeddings" : embeddings }

@router.get("/image")
def create_image_embeddings(bucket: str, image_url: str, extension: str):
    destination_url = f"./o2-files/{uuid.uuid4()}.{extension}"
    download_file(bucket, image_url, destination_url)
    embeddings = embed_images(destination_url)
    delete_file(destination_url)
    return embeddings
