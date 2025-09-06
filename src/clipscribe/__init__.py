"""ClipScribe - AI-powered video transcription and analysis tool.

Built with Voxtral-Grok pipeline for uncensored, accurate transcription of videos from 1800+ platforms.
"""

from .version import __version__


# Lazy import CLI only when needed - don't import at package level
from typing import Any


def get_cli() -> Any:
    """Get CLI instance with lazy loading."""
    from .commands.cli import cli

    return cli


__all__ = ["get_cli", "__version__"]
