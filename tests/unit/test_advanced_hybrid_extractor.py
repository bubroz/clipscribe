# tests/unit/test_advanced_hybrid_extractor.py
import pytest
from unittest.mock import Mock, patch
from clipscribe.extractors.advanced_hybrid_extractor import AdvancedHybridExtractor
from clipscribe.models import VideoIntelligence, VideoTranscript


@pytest.fixture
def mock_entity_normalizer():
    return Mock()


@pytest.fixture
def mock_enhanced_extractor():
    return Mock()


@pytest.fixture
def mock_relationship_evidence_extractor():
    return Mock()


@pytest.fixture
def mock_temporal_reference_resolver():
    return Mock()


@pytest.fixture
def extractor(
    mock_entity_normalizer,
    mock_enhanced_extractor,
    mock_relationship_evidence_extractor,
    mock_temporal_reference_resolver,
):
    """Fixture to create an AdvancedHybridExtractor instance with mocked dependencies."""
    with (
        patch(
            "clipscribe.extractors.advanced_hybrid_extractor.EntityNormalizer",
            return_value=mock_entity_normalizer,
        ),
        patch(
            "clipscribe.extractors.advanced_hybrid_extractor.EnhancedEntityExtractor",
            return_value=mock_enhanced_extractor,
        ),
        patch(
            "clipscribe.extractors.advanced_hybrid_extractor.RelationshipEvidenceExtractor",
            return_value=mock_relationship_evidence_extractor,
        ),
        patch(
            "clipscribe.extractors.advanced_hybrid_extractor.TemporalReferenceResolver",
            return_value=mock_temporal_reference_resolver,
        ),
    ):
        return AdvancedHybridExtractor()


@pytest.mark.asyncio
async def test_extract_all_with_data(
    extractor,
    mock_entity_normalizer,
    mock_enhanced_extractor,
    mock_relationship_evidence_extractor,
    mock_temporal_reference_resolver,
):
    """Test the full extraction pipeline with mock data."""
    # Arrange
    mock_video = Mock(spec=VideoIntelligence)
    mock_video.transcript = Mock(spec=VideoTranscript)
    mock_video.transcript.full_text = "Test transcript with entities and relationships."
    mock_video.transcript.segments = []

    mock_video.processing_stats = {
        "gemini_entities": [{"name": "Test Entity", "type": "TEST"}],
        "gemini_relationships": [{"subject": "Sub", "predicate": "Pred", "object": "Obj"}],
    }
    mock_video.entities = []
    mock_video.relationships = []

    # Act
    result = await extractor.extract_all(mock_video)

    # Assert
    assert result is not None
    mock_entity_normalizer.normalize_entities.assert_called_once()
    mock_enhanced_extractor.enhance_entities.assert_called_once()
    mock_relationship_evidence_extractor.extract_evidence_chains.assert_called_once()
    mock_temporal_reference_resolver.resolve_temporal_references.assert_called_once()
