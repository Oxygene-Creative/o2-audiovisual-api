import pytest
from unittest.mock import patch, MagicMock
from app.analyzers.transcription import (
    remove_non_ascii,
    transcribe,
    post_process_transcription,
    remove_timestamps_and_format
)

def test_remove_non_ascii():
    text = "Hello World! 你好世界 🌍"
    cleaned_text = remove_non_ascii(text)
    expected_output = "Hello World!"
    assert cleaned_text == expected_output, f"Expected {expected_output}, but got {cleaned_text}"

@patch("app.analyzers.transcription.transcription_model.transcribe")
def test_transcribe(mock_transcribe):
    # Mock transcription model output
    mock_segments = [
        MagicMock(start=0.0, end=10.0, text="Hello World."),
        MagicMock(start=10.0, end=20.0, text="This is a test.")
    ]
    mock_info = MagicMock(language="en", language_probability=0.98)
    mock_transcribe.return_value = (mock_segments, mock_info)

    # Call the function
    audio_url = "dummy_audio.mp3"
    result = transcribe(audio_url)

    # Expected outputs
    expected_result = {
        "language": "en",
        "language_probability": 0.98,
        "transcript": "[0.0 - 10.0] Hello World.\n [10.0 - 20.0] This is a test."
    }

    assert result == expected_result, f"Expected {expected_result}, but got {result}"
    mock_transcribe.assert_called_once_with(audio_url, beam_size=5, vad_filter=True)

@patch("app.core.llm.llm")
def test_post_process_transcription(mock_llm):
    # Mock LLM output
    processed_transcript = "[0.0 - 10.0] Hello, world! [10.0 - 20.0] This is a test."
    mock_llm.invoke.return_value = processed_transcript

    # Call the function with test inputs
    raw_transcript = "[0.0 - 10.0] hello woorld [10.0 - 20.0] this is a test"
    keywords = ["world", "test"]
    result = post_process_transcription(raw_transcript, keywords)

    # Expected result
    expected_result = "[0.0 - 10.0] Hello, world! [10.0 - 20.0] This is a test."
    assert result == expected_result, f"Expected {expected_result}, but got {result}"
    # Validate LLM invocation
    mock_llm.invoke.assert_called_once()
    assert "world" in mock_llm.invoke.call_args[0][0]["keywords"]
    assert "test" in mock_llm.invoke.call_args[0][0]["keywords"]

def test_remove_timestamps_and_format():
    transcript = """
    [0.0 - 10.0] Hello World. 
    [10.0 - 20.0] This is a test.
    """
    # Call the function
    cleaned = remove_timestamps_and_format(transcript)

    # Expected cleaned text
    expected_cleaned_text = "Hello World. This is a test."

    assert cleaned == expected_cleaned_text, f"Expected {expected_cleaned_text}, but got {cleaned}"