"""Enhanced entity extractor with confidence scores and metadata.

This module implements Phase 1 of the Enhanced Entity & Relationship Metadata
milestone (v2.19.0), adding confidence scores, source attribution, context
windows, and alias detection to entity extraction.
"""

import re
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from ..models import (
    Entity,
    EnhancedEntity,
    EntityContext,
    TemporalMention,
    VideoTranscript,
)

logger = logging.getLogger(__name__)


class EnhancedEntityExtractor:
    """Extract entities with enhanced metadata."""
    
    def __init__(self):
        """Initialize the enhanced entity extractor."""
        pass
        
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
        logger.debug(f"DEBUG: enhance_entities called with {len(entities)} entities")
        
        # Group entities by canonical form
        entity_groups = self._group_entities(entities)
        logger.debug(f"DEBUG: _group_entities returned {len(entity_groups)} groups")
        
        enhanced_entities = []
        for canonical_form, entity_group in entity_groups.items():
            logger.debug(f"DEBUG: Processing group '{canonical_form}' with {len(entity_group)} entities")
            
            # Extract source information
            sources = list({e.source for e in entity_group if hasattr(e, 'source')})
            if not sources:
                sources = ['Gemini']  # Default source
            
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
                extraction_sources=sources,
                mention_count=len(entity_group),
                context_windows=context_windows,
                aliases=self._extract_aliases(canonical_form, entity_group),
                canonical_form=canonical_form,
                temporal_distribution=temporal_distribution
            )
            
            enhanced_entities.append(enhanced)
            logger.debug(f"DEBUG: Created enhanced entity: {enhanced.entity} (type: {enhanced.type})")
            
        logger.debug(f"DEBUG: enhance_entities returning {len(enhanced_entities)} enhanced entities")
        return enhanced_entities
    
    def _group_entities(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        """Group entities by their canonical form."""
        logger.debug(f"DEBUG: _group_entities called with {len(entities)} entities")
        
        groups = defaultdict(list)
        
        # First pass: group exact matches
        for entity in entities:
            logger.debug(f"DEBUG: Processing entity: {entity}")
            canonical = self._get_canonical_form(entity.entity)
            logger.debug(f"DEBUG: Entity '{entity.entity}' -> canonical '{canonical}'")
            groups[canonical].append(entity)
        
        logger.debug(f"DEBUG: After first pass, have {len(groups)} groups")
        
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
        
        logger.debug(f"DEBUG: After merging, have {len(merged_groups)} final groups")
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