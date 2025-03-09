from typing import List, Optional
from pydantic import BaseModel, Field

class Competitor(BaseModel):
    name: str
    keywords: List[str]