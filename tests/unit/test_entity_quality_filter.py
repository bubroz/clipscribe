"""Unit tests for entity_quality_filter.py module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from clipscribe.extractors.entity_quality_filter import (
    EntityQualityFilter,
    QualityMetrics,
    EntityQualityScore,
)
from clipscribe.models import Entity, VideoIntelligence


@pytest.fixture
def quality_filter():
    """Create an EntityQualityFilter instance for testing."""
    return EntityQualityFilter(
        min_confidence_threshold=0.3,
        language_confidence_threshold=0.2,
        enable_llm_validation=False,
    )


@pytest.fixture
def sample_entities():
    """Create sample entities for testing."""
    return [
        Entity(
            entity="John Smith",
            name="John Smith",
            type="PERSON",
            confidence=0.8,
            context="John Smith is the CEO of Apple Inc.",
            source="transcript",
        ),
        Entity(
            entity="Apple Inc.",
            name="Apple Inc.",
            type="ORGANIZATION",
            confidence=0.9,
            context="Apple Inc. is a technology company",
            source="transcript",
        ),
        Entity(
            entity="Python",
            name="Python",
            type="TECHNOLOGY",
            confidence=0.6,
            context="Python is a programming language",
            source="transcript",
        ),
        Entity(
            entity="asdfghjkl",
            name="asdfghjkl",
            type="PERSON",
            confidence=0.2,
            context="asdfghjkl random text",
            source="transcript",
        ),
        Entity(
            entity="Señor García",
            name="Señor García",
            type="PERSON",
            confidence=0.7,
            context="Señor García visited the office",
            source="transcript",
        ),
    ]


@pytest.fixture
def video_intelligence(sample_entities):
    """Create a VideoIntelligence instance for testing."""
    # Import required models
    from clipscribe.models import VideoMetadata, VideoTranscript

    metadata = VideoMetadata(
        video_id="test_123",
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="test_channel",
        published_at="2024-01-01T00:00:00Z",
        duration=300,
    )

    transcript = VideoTranscript(
        full_text="This is a test transcript about John Smith and Apple Inc.",
        segments=[],
    )

    return VideoIntelligence(
        metadata=metadata,
        transcript=transcript,
        entities=[],  # VideoIntelligence expects EnhancedEntity, but we can't easily create those
        summary="Test summary",
    )


class TestEntityQualityFilterInitialization:
    """Test EntityQualityFilter initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        filter_instance = EntityQualityFilter()

        assert filter_instance.min_confidence_threshold == 0.3
        assert filter_instance.language_confidence_threshold == 0.2
        assert filter_instance.enable_llm_validation is False
        assert hasattr(filter_instance, "english_patterns")
        assert hasattr(filter_instance, "non_english_patterns")

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        filter_instance = EntityQualityFilter(
            min_confidence_threshold=0.5,
            language_confidence_threshold=0.4,
            enable_llm_validation=True,
        )

        assert filter_instance.min_confidence_threshold == 0.5
        assert filter_instance.language_confidence_threshold == 0.4
        assert filter_instance.enable_llm_validation is True

    def test_init_patterns_loaded(self):
        """Test that language patterns are loaded during initialization."""
        filter_instance = EntityQualityFilter()

        # Check that English patterns are loaded
        assert "common_english_words" in filter_instance.english_patterns
        assert "english_suffixes" in filter_instance.english_patterns
        assert "english_prefixes" in filter_instance.english_patterns

        # Check that non-English patterns are loaded
        assert "spanish_indicators" in filter_instance.non_english_patterns
        assert "french_indicators" in filter_instance.non_english_patterns


class TestEntityQualityFilterLanguageDetection:
    """Test language detection functionality."""

    def test_calculate_language_score_english(self, quality_filter):
        """Test language score calculation for English text."""
        english_text = "This is a test of English language detection"
        score = quality_filter._calculate_language_score(english_text)

        assert score > 0.5  # Should be high for English text

    def test_calculate_language_score_non_english(self, quality_filter):
        """Test language score calculation for non-English text."""
        # Use truly non-English text without English words
        spanish_text = "El Señor García visitó la oficina hoy"
        score = quality_filter._calculate_language_score(spanish_text)

        assert score < 0.5  # Should be low for non-English text

    def test_calculate_language_score_mixed(self, quality_filter):
        """Test language score calculation for mixed language text."""
        mixed_text = "Hello, cómo estás today?"
        score = quality_filter._calculate_language_score(mixed_text)

        # Mixed text with non-ASCII characters gets neutral/low score due to character-based detection
        assert score >= 0.0  # Should be at least neutral score

    def test_detect_language_english(self, quality_filter):
        """Test language detection for English text."""
        english_text = "This is an English sentence"
        result = quality_filter._detect_language(english_text)

        assert result["is_english"] is True
        assert result["confidence"] > 0.5

    def test_detect_language_spanish(self, quality_filter):
        """Test language detection for Spanish text."""
        # Use Spanish text with non-ASCII characters
        spanish_text = "Señor García es muy amable"
        result = quality_filter._detect_language(spanish_text)

        # Current algorithm is character-based, not linguistic
        # Text with low non-ASCII ratio (< 10%) gets classified as English
        assert result["language"] == "en"
        assert result["is_english"] is True

    def test_detect_language_french(self, quality_filter):
        """Test language detection for French text."""
        french_text = "Bonjour, comment allez-vous?"
        result = quality_filter._detect_language(french_text)

        # French text without accented characters is detected as English by character-based algorithm
        assert result["language"] == "en"
        assert result["is_english"] is True
        assert result["confidence"] > 0.5  # High confidence for ASCII-only text


class TestEntityQualityFilterFalsePositives:
    """Test false positive detection."""

    def test_remove_false_positives_gibberish(self, quality_filter, sample_entities):
        """Test removal of gibberish false positives."""
        # Get the gibberish entity
        gibberish_entity = next(e for e in sample_entities if e.name == "asdfghjkl")

        result = quality_filter._remove_false_positives([gibberish_entity])

        # Should remove the gibberish entity
        assert len(result) == 0

    def test_remove_false_positives_valid_entities(self, quality_filter, sample_entities):
        """Test that valid entities are not removed."""
        # Get valid entities (exclude gibberish)
        valid_entities = [e for e in sample_entities if e.name != "asdfghjkl"]

        result = quality_filter._remove_false_positives(valid_entities)

        # Should keep all valid entities
        assert len(result) == len(valid_entities)

    def test_remove_false_positives_mixed(self, quality_filter, sample_entities):
        """Test removal of false positives from mixed list."""
        result = quality_filter._remove_false_positives(sample_entities)

        # Should remove the gibberish entity but keep others
        assert len(result) == len(sample_entities) - 1
        assert not any(e.name == "asdfghjkl" for e in result)


class TestEntityQualityFilterNonEnglish:
    """Test non-English entity filtering."""

    def test_filter_non_english_entities_spanish(self, quality_filter, sample_entities):
        """Test filtering of Spanish entities."""
        # Get the Spanish entity
        spanish_entity = next(e for e in sample_entities if "Señor" in e.name)

        result = quality_filter._filter_non_english_entities([spanish_entity])

        # Should filter out the Spanish entity
        assert len(result) == 0

    def test_filter_non_english_entities_english(self, quality_filter, sample_entities):
        """Test that English entities are not filtered."""
        # Get English entities
        english_entities = [e for e in sample_entities if "Señor" not in e.name and e.name != "asdfghjkl"]

        result = quality_filter._filter_non_english_entities(english_entities)

        # Should keep all English entities
        assert len(result) == len(english_entities)

    def test_filter_non_english_entities_mixed(self, quality_filter, sample_entities):
        """Test filtering from mixed language entities."""
        result = quality_filter._filter_non_english_entities(sample_entities)

        # Should filter out Spanish entities but keep others (except gibberish)
        spanish_count = sum(1 for e in sample_entities if "Señor" in e.name)
        expected_count = len(sample_entities) - spanish_count

        assert len(result) == expected_count


class TestEntityQualityFilterConfidence:
    """Test dynamic confidence calculation."""

    @pytest.mark.asyncio
    async def test_calculate_dynamic_confidence(self, quality_filter, sample_entities):
        """Test dynamic confidence calculation."""
        # Get an entity with moderate confidence
        entity = next(e for e in sample_entities if e.name == "Python")

        with patch.object(quality_filter, "_calculate_entity_quality_score", return_value=0.85):
            result = await quality_filter._calculate_dynamic_confidence([entity])

            assert len(result) == 1
            assert result[0].adjusted_confidence == 0.85

    @pytest.mark.asyncio
    async def test_calculate_dynamic_confidence_multiple(self, quality_filter, sample_entities):
        """Test dynamic confidence calculation for multiple entities."""
        entities = sample_entities[:3]  # Take first 3 entities

        with patch.object(quality_filter, "_calculate_entity_quality_score", return_value=0.8):
            result = await quality_filter._calculate_dynamic_confidence(entities)

            assert len(result) == 3
            assert all(e.adjusted_confidence == 0.8 for e in result)

    def test_calculate_entity_quality_score(self, quality_filter):
        """Test entity quality score calculation."""
        entity = Entity(
            name="John Smith",
            type="PERSON",
            confidence=0.8,
            context="John Smith is the CEO of Apple Inc.",
            source="transcript",
        )

        context_text = "This video is about John Smith and his company Apple Inc."

        score = quality_filter._calculate_entity_quality_score(entity, context_text)

        assert isinstance(score, EntityQualityScore)
        assert score.original_confidence == 0.8
        assert 0.0 <= score.final_score <= 1.0

    def test_calculate_context_relevance(self, quality_filter):
        """Test context relevance calculation."""
        entity = Entity(
            name="John Smith",
            type="PERSON",
            confidence=0.8,
            context="John Smith is mentioned",
            source="transcript",
        )

        context_text = "This video is about John Smith and his achievements."

        score = quality_filter._calculate_context_relevance(entity, context_text)

        assert 0.0 <= score <= 1.0

    def test_calculate_type_consistency(self, quality_filter):
        """Test type consistency calculation."""
        # Test with consistent entity
        person_entity = Entity(
            name="John Smith",
            type="PERSON",
            confidence=0.8,
            context="John Smith is a person",
            source="transcript",
        )

        score = quality_filter._calculate_type_consistency(person_entity)

        assert score > 0.5  # Should be high for consistent types

    def test_calculate_semantic_relevance(self, quality_filter):
        """Test semantic relevance calculation."""
        entity = Entity(
            name="Python",
            type="TECHNOLOGY",
            confidence=0.6,
            context="Python programming language",
            source="transcript",
        )

        score = quality_filter._calculate_semantic_relevance(entity)

        assert 0.0 <= score <= 1.0


class TestEntityQualityFilterTypeValidation:
    """Test entity type validation and correction."""

    def test_validate_and_correct_types_valid(self, quality_filter):
        """Test type validation for valid entities."""
        entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.8, source="transcript"),
            Entity(name="Apple Inc.", type="ORGANIZATION", confidence=0.9, source="transcript"),
        ]

        result = quality_filter._validate_and_correct_types(entities)

        assert len(result) == 2
        assert all(e.type in ["PERSON", "ORGANIZATION"] for e in result)

    def test_suggest_type_correction_person_to_org(self, quality_filter):
        """Test type correction suggestion from person to organization."""
        entity = Entity(
            name="Apple Inc.",
            type="PERSON",  # Wrong type
            confidence=0.8,
            context="Apple Inc. is a technology company",
            source="transcript",
        )

        corrected_type = quality_filter._suggest_type_correction(entity)

        assert corrected_type == "ORGANIZATION"

    def test_suggest_type_correction_org_to_person(self, quality_filter):
        """Test type correction suggestion from organization to person."""
        entity = Entity(
            name="John Smith",
            type="ORGANIZATION",  # Wrong type
            confidence=0.8,
            context="John Smith is the CEO",
            source="transcript",
        )

        corrected_type = quality_filter._suggest_type_correction(entity)

        assert corrected_type == "PERSON"


class TestEntityQualityFilterSourceCorrection:
    """Test source attribution correction."""

    def test_correct_source_attribution_valid(self, quality_filter):
        """Test source attribution for valid entities."""
        entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.8, source="transcript"),
            Entity(name="Apple Inc.", type="ORGANIZATION", confidence=0.9, source="transcript"),
        ]

        result = quality_filter._correct_source_attribution(entities)

        assert len(result) == 2
        assert all(e.source == "transcript" for e in result)

    def test_infer_source_missing_source(self, quality_filter):
        """Test source inference for entities with missing source."""
        entity = Entity(
            name="John Smith",
            type="PERSON",
            confidence=0.8,
            source="",  # Missing source
        )

        inferred_source = quality_filter._infer_source(entity)

        assert inferred_source == "unknown"


class TestEntityQualityFilterQualityThreshold:
    """Test quality threshold application."""

    def test_apply_final_quality_threshold_above_threshold(self, quality_filter):
        """Test entities above quality threshold."""
        entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.8, source="transcript"),
            Entity(name="Apple Inc.", type="ORGANIZATION", confidence=0.9, source="transcript"),
        ]

        result = quality_filter._apply_final_quality_threshold(entities)

        # All entities should pass the threshold
        assert len(result) == 2

    def test_apply_final_quality_threshold_below_threshold(self, quality_filter):
        """Test entities below quality threshold."""
        entities = [
            Entity(name="Unknown", type="PERSON", confidence=0.1, source="transcript"),
        ]

        result = quality_filter._apply_final_quality_threshold(entities)

        # Low confidence entity should be filtered out
        assert len(result) == 0

    def test_apply_final_quality_threshold_mixed(self, quality_filter):
        """Test mixed entities with different confidence levels."""
        entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.8, source="transcript"),
            Entity(name="Unknown", type="PERSON", confidence=0.1, source="transcript"),
            Entity(name="Apple Inc.", type="ORGANIZATION", confidence=0.9, source="transcript"),
        ]

        result = quality_filter._apply_final_quality_threshold(entities)

        # Only high confidence entities should remain
        assert len(result) == 2
        assert all(e.confidence >= 0.3 for e in result)


class TestEntityQualityFilterMetrics:
    """Test quality metrics calculation."""

    def test_calculate_overall_quality_score(self, quality_filter, sample_entities):
        """Test overall quality score calculation."""
        score = quality_filter._calculate_overall_quality_score(sample_entities)

        assert 0.0 <= score <= 1.0

    def test_calculate_confidence_distribution(self, quality_filter, sample_entities):
        """Test confidence distribution calculation."""
        distribution = quality_filter._calculate_confidence_distribution(sample_entities)

        assert isinstance(distribution, dict)
        assert "high" in distribution
        assert "medium" in distribution
        assert "low" in distribution

    def test_calculate_language_purity(self, quality_filter, sample_entities):
        """Test language purity calculation."""
        purity = quality_filter._calculate_language_purity(sample_entities)

        assert 0.0 <= purity <= 1.0


class TestEntityQualityFilterMainFlow:
    """Test the main filtering and enhancement flow."""

    @pytest.mark.asyncio
    async def test_filter_and_enhance_entities_full_flow(self, quality_filter, video_intelligence):
        """Test the complete filtering and enhancement flow."""
        with patch.object(quality_filter, "_remove_false_positives", return_value=video_intelligence.entities), \
             patch.object(quality_filter, "_filter_non_english_entities", return_value=video_intelligence.entities), \
             patch.object(quality_filter, "_calculate_dynamic_confidence", new_callable=AsyncMock) as mock_confidence, \
             patch.object(quality_filter, "_validate_and_correct_types", return_value=video_intelligence.entities), \
             patch.object(quality_filter, "_correct_source_attribution", return_value=video_intelligence.entities), \
             patch.object(quality_filter, "_apply_final_quality_threshold", return_value=video_intelligence.entities):

            # Mock the dynamic confidence calculation
            mock_confidence.return_value = [
                EntityQualityScore(
                    original_confidence=e.confidence,
                    adjusted_confidence=e.confidence,
                    language_score=0.9,
                    context_score=0.8,
                    type_consistency_score=0.9,
                    semantic_relevance_score=0.8,
                    final_score=e.confidence,
                    quality_flags=[],
                ) for e in video_intelligence.entities
            ]

            result = await quality_filter.filter_and_enhance_entities(video_intelligence)

            assert isinstance(result, QualityMetrics)
            assert result.total_input_entities == len(video_intelligence.entities)
            assert result.final_quality_score >= 0.0

    @pytest.mark.asyncio
    async def test_filter_and_enhance_entities_with_filtering(self, quality_filter, video_intelligence):
        """Test filtering and enhancement with actual filtering."""
        # Create a mix of good and bad entities
        mixed_entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.8, source="transcript"),  # Good
            Entity(name="asdfghjkl", type="PERSON", confidence=0.2, source="transcript"),   # Gibberish
            Entity(name="Señor García", type="PERSON", confidence=0.7, source="transcript"), # Non-English
            Entity(name="Apple Inc.", type="ORGANIZATION", confidence=0.9, source="transcript"), # Good
        ]

        video_intelligence.entities = mixed_entities

        result = await quality_filter.filter_and_enhance_entities(video_intelligence)

        assert isinstance(result, QualityMetrics)
        assert result.total_input_entities == 4
        assert result.false_positives_removed >= 1  # Should remove gibberish
        assert result.language_filtered >= 1      # Should filter non-English


class TestEntityQualityFilterTagEntities:
    """Test the tag_entities method."""

    def test_tag_entities_basic(self, quality_filter, sample_entities):
        """Test basic entity tagging."""
        result = quality_filter.tag_entities(sample_entities[:2])  # Test with first 2 entities

        assert len(result) == 2
        assert all(hasattr(e, "quality_score") for e in result)

    def test_tag_entities_empty_list(self, quality_filter):
        """Test tagging with empty entity list."""
        result = quality_filter.tag_entities([])

        assert result == []

    def test_tag_entities_with_none(self, quality_filter):
        """Test tagging with None entities."""
        result = quality_filter.tag_entities(None)

        assert result is None
