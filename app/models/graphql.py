from typing import List
from pydantic import BaseModel
from enum import Enum

class TvStream(BaseModel):
    id: str
    tv_stream_name: str
    streaming_link: str
    format: str
    
class RadioStream(BaseModel):
    id: str
    radio_stream_name: str
    streaming_link: str
    alt_streaming_link: str
    format: str

class PrintType(Enum):
    NEWSPAPER = "NEWSPAPER"
    MAGAZINE = "MAGAZINE"
      
class PrintStream(BaseModel):
    id: str
    parent_organization: str
    print_name: str
    print_type: PrintType
    
class WebsiteType(Enum):
    BLOG = "BLOG"
    NEWS = "NEWS"
    
class WebsiteStream(BaseModel):
    id: str
    website_name: str
    website_address: str
    website_type: WebsiteType
    
class Language(BaseModel):
    id: str
    language_name: str
    language_shortcode: str
    
class Tag(BaseModel):
    id: str
    name: str
    values: List[str]
    
class Config(BaseModel):
    key: str
    value: str