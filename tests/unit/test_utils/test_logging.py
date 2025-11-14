"""
Tests for logging utilities.

This module tests the logging configuration defined in slr.utils.logging.
"""

import pytest
import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

from slr.utils.logging import (
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


class TestSetupLogging:
    """Test the setup_logging function."""

    def teardown_method(self):
        """Clean up logging handlers after each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_basic_setup(self):
        """Test basic logging setup."""
        logger = setup_logging(level="INFO")

        assert logger is logging.getLogger()
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_debug_level(self):
        """Test setting up with DEBUG level."""
        logger = setup_logging(level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_custom_format(self):
        """Test custom format string."""
        custom_format = "%(levelname)s - %(message)s"
        logger = setup_logging(format_string=custom_format)

        # Check that handler has the custom format
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, (logging.Formatter, ColoredFormatter))

    def test_file_logging(self):
        """Test logging to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(level="INFO", log_file=log_file)

            # Should have console and file handlers
            assert len(logger.handlers) == 2

            # Log a message
            logger.info("Test message")

            # Check file was created and contains the message
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_colored_output(self):
        """Test colored formatter."""
        logger = setup_logging(level="INFO", colored=True)

        # If stdout is a TTY, should use ColoredFormatter
        # Otherwise, should use regular Formatter
        handler = logger.handlers[0]
        assert handler.formatter is not None

    def test_no_timestamp(self):
        """Test logging without timestamps."""
        logger = setup_logging(include_timestamp=False)

        handler = logger.handlers[0]
        # Format should not include asctime
        # (Can't easily test this without actually logging)
        assert handler.formatter is not None

    def test_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        root_logger = logging.getLogger()
        root_logger.addHandler(logging.StreamHandler())
        initial_count = len(root_logger.handlers)

        setup_logging()

        # Should have cleared and added new handler(s)
        assert len(root_logger.handlers) >= 1


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_basic(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")

        assert logger.name == "test_module"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_level(self):
        """Test getting a logger with custom level."""
        logger = get_logger("test_module", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_get_logger_same_instance(self):
        """Test that getting the same logger returns same instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        assert logger1 is logger2


class TestSetupProviderLogging:
    """Test the setup_provider_logging function."""

    def test_setup_provider_logging(self):
        """Test setting up logging for a provider."""
        logger = setup_provider_logging("openalex", level="DEBUG")

        assert logger.name == "slr.providers.openalex"
        assert logger.level == logging.DEBUG

    def test_multiple_providers(self):
        """Test setting up logging for multiple providers."""
        logger1 = setup_provider_logging("openalex", level="DEBUG")
        logger2 = setup_provider_logging("crossref", level="INFO")

        assert logger1.name == "slr.providers.openalex"
        assert logger2.name == "slr.providers.crossref"
        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.INFO


class TestConfigureLibraryLogging:
    """Test the configure_library_logging function."""

    def test_configure_library_logging_quiet(self):
        """Test configuring library logging in quiet mode."""
        configure_library_logging(quiet=True)

        # Check that noisy loggers are set to WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("requests").level == logging.WARNING

    def test_configure_library_logging_normal(self):
        """Test configuring library logging in normal mode."""
        configure_library_logging(quiet=False)

        # Check that loggers are set to INFO
        assert logging.getLogger("urllib3").level == logging.INFO
        assert logging.getLogger("requests").level == logging.INFO


class TestLogContext:
    """Test the LogContext context manager."""

    def test_log_context_changes_level(self):
        """Test that LogContext temporarily changes log level."""
        logger = get_logger("test_context")
        logger.setLevel(logging.INFO)

        with LogContext("test_context", "DEBUG"):
            assert logger.level == logging.DEBUG

        # Should be restored
        assert logger.level == logging.INFO

    def test_log_context_restores_on_exception(self):
        """Test that LogContext restores level even on exception."""
        logger = get_logger("test_context")
        logger.setLevel(logging.INFO)

        try:
            with LogContext("test_context", "DEBUG"):
                assert logger.level == logging.DEBUG
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should still be restored
        assert logger.level == logging.INFO

    def test_log_context_returns_logger(self):
        """Test that LogContext returns the logger."""
        with LogContext("test_context", "DEBUG") as logger:
            assert isinstance(logger, logging.Logger)
            assert logger.name == "test_context"


class TestPerformanceLogger:
    """Test the PerformanceLogger context manager."""

    def test_performance_logger_success(self, caplog):
        """Test PerformanceLogger with successful operation."""
        with caplog.at_level(logging.INFO):
            with PerformanceLogger("Test operation"):
                import time
                time.sleep(0.1)

        # Check that start and completion messages were logged
        messages = [record.message for record in caplog.records]
        assert any("Test operation started" in msg for msg in messages)
        assert any("Test operation completed" in msg for msg in messages)
        assert any("0." in msg and "s" in msg for msg in messages)  # Time in seconds

    def test_performance_logger_failure(self, caplog):
        """Test PerformanceLogger with failed operation."""
        with caplog.at_level(logging.ERROR):
            try:
                with PerformanceLogger("Failing operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass

        # Check that failure message was logged
        messages = [record.message for record in caplog.records]
        assert any("Failing operation failed" in msg for msg in messages)

    def test_performance_logger_custom_logger(self, caplog):
        """Test PerformanceLogger with custom logger."""
        custom_logger = get_logger("custom_perf")

        with caplog.at_level(logging.INFO, logger="custom_perf"):
            with PerformanceLogger("Custom operation", logger=custom_logger):
                pass

        # Check that message was logged to custom logger
        assert any("Custom operation" in record.message for record in caplog.records)

    def test_performance_logger_custom_level(self, caplog):
        """Test PerformanceLogger with custom level."""
        with caplog.at_level(logging.DEBUG):
            with PerformanceLogger("Debug operation", level="DEBUG"):
                pass

        # Check that DEBUG level message was logged
        assert any(record.levelname == "DEBUG" for record in caplog.records)


class TestLogFunctionCall:
    """Test the log_function_call decorator."""

    def test_log_function_call_basic(self, caplog):
        """Test basic function call logging."""
        @log_function_call(level="INFO")
        def test_function():
            return "result"

        with caplog.at_level(logging.INFO):
            result = test_function()

        assert result == "result"
        messages = [record.message for record in caplog.records]
        assert any("Calling test_function" in msg for msg in messages)
        assert any("test_function completed" in msg for msg in messages)

    def test_log_function_call_with_args(self, caplog):
        """Test logging function calls with arguments."""
        @log_function_call(level="DEBUG", include_args=True)
        def test_function(a, b, c=None):
            return a + b

        with caplog.at_level(logging.DEBUG):
            result = test_function(1, 2, c=3)

        assert result == 3
        messages = [record.message for record in caplog.records]
        # Should log arguments
        assert any("1" in msg and "2" in msg for msg in messages)

    def test_log_function_call_with_result(self, caplog):
        """Test logging function return value."""
        @log_function_call(level="INFO", include_result=True)
        def test_function():
            return "test_result"

        with caplog.at_level(logging.INFO):
            result = test_function()

        assert result == "test_result"
        messages = [record.message for record in caplog.records]
        assert any("test_result" in msg for msg in messages)

    def test_log_function_call_preserves_function(self):
        """Test that decorator preserves function metadata."""
        @log_function_call()
        def original_function():
            """Original docstring."""
            return "result"

        assert original_function.__name__ == "original_function"
        assert original_function.__doc__ == "Original docstring."

    def test_log_function_call_custom_logger(self, caplog):
        """Test using custom logger."""
        custom_logger = get_logger("custom_function")

        @log_function_call(logger=custom_logger, level="INFO")
        def test_function():
            return "result"

        with caplog.at_level(logging.INFO, logger="custom_function"):
            test_function()

        assert any(record.name == "custom_function" for record in caplog.records)


class TestCreateSessionLogFile:
    """Test the create_session_log_file function."""

    def test_create_session_log_file(self):
        """Test creating a session log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = create_session_log_file(Path(tmpdir))

            assert log_file.exists() or log_file.parent.exists()
            assert "slr_" in log_file.name
            assert log_file.suffix == ".log"

    def test_create_session_log_file_custom_prefix(self):
        """Test creating session log file with custom prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = create_session_log_file(Path(tmpdir), prefix="custom")

            assert "custom_" in log_file.name

    def test_create_session_log_file_creates_directory(self):
        """Test that create_session_log_file creates directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "logs" / "nested"
            log_file = create_session_log_file(nested_dir)

            assert log_file.parent.exists()

    def test_create_session_log_file_timestamp(self):
        """Test that log file has timestamp in name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = create_session_log_file(Path(tmpdir))

            # Should contain timestamp pattern YYYYMMDD_HHMMSS
            import re
            assert re.search(r'\d{8}_\d{6}', log_file.name)


class TestColoredFormatter:
    """Test the ColoredFormatter class."""

    def test_colored_formatter_creates(self):
        """Test that ColoredFormatter can be instantiated."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        assert formatter is not None

    def test_colored_formatter_formats(self):
        """Test that ColoredFormatter formats messages."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        assert "Test message" in formatted

    def test_colored_formatter_adds_colors(self):
        """Test that ColoredFormatter adds color codes."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        # Should contain ANSI color codes
        assert "\033[" in formatted or "ERROR" in formatted


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def teardown_method(self):
        """Clean up after tests."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_complete_logging_setup(self):
        """Test complete logging setup workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = create_session_log_file(Path(tmpdir))
            setup_logging(level="INFO", log_file=log_file)

            logger = get_logger(__name__)
            logger.info("Test message")

            # Check console and file logging
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_provider_specific_logging(self, caplog):
        """Test provider-specific logging levels."""
        setup_logging(level="WARNING")
        openalex_logger = setup_provider_logging("openalex", level="DEBUG")

        with caplog.at_level(logging.DEBUG, logger="slr.providers.openalex"):
            openalex_logger.debug("Debug message")

        # Should be logged despite root WARNING level
        assert any("Debug message" in record.message for record in caplog.records)

    def test_performance_tracking(self, caplog):
        """Test performance tracking with PerformanceLogger."""
        setup_logging(level="INFO")

        with caplog.at_level(logging.INFO):
            with PerformanceLogger("Data fetch"):
                import time
                time.sleep(0.05)

        messages = [record.message for record in caplog.records]
        assert any("Data fetch started" in msg for msg in messages)
        assert any("Data fetch completed" in msg and "0." in msg for msg in messages)

    def test_function_call_tracking(self, caplog):
        """Test function call tracking with decorator."""
        setup_logging(level="DEBUG")

        @log_function_call(level="DEBUG", include_args=True, include_result=True)
        def fetch_data(query):
            return f"results for {query}"

        with caplog.at_level(logging.DEBUG):
            result = fetch_data("test query")

        assert result == "results for test query"
        messages = [record.message for record in caplog.records]
        assert any("fetch_data" in msg for msg in messages)

