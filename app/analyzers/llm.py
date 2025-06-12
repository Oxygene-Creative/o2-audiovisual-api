from app.core.prompts import ANALYSE_ADS_SHOWS_ENGAGEMENT_PROMPT
from app.core.llm import llm
from langchain.output_parsers import PydanticOutputParser
from app.models.analytics import LLMAnalysisModel
from langchain_core.prompts import PromptTemplate

def llm_transcript_analysis(transcript: str) -> LLMAnalysisModel:

    # Create output parser
    parser = PydanticOutputParser(pydantic_object=LLMAnalysisModel)

    # Create analysis prompt
    prompt = PromptTemplate(
        template=ANALYSE_ADS_SHOWS_ENGAGEMENT_PROMPT,
        input_variables=["transcript"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    llm_analysis = chain.invoke({ "transcript": transcript })

    return llm_analysis
