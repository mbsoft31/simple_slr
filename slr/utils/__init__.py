"""
Utility modules for Simple SLR.

This package contains utility functions and classes for:
- Exception handling
- Retry logic with backoff
- Rate limiting (coming soon)
- Logging configuration (coming soon)
- Configuration management (coming soon)
"""

from .exceptions import (
    SLRException,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    NetworkError,
    ProviderNotFoundError,
    ProviderConfigError,
    DeduplicationError,
    ValidationError,
    ConfigurationError,
    ExportError,
    QueryError,
)

from .retry import (
    retry_with_backoff,
    retry_on_rate_limit,
    retry_with_custom_strategy,
    RetryableOperation,
)

__all__ = [
    # Exceptions
    "SLRException",
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "NetworkError",
    "ProviderNotFoundError",
    "ProviderConfigError",
    "DeduplicationError",
    "ValidationError",
    "ConfigurationError",
    "ExportError",
    "QueryError",
    # Retry utilities
    "retry_with_backoff",
    "retry_on_rate_limit",
    "retry_with_custom_strategy",
    "RetryableOperation",
]

