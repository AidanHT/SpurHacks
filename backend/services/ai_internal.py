"""
Gemini 2.5 Service Adapter - Internal AI Bridge

This module provides an async adapter for Google Gemini 2.5 API with:
- Input trimming for prompts > 2000 characters
- Exponential backoff retry logic
- Shared HTTP client for performance
- Comprehensive error handling
- Security-focused logging
"""

import asyncio
import logging
import os
import random
from typing import Dict, Optional, Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global HTTP client singleton with thread-safe access
_http_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


class GeminiServiceError(Exception):
    """Custom exception for Gemini service errors."""
    
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"Gemini API error {status}: {detail}")


async def _get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client singleton with thread safety."""
    global _http_client
    if _http_client is None:
        async with _client_lock:
            # Double-check pattern to prevent race conditions
            if _http_client is None:
                _http_client = httpx.AsyncClient()
    return _http_client


async def _close_http_client():
    """Close the shared HTTP client. Used for cleanup."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _truncate_prompt(prompt: str, max_length: int = 2000) -> str:
    """
    Truncate prompt if it exceeds max_length characters.
    
    Args:
        prompt: The input prompt text
        max_length: Maximum allowed length (default: 2000)
        
    Returns:
        Truncated prompt with marker if truncation occurred
    """
    if len(prompt) <= max_length:
        return prompt
    
    # The marker "…[truncated]" is 12 characters long
    marker = "…[truncated]"
    truncated = prompt[:max_length - len(marker)]
    return f"{truncated}{marker}"


def _log_request_safely(prompt: str, max_log_length: int = 100) -> str:
    """
    Safely log request prompt by truncating to prevent log pollution.
    
    Args:
        prompt: The full prompt text
        max_log_length: Maximum length to log (default: 100)
        
    Returns:
        Truncated prompt for logging
    """
    if len(prompt) <= max_log_length:
        return prompt
    return f"{prompt[:max_log_length]}…"


async def ask_gemini(payload: Dict[str, Any], *, timeout: float = 30.0) -> Dict[str, Any]:
    """
    Send a request to Google Gemini 2.5 API with retry logic.
    
    This function handles:
    - Input validation and prompt truncation
    - Context injection for better responses
    - Exponential backoff retry on failures
    - Comprehensive error handling
    
    Args:
        payload: Request payload containing 'prompt' and optional parameters
        timeout: Request timeout in seconds (default: 30.0)
        
    Returns:
        Response dictionary from Gemini API
        
    Raises:
        GeminiServiceError: On API errors, repeated failures, or timeouts
        ValueError: On invalid input parameters
    """
    # Validate input
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary")
    
    if "prompt" not in payload:
        raise ValueError("Payload must contain 'prompt' field")
    
    # Get configuration from environment
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    
    if not api_key:
        raise GeminiServiceError(500, "GEMINI_API_KEY environment variable not set")
    
    # Process and truncate prompt
    original_prompt = payload["prompt"]
    truncated_prompt = _truncate_prompt(original_prompt)
    
    # Log request safely (truncated for security)
    log_prompt = _log_request_safely(truncated_prompt)
    logger.info(f"Gemini API request initiated: {log_prompt}")
    
    # Prepare request payload with context injection
    request_payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "You are Gemini 2.5, respond concisely."
                    }
                ]
            },
            {
                "parts": [
                    {
                        "text": truncated_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": payload.get("temperature", 0.7),
            "maxOutputTokens": payload.get("max_tokens", 4096),
            "topP": payload.get("top_p", 0.95),
            "topK": payload.get("top_k", 64)
        }
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    # Retry configuration
    max_retries = 3
    base_delay = 1.0  # seconds
    
    client = await _get_http_client()
    
    for attempt in range(max_retries):
        try:
            # Make the API request
            response = await client.post(
                f"{base_url}/models/gemini-2.0-flash-exp:generateContent",
                json=request_payload,
                headers=headers,
                timeout=timeout
            )
            
            # Check for success
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Gemini API request successful on attempt {attempt + 1}")
                return result
            
            # Handle client errors (4xx) - don't retry
            elif 400 <= response.status_code < 500:
                error_detail = response.text
                logger.error(f"Gemini API client error {response.status_code}: {error_detail}")
                raise GeminiServiceError(response.status_code, error_detail)
            
            # Handle server errors (5xx) - retry with backoff
            elif response.status_code >= 500:
                error_detail = response.text
                logger.warning(
                    f"Gemini API server error {response.status_code} on attempt {attempt + 1}: {error_detail}"
                )
                
                # Don't retry on last attempt
                if attempt == max_retries - 1:
                    raise GeminiServiceError(response.status_code, error_detail)
                
                # Calculate delay with jitter
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                jitter = random.uniform(0, 0.25)  # Add 0-250ms jitter
                total_delay = delay + jitter
                
                logger.info(f"Retrying in {total_delay:.2f} seconds...")
                await asyncio.sleep(total_delay)
                continue
            
            else:
                # Unexpected status code
                error_detail = f"Unexpected status code: {response.status_code}"
                logger.error(f"Gemini API unexpected error: {error_detail}")
                raise GeminiServiceError(response.status_code, error_detail)
                
        except httpx.ReadTimeout:
            logger.warning(f"Gemini API timeout on attempt {attempt + 1}")
            
            # Don't retry on last attempt
            if attempt == max_retries - 1:
                raise GeminiServiceError(408, "Request timeout after retries")
            
            # Retry with exponential backoff
            delay = base_delay * (2 ** attempt)
            jitter = random.uniform(0, 0.25)
            total_delay = delay + jitter
            
            logger.info(f"Retrying after timeout in {total_delay:.2f} seconds...")
            await asyncio.sleep(total_delay)
            continue
            
        except httpx.RequestError as e:
            logger.error(f"Gemini API request error on attempt {attempt + 1}: {str(e)}")
            
            # Don't retry on last attempt
            if attempt == max_retries - 1:
                raise GeminiServiceError(500, f"Request error after retries: {str(e)}")
            
            # Retry with exponential backoff
            delay = base_delay * (2 ** attempt)
            jitter = random.uniform(0, 0.25)
            total_delay = delay + jitter
            
            logger.info(f"Retrying after request error in {total_delay:.2f} seconds...")
            await asyncio.sleep(total_delay)
            continue
    
    # This should never be reached due to the logic above
    raise GeminiServiceError(500, "Maximum retries exceeded")


# Cleanup function for application shutdown
async def cleanup():
    """Cleanup resources used by the AI service."""
    await _close_http_client()
    logger.info("AI service cleanup completed") 