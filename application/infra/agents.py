import logging

from pydantic import ValidationError

from application.exceptions import AIProcessingError, TokenBudgetExceededError
from application.infra.mirascope import (
    extract_article_metadata,
    get_token_usage,
    review_article_metadata,
)
from application.interfaces import ILLMAgent
from application.models import ArticleMetadata, ArticleState, EvaluationResponse, ProcessingContext
from config import settings

logger = logging.getLogger(__name__)


class WorkerAgent(ILLMAgent):
    """Extracts initial data and attaches it to the context."""

    def __init__(self, max_retries: int = settings.worker_max_retries):
        self.max_retries = max_retries

    def process(self, context: ProcessingContext) -> ProcessingContext:
        if not context.raw_text:
            raise ValueError("WorkerAgent requires raw_text in the context.")

        attempt = 1
        last_error: str | None = None

        while attempt <= self.max_retries:
            try:
                logger.info(f"WorkerAgent extraction attempt {attempt}/{self.max_retries}...")

                response = extract_article_metadata(context.raw_text, last_error)
                token_usage = get_token_usage(response)
                context.total_tokens_used += token_usage
                if context.total_tokens_used > settings.max_token_budget:
                    logger.error(
                        f"🚨 TOKEN BUDGET EXCEEDED! Used: {context.total_tokens_used}, Limit: {settings.max_token_budget}"
                    )
                    raise TokenBudgetExceededError(
                        f"Token budget exceeded: {context.total_tokens_used} tokens used."
                    )
                draft_metadata: ArticleMetadata = response.parse()
                self._validate_draft(draft_metadata)
                # Attach the draft to the context
                context.draft_metadata = draft_metadata
                return context
            except ValidationError as e:
                last_error = f"JSON Schema / Type Validation Error: {e}"
                logger.warning(f"Attempt {attempt} failed structural check.")

            except ValueError as e:
                last_error = f"Business Logic Error: {e}"
                logger.warning(f"Attempt {attempt} failed semantic check.")
            except Exception as e:
                # Catch-all for unexpected errors
                logger.error(f"Attempt {attempt} encountered an unexpected error: {e}")

            attempt += 1
        raise AIProcessingError(
            f"WorkerAgent failed after {self.max_retries} attempts. Last error: {last_error}"
        )

    def _validate_draft(self, metadata: ArticleMetadata) -> None:
        """
        Additional semantic checks that Pydantic types cannot catch alone.
        """
        if not metadata.title or metadata.title.lower() in ["unknown", "n/a", "none"]:
            raise ValueError("LLM returned an empty or invalid Title.")

        if not metadata.authors or len(metadata.authors) == 0:
            raise ValueError("LLM failed to identify any Authors.")

        if len(metadata.abstract) < 10:
            raise ValueError("Extracted abstract is suspiciously short.")

        if len(metadata.keywords) == 0:
            raise ValueError("No keywords extracted, at least one is expected.")


class SupervisorAgent(ILLMAgent):
    """Validates the draft against the original text."""

    def process(self, context: ProcessingContext) -> ProcessingContext:
        logger.info("SupervisorAgent is reviewing the draft metadata...")
        if not context.draft_metadata:
            raise ValueError("SupervisorAgent requires a draft_metadata to review.")

        draft_metadata_json = context.draft_metadata.model_dump_json(indent=2)
        response = review_article_metadata(context.raw_text, draft_metadata_json)
        supervisor_evaluation: EvaluationResponse = response.parse()
        if supervisor_evaluation.is_approved:
            context.final_metadata = context.draft_metadata
            context.superviser_review = supervisor_evaluation
            logger.info("SupervisorAgent approved the draft metadata.")
        return context
