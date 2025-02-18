import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from faststream.redis import TestRedisBroker
from app.pipelines.transcript_analysis import (
    audio_transcribe,
    transcript_embeddings,
    transcript_sentiment,
    transcript_categories,
    transcript_keywords,
    transcript_topics,
    transcript_llm,
    save_analysis_es,
    transcript_router
)
from app.models.analytics import AnalysisModel, Segment


# ---- Core Functionality Tests ----

@pytest.mark.asyncio
async def test_audio_transcribe():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment(audio_file="test-audio-file.mp3")],
        type="audio",
        timestamp=datetime.now(),
    )
    with patch("app.pipelines.transcript_analysis.get_all_keywords", return_value=["keyword1", "keyword2"]) as mock_keywords, \
         patch("app.pipelines.transcript_analysis.transcribe", return_value="test transcript") as mock_transcribe, \
         patch("app.pipelines.transcript_analysis.post_process_transcription", return_value="processed transcript") as mock_post_process:
        result = await audio_transcribe(mock_data)
        mock_keywords.assert_called_once()
        mock_transcribe.assert_called_once_with("test-audio-file.mp3")
        mock_post_process.assert_called_once_with("test transcript", ["keyword1", "keyword2"])
        assert result.segments[0].transcript == "processed transcript"

@pytest.mark.asyncio
async def test_transcript_embeddings():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment(transcript="test transcript")],
        type="audio",
        timestamp=datetime.now(),
    )
    with patch("app.pipelines.transcript_analysis.remove_timestamps_and_format", return_value="clean transcript") as mock_clean, \
         patch("app.pipelines.transcript_analysis.embed_text", return_value="test embeddings") as mock_embed:
        result = await transcript_embeddings(mock_data)
        mock_clean.assert_called_once_with("test transcript")
        mock_embed.assert_called_once_with("clean transcript")
        assert result.segments[0].embeddings == "test embeddings"

@pytest.mark.asyncio
async def test_transcript_sentiment():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment(transcript="test transcript")],
        type="audio",
        timestamp=datetime.now(),
    )
    with patch("app.pipelines.transcript_analysis.remove_timestamps_and_format", return_value="clean transcript") as mock_clean, \
         patch("app.pipelines.transcript_analysis.sentiment_analysis", return_value="positive") as mock_sentiment:
        result = await transcript_sentiment(mock_data)
        mock_clean.assert_called_once_with("test transcript")
        mock_sentiment.assert_called_once_with("clean transcript")
        assert result.segments[0].sentiment == "positive"

@pytest.mark.asyncio
async def test_transcript_categories():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment(transcript="test transcript")],
        type="audio",
        timestamp=datetime.now(),
    )
    with patch("app.pipelines.transcript_analysis.get_tags", return_value=["tag1", "tag2"]) as mock_tags, \
         patch("app.pipelines.transcript_analysis.remove_timestamps_and_format", return_value="clean transcript") as mock_clean, \
         patch("app.pipelines.transcript_analysis.categorize_text", return_value=["category1"]) as mock_categorize:
        result = await transcript_categories(mock_data)
        mock_tags.assert_called_once_with("audio")
        mock_clean.assert_called_once_with("test transcript")
        mock_categorize.assert_called_once_with("clean transcript", ["tag1", "tag2"])
        assert result.segments[0].categories == ["category1"]

@pytest.mark.asyncio
async def test_transcript_keywords():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment(transcript="test transcript")],
        type="audio",
        timestamp=datetime.now(),
    )
    with patch("app.pipelines.transcript_analysis.get_all_keywords", return_value=["keyword1", "keyword2"]) as mock_keywords, \
         patch("app.pipelines.transcript_analysis.remove_timestamps_and_format", return_value="clean transcript") as mock_clean, \
         patch("app.pipelines.transcript_analysis.match_keywords", return_value=["keyword1"]) as mock_match:
        result = await transcript_keywords(mock_data)
        mock_keywords.assert_called_once()
        mock_clean.assert_called_once_with("test transcript")
        mock_match.assert_called_once_with("clean transcript", ["keyword1", "keyword2"])
        assert result.segments[0].keywords == ["keyword1"]

@pytest.mark.asyncio
async def test_transcript_topics():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment(transcript="test transcript")],
        type="audio",
        timestamp=datetime.now(),
    )
    with patch("app.pipelines.transcript_analysis.remove_timestamps_and_format", return_value="clean transcript") as mock_clean, \
         patch("app.pipelines.transcript_analysis.topic_modelling", return_value=["topic1", "topic2"]) as mock_topics:
        result = await transcript_topics(mock_data)
        mock_clean.assert_called_once_with("test transcript")
        mock_topics.assert_called_once_with("clean transcript")
        assert result.segments[0].topics == ["topic1", "topic2"]

@pytest.mark.asyncio
async def test_save_analysis_es():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment()],
        type="audio",
        timestamp=datetime.now(),
    )
    with patch("app.pipelines.transcript_analysis.Recording.create_from_analysis_model") as mock_recording, \
         patch("app.pipelines.transcript_analysis.SegmentRecording.create_segment_recordings_from_analysis_model") as mock_segments, \
         patch("app.pipelines.transcript_analysis.save") as mock_save, \
         patch("app.pipelines.transcript_analysis.save_bulk") as mock_save_bulk:
        await save_analysis_es(mock_data)
        mock_recording.assert_called_once_with(mock_data)
        mock_segments.assert_called_once_with(mock_data)
        mock_save.assert_called_once()
        mock_save_bulk.assert_called_once()

# ---- Redis Messaging Tests ----

@pytest.mark.asyncio
async def test_transcript_pipeline_flow():
    mock_data = AnalysisModel(
        id="test-id",
        stream_id="test-stream-id",
        stream_name="test-stream",
        segments=[Segment()],
        type="audio",
        timestamp=datetime.now(),
    )

    async with TestRedisBroker(transcript_router.broker) as br:
        # Mock each step's subscriber
        for topic in [
            "av:audio_transcribe",
            "av:transcript_embeddings",
            "av:transcript_sentiment",
            "av:transcript_categories",
            "av:transcript_keywords",
            "av:transcript_topics",
            "av:transcript_llm",
            "av:save_analysis_es",
        ]:
            mock_handler = AsyncMock()
            async with transcript_router.subscriber(topic, handler=mock_handler):
                await br.publish(mock_data, topic)
                mock_handler.assert_awaited_once_with(mock_data)