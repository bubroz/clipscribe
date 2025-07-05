"""Enhanced entity extractor with confidence scores and metadata.

This module implements Phase 1 of the Enhanced Entity & Relationship Metadata
milestone (v2.19.0), adding confidence scores, source attribution, context
windows, and alias detection to entity extraction.
"""

import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from ..models import Entity, Relationship
from ..utils.logging import get_logger

logger = get_logger(__name__)


class EntityContext(BaseModel):
    """Context window for an entity mention."""
    
    text: str = Field(..., description="Surrounding text (±50 chars)")
    timestamp: str = Field(..., description="When mentioned (HH:MM:SS)")
    confidence: float = Field(..., description="Context-specific confidence")
    speaker: Optional[str] = Field(None, description="Who mentioned it")
    visual_present: bool = Field(False, description="Entity visible on screen")


class TemporalMention(BaseModel):
    """When and how an entity is mentioned."""
    
    timestamp: str = Field(..., description="HH:MM:SS format")
    duration: float = Field(..., description="How long discussed (seconds)")
    context_type: str = Field(..., description="spoken, visual, or both")


class EnhancedEntity(BaseModel):
    """Enhanced entity with confidence and attribution."""
    
    # Core fields (backward compatible)
    entity: str = Field(..., description="The entity text")
    type: str = Field(..., description="Entity type (PERSON, ORG, LOC, etc.)")
    
    # Enhanced metadata (new in v2.19.0)
    confidence: float = Field(..., description="Overall confidence score (0.0-1.0)")
    extraction_sources: List[str] = Field(..., description="Which methods found this")
    mention_count: int = Field(..., description="Total occurrences in video")
    
    # Context windows
    context_windows: List[EntityContext] = Field(default_factory=list)
    
    # Alias management
    aliases: List[str] = Field(default_factory=list)
    canonical_form: str = Field(..., description="Normalized primary form")
    
    # Source-specific confidence
    source_confidence: Dict[str, float] = Field(default_factory=dict)
    
    # Temporal distribution
    temporal_distribution: List[TemporalMention] = Field(default_factory=list)


class EnhancedEntityExtractor:
    """Extract entities with enhanced metadata."""
    
    def __init__(self):
        """Initialize the enhanced entity extractor."""
        self.type_confidence_modifiers = {
            "PERSON": 0.05,
            "ORG": 0.03,
            "GPE": 0.04,
            "LOC": 0.04,
            "DATE": 0.08,
            "TIME": 0.06,
            "MONEY": 0.07,
            "PERCENT": 0.08,
            "MISC": -0.05,
            "UNKNOWN": -0.10
        }
        
        self.high_quality_sources = {"gemini", "gliner", "spacy", "rebel"}
        
        # Common title patterns for normalization
        self.title_patterns = [
            (r"^(President|Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.|Sen\.|Rep\.|Gov\.)\s+", ""),
            (r"^(CEO|CTO|CFO|COO)\s+", ""),
            (r"^(General|Admiral|Colonel|Captain)\s+", ""),
        ]
    
    def enhance_entities(
        self,
        entities: List[Entity],
        transcript_segments: Optional[List[Dict]] = None,
        visual_data: Optional[Dict] = None
    ) -> List[EnhancedEntity]:
        """Enhance entities with confidence scores and metadata.
        
        Args:
            entities: List of basic entities to enhance
            transcript_segments: Optional transcript data for context
            visual_data: Optional visual detection data
            
        Returns:
            List of enhanced entities with full metadata
        """
        # Group entities by canonical form
        entity_groups = self._group_entities(entities)
        
        enhanced_entities = []
        for canonical_form, entity_group in entity_groups.items():
            # Calculate confidence scores
            confidence = self._calculate_confidence(entity_group)
            
            # Extract source information
            sources = list({e.source for e in entity_group if hasattr(e, 'source')})
            source_confidence = self._calculate_source_confidence(entity_group)
            
            # Get context windows if transcript provided
            context_windows = []
            if transcript_segments:
                context_windows = self._extract_context_windows(
                    canonical_form, 
                    entity_group,
                    transcript_segments
                )
            
            # Extract temporal distribution
            temporal_distribution = self._extract_temporal_distribution(
                entity_group,
                context_windows
            )
            
            # Determine entity type (most common among group)
            entity_type = self._determine_entity_type(entity_group)
            
            # Create enhanced entity
            enhanced = EnhancedEntity(
                entity=canonical_form,
                type=entity_type,
                confidence=confidence,
                extraction_sources=sources,
                mention_count=len(entity_group),
                context_windows=context_windows,
                aliases=self._extract_aliases(canonical_form, entity_group),
                canonical_form=canonical_form,
                source_confidence=source_confidence,
                temporal_distribution=temporal_distribution
            )
            
            enhanced_entities.append(enhanced)
            
        return enhanced_entities
    
    def _group_entities(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        """Group entities by their canonical form."""
        groups = defaultdict(list)
        
        # First pass: group exact matches
        for entity in entities:
            canonical = self._get_canonical_form(entity.entity)
            groups[canonical].append(entity)
        
        # Second pass: merge similar entities
        merged_groups = {}
        processed = set()
        
        for canonical, group in groups.items():
            if canonical in processed:
                continue
                
            # Find similar entities
            similar_canonicals = []
            for other_canonical in groups:
                if other_canonical != canonical and other_canonical not in processed:
                    if self._are_entities_similar(canonical, other_canonical):
                        similar_canonicals.append(other_canonical)
                        processed.add(other_canonical)
            
            # Merge groups
            merged_group = group
            for similar in similar_canonicals:
                merged_group.extend(groups[similar])
            
            # Select best canonical form
            best_canonical = self._select_best_canonical(
                [canonical] + similar_canonicals,
                merged_group
            )
            merged_groups[best_canonical] = merged_group
            processed.add(canonical)
        
        return merged_groups
    
    def _get_canonical_form(self, entity_text: str) -> str:
        """Get canonical form of an entity."""
        canonical = entity_text.strip()
        
        # Remove common titles
        for pattern, replacement in self.title_patterns:
            canonical = re.sub(pattern, replacement, canonical, flags=re.IGNORECASE)
        
        # Normalize whitespace
        canonical = ' '.join(canonical.split())
        
        return canonical
    
    def _are_entities_similar(self, entity1: str, entity2: str) -> bool:
        """Check if two entities are similar enough to be the same."""
        # Exact match after normalization
        if entity1.lower() == entity2.lower():
            return True
        
        # One is substring of the other (e.g., "Biden" and "Joe Biden")
        if entity1 in entity2 or entity2 in entity1:
            # But not if it's too generic
            if len(entity1) > 2 and len(entity2) > 2:
                return True
        
        # Common abbreviations
        if self._are_abbreviations(entity1, entity2):
            return True
        
        return False
    
    def _are_abbreviations(self, text1: str, text2: str) -> bool:
        """Check if one text is an abbreviation of the other."""
        # Simple acronym check
        if len(text1) < len(text2):
            short, long = text1, text2
        else:
            short, long = text2, text1
        
        # Check if short is acronym of long
        if short.isupper() and len(short) >= 2:
            words = long.split()
            if len(words) == len(short):
                acronym = ''.join(w[0].upper() for w in words if w)
                if acronym == short:
                    return True
        
        return False
    
    def _select_best_canonical(
        self, 
        candidates: List[str], 
        entities: List[Entity]
    ) -> str:
        """Select the best canonical form from candidates."""
        # Prefer the most complete form (usually longest)
        # But also consider frequency
        
        frequency = defaultdict(int)
        for entity in entities:
            canonical = self._get_canonical_form(entity.entity)
            frequency[canonical] += 1
        
        # Score candidates
        scores = {}
        for candidate in candidates:
            # Length score (prefer complete names)
            length_score = len(candidate.split())
            
            # Frequency score
            freq_score = frequency.get(candidate, 0)
            
            # Combined score
            scores[candidate] = length_score * 2 + freq_score
        
        # Return highest scoring candidate
        return max(scores, key=scores.get)
    
    def _calculate_confidence(self, entity_group: List[Entity]) -> float:
        """Calculate overall confidence score for an entity group."""
        # Base confidence from source agreement
        unique_sources = set()
        for entity in entity_group:
            if hasattr(entity, 'source'):
                unique_sources.add(entity.source)
        
        source_count = len(unique_sources)
        base_confidence = min(0.5 + (source_count * 0.15), 0.95)
        
        # Get the canonical form for analysis
        canonical = self._get_canonical_form(entity_group[0].entity)
        
        # Length modifier
        word_count = len(canonical.split())
        length_modifier = 0.0
        if word_count >= 3:
            length_modifier = 0.05
        elif word_count == 1 and len(canonical) < 4:
            length_modifier = -0.10
        
        # Type modifier
        entity_type = self._determine_entity_type(entity_group)
        type_modifier = self.type_confidence_modifiers.get(entity_type, 0)
        
        # Source quality modifier
        source_quality_modifier = 0.0
        if unique_sources & self.high_quality_sources:
            source_quality_modifier = 0.05
        
        # Frequency modifier (more mentions = higher confidence)
        frequency_modifier = min(len(entity_group) * 0.01, 0.10)
        
        # Calculate final confidence
        final_confidence = (
            base_confidence + 
            length_modifier + 
            type_modifier + 
            source_quality_modifier +
            frequency_modifier
        )
        
        return max(0.1, min(0.99, final_confidence))
    
    def _calculate_source_confidence(
        self, 
        entity_group: List[Entity]
    ) -> Dict[str, float]:
        """Calculate per-source confidence scores."""
        source_confidence = {}
        source_entities = defaultdict(list)
        
        # Group by source
        for entity in entity_group:
            if hasattr(entity, 'source'):
                source_entities[entity.source].append(entity)
        
        # Calculate confidence per source
        for source, entities in source_entities.items():
            # Base confidence for the source
            if source in self.high_quality_sources:
                base = 0.85
            else:
                base = 0.70
            
            # Adjust based on consistency
            unique_forms = set(e.entity for e in entities)
            consistency_modifier = -0.05 * (len(unique_forms) - 1)
            
            source_confidence[source] = max(0.5, base + consistency_modifier)
        
        return source_confidence
    
    def _extract_context_windows(
        self,
        canonical_form: str,
        entity_group: List[Entity],
        transcript_segments: List[Dict]
    ) -> List[EntityContext]:
        """Extract context windows for entity mentions."""
        context_windows = []
        
        # Get all variations of the entity
        variations = {canonical_form}
        variations.update(e.entity for e in entity_group)
        
        for segment in transcript_segments:
            text = segment.get('text', '')
            timestamp = segment.get('timestamp', '00:00:00')
            
            # Check each variation
            for variation in variations:
                if variation.lower() in text.lower():
                    # Extract context window (±50 chars)
                    start = max(0, text.lower().find(variation.lower()) - 50)
                    end = min(len(text), text.lower().find(variation.lower()) + len(variation) + 50)
                    
                    context = EntityContext(
                        text=text[start:end],
                        timestamp=timestamp,
                        confidence=0.90,  # High confidence for direct text match
                        speaker=segment.get('speaker'),
                        visual_present=False  # Would need visual data to determine
                    )
                    
                    context_windows.append(context)
        
        return context_windows
    
    def _extract_temporal_distribution(
        self,
        entity_group: List[Entity],
        context_windows: List[EntityContext]
    ) -> List[TemporalMention]:
        """Extract temporal distribution of entity mentions."""
        temporal_mentions = []
        
        # Group context windows by timestamp
        timestamp_groups = defaultdict(list)
        for context in context_windows:
            timestamp_groups[context.timestamp].append(context)
        
        # Create temporal mentions
        for timestamp, contexts in timestamp_groups.items():
            mention = TemporalMention(
                timestamp=timestamp,
                duration=5.0,  # Default duration, would need more data
                context_type="spoken"  # Default, would need visual data
            )
            temporal_mentions.append(mention)
        
        return temporal_mentions
    
    def _determine_entity_type(self, entity_group: List[Entity]) -> str:
        """Determine the most likely entity type for the group."""
        type_counts = defaultdict(int)
        
        for entity in entity_group:
            if hasattr(entity, 'type') and entity.type:
                type_counts[entity.type] += 1
        
        if type_counts:
            return max(type_counts, key=type_counts.get)
        return "UNKNOWN"
    
    def _extract_aliases(
        self,
        canonical_form: str,
        entity_group: List[Entity]
    ) -> List[str]:
        """Extract aliases for the canonical entity."""
        aliases = set()
        
        for entity in entity_group:
            if entity.entity != canonical_form:
                aliases.add(entity.entity)
        
        return sorted(list(aliases))


class AliasNormalizer:
    """Normalize and manage entity aliases."""
    
    def __init__(self):
        """Initialize the alias normalizer."""
        self.common_aliases = {
            # Common abbreviations
            "US": "United States",
            "USA": "United States",
            "UK": "United Kingdom",
            "EU": "European Union",
            "UN": "United Nations",
            "FBI": "Federal Bureau of Investigation",
            "CIA": "Central Intelligence Agency",
            "NSA": "National Security Agency",
            
            # Common variations
            "U.S.": "United States",
            "U.K.": "United Kingdom",
            "E.U.": "European Union",
            "U.N.": "United Nations",
        }
    
    def normalize_entity(self, entity_text: str) -> str:
        """Normalize an entity to its canonical form."""
        # Check common aliases
        if entity_text in self.common_aliases:
            return self.common_aliases[entity_text]
        
        # Remove titles
        normalized = entity_text
        title_patterns = [
            r"^(President|Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)\s+",
            r"^(CEO|CTO|CFO|COO) of\s+",
            r"^(Former|Ex-)\s+",
        ]
        
        for pattern in title_patterns:
            normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)
        
        return normalized.strip()
    
    def find_aliases(self, entities: List[str]) -> Dict[str, List[str]]:
        """Find aliases among a list of entities."""
        # Group potential aliases
        alias_groups = defaultdict(set)
        
        for entity in entities:
            canonical = self.normalize_entity(entity)
            alias_groups[canonical].add(entity)
        
        # Convert to dict with lists
        return {
            canonical: sorted(list(aliases))
            for canonical, aliases in alias_groups.items()
            if len(aliases) > 1
        } 