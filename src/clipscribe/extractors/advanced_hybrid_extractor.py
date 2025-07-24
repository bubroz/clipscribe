"""
Advanced Hybrid Extractor combining multiple extraction methods.

This extractor uses:
1. SpaCy for basic NER (free)
2. GLiNER for custom entities
3. REBEL for relationships
4. Selective LLM validation for low-confidence items

This provides comprehensive intelligence extraction while maintaining cost efficiency :-)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import asyncio
from collections import defaultdict
import os
import re

import networkx as nx
import google.generativeai as genai
from google.generativeai.types import RequestOptions

from ..models import VideoIntelligence, Entity, Relationship, VideoTranscript, EnhancedEntity
from .entity_normalizer import EntityNormalizer
from .entity_quality_filter import EntityQualityFilter
from .enhanced_entity_extractor import EnhancedEntityExtractor
from .relationship_evidence_extractor import RelationshipEvidenceExtractor
from .temporal_reference_resolver import TemporalReferenceResolver
from ..config.settings import Settings

try:
    import torch
    from gliner import GLiNER
    from transformers import pipeline
    ADVANCED_EXTRACTORS_AVAILABLE = True
except ImportError:
    ADVANCED_EXTRACTORS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AdvancedHybridExtractor:
    """
    Advanced extractor that trusts Gemini's comprehensive extraction.
    This class is the single point of entry for all advanced intelligence extraction.
    """
    def __init__(self, trust_gemini: bool = True):
        """
        Initialize the extractor. The trust_gemini flag is kept for
        future compatibility but the legacy path is now removed.
        """
        if not trust_gemini:
            raise NotImplementedError("The legacy hybrid extraction path has been removed.")

        self.entity_normalizer = EntityNormalizer()
        self.quality_filter = EntityQualityFilter()
        self.enhanced_extractor = EnhancedEntityExtractor()
        self.relationship_evidence_extractor = RelationshipEvidenceExtractor()
        self.temporal_reference_resolver = TemporalReferenceResolver()
        
        logger.info("Advanced hybrid extractor initialized in TRUST_GEMINI mode.")

    async def extract_all(
        self,
        video_intel: VideoIntelligence,
        domain: Optional[str] = None
    ) -> VideoIntelligence:
        """
        Run the full advanced intelligence extraction pipeline.
        This path relies exclusively on the rich data provided by Gemini.
        """
        if not video_intel.transcript or not video_intel.transcript.full_text:
            logger.warning("Cannot extract intelligence, transcript is missing or empty.")
            return video_intel

        # Use entities and relationships directly from Gemini
        gemini_entities = video_intel.entities
        gemini_relationships = video_intel.relationships

        # Light normalization and enhancement
        normalized_entities = self.entity_normalizer.normalize_entities(gemini_entities)
        
        enhanced_entities = self.enhanced_extractor.enhance_entities(
            normalized_entities,
            transcript_segments=video_intel.transcript.segments,
            visual_data=None
        )
        video_intel.entities = enhanced_entities
        
        if gemini_relationships:
            enhanced_relationships = self.relationship_evidence_extractor.extract_evidence_chains(
                gemini_relationships,
                video_intel,
                enhanced_entities
            )
            video_intel.relationships = enhanced_relationships

        # Resolve temporal references
        temporal_references = self.temporal_reference_resolver.resolve_temporal_references(video_intel)
        video_intel.temporal_references = temporal_references

        logger.info(f"Advanced extraction complete in TRUST_GEMINI mode.")
        return video_intel 