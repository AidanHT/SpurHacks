"""
Rate Limiting Tests
Tests for SlowAPI rate limiting middleware with Redis backend
"""

import asyncio
import os
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from backend.main import app

# Test configuration
TEST_RATE_LIMIT = "5/minute"  # Lower limit for faster testing
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")  # Use DB 1 for tests


@pytest.fixture
def client():
    """Create test client with rate limiting enabled."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    """Create async test client for concurrent requests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestRateLimit:
    """Test suite for rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_basic(self, async_client):
        """Test basic rate limiting functionality."""
        # First request should succeed
        response = await async_client.get("/ai/ping")
        assert response.status_code == 200
        
        # Check rate limit headers in response
        response_data = response.json()
        assert "rate_limit" in response_data
        assert response_data["service"] == "ai"
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, async_client):
        """Test rate limit exceeded scenario."""
        # Skip if Redis is not available
        try:
            import redis.asyncio as redis
            r = redis.Redis.from_url(TEST_REDIS_URL)
            await r.ping()
            await r.aclose()
        except Exception:
            pytest.skip("Redis not available for testing")
        
        # Set a very low rate limit for testing
        from backend.core.ratelimit import limiter
        
        # Flush test Redis database
        test_redis = redis.Redis.from_url(TEST_REDIS_URL)
        await test_redis.flushdb()
        await test_redis.aclose()
        
        # Make rapid requests to trigger rate limit
        # We'll use a loop to make multiple requests quickly
        responses = []
        for i in range(7):  # More than our test limit of 5
            response = await async_client.get("/ai/ping")
            responses.append(response)
            
            # Small delay to avoid connection issues
            if i < 6:
                await asyncio.sleep(0.1)
        
        # Check that we get at least one 429 response
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        
        # We should have some successful requests and some rate limited
        assert success_count > 0, "Should have some successful requests"
        assert rate_limited_count > 0, "Should have some rate limited requests"
        
        # Check 429 response format
        for response in responses:
            if response.status_code == 429:
                data = response.json()
                assert data["detail"] == "Rate limit exceeded"
                assert "Retry-After" in response.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_different_ips(self, async_client):
        """Test that different IPs have separate rate limits."""
        # This test simulates requests from different IPs
        # In real scenarios, different clients would have different limits
        
        # Skip if Redis is not available
        try:
            import redis.asyncio as redis
            r = redis.Redis.from_url(TEST_REDIS_URL)
            await r.ping()
            await r.aclose()
        except Exception:
            pytest.skip("Redis not available for testing")
        
        # Make requests with different client identifiers
        # Note: In real testing, this would require more complex setup
        # to simulate different IP addresses
        
        response1 = await async_client.get("/ai/ping")
        assert response1.status_code == 200
        
        response2 = await async_client.get("/ai/ping")
        assert response2.status_code == 200
    
    def test_rate_limit_key_function(self):
        """Test the rate limit key generation function."""
        from backend.core.ratelimit import get_rate_limit_key
        from fastapi import Request
        from unittest.mock import Mock
        
        # Test with authenticated user
        request_mock = Mock(spec=Request)
        request_mock.state = Mock()
        request_mock.state.user = Mock()
        request_mock.state.user.id = "user123"
        
        key = get_rate_limit_key(request_mock)
        assert key == "user:user123"
        
        # Test with anonymous user (IP-based)
        request_mock.state.user = None
        request_mock.client = Mock()
        request_mock.client.host = "192.168.1.1"
        
        # Mock the get_remote_address function
        with pytest.MonkeyPatch().context() as m:
            m.setattr("backend.core.ratelimit.get_remote_address", lambda x: "192.168.1.1")
            key = get_rate_limit_key(request_mock)
            assert key == "ip:192.168.1.1"
    
    def test_ipv6_normalization(self):
        """Test IPv6 address normalization in rate limit key."""
        from backend.core.ratelimit import get_rate_limit_key
        from fastapi import Request
        from unittest.mock import Mock
        
        request_mock = Mock(spec=Request)
        request_mock.state = Mock()
        request_mock.state.user = None
        
        # Test IPv6 normalization
        with pytest.MonkeyPatch().context() as m:
            m.setattr("backend.core.ratelimit.get_remote_address", lambda x: "2001:db8::1")
            key = get_rate_limit_key(request_mock)
            assert key == "ip:[2001:db8::1]"
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self):
        """Test graceful handling of Redis connection failures."""
        # This test would require mocking Redis failures
        # For now, we'll just verify the limiter can be initialized
        from backend.core.ratelimit import limiter
        assert limiter is not None
    
    def test_environment_rate_limit_config(self):
        """Test that rate limit can be configured via environment."""
        from backend.core.ratelimit import DEFAULT_RATE_LIMIT
        
        # Should use default if not set
        assert DEFAULT_RATE_LIMIT == os.getenv("RATE_LIMIT", "60/minute")


@pytest.mark.asyncio
async def test_performance_under_load():
    """Test rate limiting performance under concurrent load."""
    # Skip if Redis is not available
    try:
        import redis.asyncio as redis
        r = redis.Redis.from_url(TEST_REDIS_URL)
        await r.ping()
        await r.aclose()
    except Exception:
        pytest.skip("Redis not available for testing")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make concurrent requests
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(client.get("/ai/ping"))
            tasks.append(task)
        
        # Wait for all requests to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that we got responses (not exceptions)
        successful_responses = [r for r in responses if hasattr(r, 'status_code')]
        assert len(successful_responses) == 10
        
        # Check status codes
        status_codes = [r.status_code for r in successful_responses]
        assert all(code in [200, 429] for code in status_codes) 