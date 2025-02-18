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
    duration: Optional[float] = 0.0
    transcript: Optional[str] = ""
    sentiment: Optional[str] = ""
    emotions: List[str] = []
    keywords: List[str] = []
    categories: List[str] = []
    topics: List[str] = []
    start_time: Optional[datetime] = None
    audio_file: Optional[str] = ""
    video_file: Optional[str] = ""
    embeddings: List[float] = []
    ads: List[Ad] = []
    audience: List[Audience] = []


class Activity(BaseModel):
    male: Optional[float] = 0.0
    female: Optional[float] = 0.0
    music: Optional[float] = 0.0
    noEnergy: Optional[float] = 0.0


class AnalysisModel(BaseModel):
    id: Optional[str] = ""
    stream_id: Optional[str] = ""
    video_path: Optional[str] = ""
    audio_path: Optional[str] = ""
    type: Optional[MediaTypeEnum] = None
    timestamp: Optional[datetime] = None
    activity: Optional[Activity] = Activity()
    segments: List[Segment] = []