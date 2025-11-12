"""
Error categorization and handling utilities.

Provides user-friendly error messages with actionable guidance.
"""

import logging
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Categorize and format errors for user-friendly display."""

    @staticmethod
    def categorize_error(error: Exception) -> Tuple[str, str, str]:
        """
        Categorize error and return (emoji, category, user_message).

        Args:
            error: Exception to categorize

        Returns:
            Tuple of (emoji, category_name, user_friendly_message)
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Network/Download errors
        if "connection" in error_str or "timeout" in error_str or "network" in error_str:
            return "🌐", "NetworkError", "Network error. Please check the URL and try again."

        # Video access errors
        if "private" in error_str or "unavailable" in error_str or "not found" in error_str:
            return (
                "🔒",
                "AccessError",
                "Video unavailable. It may be private, deleted, or geo-blocked.",
            )

        # YouTube bot detection
        if "bot" in error_str or "sign in" in error_str or "cookies" in error_str:
            return (
                "🤖",
                "BotDetectionError",
                "YouTube bot detection. Try downloading the video file directly.",
            )

        # Authentication errors
        if "unauthorized" in error_str or "forbidden" in error_str or "api key" in error_str:
            return "🔑", "AuthError", "API authentication issue. Check your API keys in .env"

        # Rate limit errors
        if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
            return "⏱️", "RateLimitError", "API rate limit reached. Try again in a few minutes."

        # Processing errors
        if "transcription" in error_str or "voxtral" in error_str:
            return (
                "🎤",
                "TranscriptionError",
                "Transcription failed. Audio may be corrupted or unsupported.",
            )

        if "extraction" in error_str or "grok" in error_str or "entity" in error_str:
            return (
                "🧠",
                "ExtractionError",
                "Intelligence extraction failed. Try again or check logs.",
            )

        # File format errors
        if "format" in error_str or "codec" in error_str or "decode" in error_str:
            return "📹", "FormatError", "Unsupported video format. Try converting to MP4."

        # Database errors
        if "database" in error_str or "sqlite" in error_str:
            return "💾", "DatabaseError", "Database error. Check logs for details."

        # Memory/Resource errors
        if "memory" in error_str or "resource" in error_str:
            return "💥", "ResourceError", "Video too large or insufficient resources."

        # Generic errors
        return "❌", error_type, f"Unexpected error: {error_type}"

    @staticmethod
    def format_cli_error(error: Exception, context: str = "") -> str:
        """
        Format error for CLI display.

        Args:
            error: Exception to format
            context: Optional context (e.g., video URL)

        Returns:
            Formatted error message for CLI
        """
        emoji, category, message = ErrorHandler.categorize_error(error)
        error_id = f"err_{int(datetime.now().timestamp())}"

        output = f"\n{emoji} {category}\n"
        output += f"{message}\n"

        if context:
            output += f"\nContext: {context}\n"

        output += f"\nError ID: {error_id}"
        output += f"\nDetails: {str(error)[:200]}"
        output += "\n\nCheck logs for full details: logs/clipscribe.log"

        logger.error(f"Error ID {error_id}: {category}: {str(error)}")

        return output

    @staticmethod
    def format_json_error(error: Exception, context: str = "") -> dict:
        """
        Format error for JSON API response.

        Args:
            error: Exception to format
            context: Optional context

        Returns:
            Dictionary with error details
        """
        emoji, category, message = ErrorHandler.categorize_error(error)
        error_id = f"err_{int(datetime.now().timestamp())}"

        logger.error(f"Error ID {error_id}: {category}: {str(error)}")

        return {
            "error": True,
            "error_id": error_id,
            "category": category,
            "message": message,
            "context": context,
            "details": str(error)[:500],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def is_retryable(error: Exception) -> bool:
        """
        Determine if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error should be retried
        """
        _, category, _ = ErrorHandler.categorize_error(error)

        # Retryable errors
        retryable_categories = {
            "NetworkError",
            "RateLimitError",
            "TranscriptionError",
            "ExtractionError",
        }

        return category in retryable_categories
