from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class File(BaseModel):
    url: Optional[str] = ""
    size: Optional[int] = 0


class Ad(BaseModel):
    brand: Optional[str] = ""
    product: Optional[str] = ""
    start: Optional[float] = 0
    stop: Optional[float] = 0


class Audience(BaseModel):
    platform: Optional[str] = ""
    identifier: Optional[str] = ""
    context: Optional[str] = ""
    start: Optional[float] = 0
    stop: Optional[float] = 0


class MediaTypeEnum(str, Enum):
    video = "video"
    audio = "audio"


class Segment(BaseModel):
    start: Optional[float] = 0.0
    stop: Optional[float] = 0.0
    transcript: Optional[str] = ""
    type: Optional[MediaTypeEnum] = None
    sentiment: Optional[str] = ""
    emotions: List[str] = []
    keywords: List[str] = []
    categories: List[str] = []
    topics: List[str] = []
    start_time: Optional[datetime] = None
    file: Optional[File] = File()
    embeddings: List[float] = []
    ads: List[Ad] = []
    audience: List[Audience] = []


class Activity(BaseModel):
    male: Optional[float] = 0.0
    female: Optional[float] = 0.0
    music: Optional[float] = 0.0


class AnalysisModel(BaseModel):
    id: Optional[str] = ""
    stream_id: Optional[str] = ""
    timestamp: Optional[datetime] = None
    activity: Optional[Activity] = Activity()
    segments: List[Segment] = []