"""
Knowledge management module for ClipScribe.

Handles Collections API integration and knowledge base management.
"""

from .collection_manager import SearchResult, VideoKnowledgeBase, VideoReference

__all__ = ["VideoKnowledgeBase", "SearchResult", "VideoReference"]
