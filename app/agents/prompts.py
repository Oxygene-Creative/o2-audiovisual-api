from langchain.prompts import PromptTemplate

POST_PROCESS_TRANSCRIPT_PROMPT = PromptTemplate(
    input_variables=["keywords", "transcript"],
    template="""You are a helpful assistant that processes radio and TV transcripts for broadcasts across Africa.
      The transcripts may contain a combination of English, Kiswahili, and Sheng (street slang). Your task is to:
      - Add necessary punctuation (periods, commas, capitalization, etc.).
      - Format numbers correctly (e.g., 'ten percent' → '10%').
      - Format words matching the keywords list to align with proper usage or standard representation:
        {keywords}.
      - Keep all timestamps intact and preserve their format [e.g., [0 - 10]] at the beginning of each line.

      The transcript:
      {transcript}

      Rules:
      - Do NOT insert any extra text such as descriptions or summaries.
      - Output the processed transcript directly as is.
      - Do NOT include markdown formatting or any other non-transcript-related output.

      Example Input: [0 - 10] Hello world ten percent
      Example Output: [0 - 10] Hello world 10%
      """
)

ANALYSE_ADS_SHOWS_ENGAGEMENT_PROMPT = """
You are a transcript analyst tasked with analyzing timestamped TV/radio transcripts. 
Extract the following details strictly in JSON format:

Instructions:
1. Show metadata:
    - Extract the host name and program name.
    - If the host name or program name is not found, use `null` (e.g., `"host": null`).
    - Include the start and stop timestamps where the host identifies themselves (if available).
2. Advertisements:
    - List all advertisements found in the transcript.
    - For each advertisement, extract:
      - `brand`: Brand name being advertised.
      - `product`: Product name being advertised.
      - `start` and `stop` timestamps indicating where the advertisement appears in the transcript.
    - If no advertisements are found, use an empty array (e.g., `"ads": []`).
3. Audience engagement:
    - Identify calls for social media engagement or direct communication (e.g., hashtags, social media handles, phone numbers, or emails).
    - For each engagement, extract:
      - `platform`: Social media platform or communication method (e.g., Twitter, phone, email).
      - `identifier`: The specific handle, hashtag, phone number, or email mentioned.
      - `context`: Context where the call to action is mentioned.
      - `start` and `stop` timestamps indicating where the engagement appears in the transcript.
    - If no audience engagements are found, use an empty array (e.g., `"engagement": []`).

Rules:
- Do NOT add descriptive text, explanations, or conversational sentences.
- Output MUST conform strictly to the JSON schema format provided below.

Example JSON output format:
{{
    "ads": [
        {{
            "brand": "Coca-Cola",
            "product": "Coke Zero",
            "start": 12.5,
            "stop": 14.0
        }}
    ],
    "show_metadata": {{
        "host": "John Doe",
        "program_name": "Morning Show",
        "start": 0.0,
        "stop": 3.0
    }},
    "engagement": [
        {{
            "platform": "Twitter",
            "identifier": "@MorningShowXYZ",
            "context": "Follow us on Twitter!",
            "start": 15.0,
            "stop": 16.0
        }}
    ]
}}

Transcript:
{transcript}

{format_instructions}
"""

TOPIC_NAME_PROMPT = """
Here are some keywords describing a topic: {keywords}."
Assign a one-word or two-word label that represents an industry, domain, or concept.
Use common and well-recognized categories.
Use plain text only. Do not include any punctuation, quotes, or formatting.
"""