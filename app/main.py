from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from faststream.redis.fastapi import RedisRouter as StreamRouter
from app.pipelines.reporting import reporting_router
from app.pipelines.video_analytics import video_router
from app.pipelines.audio_analytics import audio_router
from app.pipelines.transcript_analysis import transcript_router

core_router = StreamRouter()

# include faststream handlers
core_router.include_router(reporting_router)
core_router.include_router(video_router)
core_router.include_router(audio_router)
core_router.include_router(transcript_router)

app = FastAPI()

# Include routers for modular endpoints
app.include_router(core_router)
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
