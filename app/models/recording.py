from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timedelta
from app.models.analytics import Activity, AnalysisModel, Advertisement, AudienceEngagement, TagAnalysis, Topic
import uuid

class SegmentRecording(BaseModel):
    recording_id: str
    timestamp: datetime
    # Core segment details
    duration: float = 0.0
    raw_text: Optional[str] = ""
    language: Optional[str] = ""
    language_score: Optional[float] = 0.0
    sentiment: Optional[str] = ""
    emotions: List[str] = []
    embeddings: List[float] = []
    keywords: List[str] = []
    tags: List[TagAnalysis] = []
    topics: List[Topic] = []
    # Advertisement details
    ads: List[Advertisement] = []
    # Audience engagement details
    engagement: List[AudienceEngagement] = []
    # File and path information
    gcp_blob: str = ""
    gcp_path: str = ""
    file_size: Optional[float] = 0.0
    # Program metadata
    host: Optional[str] = ""
    program_name: Optional[str] = ""

    @classmethod
    def create_segment_recordings_from_dict(cls, data: dict) -> List["SegmentRecording"]:
        segment_recordings = []

        # Iterate over each segment in the JSON data
        for segment in data.get("segments", []):
            # Derive the absolute timestamp for the segment
            timestamp = datetime.fromisoformat(data["timestamp"]) + timedelta(seconds=segment.get("start", 0.0))

            # Create an instance of SegmentRecording for this segment
            segment_record = cls(
                recording_id=data.get("id", ""),
                timestamp=timestamp,
                duration=segment.get("duration", 0.0),
                raw_text=segment.get("raw_text", ""),
                language=segment.get("language", ""),
                language_score=segment.get("language_score", 0.0),
                sentiment=segment.get("sentiment", ""),
                emotions=segment.get("emotions", []),
                embeddings=segment.get("embeddings", []),
                keywords=segment.get("keywords", []),
                tags=[TagAnalysis(**tag) for tag in segment.get("tags", [])],
                topics=[Topic(**topic) for topic in segment.get("topics", [])],
                ads=[
                    Advertisement(
                        brand=ad.get("brand", ""),
                        product=ad.get("product", ""),
                        start=ad.get("start"),
                        stop=ad.get("stop")
                    )
                    for ad in segment.get("ads", [])
                ],
                engagement=[
                    AudienceEngagement(
                        platform=engagement.get("platform", ""),
                        identifier=engagement.get("identifier", ""),
                        context=engagement.get("context", ""),
                        start=engagement.get("start", 0.0),
                        stop=engagement.get("stop", 0.0),
                    )
                    for engagement in segment.get("engagement", [])
                ],
                gcp_blob=data.get("gcp_blob", ""),
                gcp_path=segment.get("gcp_path", ""),
                file_size=segment.get("file_size", 0.0),
                host=segment.get("show_metadata", {}).get("host", ""),
                program_name=segment.get("show_metadata", {}).get("program_name", ""),
            )

            # Append the created SegmentRecording to the result list
            segment_recordings.append(segment_record)

        return segment_recordings

class Recording(BaseModel):
    id: str
    timestamp: datetime
    stream_name: str
    stream_id: str
    type: str
    male: float
    female: float
    music: float
    noise: float
    noEnergy: float
    file_size: float
    duration: float

    @classmethod
    def create_from_analysis_model(cls, analysis: dict) -> "Recording":
        # Extract activity metrics
        activity = analysis.get("activity", {})

        # Calculate total file size as the sum of all segment file sizes
        total_file_size = sum(segment.get("file_size", 0.0) for segment in analysis.get("segments", []))

        # Calculate total duration as the sum of all segment durations
        total_duration = sum(segment.get("duration", 0.0) for segment in analysis.get("segments", []))

        # Determine the stream type (e.g., TV or RADIO)
        stream_type = "TV_STREAM" if analysis.get("type") == "video" else "RADIO_STREAM"

        # Create and return the Recording object
        return cls(
            id=analysis.get("id", ""),
            timestamp=datetime.fromisoformat(analysis.get("timestamp")),  
            stream_name=analysis.get("stream_name", ""),
            stream_id=analysis.get("stream_id", ""),
            type=stream_type,
            male=activity.get("male", 0.0),
            female=activity.get("female", 0.0),
            music=activity.get("music" or 0.0),
            noise=activity.get("noise" or 0.0),
            noEnergy=activity.get("noEnergy" or 0.0),
            file_size=total_file_size,
            duration=total_duration
        )