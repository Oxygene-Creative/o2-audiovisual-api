from fastapi import FastAPI
from routers.uploads import uploads_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from routers.uploads import uploads_router
from utils.redis import redis_broker
from streams.segmentation import segmentation_broker

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include faststream handlers
app.include_router(uploads_router, tags=["uploads"])

@app.on_event("startup")
async def start_app():
    await redis_broker.start()

@app.on_event("shutdown")
async def shutdown_app():
    await redis_broker.close()