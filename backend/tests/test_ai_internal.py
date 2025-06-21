"""
Unit tests for Gemini 2.5 AI Service Adapter

Tests cover:
- Request body validation and context injection
- Prompt truncation logic
- Retry logic with exponential backoff
- Error handling and custom exceptions
- HTTP client lifecycle management
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from backend.services.ai_internal import (
    ask_gemini,
    GeminiServiceError,
    _truncate_prompt,
    _log_request_safely,
    _get_http_client,
    _close_http_client,
    cleanup,
)


def test_truncate_prompt_under_limit():
    """Test that short prompts are not truncated."""
    prompt = "Hello world!"
    result = _truncate_prompt(prompt, max_length=2000)
    assert result == prompt


def test_truncate_prompt_over_limit():
    """Test that long prompts are truncated with marker."""
    prompt = "x" * 2500  # 2500 characters
    result = _truncate_prompt(prompt, max_length=2000)
    
    assert len(result) == 2000
    assert result.endswith("…[truncated]")


async def test_invalid_payload_type():
    """Test that non-dict payloads raise ValueError."""
    with pytest.raises(ValueError, match="Payload must be a dictionary"):
        await ask_gemini("not a dict")


async def test_missing_prompt_field():
    """Test that payloads without 'prompt' field raise ValueError."""
    with pytest.raises(ValueError, match="Payload must contain 'prompt' field"):
        await ask_gemini({"message": "Hello"})


@patch.dict(os.environ, {}, clear=True)
async def test_missing_api_key():
    """Test that missing API key raises GeminiServiceError."""
    with pytest.raises(GeminiServiceError) as exc_info:
        await ask_gemini({"prompt": "Hello"})
    
    assert exc_info.value.status == 500
    assert "GEMINI_API_KEY environment variable not set" in exc_info.value.detail


@patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"})
async def test_successful_request(monkeypatch):
    """Test successful API request with proper payload structure."""
    # Mock response
    mock_response = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello! How can I help you?"}]
                }
            }
        ]
    }

    # Mock httpx client
    mock_client = AsyncMock()
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = mock_response
    mock_client.post.return_value = mock_post_response

    # Patch the _get_http_client function
    async def mock_get_client():
        return mock_client

    monkeypatch.setattr("backend.services.ai_internal._get_http_client", mock_get_client)

    # Make the request
    result = await ask_gemini({"prompt": "Hello"})

    # Verify result
    assert result == mock_response

    # Verify the request was made correctly
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args

    # Check URL
    expected_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    assert call_args[0][0] == expected_url

    # Check headers
    headers = call_args[1]["headers"]
    assert headers["Content-Type"] == "application/json"
    assert headers["x-goog-api-key"] == "test-api-key"

    # Check request body structure
    request_body = call_args[1]["json"]
    assert "contents" in request_body
    assert len(request_body["contents"]) == 2
    
    # Check context injection
    assert request_body["contents"][0]["parts"][0]["text"] == "You are Gemini 2.5, respond concisely."
    assert request_body["contents"][1]["parts"][0]["text"] == "Hello"


@patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"})
async def test_retry_on_server_error(monkeypatch):
    """Test that 5xx errors trigger retry with exponential backoff."""
    # Mock httpx client
    mock_client = AsyncMock()
    
    # First two calls return 500, third succeeds
    responses = [
        MagicMock(status_code=500, text="Internal Server Error"),
        MagicMock(status_code=500, text="Internal Server Error"),
        MagicMock(status_code=200, json=lambda: {"candidates": []})
    ]
    mock_client.post.side_effect = responses

    # Patch the _get_http_client function
    async def mock_get_client():
        return mock_client

    monkeypatch.setattr("backend.services.ai_internal._get_http_client", mock_get_client)

    # Mock asyncio.sleep to avoid actual delays in tests
    sleep_calls = []
    async def mock_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr("backend.services.ai_internal.asyncio.sleep", mock_sleep)

    # Make the request
    result = await ask_gemini({"prompt": "Hello"})

    # Verify it eventually succeeded
    assert result == {"candidates": []}

    # Verify three attempts were made
    assert mock_client.post.call_count == 3

    # Verify sleep was called twice (between retries)
    assert len(sleep_calls) == 2


@patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"})
async def test_no_retry_on_client_error(monkeypatch):
    """Test that 4xx errors don't trigger retry."""
    # Mock httpx client
    mock_client = AsyncMock()
    mock_post_response = MagicMock()
    mock_post_response.status_code = 400
    mock_post_response.text = "Bad Request"
    mock_client.post.return_value = mock_post_response

    # Patch the _get_http_client function
    async def mock_get_client():
        return mock_client

    monkeypatch.setattr("backend.services.ai_internal._get_http_client", mock_get_client)

    # Make the request and expect immediate failure
    with pytest.raises(GeminiServiceError) as exc_info:
        await ask_gemini({"prompt": "Hello"})

    # Verify error details
    assert exc_info.value.status == 400
    assert "Bad Request" in exc_info.value.detail

    # Verify only one attempt was made
    assert mock_client.post.call_count == 1


class TestPromptUtilities:
    """Test prompt processing utility functions."""

    def test_truncate_prompt_exact_limit(self):
        """Test that prompts exactly at the limit are not truncated."""
        prompt = "x" * 2000
        result = _truncate_prompt(prompt, max_length=2000)
        assert result == prompt

    def test_log_request_safely_under_limit(self):
        """Test that short requests are logged fully."""
        prompt = "Short request"
        result = _log_request_safely(prompt, max_log_length=100)
        assert result == prompt

    def test_log_request_safely_over_limit(self):
        """Test that long requests are truncated for logging."""
        prompt = "x" * 200  # 200 characters
        result = _log_request_safely(prompt, max_log_length=100)
        
        assert len(result) == 101  # 100 + 1 for ellipsis
        assert result.endswith("…")
        assert result.startswith("x" * 100)


class TestHttpClientManagement:
    """Test HTTP client singleton management."""

    async def test_get_http_client_singleton(self):
        """Test that the same client instance is returned."""
        # Clean up any existing client
        await _close_http_client()
        
        client1 = await _get_http_client()
        client2 = await _get_http_client()
        
        assert client1 is client2
        assert isinstance(client1, httpx.AsyncClient)
        
        # Cleanup
        await _close_http_client()

    async def test_close_http_client(self):
        """Test that HTTP client is properly closed."""
        client = await _get_http_client()
        assert client is not None
        
        await _close_http_client()
        
        # Should create a new client after closing
        client2 = await _get_http_client()
        assert client2 is not client
        
        # Cleanup
        await _close_http_client()


class TestAskGeminiRetryLogic:
    """Test retry logic and error handling."""

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"})
    async def test_retry_exhaustion(self, monkeypatch):
        """Test that repeated failures eventually raise GeminiServiceError."""
        # Mock httpx client
        mock_client = AsyncMock()
        mock_post_response = MagicMock()
        mock_post_response.status_code = 500
        mock_post_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_post_response

        # Patch the _get_http_client function
        async def mock_get_client():
            return mock_client

        monkeypatch.setattr("backend.services.ai_internal._get_http_client", mock_get_client)

        # Mock asyncio.sleep to avoid delays
        monkeypatch.setattr("backend.services.ai_internal.asyncio.sleep", AsyncMock())

        # Make the request and expect failure after retries
        with pytest.raises(GeminiServiceError) as exc_info:
            await ask_gemini({"prompt": "Hello"})

        # Verify error details
        assert exc_info.value.status == 500
        assert "Internal Server Error" in exc_info.value.detail

        # Verify three attempts were made (max retries)
        assert mock_client.post.call_count == 3

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"})
    async def test_retry_on_timeout(self, monkeypatch):
        """Test that timeouts trigger retry logic."""
        # Mock httpx client
        mock_client = AsyncMock()
        
        # First two calls timeout, third succeeds
        responses = [
            httpx.ReadTimeout("Request timed out"),
            httpx.ReadTimeout("Request timed out"),
            MagicMock(status_code=200, json=lambda: {"candidates": []})
        ]
        mock_client.post.side_effect = responses

        # Patch the _get_http_client function
        async def mock_get_client():
            return mock_client

        monkeypatch.setattr("backend.services.ai_internal._get_http_client", mock_get_client)

        # Mock asyncio.sleep to avoid actual delays
        monkeypatch.setattr("backend.services.ai_internal.asyncio.sleep", AsyncMock())

        # Make the request
        result = await ask_gemini({"prompt": "Hello"})

        # Verify it eventually succeeded
        assert result == {"candidates": []}

        # Verify three attempts were made
        assert mock_client.post.call_count == 3

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"})
    async def test_timeout_exhaustion(self, monkeypatch):
        """Test that repeated timeouts eventually raise GeminiServiceError."""
        # Mock httpx client
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ReadTimeout("Request timed out")

        # Patch the _get_http_client function
        async def mock_get_client():
            return mock_client

        monkeypatch.setattr("backend.services.ai_internal._get_http_client", mock_get_client)

        # Mock asyncio.sleep to avoid delays
        monkeypatch.setattr("backend.services.ai_internal.asyncio.sleep", AsyncMock())

        # Make the request and expect failure after retries
        with pytest.raises(GeminiServiceError) as exc_info:
            await ask_gemini({"prompt": "Hello"})

        # Verify error details
        assert exc_info.value.status == 408
        assert "Request timeout after retries" in exc_info.value.detail

        # Verify three attempts were made
        assert mock_client.post.call_count == 3


class TestCleanup:
    """Test cleanup functions."""

    async def test_cleanup_function(self):
        """Test that cleanup properly closes HTTP client and logs."""
        # Get a client first
        await _get_http_client()
        
        # Mock the close function to verify it's called
        with patch("backend.services.ai_internal._close_http_client") as mock_close:
            await cleanup()
            mock_close.assert_called_once()


# Fixtures for test isolation
@pytest.fixture(scope="function")
async def clean_environment():
    """Ensure clean environment for each test."""
    # Clean up before test
    await _close_http_client()
    yield
    # Clean up after test
    await _close_http_client() 