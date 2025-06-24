from app.core.config import setup_env
from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from app.routers.ads import ads_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.core.redis import redis_router
from app.pipelines.audio_analytics import audio_router
from app.pipelines.reporting import reporting_router
from app.pipelines.video_analytics import video_router
from app.pipelines.transcript_analysis import transcript_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.pi_uploads import uploads_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # await redis_broker.connect()
    await redis_router.broker.connect()
    yield
    # await redis_broker.close()
    await redis_router.broker.close()
    
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include faststream handlers
app.include_router(audio_router)
app.include_router(video_router)
app.include_router(transcript_router)
app.include_router(reporting_router)

# Include routers for modular endpoints
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
app.include_router(ads_router, prefix="/analysis", tags=["ads"])
app.include_router(uploads, tags=["uploads"])

@app.on_event("startup")
async def startup_event():
    setup_env()