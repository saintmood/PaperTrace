import json

from mirascope import llm

from application.models import ArticleMetadata, EvaluationResponse
from config import settings


def get_token_usage(llm_response: any) -> int:
    """
    Utility function to extract token usage from a Mirascope LLM response.
    This can be used for monitoring and enforcing token budgets.
    """
    if hasattr(llm_response, "usage") and hasattr(llm_response.usage, "total_tokens"):
        return llm_response.usage.total_tokens
    return 0


@llm.call(model=settings.llm_model_name, format=ArticleMetadata)
def extract_article_metadata(raw_text: str, previous_error: str | None = None) -> ArticleMetadata:
    """
    Mirascope function to extract article metadata from raw text.
    The LLM will be prompted to return a structured ArticleMetadata object.
    """
    error_section = ""
    schema = ArticleMetadata.model_json_schema()
    if previous_error:
        error_section = f"""
        CRITICAL WARNING: 
        Your previous attempt to extract data failed with the following error:
        "{previous_error}"
        
        You MUST correct your output to resolve this issue. Do not repeat the same mistake.
        """
    return f"""
    You are an expert academic archivist. 
    Your task is to carefully read the provided scientific paper excerpts and extract the core metadata.
    
    RULES:
    1. Extract the exact Title.
    2. Extract the list of Authors.
    3. Extract the Keywords (maximum 5 keywords).
    4. Extract the Abstract, ensuring it is concise and free of any hallucinated information.

    CRITICAL RULES FOR EXTRACTING THE TITLE:
    1. The TITLE is usually the most prominent phrase near the beginning of the text, BUT it might not be the very first line.
    2. IGNORE publisher names, journal titles (e.g., "IEEE", "Nature"), ISSNs, dates, and copyright notices at the top.
    3. The TITLE almost ALWAYS precedes the list of Authors and the "Abstract".
    4. If the title is split across multiple lines, merge it into a single clean string.

    CRITICAL FORMATTING RULES:
    1. You MUST return ONLY valid JSON.
    2. DO NOT use XML. DO NOT use HTML.
    3. Your output MUST EXACTLY match the following REQUIRED JSON SCHEMA schema. DO NOT add any extra wrapper keys like "arguments" or "name". 
    4. Use the 'reasoning' field to explain how you found the title and authors BEFORE filling the 'metadata' block.
    
    PAPER TEXT:
    {raw_text}
    PREVIOUS ERROR:
    {error_section}

    REQUIRED JSON SCHEMA:
    {json.dumps(schema, indent=2)}

    """


@llm.call(model=settings.llm_model_name, format=EvaluationResponse)
def review_article_metadata(
    raw_text: str, article_metadata: str | None = None
) -> EvaluationResponse:
    schema = EvaluationResponse.model_json_schema()
    return f"""
    You are a strict academic Supervisor and Reviewer.
    Your task is to verify if the extracted "Draft Metadata" PERFECTLY matches the original "Paper Text".
    
    VERIFICATION RULES:
    1. Check if the Title is exactly as written in the text.
    2. Check if all Authors are included and spelled correctly.
    3. Ensure the Abstract is not cut off.
    4. If the draft is perfect, set 'is_approved' to true.
    5. If there are ANY errors, set 'is_approved' to false, explain the error in 'feedback', and provide the fixed metadata in 'suggested_corrections'.
    
    CRITICAL FORMATTING RULES:
    1. You MUST return ONLY pure, valid JSON.
    2. DO NOT use XML, HTML, or markdown formatting blocks (no ```json).
    3. Your output MUST EXACTLY match the following REQUIRED_JSON_SCHEMA schema. DO NOT add any extra wrapper keys like "arguments" or "name". 
    
    REQUIRED_JSON_SCHEMA:
    {json.dumps(schema, indent=2)}
    
    PAPER TEXT:
    {raw_text}
    
    DRAFT METADATA TO REVIEW:
    {article_metadata}
    """
