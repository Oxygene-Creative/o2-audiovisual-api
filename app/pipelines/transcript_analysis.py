from fastapi import FastAPI
from app.analyzers.embeddings import embed_text
from app.analyzers.llm import llm_transcript_analysis
from app.analyzers.nlp import categorize_text, match_keywords, sentiment_analysis, topic_modelling
from faststream.redis import RedisRouter
from app.models.analytics import AnalysisModel
from datetime import datetime
import time 
from app.analyzers.transcription import remove_timestamps_and_format, transcribe, post_process_transcription
from app.core.graphql import get_all_keywords, get_tags
transcript_router = RedisRouter()

@transcript_router.subscriber("audio_transcribe")
@transcript_router.publish("transcript_embeddings")
async def audio_seg(data: AnalysisModel):
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

@transcript_router.subscriber("transcript_embeddings")
@transcript_router.publish("transcript_sentiment")
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

@transcript_router.subscriber("transcript_sentiment")
@transcript_router.publish("transcript_categories")
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

@transcript_router.subscriber("transcript_categories")
@transcript_router.publish("transcript_keywords")
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

@transcript_router.subscriber("transcript_keywords")
@transcript_router.publish("transcript_topics")
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

@transcript_router.subscriber("transcript_topics")
@transcript_router.publish("transcript_llm")
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

@transcript_router.subscriber("transcript_llm")
@transcript_router.publish("upload_segments_gcp")
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
    
    return data


