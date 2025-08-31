from app.analyzers.ai_api_client import APIClient
import os

AI_API_URL = os.getenv("AI_API_URL", "https://ai-api2-350748994585.us-central1.run.app")

async def sentiment_analysis(data: list):
    try:
        client = APIClient(base_url=AI_API_URL)  
        sentiment_result = await client.analyze_sentiment(data=data)
        return sentiment_result
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close()    