import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from app.core.media_processing import extract_audio_from_video, slice_audio
from pathlib import Path


@patch("app.core.media_processing.VideoFileClip")
@patch("app.core.media_processing.subfolder_check")
def test_extract_audio_from_video(mock_subfolder_check, mock_video_file_clip):
    # Mock video file clip and audio object
    mock_audio = MagicMock()
    mock_video_file_clip.return_value.audio = mock_audio

    # Mock the write_audiofile and close methods
    audio_file_name = "test_video"
    mock_audio.write_audiofile = MagicMock()
    mock_audio.close = MagicMock()
    mock_video_file_clip.return_value.close = MagicMock()

    # Call the function with a dummy video file
    video_path = "/path/to/test_video.mp4"
    output_audio_file = extract_audio_from_video(video_path)

    # Expected output
    expected_output = f"{audio_file_name}.mp3"

    # Assertions
    assert output_audio_file == expected_output
    mock_subfolder_check.assert_called_once_with(f"{Path.cwd()}/o2-files")
    mock_audio.write_audiofile.assert_called_once_with(f"{Path.cwd()}/o2-files/{audio_file_name}.mp3")
    mock_audio.close.assert_called_once()
    mock_video_file_clip.return_value.close.assert_called_once()


@patch("app.core.media_processing.AudioSegment.from_mp3")
@patch("app.core.media_processing.AudioSegment.export")
@patch("app.core.media_processing.subfolder_check")
def test_slice_audio(mock_subfolder_check, mock_export, mock_from_mp3):
    # Mock the audio object returned by pydub
    mock_audio = MagicMock()
    mock_from_mp3.return_value = mock_audio

    # Mock segments and inputs
    speech_segments = [
        {"start": 5, "stop": 15, "duration": 10},
        {"start": 30, "stop": 40, "duration": 10},
    ]
    audio_path = "/path/to/test_audio.mp3"

    # Call the function
    extracted_files = slice_audio(speech_segments, audio_path)

    # Expected output
    expected_files = [
        {
            "start": 5,
            "stop": 15,
            "duration": 10,
            "audio_file": "test_audio_5.00_15.00.mp3",
        },
        {
            "start": 30,
            "stop": 40,
            "duration": 10,
            "audio_file": "test_audio_30.00_40.00.mp3",
        },
    ]

    # Assertions
    assert extracted_files == expected_files

    # Verify subfolder_check is called
    mock_subfolder_check.assert_called_with(f"{Path.cwd()}/o2-files")

    # Calls to extract segments
    assert mock_audio.__getitem__.call_count == 2

    # Calls to export
    assert mock_from_mp3.called_once_with(audio_path)
    assert mock_export.call_count == 2
    mock_export.assert_any_call(f"{Path.cwd()}/o2-files/test_audio_5.00_15.00.mp3", format="mp3")
    mock_export.assert_any_call(f"{Path.cwd()}/o2-files/test_audio_30.00_40.00.mp3", format="mp3")