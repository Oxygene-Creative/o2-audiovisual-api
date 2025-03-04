from app.core.config import setup_env
from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.core.redis import redis_router, redis_broker
import os
from app.pipelines.audio_analytics import audio_router
from app.pipelines.reporting import reporting_router
from app.pipelines.video_analytics import video_router
from app.pipelines.transcript_analysis import transcript_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_broker.connect()
    await redis_router.broker.connect()
    yield
    await redis_broker.close()
    await redis_router.broker.close()
    
app = FastAPI(lifespan=lifespan)

# include faststream handlers
app.include_router(audio_router)
app.include_router(video_router)
app.include_router(transcript_router)
app.include_router(reporting_router)

# Include routers for modular endpoints
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
# app.include_router(embeddings_router, prefix="/nlp", tags=["embeddings"])


@app.on_event("startup")
async def startup_event():
    setup_env()