from fastapi import APIRouter
from app.analyzers.embeddings import embed_images
from app.core.gcp import download_file
from app.core.files import delete_file
import uuid
import os

embeddings_router = APIRouter()

@embeddings_router.post("/image")
def create_image_embeddings(bucket: str, image_url: str, extension: str):
    destination_url = f"{os.getcwd()}/o2-files/{uuid.uuid4()}.{extension}"
    download_file(bucket, image_url, destination_url)
    embeddings = embed_images(destination_url)
    delete_file(destination_url)
    return embeddings
