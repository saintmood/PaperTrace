from mirascope import llm

from config import settings
from application.models import ArticleMetadata


@llm.call(model=settings.llm_model_name, format=ArticleMetadata)
def extract_article_metadata(raw_text: str, previous_error: str | None = None) -> ArticleMetadata:
    """
    Mirascope function to extract article metadata from raw text.
    The LLM will be prompted to return a structured ArticleMetadata object.
    """
    error_section = ""
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
    
    PAPER TEXT:
    {raw_text}
    PREVIOUS ERROR:
    {error_section}
    """
