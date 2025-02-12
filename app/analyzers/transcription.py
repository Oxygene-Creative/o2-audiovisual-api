from faster_whisper import WhisperModel

model_size = "turbo"
model = WhisperModel(
    model_size,
    device="cpu",
    compute_type="int8"
)

def transcribe(audio_url: str):
    segments, info = model.transcribe(audio_url, beam_size=5, vad_filter=True)

    # Language information
    transcription_info = {
        "language": info.language,
        "language_probability": info.language_probability,
        "segments": []
    }
    
    for segment in segments:
        transcription_info["segments"].append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })
        
    return transcription_info

def post_process_transcription(transcription_info: dict):
    """
    Post-process the transcribed text.
    Placeholder function for any post-processing logic (e.g., cleanup, formatting).
    """
    for segment in transcription_info["segments"]:
        # Example: Strip whitespace and capitalize text
        segment["text"] = segment["text"].strip().capitalize()
    
    return transcription_info
