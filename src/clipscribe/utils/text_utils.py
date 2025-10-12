"""
Text processing utilities.

Includes markdown stripping, smart truncation, and text cleaning.
"""

import re
from html.parser import HTMLParser
from markdown_it import MarkdownIt


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
        return ''.join(self.text_parts)


def strip_markdown(text: str) -> str:
    """
    Strip markdown formatting to get clean plain text.
    
    Uses markdown-it-py to parse markdown → HTML → plain text.
    This handles ALL markdown syntax correctly:
    - Headers (###, ##, #)
    - Bold/italic (**, __, *, _)
    - Links [text](url)
    - Code blocks and inline code
    - Lists (bullets, numbered)
    - Blockquotes
    - Horizontal rules
    
    Args:
        text: Markdown-formatted text
        
    Returns:
        Plain text with all markdown formatting removed
    """
    if not text:
        return ""
    
    # Parse markdown to HTML
    md = MarkdownIt()
    html = md.render(text)
    
    # Extract plain text from HTML
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    plain_text = extractor.get_text()
    
    # Post-processing: Remove any remaining markdown artifacts
    # (catches broken/unclosed markdown that parser left)
    plain_text = re.sub(r'\*\*', '', plain_text)  # Remove orphaned **
    plain_text = re.sub(r'__', '', plain_text)     # Remove orphaned __
    plain_text = re.sub(r'#{1,6}\s*', '', plain_text)  # Remove orphaned headers
    
    # Clean up excessive whitespace
    plain_text = re.sub(r'\n{3,}', '\n\n', plain_text)  # Max 2 newlines
    plain_text = re.sub(r' {2,}', ' ', plain_text)       # Max 1 space
    
    return plain_text.strip()


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
    last_period = max(
        truncated.rfind('. '),
        truncated.rfind('! '),
        truncated.rfind('? ')
    )
    
    # If we found a sentence boundary and it's not too short
    if last_period > 0 and last_period >= max_length * min_percentage:
        return text[:last_period + 1].strip()
    
    # No good sentence boundary - truncate at word boundary
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return text[:last_space].strip() + '...'
    
    # No spaces either - hard truncate
    return text[:max_length - 3] + '...'


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

