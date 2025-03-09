from datetime import datetime
from typing import List, Literal
from app.analyzers.llm import llm_transcript_analysis
from fastapi import APIRouter
from pydantic import BaseModel
import json

from app.models.reports import Competitor
from app.reporters.competitors import competitor_analysis
from app.reporters.demographics import demographics_analysis
from app.reporters.mentions import search_mentions

reports_router = APIRouter()

DateRangeType = Literal['daily', 'monthly']

class MentionsRequest(BaseModel):
    indexes: List[str]
    keywords: List[str]
    date: datetime
    date_range: DateRangeType = 'daily',
    
class CompetitorsRequest(BaseModel):
    indexes: List[str]
    competitors: List[Competitor]
    date: datetime
    date_range: DateRangeType = 'daily',
    
class DemographicsRequest(BaseModel):
    date: datetime
    date_range: DateRangeType = 'daily',
    
@reports_router.post("/mentions")
def mentions(request: MentionsRequest):
    result = search_mentions(
        keywords=request.keywords, 
        indexes=request.indexes, 
        date=request.date, 
        date_range = request.date_range
    )
    return result

@reports_router.post("/competitors")
def competitors(request: CompetitorsRequest):
    result = competitor_analysis(
        competitors=request.competitors, 
        indexes=request.indexes, 
        date=request.date,
        date_range = request.date_range
    )
    return result

@reports_router.post("/demographics")
def recordings(request: DemographicsRequest):
    result = demographics_analysis(
        date=request.date,
        date_range=request.date_range
    )
    return result

