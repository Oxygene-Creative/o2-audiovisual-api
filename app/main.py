from app.agents.rag import create_rag_chain
from app.core.config import setup_env
from app.models.agents import RAGQueryInput
from fastapi import FastAPI
from app.routers.embeddings import embeddings_router
from app.routers.ads import ads_router
from app.routers.transcription import transcribe_router
from app.routers.nlp import nlp_router
from app.routers.reports import reports_router
from app.routers.chat import chat_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.core.redis import redis_router, redis_broker
import os
from app.pipelines.audio_analytics import audio_router
from app.pipelines.reporting import reporting_router
from app.pipelines.video_analytics import video_router
from app.pipelines.transcript_analysis import transcript_router
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

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

# include langchain remote runnables via langserve
rag_chain = create_rag_chain()
add_routes(
    app,
    rag_chain,
    path="/rag-chain",
    input_type=RAGQueryInput,
)

# Include routers for modular endpoints
app.include_router(embeddings_router, prefix="/embeddings", tags=["embeddings"])
app.include_router(ads_router, prefix="/analysis", tags=["ads"])
app.include_router(nlp_router, prefix="/analysis", tags=["nlp"])
app.include_router(transcribe_router, prefix="/analysis", tags=["transcription"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])

@app.on_event("startup")
async def startup_event():
    setup_env()