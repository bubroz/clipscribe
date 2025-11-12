"""
Text processing utilities.

Includes markdown stripping, smart truncation, and text cleaning.
"""

import re
from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML, stripping all tags."""

    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        """Collect text data."""
        self.text_parts.append(data)

    def get_text(self) -> str:
        """Return collected text."""
        return "".join(self.text_parts)


def strip_markdown(text: str) -> str:
    """
    Strip markdown formatting but preserve paragraph structure.

    Uses regex to remove markdown syntax while keeping readability.
    Preserves: paragraph breaks, line breaks, list structure.
    Removes: ###, **, __, *, links, code blocks.

    Args:
        text: Markdown-formatted text

    Returns:
        Plain text with markdown removed but structure preserved
    """
    if not text:
        return ""

    # Remove code blocks (```)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove headers but keep content with spacing (### Header → Header\n\n)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\1\n", text, flags=re.MULTILINE)

    # Remove bold/italic but keep content
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"__(.+?)__", r"\1", text)  # __bold__
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"\1", text)  # *italic*
    text = re.sub(r"(?<!_)_(?!_)(.+?)_", r"\1", text)  # _italic_

    # Remove links but keep text [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Remove inline code (`code` → code)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove list markers but keep content (- item → item)
    text = re.sub(r"^\s*[\-\*\+]\s+", "", text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r"^[\-\*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove orphaned markdown artifacts
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"__", "", text)

    # Clean up whitespace BUT preserve paragraph structure
    text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 newlines (keeps paragraphs)
    text = re.sub(r"[ \t]{2,}", " ", text)  # Multiple spaces → one
    text = re.sub(r" +\n", "\n", text)  # Remove trailing spaces

    return text.strip()


def truncate_at_sentence(text: str, max_length: int, min_percentage: float = 0.7) -> str:
    """
    Truncate text at sentence boundary.

    Finds the last complete sentence within max_length.
    If no sentence boundary found within min_percentage of max_length,
    truncates at word boundary and adds '...'.

    Args:
        text: Text to truncate
        max_length: Maximum character length
        min_percentage: Minimum acceptable length as fraction of max_length

    Returns:
        Truncated text ending at sentence boundary or with '...'
    """
    if len(text) <= max_length:
        return text

    # Find last sentence boundary within max_length
    truncated = text[:max_length]

    # Look for sentence endings (. ! ?)
    last_period = max(truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? "))

    # If we found a sentence boundary and it's not too short
    if last_period > 0 and last_period >= max_length * min_percentage:
        return text[: last_period + 1].strip()

    # No good sentence boundary - truncate at word boundary
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return text[:last_space].strip() + "..."

    # No spaces either - hard truncate
    return text[: max_length - 3] + "..."


def clean_for_display(text: str, max_length: int = 2000) -> str:
    """
    Prepare text for display: strip markdown and truncate smartly.

    Args:
        text: Markdown-formatted text
        max_length: Maximum display length

    Returns:
        Clean plain text, truncated at sentence boundary
    """
    # Strip markdown first
    plain_text = strip_markdown(text)

    # Truncate smartly
    return truncate_at_sentence(plain_text, max_length)
