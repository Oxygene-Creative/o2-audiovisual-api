from app.agents.rag import invoke_rag_chain
from app.analyzers.llm import llm_transcript_analysis
from fastapi import APIRouter
from pydantic import BaseModel
import json
from app.models.agents import ChatInput

chat_router = APIRouter()

@chat_router.post("/chat")
def ads_and_engagement(request: ChatInput):
    response = invoke_rag_chain(request.question)
    return response

