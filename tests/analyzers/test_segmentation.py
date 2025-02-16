import os
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from app.analyzers.segmentation import speech_segments, gender_music_segmentation

def test_speech_segments():
    # Mock DataFrame that mimics processed segmentation input
    data = {
        "start": [0, 5, 15, 25, 40],
        "stop": [5, 15, 25, 35, 50],
        "labels": ["speech", "music", "speech", "noEnergy", "speech"],
        "duration": [5, 10, 10, 10, 10],  # stop - start
    }
    df = pd.DataFrame(data)

    # Call the function
    result = speech_segments(df)

    # Expected result based on logic fix
    expected_result = [
        {"start": 0, "stop": 25, "duration": 25},  
        {"start": 40, "stop": 50, "duration": 10},
    ]

    # Assert the returned segments match the expected result
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

@patch("app.analyzers.segmentation.Segmenter")
@patch("app.analyzers.segmentation.seg2csv")
@patch("app.analyzers.segmentation.pd.read_table")
@patch("app.analyzers.segmentation.delete_file")
@patch("app.analyzers.segmentation.subfolder_check")
def test_gender_music_segmentation(
    mock_subfolder_check,
    mock_delete_file,
    mock_read_table,
    mock_seg2csv,
    mock_segmenter,
):
    mock_instance = MagicMock()  # Create a mock instance for the Segmenter
    mock_segmenter.return_value = mock_instance 
    mock_instance.return_value = [
        ("speech", 0, 5),  # label, start, stop
        ("music", 5, 15),
        ("speech", 15, 25),
    ]

    # Mock the DataFrame read from the CSV (after seg2csv writes it)
    mock_read_table.return_value = pd.DataFrame({
        "start": [0, 5, 15],
        "stop": [5, 15, 25],
        "labels": ["speech", "music", "speech"],
        "duration": [5, 10, 10],
    })

    # Call the function with a dummy audio file
    audio_file = "dummy_audio.wav"
    aggregated_result, segments = gender_music_segmentation(audio_file)

    # Validate the aggregated results
    expected_aggregated = [
        {"labels": "musix", "duration": 10},
        {"labels": "speech", "duration": 15},
    ]
    assert aggregated_result == expected_aggregated, f"Expected {expected_aggregated}, but got {aggregated_result}"

    # Validate the speech segments
    expected_segments = [
        {"start": 0, "stop": 5, "duration": 5},
        {"start": 15, "stop": 25, "duration": 10},
    ]
    assert segments == expected_segments, f"Expected {expected_segments}, but got {segments}"

    # Ensure mocked methods are called correctly
    mock_subfolder_check.assert_called_once()
    mock_seg2csv.assert_called_once()
    mock_read_table.assert_called_once()
    mock_delete_file.assert_called_once()