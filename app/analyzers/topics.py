from app.core.prompts import TOPIC_NAME_PROMPT
from langchain.prompts import PromptTemplate
from app.core.llm import llm
from langchain_core.output_parsers import StrOutputParser
from app.analyzers.ai_api_client import APIClient
import os

AI_API_URL = os.getenv("AI_API_URL", "https://ai-api2-350748994585.us-central1.run.app")

async def analyze_topics(text: str):
    try:
        client = APIClient(base_url=AI_API_URL)  
        topics_result = await client.analyze_topics(text=text)

        prompt_template = PromptTemplate(
            input_variables=["keywords"],
            template=TOPIC_NAME_PROMPT
        )

        topic_names = []

        for topic_keywords in topics_result:
            prompt = prompt_template.format(keywords=topic_keywords)
            ai_message  = llm.invoke(prompt)
            topic_name = ai_message.content.strip()

            topic_names.append({
                "label": topic_name,
                "keywords": topic_keywords
            })
        
        return topic_names
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.close()
