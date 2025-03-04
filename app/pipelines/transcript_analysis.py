from fastapi import FastAPI
from app.analyzers.embeddings import embed_text
from app.analyzers.llm import llm_transcript_analysis
from app.analyzers.nlp import categorize_text, match_keywords, topic_modelling
from app.analyzers.sentiment import sentiment_analysis
from app.models.recording import Recording, SegmentRecording
from faststream.redis import fastapi
from app.models.analytics import AnalysisModel
from datetime import datetime
import time 
from app.analyzers.transcription import remove_timestamps_and_format, transcribe, post_process_transcription
from app.core.graphql import get_all_terms, get_tags
from app.core.es import save, save_bulk
import os
from app.core.redis import redis_router as transcript_router

from dotenv import load_dotenv
load_dotenv()

@transcript_router.subscriber("av:audio_transcribe")
@transcript_router.publisher("av:transcript_embeddings")
async def audio_transcribe(msg: str):
    try:
        data = AnalysisModel.model_validate_json(msg)
        keywords = get_all_terms()
        # Start timing
        start_time = time.time()
        for index, segment in enumerate(data.segments):
            transcript = transcribe(segment.audio_file)
            processed_transcript = post_process_transcription(transcript['raw_text'], keywords)
            data.segments[index].raw_text = processed_transcript
            data.segments[index].language = transcript['language']
            data.segments[index].language_score = transcript['language_score']
        
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to transcribe audio: {time_taken:.2f} seconds.")
        return data.model_dump_json()
    except Exception as e:
        print(e)
        await transcript_router.broker.publish(msg, "av:transcript_embeddings")

@transcript_router.subscriber("av:transcript_embeddings")
@transcript_router.publisher("av:transcript_sentiment")
async def transcript_embeddings(msg: str):
    try:
        data = AnalysisModel.model_validate_json(msg)
        # Start timing
        start_time = time.time()
        for index, segment in enumerate(data.segments):
            clean_transcript = remove_timestamps_and_format(segment.raw_text)
            embeddings = embed_text(clean_transcript)
            data.segments[index].embeddings = embeddings.tolist()
        
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to embed audio transcripts: {time_taken:.2f} seconds.")
        
        return data.model_dump_json()
    except Exception as e:
        print(e)
        await transcript_router.broker.publish(msg, "av:transcript_sentiment")
    
@transcript_router.subscriber("av:transcript_sentiment")
@transcript_router.publisher("av:transcript_categories")
async def transcript_sentiment(msg: str):
    try:
        data = AnalysisModel.model_validate_json(msg)
        # Start timing
        start_time = time.time()
        for index, segment in enumerate(data.segments):
            clean_transcript = remove_timestamps_and_format(segment.raw_text)
            sentiment = sentiment_analysis(clean_transcript)
            data.segments[index].sentiment = sentiment
            
            # print("Sentiment per segment: ")
            # print(data.segments[index].sentiment)
        
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to analyse sentiments for transcripts: {time_taken:.2f} seconds.")
        
        return data.model_dump_json()
    except Exception as e:
        print(e)
        await transcript_router.broker.publish(msg, "av:transcript_categories")

@transcript_router.subscriber("av:transcript_categories")
@transcript_router.publisher("av:transcript_keywords")
async def transcript_categories(msg: str):
    try:
        data = AnalysisModel.model_validate_json(msg)
        tag_name = ""
        if data.type == "audio":
            tag_name = "Radio"
        elif data.type == "video":
            tag_name == "Tv"
        categories = get_tags(tag_name)
        # Start timing
        start_time = time.time()
        for index, segment in enumerate(data.segments):
            clean_transcript = remove_timestamps_and_format(segment.raw_text)
            category_matches = categorize_text(clean_transcript, categories)
            data.segments[index].tags = category_matches

            print("Matched tags:")
            print(data.segments[index].tags)
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to categorize audio transcripts: {time_taken:.2f} seconds.")
        
        return data.model_dump_json()
    except Exception as e:
        print(e)
        await transcript_router.broker.publish(msg, "av:transcript_keywords")

@transcript_router.subscriber("av:transcript_keywords")
@transcript_router.publisher("av:transcript_topics")
async def transcript_keywords(msg: str):
    try:
        data = AnalysisModel.model_validate_json(msg)
        keywords = get_all_terms()
        # Start timing
        start_time = time.time()
        for index, segment in enumerate(data.segments):
            clean_transcript = remove_timestamps_and_format(segment.raw_text)
            keyword_matches = match_keywords(clean_transcript, keywords)
            data.segments[index].keywords = keyword_matches
        
            print("Matched queries:")
            print(data.segments[index].keywords)
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to match keywords in audio transcripts: {time_taken:.2f} seconds.")
        
        return data.model_dump_json()
    except Exception as e:
        print(e)
        await transcript_router.broker.publish(msg, "av:transcript_topics")

@transcript_router.subscriber("av:transcript_topics")
@transcript_router.publisher("av:transcript_llm")
async def transcript_topics(msg: str):
    try:
        data = AnalysisModel.model_validate_json(msg)
        # Start timing
        start_time = time.time()
        for index, segment in enumerate(data.segments):
            clean_transcript = remove_timestamps_and_format(segment.raw_text)
            topics = topic_modelling(clean_transcript)
            data.segments[index].topics = topics
            print("Topics discovered for each segment:")
            print(data.segments[index].topics)
        
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to model topics in audio transcripts: {time_taken:.2f} seconds.")
        
        return data.model_dump_json()
    except Exception as e:
        print(e)
        await transcript_router.broker.publish(msg, "av:transcript_llm")

@transcript_router.subscriber("av:transcript_llm")
async def transcript_llm(msg: str):
    data = AnalysisModel.model_validate_json(msg)
    try:
        # Start timing
        start_time = time.time()
        for index, segment in enumerate(data.segments):
            llm_analysis = llm_transcript_analysis(segment.raw_text)
            data.segments[index].ads = llm_analysis.ads
            data.segments[index].show_metadata = llm_analysis.show_metadata
            data.segments[index].engagement = llm_analysis.engagement
            # print("Ads, Show Metadata and Engagement discovered for each segment:")
            # print(data.segments[index].ads)
            # print(data.segments[index].show_metadata)
            # print(data.segments[index].engagement)
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to analyze show metadata, ads and engagement using llm: {time_taken:.2f} seconds.")
        
        if data.type == "audio":
            await transcript_router.broker.publish(data.model_dump_json(), "av:upload_audio_gcp")
        elif data.type == "video":
            await transcript_router.broker.publish(data.model_dump_json(), "av:upload_video_gcp")
    except Exception as e:
        # Handle any other exception (fallback)
        print(f"Unexpected error: {e}")
        if data.type == "audio":
            await transcript_router.broker.publish(data.model_dump_json(), "av:upload_audio_gcp")
        elif data.type == "video":
            await transcript_router.broker.publish(data.model_dump_json(), "av:upload_video_gcp")

@transcript_router.subscriber("av:save_analysis_es")
async def save_analysis_es(msg: str):
    try:
        data = AnalysisModel.model_validate_json(msg)
        # Start timing
        start_time = time.time()
        stream_type = ""
        if data.type == "audio":
            stream_type = "radio"
        elif data.type == "video":
            stream_type == "tv"
        index_id = f"{stream_type}_{data.stream_id}"
        
        segment_recordings = SegmentRecording.create_segment_recordings_from_analysis_model(data)
        recording = Recording.create_from_analysis_model(data)
        # Convert the Recording object to a dictionary
        recording_dict = dict(recording)
        
        print("Recording Info: ")
        print(recording_dict)

        save("recording", recording_dict)
        
        actions = [
            {
                "_index": index_id,  
                "_source": dict(segment),
            }
            for segment in segment_recordings
        ]
        print("Segment Info: ")
        print(actions)
        
        save_bulk(actions)
        
        # End timing
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Time taken to save recording and segments to elastic search: {time_taken:.2f} seconds.")
        
        return
    except Exception as e:
        # Handle any other exception (fallback)
        print(f"Unexpected error: {e}")
    
    