from faster_whisper import WhisperModel
import torch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
from app.core.llm import llm

# Check if a GPU is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
compute_type = "float16" if device.type == "cuda" else "int8"

model_size = "turbo"
transcription_model = WhisperModel(
    model_size,
    device=device.type,
    compute_type=compute_type
)

# Define function to remove non-ascii characters
def remove_non_ascii(text):
    return ''.join(i for i in text if ord(i) < 128).strip()

def transcribe(audio_url: str):
    segments, info = transcription_model.transcribe(audio_url, beam_size=5, vad_filter=True)

    # Language information
    transcription_info = {
        "language": info.language,
        "language_probability": info.language_probability,
        "transcript": ""
    }

    formatted_lines = []

    for segment in segments:
        text = remove_non_ascii(segment.text)
        formatted_line = f"[{segment.start:.1f} - {segment.end:.1f}] {text}"
        formatted_lines.append(formatted_line)

    transcription_info["transcript"] = "\n ".join(formatted_lines)
    return transcription_info

def post_process_transcription(transcript: str, keywords: list[str]):
    system_template = """You are a helpful assistant that analyses radio and tv transcripts for brodcats in Africs.
      The transcripts can be a mixture of English and Kiswahili languages, some street slang like Sheng'
      Insert necessary punctuation such as periods, commas, capialization, symbols like percentage signs, and
      formatting numbers instead of numeric description in words where necessary.
      Also if you come across words that match any of the words supplied in the list below, kindly format them appropriately
      {keywords}
      The timestamps are defined at the begining of each line using the formart [0 - 10]. Do not remove them

      The transcript:
      {transcript}
      """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", "{transcript}")]
    )

    chain = prompt | llm | StrOutputParser()
    processed_transcript = chain.invoke({ "keywords": ", ".join(keywords), "transcript": transcript })

    return processed_transcript

def remove_timestamps_and_format(transcript):
    # Use regex to remove timestamps in the format [start - end]
    cleaned_text = re.sub(r"\[\d+(\.\d+)?\s*-\s*\d+(\.\d+)?\]", "", transcript)

    # Remove any leftover newline characters and extra spaces
    cleaned_text = cleaned_text.replace("\n", " ").strip()

    # Handle excessive spaces between words
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text
