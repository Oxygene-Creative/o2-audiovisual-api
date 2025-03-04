from app.core.config import setup_env
from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.core.redis import redis_router
import os

load_dotenv()
# REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
# core_router = StreamRouter(REDIS_URI)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_router.broker.connect()
    yield
    await redis_router.broker.connect()
    
app = FastAPI(lifespan=lifespan)

# include faststream handlers
app.include_router(redis_router)

# Include routers for modular endpoints
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
# app.include_router(embeddings_router, prefix="/nlp", tags=["embeddings"])


@app.on_event("startup")
async def startup_event():
    setup_env()