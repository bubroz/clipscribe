"""
This module initializes the extractors package.
"""

# Modern, Gemini-first extractors
from .advanced_hybrid_extractor import AdvancedHybridExtractor
from .enhanced_entity_extractor import EnhancedEntityExtractor
from .relationship_evidence_extractor import RelationshipEvidenceExtractor
from .temporal_reference_resolver import TemporalReferenceResolver

# Core components
from .batch_extractor import BatchExtractor
from .entity_normalizer import EntityNormalizer
from .entity_quality_filter import EntityQualityFilter
from .graph_cleaner import GraphCleaner
from .multi_video_processor import MultiVideoProcessor
from .series_detector import SeriesDetector
from .streaming_extractor import StreamingExtractor


__all__ = [
    "AdvancedHybridExtractor",
    "EnhancedEntityExtractor",
    "RelationshipEvidenceExtractor",
    "TemporalReferenceResolver",
    "BatchExtractor",
    "EntityNormalizer",
    "EntityQualityFilter",
    "GraphCleaner",
    "model_manager",
    "MultiVideoProcessor",
    "SeriesDetector",
    "StreamingExtractor",
]
