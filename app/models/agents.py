from typing import List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ChatInput(BaseModel):
    question: str
    session_id: str = Field(default=None)

class Citation(BaseModel):
    source_id: int = Field(description="The integer ID of a SPECIFIC source which justifies the answer.")
    quote: str = Field(description="The VERBATIM quote from the specified source that justifies the answer.")

class QuotedAnswer(BaseModel):
    """Answer the user question based only on the given sources, and cite the sources used."""

    answer: str = Field(description="The answer to the user question, which is based only on the given sources.")
    citations: List[Citation] = Field(description="Citations from the given sources that justify the answer.")
    
class ChatResponse(BaseModel):
    answer: QuotedAnswer
    session_id: str