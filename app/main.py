from fastapi import FastAPI
from app.api import embeddings

app = FastAPI()

# Include routers for modular endpoints
app.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
