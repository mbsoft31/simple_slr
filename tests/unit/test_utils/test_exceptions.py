"""
Tests for exception hierarchy.

This module tests the custom exception classes defined in slr.utils.exceptions.
"""

import pytest
from datetime import datetime

from slr.utils.exceptions import (
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


class TestSLRException:
    """Test the base SLRException class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = SLRException("Something went wrong")
        assert str(exc) == "Something went wrong"
        assert exc.message == "Something went wrong"
        assert exc.details == {}
        assert isinstance(exc.timestamp, datetime)

    def test_exception_with_details(self):
        """Test exception with additional details."""
        details = {"key": "value", "count": 42}
        exc = SLRException("Error occurred", details=details)
        assert exc.details == details
        assert "key=value" in str(exc)
        assert "count=42" in str(exc)

    def test_exception_to_dict(self):
        """Test exception serialization to dictionary."""
        exc = SLRException("Test error", details={"foo": "bar"})
        exc_dict = exc.to_dict()

        assert exc_dict["type"] == "SLRException"
        assert exc_dict["message"] == "Test error"
        assert exc_dict["details"] == {"foo": "bar"}
        assert "timestamp" in exc_dict
        assert isinstance(exc_dict["timestamp"], str)

    def test_exception_inheritance(self):
        """Test that SLRException inherits from Exception."""
        exc = SLRException("Test")
        assert isinstance(exc, Exception)

    def test_exception_can_be_raised(self):
        """Test that exception can be raised and caught."""
        with pytest.raises(SLRException) as exc_info:
            raise SLRException("Test error")

        assert exc_info.value.message == "Test error"


class TestProviderError:
    """Test the ProviderError class."""

    def test_provider_error_basic(self):
        """Test basic provider error."""
        exc = ProviderError("openalex", "API request failed")
        assert exc.provider == "openalex"
        assert "[openalex]" in str(exc)
        assert "API request failed" in str(exc)

    def test_provider_error_with_kwargs(self):
        """Test provider error with additional keyword arguments."""
        exc = ProviderError("crossref", "Error", status_code=500, url="http://example.com")
        assert exc.provider == "crossref"
        assert exc.details["status_code"] == 500
        assert exc.details["url"] == "http://example.com"

    def test_provider_error_inheritance(self):
        """Test that ProviderError inherits from SLRException."""
        exc = ProviderError("s2", "Test")
        assert isinstance(exc, SLRException)
        assert isinstance(exc, ProviderError)


class TestRateLimitError:
    """Test the RateLimitError class."""

    def test_rate_limit_error_default(self):
        """Test rate limit error with default message."""
        exc = RateLimitError("openalex")
        assert exc.provider == "openalex"
        assert "Rate limit exceeded" in str(exc)
        assert exc.retry_after is None

    def test_rate_limit_error_with_retry_after(self):
        """Test rate limit error with retry_after value."""
        exc = RateLimitError("crossref", retry_after=60)
        assert exc.retry_after == 60
        assert exc.details["retry_after"] == 60

    def test_rate_limit_error_custom_message(self):
        """Test rate limit error with custom message."""
        exc = RateLimitError("arxiv", "Too many requests", retry_after=120)
        assert "Too many requests" in str(exc)
        assert exc.retry_after == 120

    def test_rate_limit_error_inheritance(self):
        """Test that RateLimitError inherits from ProviderError."""
        exc = RateLimitError("test")
        assert isinstance(exc, RateLimitError)
        assert isinstance(exc, ProviderError)
        assert isinstance(exc, SLRException)


class TestAuthenticationError:
    """Test the AuthenticationError class."""

    def test_authentication_error_default(self):
        """Test authentication error with default message."""
        exc = AuthenticationError("openalex")
        assert exc.provider == "openalex"
        assert "Authentication failed" in str(exc)

    def test_authentication_error_custom_message(self):
        """Test authentication error with custom message."""
        exc = AuthenticationError("s2", "Invalid API key")
        assert "Invalid API key" in str(exc)

    def test_authentication_error_with_details(self):
        """Test authentication error with additional details."""
        exc = AuthenticationError("crossref", api_key="abc123")
        assert exc.details["api_key"] == "abc123"

    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError inherits from ProviderError."""
        exc = AuthenticationError("test")
        assert isinstance(exc, AuthenticationError)
        assert isinstance(exc, ProviderError)


class TestNetworkError:
    """Test the NetworkError class."""

    def test_network_error_default(self):
        """Test network error with default message."""
        exc = NetworkError("openalex")
        assert exc.provider == "openalex"
        assert "Network error" in str(exc)
        assert exc.status_code is None

    def test_network_error_with_status_code(self):
        """Test network error with HTTP status code."""
        exc = NetworkError("crossref", "Connection timeout", status_code=504)
        assert exc.status_code == 504
        assert exc.details["status_code"] == 504
        assert "Connection timeout" in str(exc)

    def test_network_error_inheritance(self):
        """Test that NetworkError inherits from ProviderError."""
        exc = NetworkError("test")
        assert isinstance(exc, NetworkError)
        assert isinstance(exc, ProviderError)


class TestProviderNotFoundError:
    """Test the ProviderNotFoundError class."""

    def test_provider_not_found_default(self):
        """Test provider not found error with default message."""
        exc = ProviderNotFoundError("unknown_provider")
        assert exc.provider == "unknown_provider"
        assert "Provider not found" in str(exc)

    def test_provider_not_found_custom_message(self):
        """Test provider not found error with custom message."""
        exc = ProviderNotFoundError("test", "Provider 'test' is not registered")
        assert "not registered" in str(exc)


class TestProviderConfigError:
    """Test the ProviderConfigError class."""

    def test_provider_config_error_default(self):
        """Test provider config error with default message."""
        exc = ProviderConfigError("openalex")
        assert exc.provider == "openalex"
        assert "Invalid configuration" in str(exc)

    def test_provider_config_error_custom_message(self):
        """Test provider config error with custom message."""
        exc = ProviderConfigError("crossref", "Missing API key")
        assert "Missing API key" in str(exc)


class TestDeduplicationError:
    """Test the DeduplicationError class."""

    def test_deduplication_error_default(self):
        """Test deduplication error with default message."""
        exc = DeduplicationError()
        assert "Deduplication failed" in str(exc)

    def test_deduplication_error_custom_message(self):
        """Test deduplication error with custom message."""
        exc = DeduplicationError("Clustering algorithm failed", algorithm="dbscan")
        assert "Clustering algorithm failed" in str(exc)
        assert exc.details["algorithm"] == "dbscan"

    def test_deduplication_error_inheritance(self):
        """Test that DeduplicationError inherits from SLRException."""
        exc = DeduplicationError()
        assert isinstance(exc, DeduplicationError)
        assert isinstance(exc, SLRException)


class TestValidationError:
    """Test the ValidationError class."""

    def test_validation_error_default(self):
        """Test validation error with default message."""
        exc = ValidationError()
        assert "Validation failed" in str(exc)
        assert exc.field is None

    def test_validation_error_with_field(self):
        """Test validation error with field name."""
        exc = ValidationError("Invalid DOI format", field="doi")
        assert exc.field == "doi"
        assert exc.details["field"] == "doi"
        assert "Invalid DOI format" in str(exc)

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from SLRException."""
        exc = ValidationError()
        assert isinstance(exc, ValidationError)
        assert isinstance(exc, SLRException)


class TestConfigurationError:
    """Test the ConfigurationError class."""

    def test_configuration_error_default(self):
        """Test configuration error with default message."""
        exc = ConfigurationError()
        assert "Configuration error" in str(exc)
        assert exc.config_key is None

    def test_configuration_error_with_key(self):
        """Test configuration error with config key."""
        exc = ConfigurationError("Invalid rate limit", config_key="providers.openalex.rate_limit")
        assert exc.config_key == "providers.openalex.rate_limit"
        assert exc.details["config_key"] == "providers.openalex.rate_limit"
        assert "Invalid rate limit" in str(exc)

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from SLRException."""
        exc = ConfigurationError()
        assert isinstance(exc, ConfigurationError)
        assert isinstance(exc, SLRException)


class TestExportError:
    """Test the ExportError class."""

    def test_export_error_default(self):
        """Test export error with default message."""
        exc = ExportError()
        assert "Export failed" in str(exc)
        assert exc.format is None

    def test_export_error_with_format(self):
        """Test export error with format."""
        exc = ExportError("Failed to write CSV", format="csv")
        assert exc.format == "csv"
        assert exc.details["format"] == "csv"
        assert "Failed to write CSV" in str(exc)

    def test_export_error_inheritance(self):
        """Test that ExportError inherits from SLRException."""
        exc = ExportError()
        assert isinstance(exc, ExportError)
        assert isinstance(exc, SLRException)


class TestQueryError:
    """Test the QueryError class."""

    def test_query_error_default(self):
        """Test query error with default message."""
        exc = QueryError()
        assert "Query error" in str(exc)
        assert exc.query is None

    def test_query_error_with_query(self):
        """Test query error with query string."""
        exc = QueryError("Invalid boolean syntax", query="machine learning AND (")
        assert exc.query == "machine learning AND ("
        assert exc.details["query"] == "machine learning AND ("
        assert "Invalid boolean syntax" in str(exc)

    def test_query_error_inheritance(self):
        """Test that QueryError inherits from SLRException."""
        exc = QueryError()
        assert isinstance(exc, QueryError)
        assert isinstance(exc, SLRException)


class TestExceptionHierarchy:
    """Test the overall exception hierarchy."""

    def test_all_inherit_from_slr_exception(self):
        """Test that all custom exceptions inherit from SLRException."""
        exceptions = [
            ProviderError("test", "msg"),
            RateLimitError("test"),
            AuthenticationError("test"),
            NetworkError("test"),
            ProviderNotFoundError("test"),
            ProviderConfigError("test"),
            DeduplicationError(),
            ValidationError(),
            ConfigurationError(),
            ExportError(),
            QueryError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, SLRException)
            assert isinstance(exc, Exception)

    def test_provider_errors_hierarchy(self):
        """Test that provider-specific errors inherit from ProviderError."""
        provider_exceptions = [
            RateLimitError("test"),
            AuthenticationError("test"),
            NetworkError("test"),
            ProviderNotFoundError("test"),
            ProviderConfigError("test"),
        ]

        for exc in provider_exceptions:
            assert isinstance(exc, ProviderError)
            assert isinstance(exc, SLRException)

    def test_catching_base_exception(self):
        """Test that base exceptions can catch derived exceptions."""
        # Test catching ProviderError catches RateLimitError
        with pytest.raises(ProviderError):
            raise RateLimitError("test")

        # Test catching SLRException catches all
        with pytest.raises(SLRException):
            raise NetworkError("test")

    def test_exception_timestamps_are_different(self):
        """Test that different exception instances have different timestamps."""
        import time
        exc1 = SLRException("Error 1")
        time.sleep(0.01)  # Small delay
        exc2 = SLRException("Error 2")

        # They should have different timestamps (though might be very close)
        assert isinstance(exc1.timestamp, datetime)
        assert isinstance(exc2.timestamp, datetime)

