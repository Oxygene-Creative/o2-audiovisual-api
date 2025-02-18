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
from app.pipelines.transcript_analysis import  audio_transcribe
from app.models.analytics import AnalysisModel, Segment

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
async def test_audio_seg_message_publishing():
    mock_segment_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        audio_path="mock-audio.mp3",
        type="audio",
        segments=[],
        timestamp=datetime.now(),
    )

    with patch("app.pipelines.audio_analytics.gender_music_segmentation", 
               return_value=([{"labels": "male", "duration": 30}, {"labels": "female", "duration": 10}], [{"start": 0, "stop": 30, "duration": 30}])) as mock_segment, \
         patch("app.pipelines.audio_analytics.slice_audio", 
               return_value=[{"start": 0, "stop": 30, "duration": 30, "audio_file": "segment.mp3"}]) as mock_slicing:

        async with TestRedisBroker(audio_router.broker) as br:
            await br.publish( mock_segment_data, "av:audio_seg" )
            
            # verify mock calls
            mock_segment.assert_called_once_with("mock-audio.mp3")
            mock_slicing.assert_called_once()
            
            # Verify message was published to the correct topic
            audio_transcribe.mock.assert_called_once_with({"name": "John", "user_id": 1})


# @pytest.mark.asyncio
# async def test_upload_audio_gcp():
#     mock_data = AnalysisModel(
#         id="test-id",
#         stream_id="test-stream-id",
#         stream_name="test-stream",
#         audio_path="test-audio.mp3",
#         segments=[Segment(audio_file="segment-1.mp3")],
#         gcp_bucket="test-bucket",
#         gcp_blob="test-blob",
#         timestamp=datetime.now(),
#     )

#     with patch("app.pipelines.audio_analytics.extract_file_name", return_value="segment-1.mp3") as mock_extract_file_name, \
#          patch("app.pipelines.audio_analytics.calc_file_size", return_value=1024) as mock_calc_file_size, \
#          patch("app.pipelines.audio_analytics.upload") as mock_upload, \
#          patch("app.pipelines.audio_analytics.delete_file") as mock_delete_file, \
#          patch("app.pipelines.audio_analytics.delete_blob") as mock_delete_blob:

#         async with TestRedisBroker(audio_router.broker) as br:
#             published_message = await br.publish(
#                 mock_data,
#                 publish_topic="av:upload_audio_gcp",
#                 subscribe_topic="av:save_analysis_es",
#             )

#             # Validate GCP interactions
#             mock_extract_file_name.assert_called_once_with("segment-1.mp3")
#             mock_calc_file_size.assert_called_once_with("segment-1.mp3")
#             mock_upload.assert_called_once()
#             mock_delete_file.assert_called()
#             mock_delete_blob.assert_called_once_with("test-bucket", "test-blob")

#             # Assert data updates in the published message
#             assert published_message.segments[0].file_size == 1024
#             assert "audio/test-stream" in published_message.segments[0].gcp_path