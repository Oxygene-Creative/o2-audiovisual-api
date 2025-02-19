from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from faststream.redis.fastapi import RedisRouter as StreamRouter
from app.pipelines.reporting import reporting_router
from app.pipelines.video_analytics import video_router
from app.pipelines.audio_analytics import audio_router
from app.pipelines.transcript_analysis import transcript_router
from faststream.redis import RedisBroker
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

broker = RedisBroker(
    os.environ['REDIS_URI'],  
    connection_kwargs={
        "decode_responses": True
    }
)
broker = RedisBroker()

core_router = StreamRouter()

# include faststream handlers
core_router.include_router(reporting_router)
core_router.include_router(video_router)
core_router.include_router(audio_router)
core_router.include_router(transcript_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    yield
    await broker.close()
    
app = FastAPI(lifespan=lifespan)

# Include routers for modular endpoints
app.include_router(core_router)
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
