import os
from moviepy import VideoFileClip
from pydub import AudioSegment
from pathlib import Path
from app.core.files import subfolder_check
import ffmpeg
import asyncio
import logging
import time
import subprocess


logger = logging.getLogger(__name__)


def _extract_audio_sync(video_path: str, audio_path: str, timeout_seconds: int) -> None:
    # Use ffmpeg CLI directly so timeout handling is consistent across ffmpeg-python versions.
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "libmp3lame",
        audio_path,
    ]
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )


def _slice_video_sync(
    video_path: str,
    start: float,
    stop: float,
    output_file_path: str,
    codec: str,
) -> None:
    video_clip = None
    sliced_clip = None
    try:
        video_clip = VideoFileClip(video_path)
        sliced_clip = video_clip.subclipped(start, stop)
        sliced_clip.write_videofile(output_file_path, codec=codec)
    finally:
        if sliced_clip is not None:
            sliced_clip.close()
        if video_clip is not None:
            video_clip.close()

async def extract_audio_from_video(video_path):
    # extract the file name
    audio_file_name = Path(video_path).stem

    subfolder_check(f"{os.getcwd()}/o2-files")
    audio_path = f"{os.getcwd()}/o2-files/{audio_file_name}.mp3"
    timeout_seconds = int(os.getenv("AUDIO_EXTRACT_TIMEOUT_SECONDS", "180"))
    started_at = time.time()
    logger.info(
        "Audio extraction started: video=%s output=%s timeout=%ss",
        video_path,
        audio_path,
        timeout_seconds,
    )

    try:
        await asyncio.to_thread(
            _extract_audio_sync,
            video_path,
            audio_path,
            timeout_seconds,
        )
    except subprocess.CalledProcessError as err:
        stderr = err.stderr.decode("utf-8", errors="ignore") if err.stderr else ""
        raise RuntimeError(
            f"Failed to extract audio from {video_path}. ffmpeg error: {stderr}"
        ) from err
    except subprocess.TimeoutExpired as err:
        raise TimeoutError(
            f"Timed out extracting audio from {video_path} after {timeout_seconds}s"
        ) from err

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise RuntimeError(
            f"Audio extraction produced no output for {video_path} (expected {audio_path})"
        )

    logger.info(
        "Audio extraction complete: video=%s output=%s duration=%.2fs",
        video_path,
        audio_path,
        time.time() - started_at,
    )

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
        startTime = max(0, (segment['start']) * 1000)
        endTime = (segment['stop']) * 1000

        # Extract the audio data for time slice
        extract = audio[startTime:endTime]

        # Generate the output file name with start and stop values
        extract_file_name = f"{audio_file_name}_{segment['start']:.2f}_{segment['stop']:.2f}.mp3"
        extract_file_path = f"{os.getcwd()}/o2-files/{extract_file_name}"
        # Export the sliced audio
        subfolder_check(f"{os.getcwd()}/o2-files")
        extract.export(extract_file_path, format="mp3")

        extracted_files.append({
            "start": segment["start"],
            "stop": segment["stop"],
            "duration": segment["duration"],
            "file_path": extract_file_path})

    return extracted_files


async def slice_video(video_path, start, stop):
    output_file_name = f"{Path(video_path).stem}_{start}_{stop}.mp4"
    subfolder_check(f"{os.getcwd()}/o2-files")
    output_file_path = f"{os.getcwd()}/o2-files/{output_file_name}"
    timeout_seconds = int(os.getenv("VIDEO_SLICE_TIMEOUT_SECONDS", "900"))
    codec = os.getenv("VIDEO_SLICE_CODEC", "libx264")
    started_at = time.time()

    logger.info(
        "Video slicing started: input=%s start=%s stop=%s output=%s timeout=%ss codec=%s",
        video_path,
        start,
        stop,
        output_file_path,
        timeout_seconds,
        codec,
    )

    try:
        await asyncio.wait_for(
            asyncio.to_thread(
                _slice_video_sync,
                video_path,
                start,
                stop,
                output_file_path,
                codec,
            ),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError as err:
        logger.error(
            "Video slicing timeout: input=%s start=%s stop=%s output=%s timeout=%ss elapsed=%.2fs",
            video_path,
            start,
            stop,
            output_file_path,
            timeout_seconds,
            time.time() - started_at,
        )
        raise TimeoutError(
            f"Timed out slicing video {video_path} ({start}-{stop}) after {timeout_seconds}s"
        ) from err
    except Exception:
        logger.exception(
            "Video slicing failed: input=%s start=%s stop=%s output=%s",
            video_path,
            start,
            stop,
            output_file_path,
        )
        raise

    if not os.path.exists(output_file_path) or os.path.getsize(output_file_path) == 0:
        raise RuntimeError(
            f"Video slicing produced no output for {video_path} ({start}-{stop})"
        )

    logger.info(
        "Video slicing complete: input=%s start=%s stop=%s output=%s size_bytes=%s duration=%.2fs",
        video_path,
        start,
        stop,
        output_file_path,
        os.path.getsize(output_file_path),
        time.time() - started_at,
    )

    return {
        "start": start,
        "stop": stop,
        "duration": stop - start,
        "file_path": output_file_path
    }


async def check_media_integrity(file_path: str) -> bool:
    try:
        # Use ffprobe to analyze the file
        probe = ffmpeg.probe(file_path)

        # Check if we have streams
        if 'streams' not in probe or len(probe['streams']) == 0:
            print(f"No streams found in {file_path}")
            return False

        # Check each stream
        for stream in probe['streams']:
            # For video streams, check if we have basic video info
            if stream['codec_type'] == 'video':
                if 'width' not in stream or 'height' not in stream:
                    print(f"Invalid video stream in {file_path}")
                    return False

            # Check if codec is recognizable
            if 'codec_name' not in stream or stream['codec_name'] == 'unknown':
                print(f"Unknown codec in stream: {stream}")
                return False

        # Additional check: try to read first few frames
        try:
            (
                ffmpeg
                .input(file_path)
                .output('pipe:', vframes=1, f='null')
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print(f"Cannot decode frames from {file_path}: {e}")
            return False
        except Exception as e:
            print(f"Timeout or other error checking frames: {e}")
            return False

        return True

    except ffmpeg.Error as e:
        print(f"FFprobe error for {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error checking {file_path}: {e}")
        return False


async def validate_file_size(file_path: str, min_size_bytes: int = 1024) -> bool:
    try:
        file_size = os.path.getsize(file_path)
        if file_size < min_size_bytes:
            print(f"File too small: {file_size} bytes")
            return False
        return True
    except Exception as e:
        print(f"Error checking file size: {e}")
        return False
