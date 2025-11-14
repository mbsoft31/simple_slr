"""
Utility modules for Simple SLR.

This package contains utility functions and classes for:
- Exception handling
- Retry logic with backoff
- Rate limiting
- Logging configuration
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

from .rate_limit import (
    TokenBucket,
    SlidingWindowRateLimiter,
    RateLimitDecorator,
)

from .logging import (
    setup_logging,
    get_logger,
    setup_provider_logging,
    configure_library_logging,
    LogContext,
    PerformanceLogger,
    log_function_call,
    create_session_log_file,
    ColoredFormatter,
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
    # Rate limiting
    "TokenBucket",
    "SlidingWindowRateLimiter",
    "RateLimitDecorator",
    # Logging
    "setup_logging",
    "get_logger",
    "setup_provider_logging",
    "configure_library_logging",
    "LogContext",
    "PerformanceLogger",
    "log_function_call",
    "create_session_log_file",
    "ColoredFormatter",
]

