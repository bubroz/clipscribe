"""
Entity Quality Filter - Advanced Quality Enhancement for ClipScribe.

This module implements comprehensive quality filtering to address major issues in entity extraction:

QUALITY IMPROVEMENTS:
- Dynamic confidence calculation (replaces hardcoded 0.85 scores)
- Language detection and filtering (removes non-English noise)
- Semantic validation using context analysis
- False positive detection and removal
- Source attribution validation and correction
- Type consistency validation
- Context-aware confidence boosting

QUALITY METRICS:
- Pre/post-filtering statistics
- Confidence score distributions
- Language purity scores
- Semantic relevance scores
- False positive detection rates

This ensures ClipScribe produces high-quality, meaningful entity extraction 
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict
from dataclasses import dataclass

from ..models import Entity, VideoIntelligence

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Entity quality metrics for transparency and monitoring."""

    total_input_entities: int
    filtered_entities: int
    false_positives_removed: int
    language_filtered: int
    confidence_improved: int
    type_corrections: int
    source_corrections: int
    final_quality_score: float
    confidence_distribution: Dict[str, int]
    language_purity_score: float


@dataclass
class EntityQualityScore:
    """Detailed quality score for an entity."""

    original_confidence: float
    adjusted_confidence: float
    language_score: float
    context_score: float
    type_consistency_score: float
    semantic_relevance_score: float
    final_score: float
    quality_flags: List[str]


class EntityQualityFilter:
    """
    Advanced entity quality filtering system.

    QUALITY ENHANCEMENTS:
    - Replaces hardcoded confidence scores with dynamic calculation
    - Filters non-English entities to reduce noise
    - Validates semantic relevance in context
    - Corrects source attribution errors
    - Removes obvious false positives
    - Provides transparent quality metrics

    This transforms noisy entity extraction into high-quality intelligence.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.3,  # Lowered from 0.4 to be even more inclusive
        language_confidence_threshold: float = 0.2,  # Lowered from 0.3 to be much less strict
        enable_llm_validation: bool = False,
    ):
        """Initialize entity quality filter."""
        self.min_confidence_threshold = min_confidence_threshold
        self.language_confidence_threshold = language_confidence_threshold
        self.enable_llm_validation = enable_llm_validation

        # Language detection patterns (simple but effective)
        self.english_patterns = {
            "common_english_words": {
                "the",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "a",
                "an",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "can",
                "this",
                "that",
                "these",
                "those",
                "here",
                "there",
                "where",
                "when",
                "how",
                "why",
                "who",
                "what",
                "which",
                "whom",
                "whose",
                # Add more common words that might appear in simple content
                "me",
                "my",
                "you",
                "your",
                "he",
                "his",
                "she",
                "her",
                "it",
                "its",
                "we",
                "our",
                "they",
                "their",
                "zoo",
                "park",
                "home",
                "school",
                "work",
                "place",
                "time",
                "day",
                "year",
                "way",
                "man",
                "woman",
                "child",
                "person",
                "people",
                "thing",
                "things",
                "good",
                "bad",
                "new",
                "old",
                "big",
                "small",
                "great",
                "little",
                "go",
                "going",
                "come",
                "coming",
                "see",
                "look",
                "make",
                "get",
                "take",
                "give",
                "know",
                "think",
                "say",
                "said",
                "tell",
                "ask",
                "use",
                "find",
                "work",
                "call",
                "one",
                "two",
                "first",
                "last",
                "all",
                "some",
                "many",
                "few",
                "more",
                "most",
                "up",
                "down",
                "out",
                "over",
                "under",
                "about",
                "into",
                "through",
                "between",
            },
            "english_suffixes": {
                "ing",
                "ed",
                "er",
                "est",
                "ly",
                "tion",
                "sion",
                "ness",
                "ment",
                "ful",
                "less",
                "able",
                "ible",
                "ous",
                "ious",
                "al",
                "ial",
                "en",
                "fy",
                "ize",
                "ise",
            },
            "english_prefixes": {
                "un",
                "pre",
                "dis",
                "mis",
                "over",
                "under",
                "out",
                "up",
                "re",
                "anti",
                "de",
                "non",
                "in",
                "im",
                "il",
                "ir",
                "inter",
                "super",
                "sub",
                "trans",
                "ultra",
            },
        }

        # Non-English language patterns for filtering
        self.non_english_patterns = {
            "spanish_indicators": {
                # Remove common words that also appear in English
                # Only keep distinctly Spanish words
                "qué",
                "cómo",
                "dónde",
                "cuándo",
                "español",
                "señor",
                "señora",
                "mañana",
                "hasta",
                "después",
                "mientras",
                "ningún",
                "algún",
            },
            "french_indicators": {
                # Remove common words that also appear in English
                # Only keep distinctly French words
                "très",
                "après",
                "beaucoup",
                "maintenant",
                "aujourd'hui",
                "quelque",
                "même",
                "ça",
                "été",
                "être",
                "avoir",
            },
            "arabic_script": re.compile(r"[\u0600-\u06FF]"),
            "chinese_script": re.compile(r"[\u4e00-\u9fff]"),
            "cyrillic_script": re.compile(r"[\u0400-\u04FF]"),
            "japanese_script": re.compile(r"[\u3040-\u309f\u30a0-\u30ff]"),
            "korean_script": re.compile(r"[\uac00-\ud7af]"),
        }

        # False positive patterns
        self.false_positive_patterns = {
            "noise_phrases": {
                # Common transcription artifacts
                "uh",
                "um",
                "ah",
                "er",
                "mm",
                "hmm",
                # Remove overly generic filters that might catch real entities
                # Keep only true noise words
            },
            "partial_sentences": re.compile(r"^(uh|um|ah|er)\s", re.IGNORECASE),
            "single_letters": re.compile(r"^[a-zA-Z]$"),
            "special_chars_only": re.compile(r"^[^\w\s]+$"),
            "repeated_chars": re.compile(r"^(.)\1{4,}$"),  # Only filter if 5+ repeated chars
        }

        # Type validation patterns
        self.type_validation = {
            "PERSON": {
                "positive_indicators": {
                    "titles": {"mr", "mrs", "ms", "dr", "prof", "president", "senator", "general"},
                    "name_patterns": re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$"),
                    "common_names": {
                        "john",
                        "mary",
                        "james",
                        "sarah",
                        "michael",
                        "david",
                        "robert",
                    },
                },
                "negative_indicators": {
                    "organization_words": {"company", "corp", "inc", "llc", "agency", "department"},
                    "location_words": {"city", "state", "country", "building", "street", "avenue"},
                },
            },
            "ORGANIZATION": {
                "positive_indicators": {
                    "suffixes": {"inc", "corp", "llc", "ltd", "company", "agency", "department"},
                    "organization_types": {"university", "college", "hospital", "bank", "fund"},
                },
                "negative_indicators": {
                    "person_indicators": {"mr", "mrs", "ms", "dr"},
                    "location_indicators": {"city", "state", "country", "county"},
                },
            },
            "LOCATION": {
                "positive_indicators": {
                    "location_types": {"city", "state", "country", "county", "district", "region"},
                    "geographic_features": {"river", "mountain", "lake", "ocean", "sea", "bay"},
                },
                "negative_indicators": {
                    "person_indicators": {"mr", "mrs", "ms", "dr"},
                    "organization_indicators": {"inc", "corp", "llc", "company"},
                },
            },
        }

    async def filter_and_enhance_entities(
        self,
        entities: List[Entity],
        video_intel: VideoIntelligence,
        context_text: Optional[str] = None,
    ) -> Tuple[List[Entity], QualityMetrics]:
        """
        Comprehensive entity quality filtering and enhancement.

        Args:
            entities: Raw entities from extraction
            video_intel: Video intelligence for context
            context_text: Additional context for validation

        Returns:
            Tuple of (filtered_entities, quality_metrics)
        """
        logger.info(f" Starting entity quality enhancement for {len(entities)} entities")

        # Initialize metrics
        metrics = QualityMetrics(
            total_input_entities=len(entities),
            filtered_entities=0,
            false_positives_removed=0,
            language_filtered=0,
            confidence_improved=0,
            type_corrections=0,
            source_corrections=0,
            final_quality_score=0.0,
            confidence_distribution=defaultdict(int),
            language_purity_score=0.0,
        )

        if not entities:
            return [], metrics

        # Get context for validation
        if not context_text and video_intel.transcript:
            context_text = video_intel.transcript.full_text

        # Step 1: Remove obvious false positives
        step1_entities = self._remove_false_positives(entities, metrics)
        logger.info(f"Step 1: Removed {metrics.false_positives_removed} false positives")

        # Step 2: Language filtering
        step2_entities = self._filter_non_english_entities(step1_entities, metrics)
        logger.info(f"Step 2: Filtered {metrics.language_filtered} non-English entities")

        # Step 3: Dynamic confidence calculation
        step3_entities = await self._calculate_dynamic_confidence(
            step2_entities, context_text, metrics
        )
        logger.info(f"Step 3: Improved confidence for {metrics.confidence_improved} entities")

        # Step 4: Type validation and correction
        step4_entities = self._validate_and_correct_types(step3_entities, metrics)
        logger.info(f"Step 4: Corrected {metrics.type_corrections} entity types")

        # Step 5: Source attribution correction
        step5_entities = self._correct_source_attribution(step4_entities, metrics)
        logger.info(f"Step 5: Corrected {metrics.source_corrections} source attributions")

        # Step 6: Final quality threshold filtering
        final_entities = self._apply_final_quality_threshold(step5_entities, metrics)

        # Calculate final metrics
        metrics.filtered_entities = len(final_entities)
        metrics.final_quality_score = self._calculate_overall_quality_score(final_entities)
        metrics.confidence_distribution = self._calculate_confidence_distribution(final_entities)
        metrics.language_purity_score = self._calculate_language_purity(final_entities)

        logger.info(" Entity quality enhancement complete:")
        logger.info(f"    {metrics.total_input_entities} → {metrics.filtered_entities} entities")
        logger.info(f"    Quality score: {metrics.final_quality_score:.3f}")
        logger.info(f"    Language purity: {metrics.language_purity_score:.3f}")

        return final_entities, metrics

    def _remove_false_positives(
        self, entities: List[Entity], metrics: QualityMetrics
    ) -> List[Entity]:
        """Remove obvious false positives and noise."""
        filtered = []

        for entity in entities:
            is_false_positive = False

            # Check noise phrases
            if entity.entity.lower().strip() in self.false_positive_patterns["noise_phrases"]:
                is_false_positive = True

            # Check various patterns
            name_clean = entity.entity.strip()
            if (
                self.false_positive_patterns["partial_sentences"].match(name_clean)
                or self.false_positive_patterns["single_letters"].match(name_clean)
                or self.false_positive_patterns["special_chars_only"].match(name_clean)
                or self.false_positive_patterns["repeated_chars"].match(name_clean)
            ):
                is_false_positive = True

            # Check length thresholds
            if len(name_clean) < 2 or len(name_clean) > 100:
                is_false_positive = True

            # Check for excessive punctuation
            if not name_clean:
                is_false_positive = True
            else:
                punct_ratio = sum(1 for c in name_clean if not c.isalnum() and c != " ") / len(
                    name_clean
                )
                if punct_ratio > 0.5:
                    is_false_positive = True

            if is_false_positive:
                metrics.false_positives_removed += 1
            else:
                filtered.append(entity)

        return filtered

    def _filter_non_english_entities(
        self, entities: List[Entity], metrics: QualityMetrics
    ) -> List[Entity]:
        """Filter out entities that are likely not English using a combination of heuristics."""
        english_entities = []
        english_stopwords = {"the", "a", "in", "of", "to", "and", "is", "it", "for", "on"}

        for entity in entities:
            entity_text = entity.entity.lower()
            words = set(entity_text.split())

            # Heuristic 1: Filter if entity consists ONLY of stopwords.
            if words and words.issubset(english_stopwords):
                metrics.language_filtered += 1
                logger.debug(f"Filtered stopword entity: '{entity.entity}'")
                continue

            # Heuristic 2: Filter if the entity contains non-ASCII characters, which is a strong
            # indicator of a different language, especially for proper nouns.
            if not entity_text.isascii():
                metrics.language_filtered += 1
                logger.debug(f"Filtered non-ASCII entity: '{entity.entity}'")
                continue

            english_entities.append(entity)

        return english_entities

    def _calculate_language_score(self, text: str) -> float:
        """Calculate English language confidence score."""
        text_lower = text.lower()
        words = text_lower.split()

        if not words:
            return 0.0

        # Special handling for very short entities (1-2 words)
        if len(words) <= 2:
            # For short entities, be more lenient
            # Check if it's basic Latin alphabet
            if re.match(r"^[a-z\s]+$", text_lower):
                base_score = 0.7  # Start with higher base score for Latin alphabet

                # Boost if it contains common English words
                for word in words:
                    if word in self.english_patterns["common_english_words"]:
                        return 1.0  # Definitely English

                # Check for English patterns
                for word in words:
                    # Check suffixes
                    if any(
                        word.endswith(suffix)
                        for suffix in self.english_patterns["english_suffixes"]
                    ):
                        base_score += 0.2
                    # Check prefixes
                    if any(
                        word.startswith(prefix)
                        for prefix in self.english_patterns["english_prefixes"]
                    ):
                        base_score += 0.2

                # Check if it looks like a proper noun (capitalized)
                if text[0].isupper():
                    base_score += 0.1

                return min(1.0, base_score)
            else:
                # Contains non-Latin characters, check for non-English scripts
                if (
                    self.non_english_patterns["arabic_script"].search(text)
                    or self.non_english_patterns["chinese_script"].search(text)
                    or self.non_english_patterns["cyrillic_script"].search(text)
                    or self.non_english_patterns["japanese_script"].search(text)
                    or self.non_english_patterns["korean_script"].search(text)
                ):
                    return 0.0  # Definitely non-English script
                else:
                    # Mixed characters, be neutral
                    return 0.5

        # Check for English word indicators
        english_word_count = 0
        for word in words:
            # Common English words
            if word in self.english_patterns["common_english_words"]:
                english_word_count += 2

            # English suffixes
            if any(word.endswith(suffix) for suffix in self.english_patterns["english_suffixes"]):
                english_word_count += 1

            # English prefixes
            if any(word.startswith(prefix) for prefix in self.english_patterns["english_prefixes"]):
                english_word_count += 1

            # Basic English pattern (letters only, reasonable length)
            if re.match(r"^[a-z]+$", word) and 2 <= len(word) <= 15:
                english_word_count += 0.5

        # Check for non-English indicators
        non_english_penalty = 0.0
        for word in words:
            # Spanish indicators
            if word in self.non_english_patterns["spanish_indicators"]:
                non_english_penalty += 2

            # French indicators
            if word in self.non_english_patterns["french_indicators"]:
                non_english_penalty += 2

        # Check for non-Latin scripts
        if (
            self.non_english_patterns["arabic_script"].search(text)
            or self.non_english_patterns["chinese_script"].search(text)
            or self.non_english_patterns["cyrillic_script"].search(text)
            or self.non_english_patterns["japanese_script"].search(text)
            or self.non_english_patterns["korean_script"].search(text)
        ):
            non_english_penalty += 5

        # Calculate final score
        total_words = len(words)
        english_ratio = english_word_count / total_words
        penalty_ratio = non_english_penalty / total_words

        # Be more generous with scoring
        final_score = max(0.0, min(1.0, 0.3 + english_ratio - penalty_ratio))

        # Special boost for text that looks like English names/places
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", text):
            final_score = max(final_score, 0.8)

        return final_score

    async def _calculate_dynamic_confidence(
        self, entities: List[Entity], context_text: Optional[str], metrics: QualityMetrics
    ) -> List[Entity]:
        """Calculate dynamic confidence scores to replace hardcoded values."""
        enhanced_entities = []

        for entity in entities:
            # Calculate quality score
            quality_score = self._calculate_entity_quality_score(entity, context_text)

            # Determine if confidence was improved
            original_confidence = entity.confidence
            new_confidence = quality_score.final_score

            if abs(new_confidence - original_confidence) > 0.05:
                metrics.confidence_improved += 1

            # Create enhanced entity
            enhanced_entity = Entity(
                entity=entity.entity,
                type=entity.type,
                confidence=new_confidence,
                source=entity.source,
            )

            enhanced_entities.append(enhanced_entity)

        return enhanced_entities

    def _calculate_entity_quality_score(
        self, entity: Entity, context_text: Optional[str]
    ) -> EntityQualityScore:
        """Calculate comprehensive quality score for an entity."""

        # 1. Language score
        language_score = self._calculate_language_score(entity.entity)

        # 2. Context relevance score
        context_score = (
            self._calculate_context_relevance(entity, context_text) if context_text else 0.7
        )

        # 3. Type consistency score
        type_score = self._calculate_type_consistency(entity)

        # 4. Semantic relevance score
        semantic_score = self._calculate_semantic_relevance(entity)

        # Combine scores with weights
        weights = {"original": 0.3, "language": 0.2, "context": 0.2, "type": 0.15, "semantic": 0.15}

        final_score = (
            weights["original"] * entity.confidence
            + weights["language"] * language_score
            + weights["context"] * context_score
            + weights["type"] * type_score
            + weights["semantic"] * semantic_score
        )

        # Quality flags
        quality_flags = []
        if language_score < 0.7:
            quality_flags.append("low_language_score")
        if context_score < 0.5:
            quality_flags.append("low_context_relevance")
        if type_score < 0.6:
            quality_flags.append("type_inconsistency")
        if semantic_score < 0.5:
            quality_flags.append("low_semantic_relevance")

        return EntityQualityScore(
            original_confidence=entity.confidence,
            adjusted_confidence=final_score,
            language_score=language_score,
            context_score=context_score,
            type_consistency_score=type_score,
            semantic_relevance_score=semantic_score,
            final_score=final_score,
            quality_flags=quality_flags,
        )

    def _calculate_context_relevance(self, entity: Entity, context_text: str) -> float:
        """Calculate how relevant the entity is in the given context."""
        if not context_text:
            return 0.7  # Default neutral score

        entity_name_lower = entity.entity.lower()
        context_lower = context_text.lower()

        # Count occurrences
        occurrence_count = context_lower.count(entity_name_lower)

        # Context window analysis - check surrounding words
        context_quality = 0.0
        words = context_lower.split()
        total_words = len(words)

        for i, word in enumerate(words):
            if entity_name_lower in word:
                # Check surrounding words (±3 words)
                start_idx = max(0, i - 3)
                end_idx = min(total_words, i + 4)
                surrounding = " ".join(words[start_idx:end_idx])

                # Look for meaningful context indicators
                if any(
                    indicator in surrounding
                    for indicator in [
                        "said",
                        "announced",
                        "reported",
                        "according",
                        "spokesperson",
                        "president",
                        "ceo",
                        "director",
                        "official",
                        "minister",
                    ]
                ):
                    context_quality += 0.3

        # Normalize by occurrence count
        if occurrence_count > 0:
            context_quality = context_quality / occurrence_count

        # Combine occurrence frequency and context quality
        frequency_score = min(1.0, occurrence_count / 5)  # Cap at 5 occurrences

        return 0.6 * frequency_score + 0.4 * context_quality

    def _calculate_type_consistency(self, entity: Entity) -> float:
        """Calculate how consistent the entity type is with the entity name."""
        entity_type = entity.type.upper()
        entity_name_lower = entity.entity.lower()

        if entity_type in self.type_validation:
            type_config = self.type_validation[entity_type]

            # Check positive indicators
            positive_score = 0.0

            # Title matching for PERSON
            if entity_type == "PERSON":
                if "titles" in type_config["positive_indicators"]:
                    for title in type_config["positive_indicators"]["titles"]:
                        if title in entity_name_lower:
                            positive_score += 0.3

                # Name pattern matching
                if type_config["positive_indicators"]["name_patterns"].match(entity.entity):
                    positive_score += 0.4

            # Organization suffix matching
            elif entity_type == "ORGANIZATION":
                for suffix in type_config["positive_indicators"]["suffixes"]:
                    if entity_name_lower.endswith(suffix):
                        positive_score += 0.5

            # Check negative indicators
            negative_penalty = 0.0
            for neg_category, neg_indicators in type_config["negative_indicators"].items():
                for indicator in neg_indicators:
                    if indicator in entity_name_lower:
                        negative_penalty += 0.3

            return max(0.0, min(1.0, 0.5 + positive_score - negative_penalty))

        return 0.7  # Default neutral score for unknown types

    def _calculate_semantic_relevance(self, entity: Entity) -> float:
        """Calculate semantic relevance score based on entity characteristics."""
        name = entity.entity.strip()

        # Length-based scoring
        length_score = 1.0
        if len(name) < 3:
            length_score = 0.2
        elif len(name) > 50:
            length_score = 0.6

        # Capitalization patterns
        cap_score = 0.7  # Default
        if name.istitle():  # Proper noun capitalization
            cap_score = 1.0
        elif name.isupper() and len(name) <= 10:  # Acronyms
            cap_score = 0.9
        elif name.islower():
            cap_score = 0.3

        # Word structure
        words = name.split()
        structure_score = 0.7  # Default

        if len(words) == 1:
            # Single word - check if it looks like a name
            if re.match(r"^[A-Z][a-z]+$", name):
                structure_score = 0.8
        elif 2 <= len(words) <= 4:
            # Multiple words - good for names and organizations
            structure_score = 0.9
        elif len(words) > 4:
            # Too many words - might be a phrase
            structure_score = 0.5

        # Combine scores
        return 0.4 * length_score + 0.3 * cap_score + 0.3 * structure_score

    def _validate_and_correct_types(
        self, entities: List[Entity], metrics: QualityMetrics
    ) -> List[Entity]:
        """Validate and correct entity types based on patterns."""
        corrected_entities = []

        for entity in entities:
            corrected_type = self._suggest_type_correction(entity)

            if corrected_type != entity.type:
                metrics.type_corrections += 1
                corrected_entity = Entity(
                    entity=entity.entity,
                    type=corrected_type,
                    confidence=entity.confidence,
                    source=entity.source,
                )
                corrected_entities.append(corrected_entity)
            else:
                corrected_entities.append(entity)

        return corrected_entities

    def _suggest_type_correction(self, entity: Entity) -> str:
        """Suggest type correction based on entity name patterns."""
        name_lower = entity.entity.lower()

        # Person indicators
        person_indicators = [
            "mr",
            "mrs",
            "ms",
            "dr",
            "prof",
            "president",
            "senator",
            "general",
            "admiral",
        ]
        if any(indicator in name_lower for indicator in person_indicators):
            return "PERSON"

        # Organization indicators
        org_indicators = [
            "inc",
            "corp",
            "llc",
            "ltd",
            "company",
            "agency",
            "department",
            "university",
        ]
        if any(indicator in name_lower for indicator in org_indicators):
            return "ORGANIZATION"

        # Location indicators
        loc_indicators = [
            "city",
            "state",
            "country",
            "county",
            "district",
            "region",
            "street",
            "avenue",
        ]
        if any(indicator in name_lower for indicator in loc_indicators):
            return "LOCATION"

        return entity.type  # No correction needed

    def _correct_source_attribution(
        self, entities: List[Entity], metrics: QualityMetrics
    ) -> List[Entity]:
        """Correct source attribution for entities with 'Unknown' sources."""
        corrected_entities = []

        for entity in entities:
            source = entity.source or "Unknown"

            if source == "Unknown":
                # Try to infer source from other properties or patterns
                corrected_source = self._infer_source(entity)

                if corrected_source != "Unknown":
                    metrics.source_corrections += 1

                corrected_entity = Entity(
                    entity=entity.entity,
                    type=entity.type,
                    confidence=entity.confidence,
                    source=corrected_source,
                )
                corrected_entities.append(corrected_entity)
            else:
                corrected_entities.append(entity)

        return corrected_entities

    def _infer_source(self, entity: Entity) -> str:
        """Infer extraction source based on entity characteristics."""
        # Check confidence patterns
        if entity.confidence == 0.85:
            return "SpaCy"  # SpaCy commonly uses 0.85

        # Check name patterns
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", entity.entity):
            return "GLiNER"  # GLiNER good at proper nouns

        # Default inference
        return "Hybrid"

    def _apply_final_quality_threshold(
        self, entities: List[Entity], metrics: QualityMetrics
    ) -> List[Entity]:
        """Apply final quality threshold filtering."""
        return [entity for entity in entities if entity.confidence >= self.min_confidence_threshold]

    def _calculate_overall_quality_score(self, entities: List[Entity]) -> float:
        """Calculate overall quality score for the entity set."""
        if not entities:
            return 0.0

        total_confidence = sum(entity.confidence for entity in entities)
        avg_confidence = total_confidence / len(entities)

        # Factor in confidence distribution
        high_conf_count = sum(1 for e in entities if e.confidence > 0.8)
        high_conf_ratio = high_conf_count / len(entities)

        return 0.7 * avg_confidence + 0.3 * high_conf_ratio

    def _calculate_confidence_distribution(self, entities: List[Entity]) -> Dict[str, int]:
        """Calculate confidence score distribution."""
        distribution = defaultdict(int)

        for entity in entities:
            if entity.confidence >= 0.9:
                distribution["very_high"] += 1
            elif entity.confidence >= 0.8:
                distribution["high"] += 1
            elif entity.confidence >= 0.7:
                distribution["medium"] += 1
            elif entity.confidence >= 0.6:
                distribution["low"] += 1
            else:
                distribution["very_low"] += 1

        return dict(distribution)

    def _calculate_language_purity(self, entities: List[Entity]) -> float:
        """Calculate language purity score (higher = more English)."""
        if not entities:
            return 1.0

        english_scores = [self._calculate_language_score(entity.entity) for entity in entities]
        return sum(english_scores) / len(english_scores)

    def _detect_language(self, text: str) -> Dict[str, Any]:
        """
        Simple language detection based on character patterns.

        Args:
            text: Text to analyze

        Returns:
            Dict with language info
        """
        # Simple heuristic for language detection
        # Check for non-ASCII characters
        non_ascii_count = sum(1 for c in text if ord(c) > 127)
        total_chars = len(text)

        if total_chars == 0:
            return {
                "language": "unknown",
                "confidence": 0.0,
                "is_english": True,  # Default to true for empty
            }

        non_ascii_ratio = non_ascii_count / total_chars

        # Simple heuristics
        if non_ascii_ratio < 0.1:  # Less than 10% non-ASCII
            return {"language": "en", "confidence": 0.9, "is_english": True}
        elif non_ascii_ratio > 0.5:  # More than 50% non-ASCII
            return {"language": "other", "confidence": 0.7, "is_english": False}
        else:
            return {
                "language": "mixed",
                "confidence": 0.5,
                "is_english": True,  # Be lenient with mixed content
            }

    def tag_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Tag entities with language metadata instead of filtering.

        This is the NEW approach for trust_gemini mode - we tag entities
        with language information but don't remove them. Users can decide
        what to do with non-English entities.

        Args:
            entities: List of entities to tag

        Returns:
            Same list of entities (unmodified since Entity is immutable)
        """
        if entities is None:
            return None

        logger.info(f" Tagging {len(entities)} entities with language metadata")

        # Since Entity is a Pydantic model without a properties field,
        # we can't add language tags directly. Instead, we just log
        # the language information and return entities unchanged.

        non_english_count = 0
        for entity in entities:
            # Detect language
            lang_info = self._detect_language(entity.entity)

            # Log non-English entities (but don't filter)
            if not lang_info["is_english"]:
                non_english_count += 1
                logger.debug(
                    f"Non-English entity detected: '{entity.entity}' ({lang_info['language']}, conf: {lang_info['confidence']:.2f})"
                )

        logger.info(
            f" Tagged {len(entities)} entities - {non_english_count} non-English detected but not filtered"
        )
        return entities
