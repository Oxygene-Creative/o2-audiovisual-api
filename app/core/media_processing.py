import os
from moviepy import VideoFileClip
from pydub import AudioSegment
from pathlib import Path
from app.core.files import subfolder_check

async def extract_audio_from_video(video_path):
    # extract the file name
    audio_file_name = Path(video_path).stem
    
    # Load the video file
    video_clip = VideoFileClip(video_path)

    # Extract the audio
    audio = video_clip.audio

    # Write the audio to the output path
    subfolder_check(f"{os.getcwd()}/o2-files")
    audio_path = f"{os.getcwd()}/o2-files/{audio_file_name}.mp3"
    audio.write_audiofile(audio_path)

    # Close the clips
    audio.close()
    video_clip.close()

    return audio_path

async def slice_audio(speech_segments, audio_path):
    # Get the audio file name from the path
    audio_file_name = Path(audio_path).stem

    # Opening file and extracting segment
    audio = AudioSegment.from_mp3(audio_path)

    # extracted_files
    extracted_files = []

    for segment in speech_segments:
        # Time to miliseconds
        startTime =  max(0, (segment['start']) * 1000)
        endTime = (segment['stop']) * 1000

        # Extract the audio data for time slice
        extract = audio[startTime:endTime]

        # Generate the output file name with start and stop values
        extract_file_name= f"{audio_file_name}_{segment['start']:.2f}_{segment['stop']:.2f}.mp3"
        extract_file_path=f"{os.getcwd()}/o2-files/{extract_file_name}"
        # Export the sliced audio
        subfolder_check(f"{os.getcwd()}/o2-files")
        extract.export(extract_file_path, format="mp3")

        extracted_files.append({ 
            "start": segment["start"], 
            "stop": segment["stop"],
            "duration": segment["duration"],
            "file_path": extract_file_path })
        
    return extracted_files


async def slice_video(video_path, start, stop):
    output_file_name = f"{Path(video_path).stem}_{start}_{stop}.mp4"
    # Load the video file
    video_clip = VideoFileClip(video_path)

    # Trim the video between start and stop times
    sliced_clip = video_clip.subclipped(start, stop)

    # Write the sliced video to the output file
    subfolder_check(f"{os.getcwd()}/o2-files")
    output_file_path = f"{os.getcwd()}/o2-files/{output_file_name}"
    sliced_clip.write_videofile(output_file_path, codec="libx264")

    # Close the video resources
    video_clip.close()
    sliced_clip.close()

    return {
        "start": start,
        "stop": stop,
        "duration": stop - start,
        "file_path": output_file_path
    }