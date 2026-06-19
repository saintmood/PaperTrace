import json

from mirascope import llm

from config import settings
from application.models import ArticleMetadata


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
    {schema}

    """
