import os
import time
from pydub import AudioSegment

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} deleted successfully.")
    except FileNotFoundError:
        print(f"File {file_path} not found. Cannot delete.")
    except PermissionError:
        print(f"Permission denied: unable to delete {file_path}.")
    except Exception as e:
        print(f"An error occurred while deleting the file {file_path}: {str(e)}")

def extract_audio_from_video(video_file_path, audio_file_path):
    # Load the video file
    video_clip = VideoFileClip(video_file_path)

    # Extract the audio
    audio_clip = video_clip.audio

    # Write the audio to a file
    audio_clip.write_audiofile(audio_file_path)

    # Close the clips
    audio_clip.close()
    video_clip.close()

    print(f"Audio extracted and saved to {audio_file_path}")

def slice_audio(start, stop, audio_path, id):
    # Time to miliseconds
    startTime = start*1000
    endTime = stop*1000
    # Opening file and extracting segment
    song = AudioSegment.from_mp3(audio_path)
    extract = song[startTime:endTime]
    # Saving
    # Get the current timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    extract_file_name = f'recordings/{id}_extract_{timestamp}.mp3'
    extract.export(extract_file_name, format="mp3")
    return extract_file_name