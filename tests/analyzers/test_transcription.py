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

def test_post_process_transcription():
    # Input transcript (raw and containing errors)
    raw_transcript = "[0.0 - 10.0] hello woorld [10.0 - 20.0] this is a test"
    keywords = ["world", "test"]

    # Call the actual function with no mocking
    result = post_process_transcription(raw_transcript, keywords)

    # Assert part of the structure remains the same (timestamps preserved)
    assert "[0.0 - 10.0]" in result, "Expected the timestamp '[0.0 - 10.0]' to be present in the output"
    assert "[10.0 - 20.0]" in result, "Expected the timestamp '[10.0 - 20.0]' to be present in the output"

    # Ensure the known keywords are correctly formatted in the result
    assert "world" in result.lower(), "Expected the keyword 'world' to be properly formatted in the output"
    assert "test" in result.lower(), "Expected the keyword 'test' to be properly formatted in the output"

    
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