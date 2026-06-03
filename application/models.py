from enum import Enum
from pydantic import BaseModel


class ArticleState(str, Enum):
    """Represents the lifecycle state of a parsed document."""

    RAW = "RAW"
    PENDING_REVIEW = "PENDING_REVIEW"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"


class ArticleMetadata(BaseModel):
    """Pure Domain Model: Only the final structured data."""

    title: str
    authors: list[str]
    abstract: str


class DocumentRecord(BaseModel):
    """Database record representation."""

    id: str | None = None
    file_path: str
    metadata: ArticleMetadata
    state: ArticleState = ArticleState.RAW


class ProcessingContext(BaseModel):
    """
    State Object for the pipeline.
    Carries all transient data across the pipeline stages.
    """

    file_path: str
    raw_text: str
    draft_metadata: ArticleMetadata | None = None  # Populated by Worker
    final_metadata: ArticleMetadata | None = None  # Populated by Supervisor

    # We can even add tracking metadata here!
    total_tokens_used: int = 0
