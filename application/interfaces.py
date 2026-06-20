from typing import Protocol

from application.models import ProcessingContext


class IPDFReader(Protocol):
    """Contract for extracting text from specific pages."""

    def extract_optimized_text(self, file_path: str) -> str: ...


class ILLMAgent(Protocol):
    """
    Unified contract for all agents.
    Takes the current context, mutates it, and returns the updated context.
    """

    def process(self, context: ProcessingContext) -> ProcessingContext: ...


class IRepository(Protocol):
    """Contract for saving articles to a repository."""

    def save_article(self, context: ProcessingContext) -> None:
        """Save the article in the repository based on the processing context."""
        ...
