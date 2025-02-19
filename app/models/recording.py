from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timedelta
from app.models.analytics import Activity, AnalysisModel, Advertisement, AudienceEngagement
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
    topics: List[str] = []
    tags: List[str] = []
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
    def create_segment_recordings_from_analysis_model(cls, analysis: AnalysisModel) -> List["SegmentRecording"]:
        segment_recordings = []

        # Iterate over each segment in the analysis model
        for i, segment in enumerate(analysis.segments):
            # Derive the absolute timestamp for the segment
            segment_timestamp = analysis.timestamp + timedelta(seconds=segment.start or 0.0)

            # Create an instance of SegmentRecording for this segment
            segment_record = cls(
                recording_id=analysis.id or "",
                timestamp=segment_timestamp,
                duration=segment.duration or 0.0,
                raw_text=segment.raw_text,
                language=segment.language,
                language_scoew=segment.language_score,
                sentiment=segment.sentiment,
                emotions=segment.emotions,
                embeddings=segment.embeddings,
                keywords=segment.keywords,
                topics=segment.topics,
                tags=segment.tags,
                ads=[
                    Advertisement(brand=ad.brand, product=ad.product, start=ad.start, stop=ad.stop)
                    for ad in segment.ads
                ],
                engagement=[
                    AudienceEngagement(
                        platform=engagement.platform,
                        identifier=engagement.identifier,
                        context=engagement.context,
                        start=engagement.start,
                        stop=engagement.stop,
                    )
                    for engagement in segment.engagement
                ],
                gcp_blob=analysis.gcp_blob or "",
                gcp_path=segment.gcp_path or "",
                file_size=segment.file_size or 0.0,
                host=segment.show_metadata.host or "",
                program_name=segment.show_metadata.program_name or "",
            )

            # Append the created SegmentRecording to the result list
            segment_recordings.append(segment_record)

        return segment_recordings

class Recording(BaseModel):
    id: str
    timestamp: datetime
    stream_name: str
    stream_id: str
    male: float
    female: float
    music: float
    file_size: float
    duration: float

    @classmethod
    def create_from_analysis_model(cls, analysis: AnalysisModel) -> "Recording":
        # Extract activity metrics
        activity = analysis.activity or Activity()

        # Calculate total file size as the sum of all segment file sizes
        total_file_size = sum(segment.file_size or 0.0 for segment in analysis.segments)

        # Calculate total duration as the sum of all segment durations
        total_duration = sum(segment.duration or 0.0 for segment in analysis.segments)

        # Create and return the Recording object
        return cls(
            id=analysis.id,
            timestamp=analysis.timestamp or datetime.now(),  
            stream_name=analysis.stream_name or "", 
            stream_id=analysis.stream_id or "",
            male=activity.male or 0.0,
            female=activity.female or 0.0,
            music=activity.music or 0.0,
            file_size=total_file_size,
            duration=total_duration,
        )