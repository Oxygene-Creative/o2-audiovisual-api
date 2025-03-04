from fastapi import FastAPI
from faststream.redis import RedisRouter
import os
from app.core.redis import redis_broker

reporting_router = RedisRouter(redis_broker)

@reporting_router.subscriber("av_reporting")
async def reporting_handler():
    return
