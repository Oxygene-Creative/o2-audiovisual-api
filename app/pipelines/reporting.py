from fastapi import FastAPI
from faststream.redis import RedisRouter
import os
from app.core.redis import redis_broker


@redis_broker.subscriber("av_reporting")
async def reporting_handler():
    return


