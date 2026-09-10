"""
Custom exceptions for LLM Service.
"""


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class InputValidationError(LLMServiceError):
    """Raised when input validation fails."""
    pass


class OutputValidationError(LLMServiceError):
    """Raised when output validation fails."""
    pass


class APIError(LLMServiceError):
    """Raised when API call fails."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(APIError):
    """Raised when authentication fails."""
    pass


class ChunkingError(LLMServiceError):
    """Raised when transcript chunking fails."""
    pass


class RetryLimitExceededError(LLMServiceError):
    """Raised when retry limit is exceeded."""
    pass
