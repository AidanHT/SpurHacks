"""
AI Services Package

This package contains adapters for AI service providers like Google Gemini.
"""

from .ai_internal import ask_gemini, GeminiServiceError

__all__ = ["ask_gemini", "GeminiServiceError"] 