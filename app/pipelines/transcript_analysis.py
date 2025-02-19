from fastapi import FastAPI
from app.analyzers.embeddings import embed_text
from app.analyzers.llm import llm_transcript_analysis
from app.analyzers.nlp import categorize_text, match_keywords, sentiment_analysis, topic_modelling
from app.models.recording import Recording, SegmentRecording
from faststream.redis import fastapi
from app.models.analytics import AnalysisModel
from datetime import datetime
import time 
from app.analyzers.transcription import remove_timestamps_and_format, transcribe, post_process_transcription
from app.core.graphql import get_all_keywords, get_tags
from app.core.es import save, save_bulk
import os

transcript_router = fastapi.RedisRouter(os.environ['REDIS_URI'])

@transcript_router.subscriber("av:audio_transcribe")
# @transcript_router.publisher("av:transcript_embeddings")
@transcript_router.publisher("av:transcript_sentiment")
async def audio_transcribe(data: AnalysisModel):
    keywords = get_all_keywords()
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        transcript = transcribe(segment.audio_file)
        processed_transcript = post_process_transcription(transcript, keywords)
        data.segments[index].transcript = processed_transcript
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to transcribe audio: {time_taken:.2f} seconds.")
    return data

@transcript_router.subscriber("av:transcript_embeddings")
@transcript_router.publisher("av:transcript_sentiment")
async def transcript_embeddings(data: AnalysisModel):
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        clean_transcript = remove_timestamps_and_format(segment.transcript)
        embeddings = embed_text(clean_transcript)
        data.segments[index].embeddings = embeddings
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to embed audio transcripts: {time_taken:.2f} seconds.")
    
    return data

@transcript_router.subscriber("av:transcript_sentiment")
@transcript_router.publisher("av:transcript_categories")
async def transcript_sentiment(data: AnalysisModel):
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        clean_transcript = remove_timestamps_and_format(segment.transcript)
        sentiment = sentiment_analysis(clean_transcript)
        data.segments[index].sentiment = sentiment
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to analyse sentiments for transcripts: {time_taken:.2f} seconds.")
    
    return data

@transcript_router.subscriber("av:transcript_categories")
@transcript_router.publisher("av:transcript_keywords")
async def transcript_categories(data: AnalysisModel):
    categories = get_tags(data.type)
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        clean_transcript = remove_timestamps_and_format(segment.transcript)
        category_matches = categorize_text(clean_transcript, categories)
        data.segments[index].categories = category_matches
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to categorize audio transcripts: {time_taken:.2f} seconds.")
    
    return data

@transcript_router.subscriber("av:transcript_keywords")
@transcript_router.publisher("av:transcript_topics")
async def transcript_keywords(data: AnalysisModel):
    keywords = get_all_keywords()
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        clean_transcript = remove_timestamps_and_format(segment.transcript)
        keyword_matches = match_keywords(clean_transcript, keywords)
        data.segments[index].keywords = keyword_matches
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to match keywords in audio transcripts: {time_taken:.2f} seconds.")
    
    return data

@transcript_router.subscriber("av:transcript_topics")
@transcript_router.publisher("av:transcript_llm")
async def transcript_topics(data: AnalysisModel):
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        clean_transcript = remove_timestamps_and_format(segment.transcript)
        topics = topic_modelling(clean_transcript)
        data.segments[index].topics = topics
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to model topics in audio transcripts: {time_taken:.2f} seconds.")
    
    return data

@transcript_router.subscriber("av:transcript_llm")
async def transcript_llm(data: AnalysisModel):
    # Start timing
    start_time = time.time()
    for index, segment in enumerate(data.segments):
        llm_analysis = llm_transcript_analysis(segment.transcript)
        data.segments[index].ads = llm_analysis.ads
        data.segments[index].show_metadata = llm_analysis.show_metadata
        data.segments[index].engagement = llm_analysis.engagement
    
    # End timing
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to analyze show metadata, ads and engagement using llm: {time_taken:.2f} seconds.")
    
    if data.type == "audio":
        await transcript_router.broker.publish(data, "av:upload_audio_gcp")
    elif data.type == "video":
        await transcript_router.broker.publish(data, "av:upload_video_gcp")


@transcript_router.subscriber("av:save_analysis_es")
async def save_analysis_es(data: AnalysisModel):
    # Start timing
    start_time = time.time()
    
    index_id = f"{data.type}_{data.stream_id}"
    
    segment_recordings = SegmentRecording.create_segment_recordings_from_analysis_model(data)
    recording = Recording.create_from_analysis_model(data)
    # Convert the Recording object to a dictionary
    recording_dict = recording.dict()
    
    print("Recording Info: ")
    print(recording_dict)

    save("recording", recording_dict)
    
    actions = [
        {
            "_index": index_id,  
            "_source": segment.dict(),
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