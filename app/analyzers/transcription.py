from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
from app.core.llm import llm
from app.analyzers.ai_api_client import APIClient
import os

AI_API_URL = os.getenv("AI_API_URL", "https://ai-api2-350748994585.us-central1.run.app")

async def transcribe(data: list[dict]):
    try:
        client = APIClient(base_url=AI_API_URL, timeout=600.0)  
        result = await client.transcribe_audio(data=data)
        
        if result is not None:
            return result

        else: 
            return []
   
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close() 


async def post_process_transcription(transcript: str):
    system_template = """You are a helpful assistant that post-processes transcripts of radio and TV broadcasts in Africa.
    The transcripts can contain a mixture of multiple African languages, regional slang, and dialects.
    Insert necessary punctuation such as periods, commas, capitalization, symbols like percentage signs, and
    format numbers instead of numeric descriptions in words where necessary. Do not change the context or meaning
    of the transcript in any way. 
    
    The timestamps are defined at the beginning of each line using the format [0 - 10]. Do not remove or alter them.

    Output only the updated transcript without extra information:

    {transcript}
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", "{transcript}")]
    )

    chain = prompt | llm | StrOutputParser()
    processed_transcript = chain.invoke({ "transcript": transcript })

    return processed_transcript.strip()

def remove_timestamps_and_format(transcript):
    # Use regex to remove timestamps in the format [start - end]
    cleaned_text = re.sub(r"\[\d+(\.\d+)?\s*-\s*\d+(\.\d+)?\]", "", transcript)

    # Remove any leftover newline characters and extra spaces
    cleaned_text = cleaned_text.replace("\n", " ").strip()

    # Handle excessive spaces between words
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text
