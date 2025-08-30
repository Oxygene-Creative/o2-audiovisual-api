import asyncio
import time
from app.analyzers.transcription import post_process_transcription, transcribe
from app.core.graphql import get_all_terms
from app.core.redis import redis_router as asr_broker
from faststream.redis import StreamSub
from app.core.es import fetch_stream_data, update_stream_data
import logging

# Configure the logger
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Create logger instance
logger = logging.getLogger(__name__)

async def _process_asr(data: list[dict]):
    try:
        # Start timing
        start_time = time.time() 
        data = fetch_stream_data(data)

        # Define an async function for processing a single segment
        async def process_segment(index, segment):
            # Async transcription using the process pool
            transcript = await transcribe(segment["audio_file"])
            
            # Introduce a delay before calling the LLM-powered function
            await asyncio.sleep(0.5) 
            raw_text = transcript["raw_text"]
            word_count = len(raw_text.split())
            if raw_text.strip() and word_count > 5:
                processed_transcript = await post_process_transcription(
                    transcript["raw_text"]
                )

                data[index]["raw_text"] = processed_transcript
                data["segments"][index]["language"] = transcript["language"]
                data["segments"][index]["language_score"] = transcript["language_score"]

    except Exception as e:
        logger.error(f"An unexpected error occurred during audience: {e}")
        raise


@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="audiovisual:asr_group",
        consumer="asr_worker_1",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_1(messages):
    return


@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="audiovisual:asr_group",
        consumer="asr_worker_2",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_2(messages):
    return

@asr_broker.subscriber(stream=StreamSub(
        "audiovisual:asr_stream",
        group="audiovisual:asr_group",
        consumer="asr_worker_3",
        batch=True,
        max_records=10,
        polling_interval=100,
    )
)
async def process_asr_worker_3(messages):
    return