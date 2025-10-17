from fastapi import FastAPI, Request
from routers.uploads import uploads_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from routers.uploads import uploads_router
from utils.redis import redis_broker
# from streams.segmentation import segmentation_broker
from streams.media_processing import media_processing_broker
from streams.queue import queue_processor
import asyncio 
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

load_dotenv()

class LimitRequestSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        # Check the size of the incoming request
        request_body = await request.body()
        if len(request_body) > self.max_body_size:
            return JSONResponse(
                {"error": "Request size exceeds the allowed limit of 2 GB."}, status_code=413
            )
        return await call_next(request)

app = FastAPI()

# middlewares configs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Set the maximum request size to 2 GB
app.add_middleware(LimitRequestSizeMiddleware, max_body_size=2 * 1024**3)

# include faststream handlers
app.include_router(uploads_router, tags=["uploads"])

@app.on_event("startup")
async def start_app():
    await redis_broker.start()
    # Start the background worker task
    asyncio.create_task(queue_processor())

@app.on_event("shutdown")
async def shutdown_app():
    await redis_broker.close()