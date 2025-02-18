import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from faststream.redis import TestRedisBroker
from app.pipelines.video_analytics import (
    start_video_analysis,
    upload_video_gcp,
    video_router,
)
from app.models.analytics import AnalysisModel, Segment


# ---- Core Functionality Tests ----

@pytest.mark.asyncio
async def test_start_video_analysis():
    mock_upload = MagicMock()
    mock_upload.stream_id = "test-stream-id"
    mock_upload.stream_name = "test-stream"
    mock_upload.bucket = "test-bucket"
    mock_upload.blob = "test-blob"
    mock_upload.timestamp_str = "2023-10-01T10:00:00"

    with patch("app.pipelines.video_analytics.extract_file_name", return_value="test-file.mp4") as mock_extract_file_name, \
         patch("app.pipelines.video_analytics.subfolder_check") as mock_subfolder_check, \
         patch("app.pipelines.video_analytics.download_file") as mock_download_file, \
         patch("app.pipelines.video_analytics.extract_audio_from_video", return_value="test-audio-file.mp3") as mock_extract_audio, \
         patch("app.pipelines.video_analytics.video_router.broker.publish") as mock_publish:
        response = await start_video_analysis(mock_upload)

        mock_extract_file_name.assert_called_once_with("test-blob")
        mock_subfolder_check.assert_called_once()
        mock_download_file.assert_called_once_with("test-bucket", "test-blob", f"{os.getcwd()}/o2-files/test-file.mp4")
        mock_extract_audio.assert_called_once_with(f"{os.getcwd()}/o2-files/test-file.mp4")
        mock_publish.assert_awaited_once()
        assert response == "Video file is downloaded and analysis is ongoing!"

@pytest.mark.asyncio
async def test_upload_video_gcp():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        video_path="test-video.mp4",
        audio_path="test-audio.mp3",
        segments=[
            Segment(start=0, stop=15, audio_file="segment-audio-1.mp3"),
            Segment(start=16, stop=30, audio_file="segment-audio-2.mp3"),
        ],
        gcp_bucket="test-gcp-bucket",
        gcp_blob="test-gcp-blob",
        timestamp=datetime.now(),
    )

    with patch("app.pipelines.video_analytics.slice_video", side_effect=["segment-video-1.mp4", "segment-video-2.mp4"]) as mock_slice_video, \
         patch("app.pipelines.video_analytics.extract_file_name", side_effect=["segment-video-1.mp4", "segment-video-2.mp4"]) as mock_extract_name, \
         patch("app.pipelines.video_analytics.calc_file_size", return_value=1024) as mock_calc_file_size, \
         patch("app.pipelines.video_analytics.upload") as mock_upload, \
         patch("app.pipelines.video_analytics.delete_file") as mock_delete_file, \
         patch("app.pipelines.video_analytics.delete_blob") as mock_delete_blob:
        result = await upload_video_gcp(mock_data)

        # Assertions for slicing, file extraction, and uploading
        assert mock_slice_video.call_count == 2
        assert mock_extract_name.call_count == 2
        assert mock_calc_file_size.call_count == 2
        assert mock_upload.call_count == 2
        assert mock_delete_file.call_count == 5  # Includes segments, video file, and audio file
        mock_delete_blob.assert_called_once_with("test-gcp-bucket", "test-gcp-blob")

        # Validate returned data properties
        assert len(result.segments) == 2
        assert result.segments[0].file_size == 1024
        assert "video/test-stream" in result.segments[0].gcp_path


# ---- Redis Messaging Tests ----

@pytest.mark.asyncio
async def test_video_router_analysis_flow():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        video_path="test-video.mp4",
        audio_path="test-audio.mp3",
        segments=[],
        gcp_bucket="test-gcp-bucket",
        timestamp=datetime.now(),
    )

    async with TestRedisBroker(video_router.broker) as br:
        # Mock subscriber for "av:upload_video_gcp"
        mock_upload_video_gcp = AsyncMock()
        async with video_router.subscriber("av:upload_video_gcp", handler=mock_upload_video_gcp):
            await br.publish(mock_data, "av:upload_video_gcp")
            mock_upload_video_gcp.assert_awaited_once_with(mock_data)


@pytest.mark.asyncio
async def test_start_video_analysis_message_publishing():
    mock_upload = {
        "stream_id": "test-stream-id",
        "stream_name": "test-stream",
        "bucket": "test-bucket",
        "blob": "test-video-blob",
        "timestamp_str": "2023-10-01T12:00:00",
    }

    mock_analysis = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        video_path="mock-video.mp4",
        audio_path="mock-audio.mp3",
        type="video",
        timestamp=datetime.now(),
    )

    async with TestRedisBroker(video_router.broker) as br:
        mock_publish = AsyncMock()
        async with video_router.broker.publisher("av:audio_seg", handler=mock_publish):
            await br.publish(mock_analysis, "av:audio_seg")
            mock_publish.assert_awaited_once_with(mock_analysis)


@pytest.mark.asyncio
async def test_upload_video_gcp_message_flow():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        video_path="mock-video-path.mp4",
        audio_path="mock-audio-path.mp3",
        segments=[],
        gcp_bucket="test-bucket",
        timestamp=datetime.now(),
    )

    async with TestRedisBroker(video_router.broker) as br:
        # Mock subscriber for "av:upload_video_gcp"
        mock_upload_video_gcp = AsyncMock(return_value=mock_data)

        # Subscriber and flow validation
        async with video_router.subscriber("av:upload_video_gcp", handler=mock_upload_video_gcp):
            await br.publish(mock_data, "av:upload_video_gcp")
            mock_upload_video_gcp.assert_awaited_once_with(mock_data)

