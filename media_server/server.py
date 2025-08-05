from fastapi import FastAPI
from routers.uploads import uploads_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.routers.pi_uploads import uploads_router

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