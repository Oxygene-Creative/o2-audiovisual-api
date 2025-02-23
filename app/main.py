from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from faststream.redis.fastapi import RedisRouter as StreamRouter
from app.pipelines.reporting import reporting_router
from app.pipelines.video_analytics import video_router
from app.pipelines.audio_analytics import audio_router
from app.pipelines.transcript_analysis import transcript_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.core.redis import redis_broker
import os

load_dotenv()
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
core_router = StreamRouter(REDIS_URI)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_broker.connect()
    await core_router.broker.connect()
    yield
    await redis_broker.close()
    await core_router.broker.close()
    
app = FastAPI(lifespan=lifespan)

# include faststream handlers

core_router.include_router(reporting_router)
core_router.include_router(video_router)
core_router.include_router(audio_router)
core_router.include_router(transcript_router)

# Include routers for modular endpoints
app.include_router(core_router)
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
# app.include_router(embeddings_router, prefix="/nlp", tags=["embeddings"])
