from fastapi import FastAPI
from faststream.redis import RedisRouter

reporting_router = RedisRouter()

@reporting_router.subscriber("av_reporting")
async def reporting_handler():
    return


