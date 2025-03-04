
import os
from app.core.redis import redis_router as reporting_router

@reporting_router.subscriber("av_reporting")
async def reporting_handler():
    return
