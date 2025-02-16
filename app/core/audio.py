import os
from moviepy import VideoFileClip
from pydub import AudioSegment
from pathlib import Path
from app.core.files import subfolder_check

def extract_audio_from_video(video_path):
    # extract the file name
    audio_file_name = Path(video_path).stem
    
    # Load the video file
    video_clip = VideoFileClip(video_path)

    # Extract the audio
    audio = video_clip.audio

    # Write the audio to the output path
    subfolder_check(f"{os.getcwd()}/o2-files")
    audio.write_audiofile(f"{os.getcwd()}/o2-files/{audio_file_name}.mp3")

    # Close the clips
    audio.close()
    video_clip.close()

    return f"{ audio_file_name }.mp3"

def slice_audio(speech_segments, audio_path):
    # Get the audio file name from the path
    audio_file_name = Path(audio_path).stem

    # Opening file and extracting segment
    audio = AudioSegment.from_mp3(audio_path)

    # extracted_files
    extracted_files = []

    for segment in speech_segments:
        # Time to miliseconds
        startTime =  max(0, (segment['start'] - 10) * 1000)
        endTime = (segment['stop'] + 10) * 1000

        # Extract the audio data for time slice
        extract = audio[startTime:endTime]

        # Generate the output file name with start and stop values
        extract_file_name= f"{audio_file_name}_{segment['start']:.2f}_{segment['stop']:.2f}.mp3"

        # Export the sliced audio
        subfolder_check(f"{os.getcwd()}/o2-files")
        extract.export(f"{os.getcwd()}/o2-files/{extract_file_name}", format="mp3")

        extracted_files.append({ 
            "start": segment["start"], 
            "stop": segment["stop"],
            "duration": segment["duration"],
            "audio_file": extract_file_name })
        
    return extracted_files