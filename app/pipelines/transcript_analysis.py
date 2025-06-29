from fastapi import FastAPI
from app.analyzers.embeddings import embed_text
from app.analyzers.emotion import analyze_emotions
from app.analyzers.llm import llm_transcript_analysis
from app.analyzers.nlp import categorize_text, match_keywords
from app.analyzers.sentiment import sentiment_analysis
from app.analyzers.topics import analyze_topics
from app.models.recording import Recording, SegmentRecording
from faststream.redis import fastapi
from app.models.analytics import AnalysisModel, ShowMetadata, Topic, TopicWord
from datetime import datetime, timezone, timedelta
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
import requests

# Define the EAT timezone as UTC+03:00
EAT = timezone(timedelta(hours=3))

# Create a global executor for process-based parallelism
executor = ProcessPoolExecutor()

GPU_ACTIVATED = os.getenv("GPU_ACTIVATED", "false").lower() == "true"
TRANSCRIPTION_GPU_URL = os.getenv("TRANSCRIPTION_GPU_URL", "").strip()

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
            transcript = await transcribe(segment["audio_file"])
            
            # Introduce a delay before calling the LLM-powered function
            await asyncio.sleep(0.5) 
            raw_text = transcript["raw_text"]
            word_count = len(raw_text.split())
            if raw_text.strip() and word_count > 5:
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

        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to transcribe audio: {time_taken:.2f} seconds.")

        # Return updated data object
        return json.dumps(data)

    except Exception as e:
        print(f"Error during audio transcription: {e}")
        # await transcript_router.broker.publish(msg, "av:transcript_embeddings")

async def handle_transcript_analysis(msg: str):
    try:
        
        data = json.loads(msg)

        # Start timing
        start_time = time.time()

        tag_name = "Radio" if data["type"] == "audio" else "Tv"
        categories = await asyncio.to_thread(get_tags, tag_name)

        # Semaphore to control concurrent execution
        semaphore = asyncio.Semaphore(5)  # Max 5 async tasks at a time

        async def process_segment(index, segment):
            async with semaphore:
                try:
                    raw_text = segment.get("raw_text", "").strip()
                    word_count = len(raw_text.split())

                    # Skip segments with fewer than 5 words
                    if not raw_text or word_count < 5:
                        print(f"Segment {index} skipped. Missing or too few words (word count: {word_count}).")
                        return

                    # Clean transcript text
                    clean_transcript = await asyncio.to_thread(remove_timestamps_and_format, raw_text)

                    tag_matches, topics_result, emotions, sentiment, embeddings  = await asyncio.gather(
                        categorize_text(clean_transcript, categories),
                        analyze_topics(clean_transcript),
                        analyze_emotions(clean_transcript),
                        sentiment_analysis(clean_transcript),
                        embed_text(clean_transcript)
                    )

                    # Save results back to the segment
                    segment["embeddings"] = embeddings
                    segment["sentiment"] = sentiment
                    segment["tags"] =tag_matches
                    segment["emotions"] = emotions
                    segment["topics"] = topics_result

                except Exception as segment_error:
                    print(f"Error processing segment {index}: {segment_error}")

        # Create tasks for all segments
        tasks = [process_segment(index, segment) for index, segment in enumerate(data["segments"])]
        await asyncio.gather(*tasks)  # Run all segment tasks concurrently

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

async def handle_transcript_llm(msg: str):
    try:
        data = json.loads(msg)

        # Start timing
        start_time = time.time()

        for index, segment in enumerate(data["segments"]):
            # Ensure `raw_text` exists and has enough words
            raw_text = segment.get("raw_text", "").strip()
            word_count = len(raw_text.split())  # Count the number of words

            if not raw_text or word_count < 5:  # Skip text with fewer than 5 words
                print(f"Segment {index} skipped. Missing or too few words (word count: {word_count}).")
                continue

            await asyncio.sleep(5) 

            llm_analysis = await asyncio.to_thread(
                llm_transcript_analysis, segment["raw_text"]
            )

            llm_analysis_json = llm_analysis.model_dump_json()
            llm_analysis_dict = json.loads(llm_analysis_json)
            data["segments"][index].update(llm_analysis_dict)

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
    
async def handle_save_analysis_es(msg: str):
    try:
        data = json.loads(msg)

        # Start timing
        start_time = time.time()

        stream_type = "radio" if data["type"] == "audio" else "tv"
        index_id = f"{stream_type}_{data['stream_id']}"

        # Generate Segment Recordings
        segment_recordings = SegmentRecording.create_segment_recordings_from_dict(data)

        for segment in segment_recordings:
            await asyncio.to_thread(save, index_id, json.dumps(segment))

        recording = Recording.create_from_analysis_model(data)

        # Concatenate all `gcp_path` values from the segments into a comma-separated list
        file_paths = ",".join(segment["gcp_path"] for segment in data.get("segments", []) if segment.get("gcp_path"))

        timestamp = recording.get("timestamp", "")
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
            else:
                dt = datetime.now(timezone.utc)
            
            timestamp = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        except ValueError:
            dt = datetime.now(EAT)
            timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        if recording.get("type") == "TV_STREAM":
            add_tv_stream_upload(
                tv_stream_id=recording.get("stream_id", ""),
                file_path=file_paths,
                file_name=recording.get("stream_name", ""),
                file_size=recording.get("file_size", 0.0),
                timestamp=timestamp,
                male=float(recording.get("male", 0.0)),
                female=float(recording.get("female", 0.0)),
                music=float(recording.get("music", 0.0)),
                noise=float(recording.get("noise", 0.0)),
                noEnergy=float(recording.get("noEnergy", 0.0)),
                recording_id=recording.get("id", ""),
                duration=recording.get("duration", 0.0),
            )
        elif recording.get("type") == "RADIO_STREAM":
            add_radio_stream_upload(
                radio_stream_id=recording.get("stream_id", ""),
                file_path=file_paths,
                file_name=recording.get("stream_name", ""),
                file_size=recording.get("file_size", 0.0),
                timestamp=timestamp,  
                male=float(recording.get("male", 0.0)),
                female=float(recording.get("female", 0.0)),
                music=float(recording.get("music", 0.0)),
                noise=float(recording.get("noise", 0.0)),
                noEnergy=float(recording.get("noEnergy", 0.0)),
                recording_id=recording.get("id", ""),
                duration=recording.get("duration", 0.0),
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
    