import asyncio
import logging
from app.core.config import setup_env
from fastapi import FastAPI
from app.routers.ads import ads_router
from app.routers.ingestion import ingestion_router
from dotenv import load_dotenv
from app.streams.asr import asr_broker
from app.streams.audience import audience_broker
from app.streams.llm import llm_broker
from app.streams.nlp import nlp_broker
from app.streams.segmentation import segmentation_broker
from app.streams.queue import queue_processor
from fastapi.middleware.cors import CORSMiddleware
from app.routers.pi_uploads import uploads_router
from app.core.redis import redis_broker
import os
import urllib3

# disable ssl warnings
urllib3.disable_warnings()

load_dotenv()
os.environ["GRPC_FORK_SUPPORT_ENABLED"] = "0"

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for modular endpoints
app.include_router(ads_router, prefix="/analysis", tags=["ads"])
app.include_router(uploads_router, tags=["uploads"])
app.include_router(ingestion_router, tags=["ingestion"])

@app.on_event("startup")
async def start_app():
    while True:
        try:
            await redis_broker.start()
            break
        except Exception as exc:
            logger.error(
                "Redis broker startup failed, retrying in 3s: %s",
                exc,
            )
            await asyncio.sleep(3)

    setup_env()
    # Start the background worker task
    asyncio.create_task(queue_processor())

@app.on_event("shutdown")
async def shutdown_app():
    await redis_broker.close()