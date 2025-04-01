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
from app.reporters.ppt_generators.generate_digital_ppt import generate_pptx

from fastapi.responses import StreamingResponse
from io import BytesIO
import os

reports_router = APIRouter()

DateRangeType = Literal['hourly', 'daily', 'monthly']
ReportFormat = Literal['pptx', 'pdf']

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
    report_date: datetime
    date_range: DateRangeType = 'daily',
    
    
class ReportsRequest(BaseModel):
    date: datetime
    interval: DateRangeType = 'daily',
    format: ReportFormat
    
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


class ReportsRequest(BaseModel):
    date: str 
    interval: DateRangeType = 'daily',
    format: ReportFormat
    
    
@reports_router.post("/generate")
def generate_report(request: ReportsRequest):
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        template_path = os.path.join(BASE_DIR, "app/reporters/ppt_generators", "templates/ppt_template.pptx")
        output_path = os.path.join(BASE_DIR, "app/reporters", "samples/digital_safaricom.pptx")
        data_path = os.path.join(BASE_DIR, "app/reporters", "samples/data/digital_liz.json")
        
        # Load sample data
        with open(data_path, 'r', encoding='utf-8') as f:
            digital_data = json.load(f)
        
        date_obj = datetime.strptime(request.date, '%d-%m-%Y')
        report_date = date_obj.strftime('%d %B %Y')
        
        # Create a BytesIO object to store the presentation
        pptx_buffer = BytesIO()
        
        generate_pptx(
            digital_data, 
            template_path, 
            output_path, 
            request.interval,
            report_date
        )
        
        # Seek to start of buffer
        # pptx_buffer.seek(0)
        
        # Return the file as a downloadable response
        # return StreamingResponse(
        #     pptx_buffer,
        #     media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        #     headers={
        #         'Content-Disposition': f'attachment; filename="report_{request.date}.pptx"'
        #     }
        # )
    except Exception as e:
        print(f"Error in main: {e}")

