from app.core.config import setup_env
from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.core.redis import redis_router, redis_broker
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_broker.connect()
    yield
    await redis_broker.connect()
    
app = FastAPI(lifespan=lifespan)

# include faststream handlers
app.include_router(redis_router)

# Include routers for modular endpoints
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
# app.include_router(embeddings_router, prefix="/nlp", tags=["embeddings"])


@app.on_event("startup")
async def startup_event():
    setup_env()