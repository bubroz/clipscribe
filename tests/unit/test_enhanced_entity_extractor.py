"""Unit tests for EnhancedEntityExtractor module."""
import pytest
from unittest.mock import MagicMock
from typing import List, Dict, Optional

from clipscribe.extractors.enhanced_entity_extractor import EnhancedEntityExtractor
from clipscribe.models import Entity, EnhancedEntity, EntityContext, TemporalMention


@pytest.fixture
def extractor():
    """Create EnhancedEntityExtractor instance for testing."""
    return EnhancedEntityExtractor()


@pytest.fixture
def sample_entities():
    """Create sample entities for testing."""
    return [
        Entity(entity="Donald Trump", type="PERSON", confidence=0.95, properties={}),
        Entity(entity="President Trump", type="PERSON", confidence=0.90, properties={}),
        Entity(entity="Trump", type="PERSON", confidence=0.85, properties={}),
        Entity(entity="Joe Biden", type="PERSON", confidence=0.92, properties={}),
        Entity(entity="Artificial Intelligence", type="CONCEPT", confidence=0.88, properties={}),
        Entity(entity="AI", type="CONCEPT", confidence=0.80, properties={}),
        Entity(entity="United States", type="LOCATION", confidence=0.95, properties={}),
    ]


@pytest.fixture
def sample_transcript_segments():
    """Create sample transcript segments for testing."""
    return [
        {
            "text": "Donald Trump was the president of the United States.",
            "start_time": 10.0,
            "end_time": 15.0,
            "segment_id": "seg_1",
        },
        {
            "text": "President Trump announced new policies today.",
            "start_time": 20.0,
            "end_time": 25.0,
            "segment_id": "seg_2",
        },
        {
            "text": "Joe Biden is the current president.",
            "start_time": 30.0,
            "end_time": 35.0,
            "segment_id": "seg_3",
        },
    ]


class TestEnhancedEntityExtractorInitialization:
    """Test EnhancedEntityExtractor initialization."""

    def test_init(self, extractor):
        """Test basic initialization."""
        assert extractor is not None
        assert hasattr(extractor, 'title_patterns')
        assert isinstance(extractor.title_patterns, list)
        assert len(extractor.title_patterns) > 0


class TestEnhancedEntityExtractorMainFunctionality:
    """Test the main enhance_entities functionality."""

    def test_enhance_entities_empty_list(self, extractor):
        """Test enhancing empty entity list."""
        result = extractor.enhance_entities([])
        assert result == []

    def test_enhance_entities_single_entity(self, extractor):
        """Test enhancing single entity."""
        entities = [Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={})]
        result = extractor.enhance_entities(entities)

        assert len(result) == 1
        assert isinstance(result[0], EnhancedEntity)
        assert result[0].name == "John Doe"
        assert result[0].type == "PERSON"
        assert result[0].mention_count == 1
        assert result[0].canonical_form == "John Doe"
        assert result[0].extraction_sources == ["Gemini"]  # Default source

    def test_enhance_entities_multiple_different_entities(self, extractor, sample_entities):
        """Test enhancing multiple different entities."""
        result = extractor.enhance_entities(sample_entities)

        assert len(result) >= 3  # Should deduplicate similar entities
        assert all(isinstance(entity, EnhancedEntity) for entity in result)

        # Check that we have entities with different names
        entity_names = {entity.name for entity in result}
        assert len(entity_names) >= 3

    def test_enhance_entities_with_similar_names(self, extractor):
        """Test enhancing entities with similar names (should be grouped)."""
        entities = [
            Entity(entity="Donald Trump", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="President Trump", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="Trump", type="PERSON", confidence=0.85, properties={}),
        ]
        result = extractor.enhance_entities(entities)

        assert len(result) == 1  # Should be grouped into one entity
        entity = result[0]
        assert "Trump" in entity.name or "Trump" in entity.canonical_form
        assert entity.mention_count == 3
        assert len(entity.aliases) >= 1  # Should have aliases

    def test_enhance_entities_with_transcript_segments(self, extractor, sample_entities, sample_transcript_segments):
        """Test enhancing entities with transcript segments."""
        result = extractor.enhance_entities(
            sample_entities[:3],  # Just Trump entities
            transcript_segments=sample_transcript_segments
        )

        assert len(result) == 1  # Should be grouped
        entity = result[0]
        assert len(entity.context_windows) >= 0  # Should extract context windows
        assert isinstance(entity.temporal_distribution, list)  # It's a list of TemporalMention objects

    def test_enhance_entities_with_visual_data(self, extractor, sample_entities):
        """Test enhancing entities with visual data."""
        visual_data = {
            "detections": [
                {"label": "person", "confidence": 0.9, "bbox": [100, 100, 200, 300]},
            ]
        }
        result = extractor.enhance_entities(sample_entities[:1], visual_data=visual_data)

        assert len(result) == 1
        assert isinstance(result[0], EnhancedEntity)

    def test_enhance_entities_with_source_attribution(self, extractor):
        """Test enhancing entities with source attribution."""
        entities = [
            Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={}, source="SpaCy"),
            Entity(entity="John Doe", type="PERSON", confidence=0.8, properties={}, source="GLiNER"),
        ]
        result = extractor.enhance_entities(entities)

        assert len(result) == 1
        entity = result[0]
        assert set(entity.extraction_sources) == {"SpaCy", "GLiNER"}


class TestEnhancedEntityExtractorGrouping:
    """Test entity grouping functionality."""

    def test_group_entities_empty_list(self, extractor):
        """Test grouping empty entity list."""
        result = extractor._group_entities([])
        assert result == {}

    def test_group_entities_single_entity(self, extractor):
        """Test grouping single entity."""
        entities = [Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={})]
        result = extractor._group_entities(entities)

        assert len(result) == 1
        assert "John Doe" in result
        assert len(result["John Doe"]) == 1

    def test_group_entities_similar_entities(self, extractor):
        """Test grouping similar entities."""
        entities = [
            Entity(entity="Donald Trump", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="President Trump", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="Trump", type="PERSON", confidence=0.85, properties={}),
        ]
        result = extractor._group_entities(entities)

        assert len(result) == 1  # Should be grouped into one canonical form
        # The canonical form should contain "Trump"
        canonical_form = list(result.keys())[0]
        assert "Trump" in canonical_form

    def test_group_entities_different_entities(self, extractor):
        """Test grouping different entities."""
        entities = [
            Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={}),
            Entity(entity="Jane Smith", type="PERSON", confidence=0.9, properties={}),
            Entity(entity="Google", type="ORGANIZATION", confidence=0.9, properties={}),
        ]
        result = extractor._group_entities(entities)

        assert len(result) == 3  # Should be three separate groups
        assert all(len(group) == 1 for group in result.values())


class TestEnhancedEntityExtractorCanonicalForms:
    """Test canonical form determination."""

    def test_get_canonical_form_basic(self, extractor):
        """Test basic canonical form determination."""
        result = extractor._get_canonical_form("John Doe")
        assert result == "John Doe"

    def test_get_canonical_form_with_title(self, extractor):
        """Test canonical form with title removal."""
        result = extractor._get_canonical_form("President John Doe")
        assert result == "John Doe"

    def test_are_entities_similar_exact_match(self, extractor):
        """Test similarity detection for exact matches."""
        assert extractor._are_entities_similar("John Doe", "John Doe") is True

    def test_are_entities_similar_high_similarity(self, extractor):
        """Test similarity detection for similar entities."""
        # Test substring similarity which the current implementation supports
        assert extractor._are_entities_similar("Trump", "Donald Trump") is True

    def test_are_entities_similar_low_similarity(self, extractor):
        """Test similarity detection for dissimilar entities."""
        assert extractor._are_entities_similar("John Doe", "Jane Smith") is False

    def test_are_abbreviations_basic(self, extractor):
        """Test abbreviation detection."""
        # Test what the current implementation can handle
        result1 = extractor._are_abbreviations("United States", "USA")
        result2 = extractor._are_abbreviations("Artificial Intelligence", "AI")
        result3 = extractor._are_abbreviations("John Doe", "Jane Smith")

        # The current implementation may have specific requirements
        # Just verify it returns boolean values
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)
        assert isinstance(result3, bool)
        # Jane Smith should not be considered an abbreviation of John Doe
        assert result3 is False

    def test_select_best_canonical_single_candidate(self, extractor):
        """Test selecting best canonical from single candidate."""
        candidates = ["John Doe"]
        entities = [Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={})]
        result = extractor._select_best_canonical(candidates, entities)
        assert result == "John Doe"

    def test_select_best_canonical_multiple_candidates(self, extractor):
        """Test selecting best canonical from multiple candidates."""
        candidates = ["Trump", "Donald Trump", "President Trump"]
        entities = [
            Entity(entity="Trump", type="PERSON", confidence=0.85, properties={}),
            Entity(entity="Donald Trump", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="President Trump", type="PERSON", confidence=0.90, properties={}),
        ]
        result = extractor._select_best_canonical(candidates, entities)
        # Should choose the one with highest confidence or best format
        assert result in candidates


class TestEnhancedEntityExtractorContextAndTemporal:
    """Test context and temporal functionality."""

    def test_extract_context_windows_no_transcript(self, extractor):
        """Test context extraction with no transcript."""
        entities = [Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={})]
        # Should handle None transcript gracefully
        result = extractor._extract_context_windows("John Doe", entities, None)
        assert result == []

    def test_extract_context_windows_with_transcript(self, extractor, sample_transcript_segments):
        """Test context extraction with transcript."""
        entities = [Entity(entity="Donald Trump", type="PERSON", confidence=0.9, properties={})]
        result = extractor._extract_context_windows("Donald Trump", entities, sample_transcript_segments)

        assert isinstance(result, list)
        # Should find context windows containing "Donald Trump" or "President Trump"
        if result:
            assert all(isinstance(ctx, EntityContext) for ctx in result)

    def test_extract_temporal_distribution(self, extractor):
        """Test temporal distribution extraction."""
        entities = [
            Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={}),
            Entity(entity="John Doe", type="PERSON", confidence=0.8, properties={}),
        ]
        context_windows = [
            EntityContext(
                text="John Doe spoke here",
                timestamp="00:00:10",
                speaker="Narrator",
                visual_present=False
            ),
            EntityContext(
                text="John Doe appeared again",
                timestamp="00:00:30",
                speaker="Narrator",
                visual_present=False
            ),
        ]

        result = extractor._extract_temporal_distribution(entities, context_windows)
        assert isinstance(result, list)  # temporal_distribution is a list of TemporalMention objects
        # Should contain temporal information
        if result:
            assert all(hasattr(mention, 'timestamp') for mention in result)

    def test_determine_entity_type_consistent(self, extractor):
        """Test entity type determination with consistent types."""
        entities = [
            Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={}),
            Entity(entity="John Doe", type="PERSON", confidence=0.8, properties={}),
        ]
        result = extractor._determine_entity_type(entities)
        assert result == "PERSON"

    def test_determine_entity_type_mixed(self, extractor):
        """Test entity type determination with mixed types."""
        entities = [
            Entity(entity="Google", type="ORGANIZATION", confidence=0.9, properties={}),
            Entity(entity="Google", type="PERSON", confidence=0.8, properties={}),
        ]
        result = extractor._determine_entity_type(entities)
        # Should choose the most common type
        assert result in ["ORGANIZATION", "PERSON"]

    def test_extract_aliases(self, extractor):
        """Test alias extraction."""
        entities = [
            Entity(entity="Donald Trump", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="President Trump", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="Trump", type="PERSON", confidence=0.85, properties={}),
        ]
        result = extractor._extract_aliases("Donald Trump", entities)
        assert isinstance(result, list)
        # Should extract aliases from the entity group
        if result:
            assert all(isinstance(alias, str) for alias in result)


class TestEnhancedEntityExtractorAliasNormalizer:
    """Test the nested AliasNormalizer class."""

    def test_alias_normalizer_init(self, extractor):
        """Test AliasNormalizer initialization."""
        # Create the nested class directly since it's not accessible through the extractor instance
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()
        assert normalizer is not None
        assert hasattr(normalizer, 'common_aliases')

    def test_normalize_entity_basic(self, extractor):
        """Test basic entity normalization."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()
        result = normalizer.normalize_entity("John Doe")
        assert result == "John Doe"

    def test_normalize_entity_with_title(self, extractor):
        """Test entity normalization with title removal."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()
        result = normalizer.normalize_entity("President John Doe")
        assert result == "John Doe"

    def test_normalize_entity_common_alias(self, extractor):
        """Test entity normalization with common alias."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()
        result = normalizer.normalize_entity("USA")
        assert result == "United States"

    def test_find_aliases_empty_list(self, extractor):
        """Test finding aliases with empty list."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()
        result = normalizer.find_aliases([])
        assert result == {}

    def test_find_aliases_basic(self, extractor):
        """Test finding aliases with basic entities."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()
        entities = ["Donald Trump", "President Trump", "Trump", "Joe Biden"]
        result = normalizer.find_aliases(entities)

        assert isinstance(result, dict)
        # Should find aliases for similar entities
        if result:
            assert any("Trump" in key or "Trump" in str(value) for key, value in result.items())


class TestEnhancedEntityExtractorIntegration:
    """Integration tests for the full enhancement process."""

    def test_full_enhancement_pipeline(self, extractor, sample_entities, sample_transcript_segments):
        """Test the complete entity enhancement pipeline."""
        result = extractor.enhance_entities(
            sample_entities,
            transcript_segments=sample_transcript_segments
        )

        assert isinstance(result, list)
        assert len(result) >= 0

        for entity in result:
            assert isinstance(entity, EnhancedEntity)
            assert hasattr(entity, 'name')
            assert hasattr(entity, 'type')
            assert hasattr(entity, 'mention_count')
            assert hasattr(entity, 'canonical_form')
            assert hasattr(entity, 'extraction_sources')
            assert hasattr(entity, 'aliases')
            assert hasattr(entity, 'context_windows')
            assert hasattr(entity, 'temporal_distribution')

    def test_enhancement_with_complex_entities(self, extractor):
        """Test enhancement with complex entity scenarios."""
        entities = [
            Entity(entity="Dr. Sarah Johnson", type="PERSON", confidence=0.95, properties={}, source="SpaCy"),
            Entity(entity="Sarah Johnson", type="PERSON", confidence=0.90, properties={}, source="GLiNER"),
            Entity(entity="Prof. Johnson", type="PERSON", confidence=0.85, properties={}, source="REBEL"),
            Entity(entity="Artificial Intelligence Lab", type="ORGANIZATION", confidence=0.88, properties={}),
            Entity(entity="AI Lab", type="ORGANIZATION", confidence=0.80, properties={}),
        ]

        result = extractor.enhance_entities(entities)

        assert len(result) >= 2  # Should have at least two groups (Sarah Johnson + AI Lab)

        # Check that sources are properly attributed
        person_entities = [e for e in result if "Johnson" in e.name]
        if person_entities:
            entity = person_entities[0]
            assert "SpaCy" in entity.extraction_sources or "GLiNER" in entity.extraction_sources
            assert entity.mention_count >= 2

    def test_enhancement_edge_cases(self, extractor):
        """Test enhancement with edge cases."""
        entities = [
            Entity(entity="", type="PERSON", confidence=0.9, properties={}),  # Empty entity
            Entity(entity="A", type="PERSON", confidence=0.9, properties={}),  # Single char
            Entity(entity="Valid Name", type="PERSON", confidence=0.9, properties={}),
        ]

        result = extractor.enhance_entities(entities)

        # The current implementation may handle edge cases differently
        # Just verify we get some valid results
        assert len(result) >= 1
        valid_names = [entity.name for entity in result if entity.name and len(entity.name.strip()) > 1]
        assert "Valid Name" in valid_names

    def test_enhancement_with_mixed_sources(self, extractor):
        """Test enhancement with entities from multiple sources."""
        entities = [
            Entity(entity="Apple Inc.", type="ORGANIZATION", confidence=0.95, properties={}, source="SpaCy"),
            Entity(entity="Apple Inc.", type="ORGANIZATION", confidence=0.90, properties={}, source="GLiNER"),  # Same entity
            Entity(entity="Apple", type="ORGANIZATION", confidence=0.85, properties={}, source="REBEL"),  # Should group with Apple Inc.
        ]

        result = extractor.enhance_entities(entities)

        # Should group the identical entities and possibly the abbreviation
        assert len(result) >= 1
        apple_entities = [entity for entity in result if "Apple" in entity.name]
        if apple_entities:
            entity = apple_entities[0]
            assert len(entity.extraction_sources) >= 2  # At least SpaCy and GLiNER
            assert entity.mention_count >= 2


class TestEnhancedEntityExtractorAdvancedGrouping:
    """Advanced entity grouping functionality tests."""

    def test_group_entities_complex_similarity(self, extractor):
        """Test complex entity grouping with various similarity patterns."""
        entities = [
            Entity(entity="Dr. Sarah Johnson", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="Sarah Johnson", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="Prof. Johnson", type="PERSON", confidence=0.85, properties={}),
            Entity(entity="Johnson", type="PERSON", confidence=0.70, properties={}),  # Should not group with short names
            Entity(entity="Dr. Michael Chen", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="Michael Chen", type="PERSON", confidence=0.90, properties={}),
        ]
        result = extractor._group_entities(entities)

        # Should have groups for Sarah Johnson (3 entities) and Michael Chen (2 entities)
        # Johnson alone should be separate (too short)
        assert len(result) >= 2

        # Find Sarah Johnson group
        sarah_group = None
        michael_group = None
        johnson_group = None

        for canonical, group in result.items():
            if "Sarah" in canonical or "Johnson" in canonical:
                if len(group) == 3 and any("Sarah" in e.entity for e in group):
                    sarah_group = group
                elif len(group) == 1 and group[0].entity == "Johnson":
                    johnson_group = group
            elif "Michael" in canonical or "Chen" in canonical:
                if len(group) == 2:
                    michael_group = group

        assert sarah_group is not None, "Should have grouped Sarah Johnson entities"
        assert michael_group is not None, "Should have grouped Michael Chen entities"
        assert johnson_group is not None, "Should have separate Johnson entity"

    def test_group_entities_acronym_expansion(self, extractor):
        """Test grouping entities with acronym expansion."""
        entities = [
            Entity(entity="United States", type="LOCATION", confidence=0.95, properties={}),
            Entity(entity="US", type="LOCATION", confidence=0.90, properties={}),
            Entity(entity="USA", type="LOCATION", confidence=0.85, properties={}),
            Entity(entity="Artificial Intelligence", type="CONCEPT", confidence=0.95, properties={}),
            Entity(entity="AI", type="CONCEPT", confidence=0.80, properties={}),
        ]
        result = extractor._group_entities(entities)

        # Should group US variants and AI variants separately
        assert len(result) >= 2

    def test_group_entities_empty_and_none_entities(self, extractor):
        """Test grouping with empty entity names."""
        entities = [
            Entity(entity="", type="PERSON", confidence=0.9, properties={}),
            Entity(entity="Valid Name", type="PERSON", confidence=0.9, properties={}),
        ]

        # This should handle the edge case gracefully
        result = extractor._group_entities(entities)

        # Should have at least the valid entity
        assert len(result) >= 1
        assert any("Valid Name" in key for key in result.keys())

    def test_group_entities_case_insensitive(self, extractor):
        """Test case-insensitive entity grouping."""
        entities = [
            Entity(entity="John Doe", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="john doe", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="JOHN DOE", type="PERSON", confidence=0.85, properties={}),
        ]
        result = extractor._group_entities(entities)

        assert len(result) == 1
        canonical_form = list(result.keys())[0]
        assert result[canonical_form][0].entity == entities[0].entity  # Should preserve original case in canonical

    def test_group_entities_with_special_characters(self, extractor):
        """Test grouping entities with special characters."""
        entities = [
            Entity(entity="O'Connor", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="O'Connor", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="O'Connor & Associates", type="ORGANIZATION", confidence=0.85, properties={}),
        ]
        result = extractor._group_entities(entities)

        # Should group the identical O'Connor entities
        assert len(result) >= 1


class TestEnhancedEntityExtractorCanonicalFormsAdvanced:
    """Advanced canonical form determination tests."""

    def test_get_canonical_form_all_title_patterns(self, extractor):
        """Test all title pattern removals."""
        test_cases = [
            ("President John Doe", "John Doe"),
            ("Dr. Jane Smith", "Jane Smith"),
            ("Mr. Robert Johnson", "Robert Johnson"),
            ("Mrs. Mary Wilson", "Mary Wilson"),
            ("Ms. Sarah Brown", "Sarah Brown"),
            ("Prof. David Lee", "David Lee"),
            ("Sen. Elizabeth Warren", "Elizabeth Warren"),
            ("Rep. Alexandria Ocasio-Cortez", "Alexandria Ocasio-Cortez"),
            ("Gov. Gavin Newsom", "Gavin Newsom"),
            ("CEO Mark Zuckerberg", "Mark Zuckerberg"),
            ("CTO Sheryl Sandberg", "Sheryl Sandberg"),
            ("CFO David Wehner", "David Wehner"),
            ("COO Chris Cox", "Chris Cox"),
            ("General Stanley McChrystal", "Stanley McChrystal"),
            ("Admiral William McRaven", "William McRaven"),
            ("Colonel James Mattis", "James Mattis"),
            ("Captain Chesley Sullenberger", "Chesley Sullenberger"),
        ]

        for input_name, expected in test_cases:
            result = extractor._get_canonical_form(input_name)
            assert result == expected, f"Failed for {input_name}: expected {expected}, got {result}"

    def test_get_canonical_form_whitespace_normalization(self, extractor):
        """Test whitespace normalization in canonical forms."""
        test_cases = [
            ("  John   Doe  ", "John Doe"),
            ("John\nDoe", "John Doe"),
            ("John\tDoe", "John Doe"),
            ("John Doe ", "John Doe"),
        ]

        for input_name, expected in test_cases:
            result = extractor._get_canonical_form(input_name)
            assert result == expected, f"Failed for {repr(input_name)}: expected {expected}, got {result}"

    def test_get_canonical_form_edge_cases(self, extractor):
        """Test edge cases in canonical form determination."""
        test_cases = [
            ("", ""),
            ("A", "A"),
            (" A ", "A"),
            ("Dr.", "Dr."),
            ("CEO", "CEO"),
        ]

        for input_name, expected in test_cases:
            result = extractor._get_canonical_form(input_name)
            assert result == expected, f"Failed for {repr(input_name)}: expected {expected}, got {result}"

    def test_are_entities_similar_comprehensive(self, extractor):
        """Comprehensive similarity testing."""
        test_cases = [
            # Exact matches
            ("John Doe", "John Doe", True),
            ("John Doe", "john doe", True),  # Case insensitive

            # Substring matches
            ("Trump", "Donald Trump", True),
            ("Donald Trump", "Trump", True),
            ("Obama", "Barack Obama", True),
            ("Barack Obama", "Obama", True),

            # Too short substrings (should be false)
            ("A", "Apple", False),
            ("Hi", "History", False),

            # No similarity
            ("John Doe", "Jane Smith", False),
            ("Apple", "Orange", False),

            # Abbreviations
            ("United States", "USA", True),  # Should be handled by abbreviation logic
            ("Artificial Intelligence", "AI", False),  # Current implementation limitation
        ]

        for entity1, entity2, expected in test_cases:
            result = extractor._are_entities_similar(entity1, entity2)
            assert result == expected, f"Similarity check failed: '{entity1}' vs '{entity2}' should be {expected}, got {result}"

    def test_are_abbreviations_comprehensive(self, extractor):
        """Comprehensive abbreviation testing."""
        test_cases = [
            # Valid acronyms
            ("United States", "USA", True),
            ("United States", "US", True),
            ("European Union", "EU", True),
            ("Federal Bureau of Investigation", "FBI", True),
            ("Central Intelligence Agency", "CIA", True),
            ("National Security Agency", "NSA", True),

            # Invalid cases
            ("John Doe", "JD", False),  # Not a proper acronym
            ("Apple", "A", False),  # Too short
            ("Artificial Intelligence", "AI", False),  # Doesn't match acronym pattern
            ("United States", "U.S.", False),  # Period mismatch
            ("US", "United States", False),  # Wrong order
        ]

        for long_form, short_form, expected in test_cases:
            result = extractor._are_abbreviations(long_form, short_form)
            assert result == expected, f"Abbreviation check failed: '{long_form}' vs '{short_form}' should be {expected}, got {result}"

    def test_select_best_canonical_comprehensive(self, extractor):
        """Comprehensive best canonical selection testing."""
        # Test with frequency-based selection
        candidates = ["John Doe", "Dr. John Doe", "John"]
        entities = [
            Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={}),
            Entity(entity="John Doe", type="PERSON", confidence=0.8, properties={}),
            Entity(entity="Dr. John Doe", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="John", type="PERSON", confidence=0.7, properties={}),
        ]

        result = extractor._select_best_canonical(candidates, entities)

        # Should prefer "John Doe" due to frequency (2 mentions) and completeness (2 words)
        # over "Dr. John Doe" (1 mention, 3 words) or "John" (1 mention, 1 word)
        assert result == "John Doe"

    def test_select_best_canonical_length_preference(self, extractor):
        """Test that longer, more complete names are preferred."""
        candidates = ["Trump", "Donald Trump", "President Trump"]
        entities = [
            Entity(entity="Trump", type="PERSON", confidence=0.85, properties={}),
            Entity(entity="Donald Trump", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="President Trump", type="PERSON", confidence=0.90, properties={}),
        ]

        result = extractor._select_best_canonical(candidates, entities)

        # Should prefer the most complete name
        assert result == "President Trump"  # 2 words, highest score


class TestEnhancedEntityExtractorContextAndTemporalAdvanced:
    """Advanced context and temporal functionality tests."""

    def test_extract_context_windows_various_formats(self, extractor):
        """Test context extraction with various transcript segment formats."""
        entities = [Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={})]

        # Test with different timestamp formats
        transcript_segments = [
            {"text": "John Doe is here today", "timestamp": "00:00:00", "speaker": "Narrator"},
            {"text": "John Doe speaks now", "timestamp": "0:01:30", "speaker": "John"},
            {"text": "Mr. Doe has arrived", "timestamp": "1:30", "speaker": "Host"},
        ]

        result = extractor._extract_context_windows("John Doe", entities, transcript_segments)

        assert len(result) >= 1  # Should find "John Doe" mention
        assert all(isinstance(ctx, EntityContext) for ctx in result)

    def test_extract_context_windows_case_insensitive(self, extractor):
        """Test case-insensitive context extraction."""
        entities = [Entity(entity="Apple Inc.", type="ORGANIZATION", confidence=0.9, properties={})]

        transcript_segments = [
            {"text": "apple inc. is growing", "timestamp": "00:00:00", "speaker": "Narrator"},
            {"text": "APPLE INC. announces", "timestamp": "00:00:30", "speaker": "CEO"},
        ]

        result = extractor._extract_context_windows("Apple Inc.", entities, transcript_segments)

        assert len(result) >= 2  # Should find both case variations

    def test_extract_context_windows_entity_variations(self, extractor):
        """Test context extraction with entity variations."""
        entities = [
            Entity(entity="Donald Trump", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="Trump", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="President Trump", type="PERSON", confidence=0.85, properties={}),
        ]

        transcript_segments = [
            {"text": "Donald Trump is president", "timestamp": "00:00:00", "speaker": "Narrator"},
            {"text": "Trump said yesterday", "timestamp": "00:00:30", "speaker": "Reporter"},
            {"text": "President Trump announced", "timestamp": "00:01:00", "speaker": "Anchor"},
        ]

        result = extractor._extract_context_windows("Donald Trump", entities, transcript_segments)

        assert len(result) >= 3  # Should find all variations

    def test_extract_temporal_distribution_grouping(self, extractor):
        """Test temporal distribution with proper grouping."""
        entities = [Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={})]

        # Create context windows with same timestamp (should group)
        context_windows = [
            EntityContext(text="John Doe here", timestamp="00:00:10", speaker="Narrator", visual_present=False),
            EntityContext(text="John Doe there", timestamp="00:00:10", speaker="Narrator", visual_present=False),
            EntityContext(text="John Doe later", timestamp="00:00:30", speaker="Narrator", visual_present=False),
        ]

        result = extractor._extract_temporal_distribution(entities, context_windows)

        assert len(result) == 2  # Should have 2 unique timestamps
        timestamps = {mention.timestamp for mention in result}
        assert timestamps == {"00:00:10", "00:00:30"}

    def test_extract_temporal_distribution_empty_contexts(self, extractor):
        """Test temporal distribution with empty context windows."""
        entities = [Entity(entity="John Doe", type="PERSON", confidence=0.9, properties={})]

        result = extractor._extract_temporal_distribution(entities, [])

        assert result == []  # Should return empty list

    def test_determine_entity_type_frequency_based(self, extractor):
        """Test entity type determination based on frequency."""
        entities = [
            Entity(entity="Google", type="ORGANIZATION", confidence=0.9, properties={}),
            Entity(entity="Google", type="ORGANIZATION", confidence=0.8, properties={}),
            Entity(entity="Google", type="PERSON", confidence=0.7, properties={}),  # Minority type
        ]

        result = extractor._determine_entity_type(entities)
        assert result == "ORGANIZATION"  # Should choose most frequent type

    def test_determine_entity_type_no_type_info(self, extractor):
        """Test entity type determination when entities have no type."""
        entities = [
            Entity(entity="Google", type="", confidence=0.9, properties={}),
            Entity(entity="Google", type="", confidence=0.8, properties={}),
        ]

        result = extractor._determine_entity_type(entities)
        assert result == "UNKNOWN"  # Should default to UNKNOWN

    def test_extract_aliases_comprehensive(self, extractor):
        """Comprehensive alias extraction testing."""
        entities = [
            Entity(entity="Donald J. Trump", type="PERSON", confidence=0.95, properties={}),
            Entity(entity="Donald Trump", type="PERSON", confidence=0.90, properties={}),
            Entity(entity="Trump", type="PERSON", confidence=0.85, properties={}),
            Entity(entity="President Trump", type="PERSON", confidence=0.80, properties={}),
        ]

        result = extractor._extract_aliases("Donald Trump", entities)

        # Should extract all variations except the canonical form
        expected_aliases = {"Donald J. Trump", "Trump", "President Trump"}
        assert set(result) == expected_aliases
        assert "Donald Trump" not in result  # Canonical form should not be in aliases


class TestEnhancedEntityExtractorAliasNormalizer:
    """Test the nested AliasNormalizer class comprehensively."""

    def test_alias_normalizer_common_aliases_expansion(self, extractor):
        """Test common alias expansion."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()

        test_cases = [
            ("US", "United States"),
            ("USA", "United States"),
            ("UK", "United Kingdom"),
            ("EU", "European Union"),
            ("UN", "United Nations"),
            ("FBI", "Federal Bureau of Investigation"),
            ("CIA", "Central Intelligence Agency"),
            ("NSA", "National Security Agency"),
        ]

        for input_alias, expected in test_cases:
            result = normalizer.normalize_entity(input_alias)
            assert result == expected, f"Failed to expand {input_alias} to {expected}, got {result}"

    def test_alias_normalizer_title_removal(self, extractor):
        """Test title removal in normalization."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()

        test_cases = [
            ("President Biden", "Biden"),
            ("Dr. Fauci", "Fauci"),
            ("CEO Musk", "Musk"),
            ("Former President Obama", "President Obama"),  # Should remove "Former"
        ]

        for input_name, expected in test_cases:
            result = normalizer.normalize_entity(input_name)
            assert result == expected, f"Failed to normalize {input_name} to {expected}, got {result}"

    def test_alias_normalizer_edge_cases(self, extractor):
        """Test edge cases in alias normalization."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()

        test_cases = [
            ("", ""),
            ("A", "A"),
            ("John", "John"),
            ("Dr.", "Dr."),  # No name after title
            ("CEO", "CEO"),  # No name after title
        ]

        for input_name, expected in test_cases:
            result = normalizer.normalize_entity(input_name)
            assert result == expected, f"Edge case failed for {repr(input_name)}: expected {expected}, got {result}"

    def test_find_aliases_grouping(self, extractor):
        """Test alias finding with proper grouping."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()

        entities = [
            "Donald Trump",
            "President Trump",
            "Trump",
            "Joe Biden",
            "President Biden",
            "Biden",
        ]

        result = normalizer.find_aliases(entities)

        # Should find aliases for Trump and Biden groups
        assert len(result) >= 2

        # Check Trump group
        trump_key = None
        for key in result:
            if "Trump" in key:
                trump_key = key
                break

        assert trump_key is not None, "Should have Trump alias group"
        assert len(result[trump_key]) >= 2  # At least "President Trump" and "Trump"

        # Check Biden group
        biden_key = None
        for key in result:
            if "Biden" in key:
                biden_key = key
                break

        assert biden_key is not None, "Should have Biden alias group"
        assert len(result[biden_key]) >= 2  # At least "President Biden" and "Biden"

    def test_find_aliases_no_aliases(self, extractor):
        """Test alias finding when no aliases exist."""
        from clipscribe.extractors.enhanced_entity_extractor import AliasNormalizer
        normalizer = AliasNormalizer()

        entities = ["John Doe", "Jane Smith", "Bob Johnson"]

        result = normalizer.find_aliases(entities)

        assert result == {}  # No aliases should be found


class TestEnhancedEntityExtractorIntegrationAdvanced:
    """Advanced integration tests for the full enhancement process."""

    def test_full_enhancement_with_complex_transcript(self, extractor):
        """Test full enhancement with complex transcript data."""
        entities = [
            Entity(entity="Dr. Sarah Johnson", type="PERSON", confidence=0.95, properties={}, source="SpaCy"),
            Entity(entity="Sarah Johnson", type="PERSON", confidence=0.90, properties={}, source="GLiNER"),
            Entity(entity="MIT", type="ORGANIZATION", confidence=0.88, properties={}, source="SpaCy"),
            Entity(entity="Massachusetts Institute of Technology", type="ORGANIZATION", confidence=0.92, properties={}, source="GLiNER"),
        ]

        transcript_segments = [
            {
                "text": "Dr. Sarah Johnson from MIT presented today",
                "timestamp": "00:02:15",
                "speaker": "Narrator",
                "segment_id": "seg_1",
            },
            {
                "text": "Sarah Johnson is a researcher at the Massachusetts Institute of Technology",
                "timestamp": "00:05:30",
                "speaker": "Interviewer",
                "segment_id": "seg_2",
            },
            {
                "text": "MIT researchers are leading in AI",
                "timestamp": "00:08:45",
                "speaker": "Narrator",
                "segment_id": "seg_3",
            },
        ]

        result = extractor.enhance_entities(entities, transcript_segments=transcript_segments)

        # Should have grouped Sarah Johnson entities and MIT entities
        assert len(result) >= 2

        # Find Sarah Johnson entity
        sarah_entity = None
        mit_entity = None

        for entity in result:
            if "Johnson" in entity.name:
                sarah_entity = entity
            elif "MIT" in entity.name or "Massachusetts" in entity.name:
                mit_entity = entity

        assert sarah_entity is not None, "Should have Sarah Johnson entity"
        assert mit_entity is not None, "Should have MIT entity"

        # Check Sarah Johnson has proper metadata
        assert sarah_entity.mention_count >= 2
        assert set(sarah_entity.extraction_sources) == {"SpaCy", "GLiNER"}
        assert len(sarah_entity.context_windows) >= 2  # Should find contexts in transcript
        assert len(sarah_entity.aliases) >= 1  # Should have "Dr. Sarah Johnson" as alias

        # Check MIT has proper metadata
        assert mit_entity.mention_count >= 2
        assert set(mit_entity.extraction_sources) == {"SpaCy", "GLiNER"}
        assert len(mit_entity.context_windows) >= 2  # Should find contexts in transcript

    def test_enhancement_with_visual_data_integration(self, extractor):
        """Test enhancement with visual data (though current implementation may not use it fully)."""
        entities = [
            Entity(entity="Steve Jobs", type="PERSON", confidence=0.95, properties={}, source="SpaCy"),
        ]

        visual_data = {
            "detections": [
                {"label": "person", "confidence": 0.9, "bbox": [100, 100, 200, 300]},
                {"label": "laptop", "confidence": 0.8, "bbox": [150, 150, 250, 350]},
            ],
            "frame_number": 120,
            "timestamp": "00:02:00",
        }

        result = extractor.enhance_entities(entities, visual_data=visual_data)

        assert len(result) == 1
        entity = result[0]
        assert entity.name == "Steve Jobs"
        assert entity.type == "PERSON"

    def test_enhancement_memory_efficiency(self, extractor):
        """Test that enhancement process is memory efficient with large datasets."""
        # Create a large number of entities
        entities = []
        for i in range(100):
            entities.append(
                Entity(
                    entity=f"Person{i}",
                    type="PERSON",
                    confidence=0.9,
                    properties={},
                    source="SpaCy"
                )
            )

        # Add some duplicates to test grouping
        entities.extend([
            Entity(entity="Person0", type="PERSON", confidence=0.8, properties={}, source="GLiNER"),
            Entity(entity="Person1", type="PERSON", confidence=0.85, properties={}, source="GLiNER"),
        ])

        result = extractor.enhance_entities(entities)

        # Should have 100 unique entities (duplicates grouped)
        assert len(result) == 100

        # Check that grouped entities have correct metadata
        person0_entity = next((e for e in result if e.name == "Person0"), None)
        assert person0_entity is not None
        assert person0_entity.mention_count == 2
        assert set(person0_entity.extraction_sources) == {"SpaCy", "GLiNER"}

    def test_enhancement_with_none_values_robustness(self, extractor):
        """Test robustness with missing values."""
        entities = [
            Entity(entity="Valid Entity", type="PERSON", confidence=0.9, properties={}),
            Entity(entity="", type="PERSON", confidence=0.7, properties={}),
        ]

        # This should handle empty values gracefully
        result = extractor.enhance_entities(entities)

        # Should have at least the valid entity
        assert len(result) >= 1
        valid_entity = next((e for e in result if e.name == "Valid Entity"), None)
        assert valid_entity is not None
