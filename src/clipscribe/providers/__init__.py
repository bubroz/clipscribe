"""Provider abstraction layer for ClipScribe v3.0.0.

This module provides swappable providers for transcription and intelligence extraction.
Enables testing, flexibility, and future support for additional providers.
"""

from .factory import get_intelligence_provider, get_transcription_provider

__all__ = [
    "get_transcription_provider",
    "get_intelligence_provider",
]
