from fastapi import FastAPI
from faststream.redis import fastapi
import os
from app.core.redis import redis_broker

REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
reporting_router = fastapi.RedisRouter(REDIS_URI)

@reporting_router.subscriber("av_reporting")
async def reporting_handler():
    return
