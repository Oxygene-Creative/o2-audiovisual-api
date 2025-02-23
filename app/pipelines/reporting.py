from fastapi import FastAPI
from faststream.redis import RedisRouter
import os

reporting_router = RedisRouter(os.environ['REDIS_URI'])

@reporting_router.subscriber("av_reporting")
async def reporting_handler():
    return


