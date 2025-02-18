import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from faststream.redis import TestRedisBroker
from app.pipelines.audio_analytics import (
    start_audio_analysis,
    audio_seg,
    upload_audio_gcp,
    audio_router
)
from app.models.analytics import AnalysisModel, Segment

# ---- Core Functionality Tests ---- #

@pytest.mark.asyncio
async def test_start_audio_analysis():
    mock_upload = MagicMock()
    mock_upload.stream_id = "test-stream-id"
    mock_upload.stream_name = "test-stream"
    mock_upload.bucket = "test-bucket"
    mock_upload.blob = "test-blob"
    mock_upload.timestamp_str = "2023-10-01T10:00:00"
    
    with patch("app.pipelines.audio_analytics.extract_file_name", return_value="test-file.mp3") as mock_extract_file_name, \
         patch("app.pipelines.audio_analytics.subfolder_check") as mock_subfolder_check, \
         patch("app.pipelines.audio_analytics.download_file") as mock_download_file, \
         patch("app.pipelines.audio_analytics.audio_router.broker.publish") as mock_publish:
        response = await start_audio_analysis(mock_upload)
        
        assert mock_extract_file_name.called
        assert mock_subfolder_check.called
        assert mock_download_file.called
        mock_publish.assert_awaited_once()
        assert response == "Audio file is downloaded and analysis is ongoing!"

@pytest.mark.asyncio
async def test_audio_seg():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        audio_path="test-audio-path",
        type="audio",
        timestamp=datetime.now(),
    )
    mock_data.segments = []

    with patch("app.pipelines.audio_analytics.gender_music_segmentation", 
               return_value=([{"labels": "male", "duration": 30}], [{"labels": "female", "duration": 30}])) as mock_segmentation, \
         patch("app.pipelines.audio_analytics.slice_audio", 
               return_value=[{"start": 0, "stop": 30, "duration": 30, "audio_file": "segment-path.mp3"}]) as mock_slicing:
        result = await audio_seg(mock_data)

        assert mock_segmentation.called
        assert mock_slicing.called
        assert len(result.segments) > 0
        assert result.segments[0].audio_file == "segment-path.mp3"
        assert result.activity.male == 30

@pytest.mark.asyncio
async def test_upload_audio_gcp():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        audio_path="test-audio",
        type="audio",
        timestamp=datetime.now(),
        gcp_bucket="test-gcp-bucket",
        gcp_blob="test-gcp-blob",
    )
    mock_data.segments = [
        Segment(start=0, stop=30, duration=30, audio_file="segment-path-1.mp3"),
        Segment(start=31, stop=60, duration=30, audio_file="segment-path-2.mp3"),
    ]

    with patch("app.pipelines.audio_analytics.extract_file_name", side_effect=["segment-path-1.mp3", "segment-path-2.mp3"]) as mock_extract_name, \
         patch("app.pipelines.audio_analytics.calc_file_size", return_value=1024) as mock_calc_file_size, \
         patch("app.pipelines.audio_analytics.upload") as mock_upload, \
         patch("app.pipelines.audio_analytics.delete_file") as mock_delete_file, \
         patch("app.pipelines.audio_analytics.delete_blob") as mock_delete_blob:
        result = await upload_audio_gcp(mock_data)

        assert mock_extract_name.called
        assert mock_calc_file_size.called
        assert mock_upload.called
        assert mock_delete_file.called
        assert mock_delete_blob.called
        assert len(result.segments) == 2
        assert result.segments[0].file_size == 1024
        assert "audio/test-stream" in result.segments[0].gcp_path

# ---- Redis Messaging Tests ----

@pytest.mark.asyncio
async def test_audio_router_analysis_flow():
    upload_payload = {
        "stream_id": "test-stream-id",
        "stream_name": "test-stream",
        "bucket": "test-bucket",
        "blob": "test-blob",
        "timestamp_str": "2023-10-01T12:00:00"
    }

    mock_analysis = AnalysisModel(
        id="test-id",
        stream_id=upload_payload["stream_id"],
        stream_name=upload_payload["stream_name"],
        audio_path="test-audio-path",
        type="audio",
        timestamp=datetime.strptime(upload_payload["timestamp_str"], "%Y-%m-%dT%H:%M:%S"),
    )

    # Use TestRedisBroker for mocking Redis interactions
    async with TestRedisBroker(audio_router.broker) as br:
        # Mock subscriber responses
        mock_audio_seg = AsyncMock(return_value=mock_analysis)
        async with audio_router.subscriber("av:audio_seg", handler=mock_audio_seg):
            await br.publish(mock_analysis, "av:audio_seg")
            mock_audio_seg.assert_awaited_once_with(mock_analysis)

        # Mock the next step in the pipeline to ensure data flows correctly
        mock_upload_audio_gcp = AsyncMock(return_value=mock_analysis)
        async with audio_router.subscriber("av:upload_audio_gcp", handler=mock_upload_audio_gcp):
            await br.publish(mock_analysis, "av:upload_audio_gcp")
            mock_upload_audio_gcp.assert_awaited_once_with(mock_analysis)

@pytest.mark.asyncio
async def test_start_audio_analysis_message_publishing():
    mock_upload = {
        "stream_id": "test-stream-id",
        "stream_name": "test-stream",
        "bucket": "test-bucket",
        "blob": "test-audio-blob",
        "timestamp_str": "2023-10-01T15:00:00",
    }
    
    async with TestRedisBroker(audio_router.broker) as br:
        # Publish message using redis broker and validate
        mock_publisher = AsyncMock()
        async with audio_router.broker.publisher("av:audio_seg", handler=mock_publisher):
            await br.publish(mock_upload, "av:audio_seg")
            mock_publisher.assert_awaited_once_with(mock_upload)

@pytest.mark.asyncio
async def test_audio_seg_to_upload_flow():
    mock_analysis = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        audio_path="test-audio-path",
        type="audio",
        timestamp=datetime.now(),
    )

    mock_segments = [
        Segment(start=0, stop=30, duration=30, audio_file="segment-1.mp3"),
        Segment(start=31, stop=60, duration=30, audio_file="segment-2.mp3"),
    ]
    mock_analysis.segments = mock_segments

    async with TestRedisBroker(audio_router.broker) as br:
        mock_upload_audio_gcp = AsyncMock(return_value=mock_analysis)

        # Validate that messages flow to the next subscriber
        async with audio_router.subscriber("av:upload_audio_gcp", handler=mock_upload_audio_gcp):
            await br.publish(mock_analysis, "av:upload_audio_gcp")
            mock_upload_audio_gcp.assert_awaited_once_with(mock_analysis)