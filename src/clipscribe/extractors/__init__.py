"""
Extractors package for ClipScribe.

Provides entity normalization, metadata extraction, and model management.
"""

from .entity_normalizer import EntityNormalizer
from .metadata_extractor import MetadataExtractor
from .model_manager import get_model_manager

__all__ = [
    "EntityNormalizer",
    "MetadataExtractor",
    "get_model_manager",
]
