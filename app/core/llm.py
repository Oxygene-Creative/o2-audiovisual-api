from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import RunnableLambda
from langchain_core.rate_limiters import InMemoryRateLimiter

gemini_rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,  # <-- Can only make a request once every 2 seconds!!
    check_every_n_seconds=0.1,  # Wake up every 100 ms to check whether allowed to make a request,
    max_bucket_size=10,  # Controls the maximum burst size.
)

load_dotenv()

# Initialize language model
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    rate_limiter=gemini_rate_limiter
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
        return primary_llm.invoke(input_data)
    except Exception as e:
        print(f"Primary LLM failed, using fallback. Error: {e}")
        return fallback_llm.invoke(input_data)
    
# Create a runnable that includes fallback logic
llm = RunnableLambda(try_with_fallback)