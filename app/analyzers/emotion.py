from typing import List, Dict, Union
from app.analyzers.ai_api_client import APIClient
import os

AI_API_URL = os.getenv("AI_API_URL", "https://ai-api2-350748994585.us-central1.run.app")

async def analyze_emotions(data: list) -> Dict:
    try:
        client = APIClient(base_url=AI_API_URL)    
        # Emotions example
        emotions_result = await client.get_emotions(data=data)
        return emotions_result
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close()
    