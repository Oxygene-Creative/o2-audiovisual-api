from fastapi import FastAPI
from app.analyzers.embeddings import embed_text
from app.analyzers.llm import llm_transcript_analysis
from app.analyzers.nlp import categorize_text, match_keywords, topic_modelling
from app.analyzers.sentiment import sentiment_analysis
from app.models.recording import Recording, SegmentRecording
from faststream.redis import fastapi
from app.models.analytics import AnalysisModel, ShowMetadata, Topic, TopicWord
from datetime import datetime
import time 
from app.analyzers.transcription import remove_timestamps_and_format, transcribe, post_process_transcription
from app.core.graphql import add_radio_stream_upload, add_tv_stream_upload, get_all_terms, get_tags
from app.core.es import save
import os
from app.core.redis import redis_router as transcript_router
import asyncio
from concurrent.futures import ProcessPoolExecutor
import httpx
import json
from dotenv import load_dotenv
load_dotenv()

# Create a global executor for process-based parallelism
executor = ProcessPoolExecutor()

GPU_ACTIVATED = os.getenv("GPU_ACTIVATED", "false").lower() == "true"
TRANSCRIPTION_GPU_URL = os.getenv("TRANSCRIPTION_GPU_URL", "").strip()

async def async_audio_transcription(audio_path):
    if GPU_ACTIVATED and TRANSCRIPTION_GPU_URL:
        try:
            async with httpx.AsyncClient() as client:
                # Open the audio file for binary upload
                with open(audio_path, "rb") as audio_file:
                    files = {"file": (os.path.basename(audio_path), audio_file, "audio/mpeg")}
                    response = await client.post(f"{TRANSCRIPTION_GPU_URL}/transcribe", files=files)
                    response.raise_for_status()
                    response_data = response.json()
                    return response_data["transcription"]
        except httpx.HTTPError as e:
            print(f"HTTP error during GPU segmentation: {e}")
            raise
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, transcribe, audio_path)

async def handle_audio_transcribe(msg: str):
    try:
        data = json.loads(msg)
        keywords = await asyncio.to_thread(get_all_terms)  # Fetch keywords asynchronously

        # Start timing
        start_time = time.time()

        # Allow up to 2 concurrent calls to LLM
        llm_semaphore = asyncio.Semaphore(2)  

        # Define an async function for processing a single segment
        async def process_segment(index, segment):
            # Async transcription using the process pool
            transcript = await async_audio_transcription(segment["audio_file"])
            
            # Introduce a delay before calling the LLM-powered function
            await asyncio.sleep(0.5) 

            # Control access to the LLM with the semaphore
            async with llm_semaphore:
                processed_transcript = await asyncio.to_thread(
                    post_process_transcription, transcript["raw_text"], keywords
                )

            data["segments"][index]["raw_text"] = processed_transcript
            data["segments"][index]["language"] = transcript["language"]
            data["segments"][index]["language_score"] = transcript["language_score"]


        # Create tasks for all segments
        tasks = [
            process_segment(index, segment) for index, segment in enumerate(data["segments"])
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

        # for index, segment in enumerate(data.segments):
        #     # Transcribe audio
        #     transcript = await asyncio.to_thread(transcribe, segment.audio_file)

        #     # Process transcript
        #     processed_transcript = await asyncio.to_thread(
        #         post_process_transcription, transcript["raw_text"], keywords
        #     )

        #     # Update segment attributes
        #     data.segments[index].raw_text = processed_transcript
        #     data.segments[index].language = transcript["language"]
        #     data.segments[index].language_score = transcript["language_score"]

        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to transcribe audio: {time_taken:.2f} seconds.")

        # Return updated data object
        return json.dumps(data)

    except Exception as e:
        print(f"Error during audio transcription: {e}")
        await transcript_router.broker.publish(msg, "av:transcript_embeddings")

async def handle_transcript_analysis(msg: str):
    try:
        data = json.loads(msg)

        # Start timing
        start_time = time.time()

        tag_name = "Radio" if data["type"] == "audio" else "Tv"
        categories = await asyncio.to_thread(get_tags, tag_name)

        for index, segment in enumerate(data["segments"]):
            # Clean transcript text
            clean_transcript = await asyncio.to_thread(
                remove_timestamps_and_format, segment["raw_text"]
            )

            # Create embeddings
            embeddings = await asyncio.to_thread(embed_text, clean_transcript)
            data["segments"][index]["embeddings"] = embeddings.tolist()

            # Sentiment analysis
            sentiment = await asyncio.to_thread(sentiment_analysis, clean_transcript)
            data["segments"][index]["sentiment"] = sentiment

            # Category analysis
            category_matches = await asyncio.to_thread(
                categorize_text, clean_transcript, categories
            )
            data["segments"][index]["tags"] = category_matches

        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(
            f"Time taken to perform NLP analysis on transcripts: {time_taken:.2f} seconds."
        )

        # Return updated data object
        return json.dumps(data)

    except Exception as e:
        print(f"Error during transcript analysis: {e}")
        await transcript_router.broker.publish(msg, "av:transcript_sentiment")


async def handle_transcript_llm(msg: str):
    try:
        data = json.loads(msg)

        # Start timing
        start_time = time.time()

        for index, segment in enumerate(data["segments"]):
            llm_analysis = await asyncio.to_thread(
                llm_transcript_analysis, segment["raw_text"]
            )

            # Update segment attributes
            data["segments"][index]["ads"] = llm_analysis.get("ads", [])
            data["segments"][index]["show_metadata"] = llm_analysis.get("show_metadata", ShowMetadata()).dict()
            data["segments"][index]["engagement"] = llm_analysis.get("engagement", [])

        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(
            f"Time taken to analyze show metadata, ads, and engagement using LLM: {time_taken:.2f} seconds."
        )

        # Publish based on type
        if data["type"]  == "audio":
            await transcript_router.broker.publish(
                json.dumps(data), "av:upload_audio_gcp"
            )
        elif data["type"] == "video":
            await transcript_router.broker.publish(
                json.dumps(data), "av:upload_video_gcp"
            )

    except Exception as e:
        print(f"Error during LLM transcript analysis: {e}")
        if data["type"] == "audio":
            await transcript_router.broker.publish(
                json.dumps(data), "av:upload_audio_gcp"
            )
        elif data["type"] == "video":
            await transcript_router.broker.publish(
                json.dumps(data), "av:upload_video_gcp"
            )
    
async def handle_save_analysis_es(msg: str):
    try:
        data = json.loads(msg)

        # Start timing
        start_time = time.time()

        stream_type = "radio" if data["type"] == "audio" else "tv"
        index_id = f"{stream_type}_{data['stream_id']}"

        # Create segment recordings
        segment_recordings = SegmentRecording.create_segment_recordings_from_dict(data)

        for segment in segment_recordings:
            segment_json = segment.model_dump()()
            await asyncio.to_thread(save, index_id, json.dumps(segment_json))

        recording = Recording.create_from_analysis_model(data)

        # Concatenate all `gcp_path` values from the segments into a comma-separated list
        file_paths = ",".join(segment["gcp_path"] for segment in data.get("segments", []) if segment.get("gcp_path"))

        if recording.type == "TV_STREAM":
            add_tv_stream_upload(
                tv_stream_id=recording.stream_id,
                file_path=file_paths,
                file_name=recording.stream_name,
                file_size=recording.file_size,
                timestamp=recording.timestamp.isoformat(),
                male=recording.male,
                female=recording.female,
                music=recording.music,
                noise=recording.noise,
                noEnergy=recording.noEnergy,
                recording_id=recording.id,
                duration=recording.duration
            )
        elif recording.type == "RADIO_STREAM":
            add_radio_stream_upload(
                radio_stream_id=recording.stream_id,
                file_path=file_paths,
                file_name=recording.stream_name,
                file_size=recording.file_size,
                timestamp=recording.timestamp.isoformat(),
                male=recording.male,
                female=recording.female,
                music=recording.music,
                noise=recording.noise,
                noEnergy=recording.noEnergy,
                recording_id=recording.id,
                duration=recording.duration
            )
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(
            f"Time taken to save recording and segments to Elasticsearch: {time_taken:.2f} seconds."
        )

    except Exception as e:
        print(f"Error during Elasticsearch save operation: {e}")

@transcript_router.subscriber("av:audio_transcribe")
@transcript_router.publisher("av:transcript_analysis")
async def audio_transcribe(msg: str):
    return await handle_audio_transcribe(msg)

@transcript_router.subscriber("av:transcript_analysis")
@transcript_router.publisher("av:transcript_llm")
async def transcript_analysis(msg: str):
    return await handle_transcript_analysis(msg)


@transcript_router.subscriber("av:transcript_llm")
async def transcript_llm(msg: str):
    await handle_transcript_llm(msg)

@transcript_router.subscriber("av:save_analysis_es")
async def save_analysis_es(msg: str):
    await handle_save_analysis_es(msg)
    