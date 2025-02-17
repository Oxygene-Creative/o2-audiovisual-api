from fastapi import FastAPI
from faststream.redis import RedisRouter

audio_router = RedisRouter()

@audio_router.subscriber("av_reporting")
async def reporting_handler():
    return


