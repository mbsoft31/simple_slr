"""
Tests for rate limiting utilities.

This module tests the rate limiting mechanisms defined in slr.utils.rate_limit.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from slr.utils.rate_limit import (
    TokenBucket,
    SlidingWindowRateLimiter,
    RateLimitDecorator,
)
from slr.utils.exceptions import RateLimitError


class TestTokenBucket:
    """Test the TokenBucket rate limiter."""

    def test_initialization(self):
        """Test token bucket initialization."""
        bucket = TokenBucket(rate=10.0, capacity=20)
        assert bucket.rate == 10.0
        assert bucket.capacity == 20
        assert bucket.tokens == 20.0

    def test_invalid_rate(self):
        """Test that invalid rate raises ValueError."""
        with pytest.raises(ValueError, match="Rate must be positive"):
            TokenBucket(rate=0, capacity=10)

        with pytest.raises(ValueError, match="Rate must be positive"):
            TokenBucket(rate=-5, capacity=10)

    def test_invalid_capacity(self):
        """Test that invalid capacity raises ValueError."""
        with pytest.raises(ValueError, match="Capacity must be positive"):
            TokenBucket(rate=10.0, capacity=0)

        with pytest.raises(ValueError, match="Capacity must be positive"):
            TokenBucket(rate=10.0, capacity=-5)

    def test_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(rate=10.0, capacity=20)
        assert bucket.consume(5)
        assert bucket.tokens == 15.0

    def test_consume_failure(self):
        """Test token consumption failure when insufficient tokens."""
        bucket = TokenBucket(rate=10.0, capacity=10)
        bucket.tokens = 3.0
        assert not bucket.consume(5)
        assert bucket.tokens == 3.0  # Tokens unchanged

    def test_consume_exact_amount(self):
        """Test consuming exact available tokens."""
        bucket = TokenBucket(rate=10.0, capacity=10)
        bucket.tokens = 5.0
        assert bucket.consume(5)
        assert bucket.tokens == 0.0

    def test_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(rate=10.0, capacity=20)
        bucket.tokens = 5.0

        # Sleep for 0.5 seconds -> should add 5 tokens (10 * 0.5)
        time.sleep(0.5)

        # Trigger refill by checking available tokens
        available = bucket.available_tokens()
        assert available >= 9.5  # Allow small tolerance
        assert available <= 10.5

    def test_refill_does_not_exceed_capacity(self):
        """Test that refill respects capacity limit."""
        bucket = TokenBucket(rate=100.0, capacity=10)
        bucket.tokens = 5.0

        # Sleep long enough to theoretically add more than capacity
        time.sleep(1.0)

        available = bucket.available_tokens()
        assert available <= 10.0  # Should be capped at capacity

    def test_wait_for_token_success(self):
        """Test waiting for tokens successfully."""
        bucket = TokenBucket(rate=10.0, capacity=10)
        bucket.tokens = 0.0

        # Should wait briefly and succeed
        start = time.time()
        result = bucket.wait_for_token(1, timeout=2.0)
        elapsed = time.time() - start

        assert result
        assert elapsed >= 0.08  # Should take at least 0.1s to refill 1 token
        assert elapsed < 0.5  # But not too long

    def test_wait_for_token_timeout(self):
        """Test waiting for tokens with timeout."""
        bucket = TokenBucket(rate=1.0, capacity=10)
        bucket.tokens = 0.0

        # Request more tokens than can be refilled in timeout period
        start = time.time()
        result = bucket.wait_for_token(10, timeout=0.5)
        elapsed = time.time() - start

        assert not result
        assert elapsed >= 0.4  # Should wait approximately the timeout
        assert elapsed < 0.7

    def test_reset(self):
        """Test resetting the bucket."""
        bucket = TokenBucket(rate=10.0, capacity=20)
        bucket.tokens = 5.0

        bucket.reset()

        assert bucket.tokens == 20.0

    def test_available_tokens(self):
        """Test getting available tokens."""
        bucket = TokenBucket(rate=10.0, capacity=20)
        bucket.tokens = 15.0

        available = bucket.available_tokens()
        assert available == 15.0

    def test_time_until_tokens(self):
        """Test calculating time until tokens available."""
        bucket = TokenBucket(rate=10.0, capacity=10)
        bucket.tokens = 3.0

        # Need 2 more tokens
        time_needed = bucket.time_until_tokens(5)
        assert time_needed >= 0.19  # 2 tokens / 10 per second = 0.2s
        assert time_needed <= 0.21

    def test_time_until_tokens_available_now(self):
        """Test time_until_tokens when tokens already available."""
        bucket = TokenBucket(rate=10.0, capacity=10)
        bucket.tokens = 10.0

        time_needed = bucket.time_until_tokens(5)
        assert time_needed == 0.0

    def test_thread_safety(self):
        """Test that TokenBucket is thread-safe."""
        bucket = TokenBucket(rate=100.0, capacity=100)
        consumed_count = [0]

        def consumer():
            for _ in range(10):
                if bucket.consume(1):
                    consumed_count[0] += 1
                time.sleep(0.01)

        threads = [threading.Thread(target=consumer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All consumptions should succeed (50 total, well under capacity)
        assert consumed_count[0] == 50


class TestSlidingWindowRateLimiter:
    """Test the SlidingWindowRateLimiter."""

    def test_initialization(self):
        """Test sliding window initialization."""
        limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60
        assert len(limiter.requests) == 0

    def test_invalid_max_requests(self):
        """Test that invalid max_requests raises ValueError."""
        with pytest.raises(ValueError, match="max_requests must be positive"):
            SlidingWindowRateLimiter(max_requests=0, window_seconds=60)

        with pytest.raises(ValueError, match="max_requests must be positive"):
            SlidingWindowRateLimiter(max_requests=-10, window_seconds=60)

    def test_invalid_window_seconds(self):
        """Test that invalid window_seconds raises ValueError."""
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            SlidingWindowRateLimiter(max_requests=100, window_seconds=0)

        with pytest.raises(ValueError, match="window_seconds must be positive"):
            SlidingWindowRateLimiter(max_requests=100, window_seconds=-30)

    def test_allow_request_within_limit(self):
        """Test allowing requests within the limit."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0)

        # All 5 requests should be allowed
        for i in range(5):
            assert limiter.allow_request()

        assert limiter.current_usage() == 5

    def test_deny_request_over_limit(self):
        """Test denying requests over the limit."""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=1.0)

        # First 3 should be allowed
        assert limiter.allow_request()
        assert limiter.allow_request()
        assert limiter.allow_request()

        # 4th should be denied
        assert not limiter.allow_request()

    def test_window_slides(self):
        """Test that the window slides and old requests expire."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=0.5)

        # Use both slots
        assert limiter.allow_request()
        assert limiter.allow_request()
        assert not limiter.allow_request()

        # Wait for window to slide
        time.sleep(0.6)

        # Should be allowed again
        assert limiter.allow_request()

    def test_wait_for_slot_success(self):
        """Test waiting for a slot successfully."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=0.5)

        # Fill the slots
        assert limiter.allow_request()
        assert limiter.allow_request()

        # Wait for a slot (should succeed after window expires)
        start = time.time()
        result = limiter.wait_for_slot(timeout=1.0)
        elapsed = time.time() - start

        assert result
        assert elapsed >= 0.4  # Should wait approximately the window duration
        assert elapsed < 0.8

    def test_wait_for_slot_timeout(self):
        """Test waiting for a slot with timeout."""
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=2.0)

        # Fill the slot
        assert limiter.allow_request()

        # Try to wait with short timeout
        start = time.time()
        result = limiter.wait_for_slot(timeout=0.5)
        elapsed = time.time() - start

        assert not result
        assert elapsed >= 0.4
        assert elapsed < 0.8

    def test_reset(self):
        """Test resetting the limiter."""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=1.0)

        limiter.allow_request()
        limiter.allow_request()
        assert limiter.current_usage() == 2

        limiter.reset()

        assert limiter.current_usage() == 0

    def test_current_usage(self):
        """Test getting current usage."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0)

        assert limiter.current_usage() == 0

        limiter.allow_request()
        limiter.allow_request()

        assert limiter.current_usage() == 2

    def test_time_until_slot(self):
        """Test calculating time until slot available."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=1.0)

        # No requests yet
        assert limiter.time_until_slot() == 0.0

        # Fill slots
        limiter.allow_request()
        time.sleep(0.1)
        limiter.allow_request()

        # Should need to wait approximately 0.9s (1.0 - 0.1)
        time_needed = limiter.time_until_slot()
        assert time_needed >= 0.85
        assert time_needed <= 0.95

    def test_thread_safety(self):
        """Test that SlidingWindowRateLimiter is thread-safe."""
        limiter = SlidingWindowRateLimiter(max_requests=50, window_seconds=1.0)
        allowed_count = [0]
        denied_count = [0]

        def requester():
            for _ in range(10):
                if limiter.allow_request():
                    allowed_count[0] += 1
                else:
                    denied_count[0] += 1
                time.sleep(0.01)

        threads = [threading.Thread(target=requester) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have allowed exactly max_requests
        assert allowed_count[0] <= 50
        assert allowed_count[0] + denied_count[0] == 50


class TestRateLimitDecorator:
    """Test the RateLimitDecorator."""

    def test_decorator_with_token_bucket_wait(self):
        """Test decorator with TokenBucket in wait mode."""
        bucket = TokenBucket(rate=10.0, capacity=5)

        @RateLimitDecorator(bucket, wait=True)
        def limited_function():
            return "success"

        # Should succeed
        result = limited_function()
        assert result == "success"

    def test_decorator_with_token_bucket_no_wait(self):
        """Test decorator with TokenBucket in no-wait mode."""
        bucket = TokenBucket(rate=10.0, capacity=2)

        @RateLimitDecorator(bucket, wait=False)
        def limited_function():
            return "success"

        # First 2 should succeed
        assert limited_function() == "success"
        assert limited_function() == "success"

        # 3rd should fail
        with pytest.raises(RateLimitError):
            limited_function()

    def test_decorator_with_sliding_window_wait(self):
        """Test decorator with SlidingWindowRateLimiter in wait mode."""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=0.5)

        @RateLimitDecorator(limiter, wait=True, timeout=1.0)
        def limited_function():
            return "success"

        # Should succeed
        result = limited_function()
        assert result == "success"

    def test_decorator_with_sliding_window_no_wait(self):
        """Test decorator with SlidingWindowRateLimiter in no-wait mode."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=1.0)

        @RateLimitDecorator(limiter, wait=False)
        def limited_function():
            return "success"

        # First 2 should succeed
        assert limited_function() == "success"
        assert limited_function() == "success"

        # 3rd should fail
        with pytest.raises(RateLimitError):
            limited_function()

    def test_decorator_with_callback(self):
        """Test decorator with on_limit callback."""
        bucket = TokenBucket(rate=10.0, capacity=1)
        callback_called = [False]

        def on_limit_callback():
            callback_called[0] = True

        @RateLimitDecorator(bucket, wait=False, on_limit=on_limit_callback)
        def limited_function():
            return "success"

        # First call succeeds
        limited_function()

        # Second call should trigger callback
        with pytest.raises(RateLimitError):
            limited_function()

        assert callback_called[0]

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name and docstring."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        @RateLimitDecorator(bucket)
        def my_function():
            """My docstring."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    def test_decorator_with_invalid_limiter(self):
        """Test decorator with invalid limiter type."""
        @RateLimitDecorator("not a limiter", wait=False)
        def limited_function():
            return "success"

        with pytest.raises(TypeError, match="Unsupported limiter type"):
            limited_function()

    def test_decorator_timeout(self):
        """Test decorator with timeout."""
        bucket = TokenBucket(rate=1.0, capacity=1)
        bucket.tokens = 0.0  # Empty bucket

        @RateLimitDecorator(bucket, wait=True, timeout=0.2)
        def limited_function():
            return "success"

        # Should timeout and raise
        with pytest.raises(RateLimitError):
            limited_function()


class TestRateLimitingIntegration:
    """Integration tests for rate limiting."""

    def test_realistic_api_throttling(self):
        """Test realistic API throttling scenario."""
        # Simulate API with 5 requests per second limit
        limiter = TokenBucket(rate=5.0, capacity=10)
        call_count = 0

        @RateLimitDecorator(limiter, wait=True)
        def api_call():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        # Make 10 calls (should throttle but all succeed)
        start = time.time()
        results = []
        for _ in range(10):
            results.append(api_call())
        elapsed = time.time() - start

        assert len(results) == 10
        assert call_count == 10
        # Should take at least some time due to throttling
        # (10 tokens at 5/sec starting with 10 in bucket = should be quick)
        assert elapsed < 2.0  # But not too long

    def test_burst_handling(self):
        """Test handling of burst requests."""
        # Allow bursts of 10, but sustained rate of 5/sec
        limiter = TokenBucket(rate=5.0, capacity=10)

        @RateLimitDecorator(limiter, wait=False)
        def api_call():
            return "success"

        # Burst of 10 should succeed (uses capacity)
        for _ in range(10):
            assert api_call() == "success"

        # 11th should fail (exceeded capacity)
        with pytest.raises(RateLimitError):
            api_call()

    def test_concurrent_rate_limiting(self):
        """Test rate limiting with concurrent requests."""
        limiter = TokenBucket(rate=20.0, capacity=20)
        results = []
        lock = threading.Lock()

        @RateLimitDecorator(limiter, wait=True, timeout=2.0)
        def concurrent_api_call(thread_id):
            with lock:
                results.append(thread_id)
            return thread_id

        def worker(tid):
            try:
                concurrent_api_call(tid)
            except RateLimitError:
                pass

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Most should succeed
        assert len(results) >= 10

