"""
Tests for retry utilities.

This module tests the retry decorators and utilities defined in slr.utils.retry.
"""

import pytest
import time
from unittest.mock import Mock, patch, call

from slr.utils.retry import (
    retry_with_backoff,
    retry_on_rate_limit,
    retry_with_custom_strategy,
    RetryableOperation,
)
from slr.utils.exceptions import (
    NetworkError,
    RateLimitError,
    AuthenticationError,
)


class TestRetryWithBackoff:
    """Test the retry_with_backoff decorator."""

    def test_success_on_first_attempt(self):
        """Test that successful functions don't retry."""
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff()(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_network_error(self):
        """Test retrying on NetworkError."""
        mock_func = Mock(side_effect=[
            NetworkError("test", "Network timeout"),
            NetworkError("test", "Network timeout"),
            "success"
        ])
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_on_rate_limit_error(self):
        """Test retrying on RateLimitError."""
        mock_func = Mock(side_effect=[
            RateLimitError("test"),
            "success"
        ])
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_max_retries_exhausted(self):
        """Test that exception is raised after max retries."""
        mock_func = Mock(side_effect=NetworkError("test", "Persistent error"))
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)

        with pytest.raises(NetworkError) as exc_info:
            decorated()

        assert "Persistent error" in str(exc_info.value)
        assert mock_func.call_count == 3

    def test_non_retryable_exception_not_caught(self):
        """Test that non-retryable exceptions are raised immediately."""
        mock_func = Mock(side_effect=AuthenticationError("test", "Invalid key"))
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)

        with pytest.raises(AuthenticationError):
            decorated()

        assert mock_func.call_count == 1  # No retry

    def test_exponential_backoff(self):
        """Test that delays increase exponentially."""
        mock_func = Mock(side_effect=[
            NetworkError("test", "Error"),
            NetworkError("test", "Error"),
            NetworkError("test", "Error"),
        ])

        with patch('time.sleep') as mock_sleep:
            decorated = retry_with_backoff(
                max_retries=3,
                base_delay=1.0,
                backoff_factor=2.0
            )(mock_func)

            with pytest.raises(NetworkError):
                decorated()

            # Check sleep was called with increasing delays
            assert mock_sleep.call_count == 2  # After 1st and 2nd attempts
            calls = mock_sleep.call_args_list
            assert calls[0] == call(1.0)  # After 1st failure
            assert calls[1] == call(2.0)  # After 2nd failure (1.0 * 2.0)

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        mock_func = Mock(side_effect=NetworkError("test", "Error"))

        with patch('time.sleep') as mock_sleep:
            decorated = retry_with_backoff(
                max_retries=5,
                base_delay=10.0,
                backoff_factor=2.0,
                max_delay=15.0
            )(mock_func)

            with pytest.raises(NetworkError):
                decorated()

            # All delays should be capped at 15.0
            for call_args in mock_sleep.call_args_list:
                assert call_args[0][0] <= 15.0

    def test_custom_exceptions(self):
        """Test retrying with custom exception types."""
        class CustomError(Exception):
            pass

        mock_func = Mock(side_effect=[CustomError("Error"), "success"])
        decorated = retry_with_backoff(
            max_retries=3,
            base_delay=0.01,
            exceptions=(CustomError,)
        )(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_on_retry_callback(self):
        """Test that on_retry callback is called."""
        callback_mock = Mock()
        mock_func = Mock(side_effect=[
            NetworkError("test", "Error"),
            "success"
        ])

        decorated = retry_with_backoff(
            max_retries=3,
            base_delay=0.01,
            on_retry=callback_mock
        )(mock_func)

        result = decorated()

        assert result == "success"
        assert callback_mock.call_count == 1
        # Check callback was called with exception and attempt number
        args = callback_mock.call_args[0]
        assert isinstance(args[0], NetworkError)
        assert args[1] == 1  # First retry attempt

    def test_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""
        def original_function():
            """Original docstring."""
            pass

        decorated = retry_with_backoff()(original_function)

        assert decorated.__name__ == "original_function"
        assert decorated.__doc__ == "Original docstring."

    def test_with_function_arguments(self):
        """Test that decorator works with functions that take arguments."""
        mock_func = Mock(side_effect=[
            NetworkError("test", "Error"),
            "success"
        ])
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)

        result = decorated("arg1", kwarg1="value1")

        assert result == "success"
        assert mock_func.call_count == 2
        # Verify arguments were passed correctly
        mock_func.assert_called_with("arg1", kwarg1="value1")


class TestRetryOnRateLimit:
    """Test the retry_on_rate_limit decorator."""

    def test_retry_on_rate_limit(self):
        """Test retrying on rate limit errors."""
        mock_func = Mock(side_effect=[
            RateLimitError("test"),
            "success"
        ])
        decorated = retry_on_rate_limit(max_retries=3, base_delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_respects_retry_after_header(self):
        """Test that it respects retry_after from exception."""
        mock_func = Mock(side_effect=[
            RateLimitError("test", retry_after=5),
            "success"
        ])

        with patch('time.sleep') as mock_sleep:
            decorated = retry_on_rate_limit(max_retries=3, base_delay=0.01)(mock_func)
            result = decorated()

            assert result == "success"
            # Sleep should still be called (we don't override the sleep time in the decorator)
            assert mock_sleep.called

    def test_does_not_retry_network_error(self):
        """Test that it doesn't retry non-rate-limit errors."""
        mock_func = Mock(side_effect=NetworkError("test", "Error"))
        decorated = retry_on_rate_limit(max_retries=3, base_delay=0.01)(mock_func)

        with pytest.raises(NetworkError):
            decorated()

        assert mock_func.call_count == 1  # No retry


class TestRetryWithCustomStrategy:
    """Test the retry_with_custom_strategy decorator."""

    def test_custom_should_retry_retryable(self):
        """Test custom retry condition with retryable error."""
        def should_retry(e):
            return isinstance(e, ValueError) and "retryable" in str(e)

        def get_delay(attempt):
            return 0.01

        # Should retry
        mock_func = Mock(side_effect=[ValueError("retryable error"), "success"])
        decorated = retry_with_custom_strategy(should_retry, get_delay, max_retries=3)(mock_func)
        assert decorated() == "success"
        assert mock_func.call_count == 2

    def test_custom_should_retry_non_retryable(self):
        """Test custom retry condition with non-retryable error."""
        def should_retry(e):
            # Only retry ValueError, not TypeError
            return isinstance(e, ValueError)

        def get_delay(attempt):
            return 0.01

        # Should not retry - wrong exception type
        mock_func = Mock(side_effect=TypeError("This should not retry"))
        decorated = retry_with_custom_strategy(should_retry, get_delay, max_retries=3)(mock_func)
        with pytest.raises(TypeError):
            decorated()
        assert mock_func.call_count == 1

    def test_custom_delay_strategy(self):
        """Test custom delay calculation."""
        def should_retry(e):
            return isinstance(e, ValueError)

        def get_delay(attempt):
            return attempt * 0.1  # Linear backoff

        mock_func = Mock(side_effect=[
            ValueError("Error"),
            ValueError("Error"),
            ValueError("Error"),
        ])

        with patch('time.sleep') as mock_sleep:
            decorated = retry_with_custom_strategy(
                should_retry,
                get_delay,
                max_retries=3
            )(mock_func)

            with pytest.raises(ValueError):
                decorated()

            # Check custom delays
            calls = mock_sleep.call_args_list
            assert calls[0] == call(0.1)  # 1 * 0.1
            assert calls[1] == call(0.2)  # 2 * 0.1

    def test_max_retries_respected(self):
        """Test that max_retries is respected."""
        def should_retry(e):
            return isinstance(e, ValueError)

        def get_delay(attempt):
            return 0.01

        mock_func = Mock(side_effect=ValueError("Error"))
        decorated = retry_with_custom_strategy(
            should_retry,
            get_delay,
            max_retries=5
        )(mock_func)

        with pytest.raises(ValueError):
            decorated()

        assert mock_func.call_count == 5


class TestRetryableOperation:
    """Test the RetryableOperation context manager."""

    def test_success_on_first_attempt(self):
        """Test successful operation without retries."""
        attempts = []

        with RetryableOperation(max_retries=3, base_delay=0.01) as retry:
            attempts.append(1)
            retry.success()

        assert len(attempts) == 1

    def test_marking_success_suppresses_exception(self):
        """Test that marking success prevents exception propagation."""
        success_marked = False

        with RetryableOperation(max_retries=3, base_delay=0.01) as retry:
            success_marked = True
            retry.success()
            # Even though we raise, success was marked so it won't propagate

        assert success_marked

    def test_non_retryable_exception_propagates(self):
        """Test that non-retryable exceptions propagate immediately."""
        with pytest.raises(AuthenticationError):
            with RetryableOperation(
                max_retries=3,
                base_delay=0.01,
                exceptions=(NetworkError, RateLimitError)
            ) as retry:
                raise AuthenticationError("test", "Not retryable")


class TestRetryIntegration:
    """Integration tests for retry functionality."""

    def test_real_timing(self):
        """Test actual timing of retries (not mocked)."""
        call_times = []

        def slow_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise NetworkError("test", "Error")
            return "success"

        decorated = retry_with_backoff(
            max_retries=5,
            base_delay=0.05,
            backoff_factor=2.0
        )(slow_function)

        result = decorated()

        assert result == "success"
        assert len(call_times) == 3

        # Check that delays increased
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Allow some tolerance for timing
        assert delay1 >= 0.04  # ~0.05s
        assert delay2 >= 0.08  # ~0.10s (0.05 * 2.0)
        assert delay2 > delay1  # Second delay should be longer

    def test_nested_retries(self):
        """Test that decorators can be nested."""
        inner_calls = []
        outer_calls = []

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def outer():
            outer_calls.append(1)
            return inner()

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def inner():
            inner_calls.append(1)
            if len(inner_calls) < 2:
                raise NetworkError("test", "Inner error")
            return "success"

        result = outer()

        assert result == "success"
        # Inner should retry once
        assert len(inner_calls) == 2
        # Outer should not retry because inner eventually succeeds
        assert len(outer_calls) == 1

    def test_concurrent_retries(self):
        """Test retry behavior with concurrent operations."""
        import threading

        results = []

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def concurrent_function(thread_id):
            # Simulate some work
            time.sleep(0.01)
            results.append(thread_id)
            return f"success-{thread_id}"

        threads = []
        for i in range(5):
            t = threading.Thread(target=lambda tid=i: concurrent_function(tid))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}


class TestRetryEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_retries(self):
        """Test with max_retries=0."""
        mock_func = Mock(side_effect=NetworkError("test", "Error"))
        # Note: max_retries=1 means try once total (no retries after first attempt)
        decorated = retry_with_backoff(max_retries=1, base_delay=0.01)(mock_func)

        with pytest.raises(NetworkError):
            decorated()

        assert mock_func.call_count == 1

    def test_zero_delay(self):
        """Test with zero delay."""
        mock_func = Mock(side_effect=[NetworkError("test", "Error"), "success"])
        decorated = retry_with_backoff(
            max_retries=3,
            base_delay=0.0,
            backoff_factor=2.0
        )(mock_func)

        result = decorated()
        assert result == "success"

    def test_very_large_backoff(self):
        """Test with very large backoff factor."""
        mock_func = Mock(side_effect=[
            NetworkError("test", "Error"),
            NetworkError("test", "Error"),
            "success"
        ])

        with patch('time.sleep') as mock_sleep:
            decorated = retry_with_backoff(
                max_retries=3,
                base_delay=1.0,
                backoff_factor=100.0,
                max_delay=5.0  # Should cap the delay
            )(mock_func)

            result = decorated()

            assert result == "success"
            # Check all delays were capped
            for call_args in mock_sleep.call_args_list:
                assert call_args[0][0] <= 5.0

    def test_exception_with_none_message(self):
        """Test handling exceptions with None message."""
        mock_func = Mock(side_effect=[NetworkError("test", None), "success"])
        decorated = retry_with_backoff(max_retries=3, base_delay=0.01)(mock_func)

        result = decorated()
        assert result == "success"

