from app.core.llm import llm
from langchain.output_parsers import PydanticOutputParser
from app.models.analytics import LLMAnalysisModel
from langchain_core.prompts import PromptTemplate

def llm_transcript_analysis(transcript: str) -> LLMAnalysisModel:

    # Create output parser
    parser = PydanticOutputParser(pydantic_object=LLMAnalysisModel)

    # Create analysis prompt
    prompt_template = """
    You are a transcript analyst that looks out for potential adverts, audience engagement and show metadata from a tv/radio broadcast.
    Analyze the timestamped transcript and extract the requested information identified below:
    1. Show metadata (host name and program name).  If you cant find the host name or program name, just respond with a blank string on both fields
    2. Advertisements of products
    3. Calls for social media engagement or direct communication via phone or email. For socials, extract the social media handles or hashtags

    Transcript:
    {transcript}

    {format_instructions}
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["transcript"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    llm_analysis = chain.invoke({ "transcript": transcript })

    return llm_analysis
