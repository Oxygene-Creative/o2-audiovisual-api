from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
from app.core.llm import llm
from app.analyzers.ai_api_client import APIClient
import os

AI_API_URL = os.getenv("AI_API_URL", "https://ai-api2-350748994585.us-central1.run.app")

async def transcribe(audio_url: str):
    try:
        client = APIClient(base_url=AI_API_URL)  
        transcription_result = await client.transcribe_audio(audio_path=audio_url)
        
        if transcription_result is not None:
            return transcription_result["transcription"]

        else: 
            return { "raw_text": "" }
   
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close() 

async def post_process_transcription(transcript: str, keywords: list[str]):
    system_template = """You are a helpful assistant that analyses radio and tv transcripts for brodcats in Africs.
      The transcripts can be a mixture of English and Kiswahili languages, some street slang like Sheng'
      Insert necessary punctuation such as periods, commas, capialization, symbols like percentage signs, and
      formatting numbers instead of numeric description in words where necessary.
      The timestamps are defined at the begining of each line using the formart [0 - 10]. Do not remove them

      The transcript:
      {transcript}
      """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", "{transcript}")]
    )

    chain = prompt | llm | StrOutputParser()
    processed_transcript = chain.invoke({ "keywords": ", ".join(keywords), "transcript": transcript })

    return processed_transcript.strip()

def remove_timestamps_and_format(transcript):
    # Use regex to remove timestamps in the format [start - end]
    cleaned_text = re.sub(r"\[\d+(\.\d+)?\s*-\s*\d+(\.\d+)?\]", "", transcript)

    # Remove any leftover newline characters and extra spaces
    cleaned_text = cleaned_text.replace("\n", " ").strip()

    # Handle excessive spaces between words
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text
