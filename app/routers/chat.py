from app.agents.rag import invoke_rag_chain
from fastapi import APIRouter
import json
from app.models.agents import ChatInput

chat_router = APIRouter()

@chat_router.post("/rag")
def rag(request: ChatInput):
    response = invoke_rag_chain(request.question)
    return response

