from fastapi import FastAPI
from faststream.redis import RedisRouter

video_router = RedisRouter()

@video_router.subscriber("av_reporting")
async def reporting_handler():
    return


