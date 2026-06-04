class AIProcessingError(Exception):
    """Base exception for AI-related failures."""

    pass


class TokenBudgetExceededError(AIProcessingError):
    """Raised when the LLM consumes more tokens than allowed by the configuration."""

    pass
