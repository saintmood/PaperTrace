from enum import Enum

from pydantic import BaseModel


class ArticleState(str, Enum):
    """Represents the lifecycle state of a parsed document."""

    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"
    RAW = "RAW"


class DocumentRecord(BaseModel):
    """Database record representation."""

    id: str | None = None
    file_path: str
    metadata: ArticleMetadata
    state: ArticleState = ArticleState.RAW


class ArticleMetadata(BaseModel):
    """Pure Domain Model: Only the final structured data."""

    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]
    reasoning: str | None = None  # Optional field to capture LLM's reasoning process


class EvaluationResponse(BaseModel):
    """Structured response from the SupervisorAgent's evaluation."""

    is_approved: bool
    feedback: str
    suggested_corrections: ArticleMetadata | None = None
    proposed_filename: str


class ProcessingContext(BaseModel):
    """
    State Object for the pipeline.
    Carries all transient data across the pipeline stages.
    """

    file_path: str
    raw_text: str
    draft_metadata: ArticleMetadata | None = None  # Populated by Worker
    final_metadata: ArticleMetadata | None = None  # Populated by Supervisor
    supervisor_review: EvaluationResponse | None = None  # Supervisor's feedback and approval status

    # We can even add tracking metadata here!
    total_tokens_used: int = 0
