"""ClipScribe - AI-powered video transcription and analysis tool.

Built with Gemini 2.5 Flash for fast, accurate transcription of videos from 1800+ platforms.
"""

__version__ = "2.0.0"

from .commands import cli

__all__ = ["cli", "__version__"] 