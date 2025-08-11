"""
Relationship Evidence Extractor - Phase 2 of Enhanced Metadata.

Extracts evidence chains, direct quotes, and visual context for relationships,
providing comprehensive support for each relationship with confidence scoring.
"""

import logging
import re
from typing import List, Dict, Optional

from ..models import (
    Relationship,
    RelationshipEvidence,
    VideoIntelligence,
    VideoTranscript,
    EnhancedEntity,
)

logger = logging.getLogger(__name__)


# RelationshipEvidence and enhanced Relationship models are now in models.py


class RelationshipEvidenceExtractor:
    """
    Extract evidence chains and quotes supporting relationships.

    Phase 2 implementation that enhances relationships with:
    - Direct quote extraction from transcripts
    - Visual context correlation
    - Evidence confidence scoring
    - Contradiction detection
    - Supporting mention tracking
    """

    def __init__(self):
        """Initialize the relationship evidence extractor."""
        self.quote_patterns = [
            # Direct speech patterns
            r'"([^"]+)"',
            r'"([^"]+)"',
            r"'([^']+)'",
            r'said\s+"([^"]+)"',
            r'stated\s+"([^"]+)"',
            r'announced\s+"([^"]+)"',
            r'declared\s+"([^"]+)"',
            r'according to .+,\s+"([^"]+)"',
        ]

        # Action verbs that indicate relationships
        self.action_verbs = {
            "announced",
            "declared",
            "stated",
            "said",
            "claimed",
            "revealed",
            "signed",
            "approved",
            "vetoed",
            "appointed",
            "nominated",
            "fired",
            "acquired",
            "merged",
            "partnered",
            "invested",
            "funded",
            "supported",
            "criticized",
            "praised",
            "attacked",
            "defended",
            "met",
            "visited",
            "founded",
            "created",
            "launched",
            "developed",
            "discovered",
        }

        # Visual context indicators
        self.visual_indicators = [
            "shown on screen",
            "displayed",
            "visible",
            "footage shows",
            "video shows",
            "image shows",
            "graphic shows",
            "chart shows",
            "document shows",
            "slide shows",
            "presentation shows",
        ]

    def extract_evidence_chains(
        self,
        relationships: List[Relationship],
        video_intel: VideoIntelligence,
        enhanced_entities: List[EnhancedEntity],
    ) -> List[Relationship]:
        """
        Extract evidence chains for relationships.

        Args:
            relationships: Basic relationships from REBEL
            video_intel: Complete video intelligence with transcript
            enhanced_entities: Enhanced entities with context

        Returns:
            List of enhanced relationships with evidence
        """
        logger.info(f"Extracting evidence chains for {len(relationships)} relationships...")

        enhanced_relationships = []

        # Create entity lookup for faster access
        entity_lookup = {entity.canonical_form.lower(): entity for entity in enhanced_entities}

        for relationship in relationships:
            # Extract evidence for this relationship
            evidence_chain = self._extract_relationship_evidence(
                relationship, video_intel, entity_lookup
            )

            # Count supporting mentions
            supporting_mentions = self._count_supporting_mentions(
                relationship, video_intel.transcript
            )

            # Check for contradictions
            contradictions = self._detect_contradictions(relationship, video_intel.transcript)

            # Check for visual correlation
            visual_correlation = self._check_visual_correlation(relationship, video_intel)

            # Create enhanced relationship using the Pydantic model
            enhanced_rel = Relationship(
                subject=relationship.subject,
                predicate=relationship.predicate,
                object=relationship.object,
                source=getattr(relationship, "source", "REBEL"),
                evidence_chain=evidence_chain,
                supporting_mentions=supporting_mentions,
                contradictions=contradictions,
                visual_correlation=visual_correlation,
            )

            enhanced_relationships.append(enhanced_rel)

        logger.info(f"Enhanced {len(enhanced_relationships)} relationships with evidence chains")
        return enhanced_relationships

    def _extract_relationship_evidence(
        self,
        relationship: Relationship,
        video_intel: VideoIntelligence,
        entity_lookup: Dict[str, EnhancedEntity],
    ) -> List[RelationshipEvidence]:
        """Extract evidence supporting a specific relationship."""
        evidence_chain = []

        if not video_intel.transcript or not video_intel.transcript.segments:
            return evidence_chain

        # Get entity context windows for relationship participants
        subject_entity = entity_lookup.get(relationship.subject.lower())
        _ = entity_lookup.get(relationship.object.lower())

        # Search transcript segments for evidence
        for segment in video_intel.transcript.segments:
            text = segment.get("text", "")
            timestamp = segment.get("timestamp", "00:00:00")
            speaker = segment.get("speaker")

            # Check if this segment mentions both entities
            if self._segment_mentions_relationship(text, relationship):
                # Extract direct quotes from this segment
                quotes = self._extract_quotes_from_segment(text, relationship)

                for quote in quotes:
                    # Determine evidence type
                    evidence_type = self._determine_evidence_type(text)

                    # Get visual context if available
                    visual_context = self._extract_visual_context(text)

                    evidence = RelationshipEvidence(
                        direct_quote=quote,
                        timestamp=timestamp,
                        speaker=speaker,
                        visual_context=visual_context,
                        context_window=text[:200],  # First 200 chars as context
                        evidence_type=evidence_type,
                    )

                    evidence_chain.append(evidence)

        # Also check entity context windows for additional evidence
        if subject_entity and subject_entity.context_windows:
            for context in subject_entity.context_windows:
                if self._context_supports_relationship(context.text, relationship):
                    evidence = RelationshipEvidence(
                        direct_quote=self._extract_key_phrase(context.text, relationship),
                        timestamp=context.timestamp,
                        speaker=context.speaker,
                        context_window=context.text,
                        evidence_type="entity_context",
                    )
                    evidence_chain.append(evidence)

        return evidence_chain

    def _segment_mentions_relationship(self, text: str, relationship: Relationship) -> bool:
        """Check if a segment mentions both entities in the relationship."""
        text_lower = text.lower()
        subject_lower = relationship.subject.lower()
        object_lower = relationship.object.lower()

        # Check for direct mentions
        has_subject = subject_lower in text_lower
        has_object = object_lower in text_lower

        # Check for partial matches (first/last names)
        if not has_subject:
            subject_parts = subject_lower.split()
            has_subject = any(part in text_lower for part in subject_parts if len(part) > 2)

        if not has_object:
            object_parts = object_lower.split()
            has_object = any(part in text_lower for part in object_parts if len(part) > 2)

        return has_subject and has_object

    def _extract_quotes_from_segment(self, text: str, relationship: Relationship) -> List[str]:
        """Extract direct quotes from a text segment."""
        quotes = []

        # Try each quote pattern
        for pattern in self.quote_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                quote = match.group(1) if match.groups() else match.group(0)
                if len(quote) > 10:  # Filter out very short quotes
                    quotes.append(quote.strip())

        # If no quoted text found, extract key phrases with action verbs
        if not quotes:
            for verb in self.action_verbs:
                if verb in text.lower():
                    # Extract sentence containing the action verb
                    sentences = text.split(".")
                    for sentence in sentences:
                        if verb in sentence.lower():
                            quotes.append(sentence.strip())
                            break

        return quotes

    def _determine_evidence_type(self, text: str) -> str:
        """Determine the type of evidence based on text content."""
        text_lower = text.lower()

        # Check for visual indicators
        if any(indicator in text_lower for indicator in self.visual_indicators):
            return "visual"

        # Check for document references
        if any(word in text_lower for word in ["document", "letter", "report", "statement"]):
            return "document"

        # Default to spoken
        return "spoken"

    def _extract_visual_context(self, text: str) -> Optional[str]:
        """Extract visual context description from text."""
        text_lower = text.lower()

        for indicator in self.visual_indicators:
            if indicator in text_lower:
                # Find the sentence containing the visual indicator
                sentences = text.split(".")
                for sentence in sentences:
                    if indicator in sentence.lower():
                        return sentence.strip()

        return None

    def _context_supports_relationship(self, context_text: str, relationship: Relationship) -> bool:
        """Check if context text supports the relationship."""
        text_lower = context_text.lower()

        # Check for relationship predicate or related terms
        predicate_lower = relationship.predicate.lower()

        # Direct predicate match
        if predicate_lower in text_lower:
            return True

        # Check for action verbs related to the predicate
        if any(verb in text_lower for verb in self.action_verbs):
            return True

        return False

    def _extract_key_phrase(self, text: str, relationship: Relationship) -> str:
        """Extract key phrase from context that supports the relationship."""
        # Find sentence with action verb or predicate
        sentences = text.split(".")

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if relationship.predicate.lower() in sentence_lower or any(
                verb in sentence_lower for verb in self.action_verbs
            ):
                return sentence.strip()

        # Fallback to first 100 characters
        return text[:100] + "..." if len(text) > 100 else text

    def _count_supporting_mentions(
        self, relationship: Relationship, transcript: VideoTranscript
    ) -> int:
        """Count supporting mentions of the relationship."""
        count = 0

        if not transcript or not transcript.segments:
            return count

        for segment in transcript.segments:
            text = segment.get("text", "")
            if self._segment_mentions_relationship(text, relationship):
                count += 1

        return count

    def _detect_contradictions(
        self, relationship: Relationship, transcript: VideoTranscript
    ) -> List[str]:
        """Detect contradictions to the relationship."""
        contradictions = []

        # Contradiction patterns
        contradiction_words = ["not", "never", "denied", "refuted", "disputed", "rejected"]

        if not transcript or not transcript.segments:
            return contradictions

        for segment in transcript.segments:
            text = segment.get("text", "")
            text_lower = text.lower()

            # Check if segment mentions relationship entities
            if self._segment_mentions_relationship(text, relationship):
                # Check for contradiction words
                if any(word in text_lower for word in contradiction_words):
                    contradictions.append(text[:150] + "...")

        return contradictions

    def _check_visual_correlation(
        self, relationship: Relationship, video_intel: VideoIntelligence
    ) -> bool:
        """Check if relationship has visual correlation."""
        if not video_intel.transcript or not video_intel.transcript.segments:
            return False

        for segment in video_intel.transcript.segments:
            text = segment.get("text", "")

            # Check if segment mentions relationship and has visual indicators
            if self._segment_mentions_relationship(text, relationship) and any(
                indicator in text.lower() for indicator in self.visual_indicators
            ):
                return True

        return False

    # No conversion needed - working directly with enhanced Relationship model
