from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)

# Load environment variables from '.env'
load_dotenv()

# Initialize language model
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

fallback_llm = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    api_version="2023-06-01-preview",  # or your api version
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

def try_with_fallback(input_data):
    try:
        print("using primary llm")
        return primary_llm.invoke(input_data)
    except Exception as e:
        print(f"Primary LLM failed, using fallback. Error: {e}")
        return fallback_llm.invoke(input_data)
    
# Create a runnable that includes fallback logic
llm = RunnableLambda(try_with_fallback)