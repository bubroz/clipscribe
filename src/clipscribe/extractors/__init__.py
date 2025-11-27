"""
This module initializes the extractors package.
"""

# Legacy extractors (deprecated - use HybridProcessor)
# from .advanced_hybrid_extractor import AdvancedHybridExtractor  # Deprecated - uses Gemini
# Core components
from .batch_extractor import BatchExtractor
from .enhanced_entity_extractor import EnhancedEntityExtractor
from .entity_normalizer import EntityNormalizer
from .entity_quality_filter import EntityQualityFilter
from .graph_cleaner import GraphCleaner
from .multi_video_processor import MultiVideoProcessor
from .relationship_evidence_extractor import RelationshipEvidenceExtractor
from .series_detector import SeriesDetector
from .streaming_extractor import StreamingExtractor
from .temporal_reference_resolver import TemporalReferenceResolver

__all__ = [
    # "AdvancedHybridExtractor",  # Deprecated - uses Gemini
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
