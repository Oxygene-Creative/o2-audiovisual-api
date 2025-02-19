from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from faststream.redis.fastapi import RedisRouter as StreamRouter
from app.pipelines.reporting import reporting_router
from app.pipelines.video_analytics import video_router
from app.pipelines.audio_analytics import audio_router
from app.pipelines.transcript_analysis import transcript_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await audio_router.broker.connect()
    await video_router.broker.connect()
    await transcript_router.broker.connect()
    await reporting_router.broker.connect()
    yield
    await audio_router.broker.close()
    await video_router.broker.close()
    await transcript_router.broker.close()
    await reporting_router.broker.close()
    
app = FastAPI(lifespan=lifespan)

# include faststream handlers
core_router = StreamRouter()
core_router.include_router(reporting_router)
core_router.include_router(video_router)
core_router.include_router(audio_router)
core_router.include_router(transcript_router)

# Include routers for modular endpoints
app.include_router(core_router)
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
