from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class Advertisement(BaseModel):
    brand: Optional[str] = Field(description="Brand name being advertised")
    product: Optional[str] = Field(description="Product being advertised")
    start: Optional[float] = Field(description="Timestamp in transcript where ad starts")
    stop: Optional[float] = Field(description="Timestamp in transcript where ad stops")

class AudienceEngagement(BaseModel):
    platform: Optional[str] = Field(description="Social media platform or communication method")
    identifier: Optional[str] = Field(description="Handle, hashtag, phone number, etc.")
    context: Optional[str] = Field(description="Context of the call to action")
    start: Optional[float] = Field(description="Timestamp in transcript the engagement starts")
    start: Optional[float] = Field(description="Timestamp in transcript the engagement stops")

class ShowMetadata(BaseModel):
    host: Optional[str] = Field(description="Name of the radio host(s)")
    program_name: Optional[str] = Field(description="Name of the radio program")
    start: Optional[float] = Field(description="Start timestamp in transcript the host identifies themselves")
    start: Optional[float] = Field(description="Stop timestamp in transcript the host identifies themselves")

class File(BaseModel):
    url: Optional[str] = ""
    size: Optional[int] = 0


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
    gcp_path: Optional[str] = ""
    file_size: Optional[float] = 0.0
    embeddings: List[float] = []
    ads: List[Advertisement] = []
    show_metadata: Optional[ShowMetadata] = None
    engagement: List[AudienceEngagement] = []


class Activity(BaseModel):
    male: Optional[float] = 0.0
    female: Optional[float] = 0.0
    music: Optional[float] = 0.0
    noEnergy: Optional[float] = 0.0

class AnalysisModel(BaseModel):
    id: Optional[str] = ""
    stream_id: Optional[str] = ""
    stream_name: Optional[str] = ""
    gcp_bucket: Optional[str] = ""
    gcp_blob: Optional[str] = ""
    video_path: Optional[str] = ""
    audio_path: Optional[str] = ""
    type: Optional[MediaTypeEnum] = None
    timestamp: Optional[datetime] = None
    activity: Optional[Activity] = Activity()
    segments: List[Segment] = []
    

class LLMAnalysisModel(BaseModel):
    ads: List[Advertisement] = []
    show_metadata: Optional[ShowMetadata] = None
    engagement: List[AudienceEngagement] = []