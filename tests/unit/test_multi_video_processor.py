"""Unit tests for MultiVideoProcessor module."""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from typing import List

from clipscribe.extractors.multi_video_processor import MultiVideoProcessor
from clipscribe.models import (
    VideoIntelligence, MultiVideoIntelligence, CrossVideoEntity,
    CrossVideoRelationship, VideoCollectionType, Entity, Topic,
    InformationFlowMap, ConceptNode, ConceptDependency,
    InformationFlow, ConceptEvolutionPath, ConceptCluster,
    ConceptMaturityLevel
)
from tests.helpers import create_mock_video_intelligence


@pytest.fixture
def mock_video_intelligence():
    """Create mock VideoIntelligence for testing."""
    mock_vi = MagicMock(spec=VideoIntelligence)
    mock_vi.entities = [Entity(entity="Test Entity", type="PERSON", properties={})]
    mock_vi.relationships = []
    mock_vi.topics = [Topic(name="AI")]
    mock_vi.title = "Test Video"
    mock_vi.metadata = MagicMock()
    mock_vi.metadata.video_id = "video_123"
    mock_vi.transcript = MagicMock()
    mock_vi.transcript.full_text = "This is a test transcript about AI technology."
    return mock_vi


@pytest.fixture
def mock_videos(mock_video_intelligence):
    """Create a list of mock VideoIntelligence objects."""
    videos = []
    for i in range(3):
        mock_vi = MagicMock(spec=VideoIntelligence)
        mock_vi.entities = [Entity(entity=f"Entity {i}", type="PERSON", properties={})]
        mock_vi.relationships = []
        mock_vi.topics = [Topic(name=f"Topic {i}")]
        mock_vi.title = f"Video {i}"
        mock_vi.metadata = MagicMock()
        mock_vi.metadata.video_id = f"video_{i}"
        mock_vi.transcript = MagicMock()
        mock_vi.transcript.full_text = f"This is test transcript {i} about technology."
        videos.append(mock_vi)
    return videos


@pytest.fixture
def reset_multi_video_processor():
    """Reset MultiVideoProcessor for each test."""
    with patch('clipscribe.extractors.multi_video_processor.EntityNormalizer') as mock_normalizer_class, \
         patch('clipscribe.extractors.multi_video_processor.SeriesDetector') as mock_detector_class, \
         patch('clipscribe.extractors.multi_video_processor.Settings') as mock_settings_class:

        # Create mock instances
        mock_normalizer = MagicMock()
        mock_detector = MagicMock()
        mock_settings = MagicMock()
        mock_settings.google_api_key = "test-key"

        # Configure class constructors
        mock_normalizer_class.return_value = mock_normalizer
        mock_detector_class.return_value = mock_detector
        mock_settings_class.return_value = mock_settings

        # Create processor
        processor = MultiVideoProcessor(use_ai_validation=False)  # Disable AI for easier testing

        yield processor, {
            'normalizer': mock_normalizer,
            'detector': mock_detector,
            'settings': mock_settings
        }


class TestMultiVideoProcessorInitialization:
    """Test MultiVideoProcessor initialization."""

    def test_init_default_params(self, reset_multi_video_processor):
        """Test initialization with default parameters."""
        processor, mocks = reset_multi_video_processor

        assert processor.use_ai_validation is False  # We disabled AI for testing
        assert processor.entity_normalizer is not None
        assert processor.series_detector is not None
        assert processor.settings is not None

    def test_init_with_ai_validation_disabled(self, reset_multi_video_processor):
        """Test initialization with AI validation disabled."""
        processor, mocks = reset_multi_video_processor

        # Should not have ai_model when disabled
        assert not hasattr(processor, 'ai_model')

    def test_init_with_ai_validation_enabled(self):
        """Test initialization with AI validation enabled."""
        with patch('clipscribe.extractors.multi_video_processor.EntityNormalizer'), \
             patch('clipscribe.extractors.multi_video_processor.SeriesDetector'), \
             patch('clipscribe.extractors.multi_video_processor.Settings') as mock_settings_class, \
             patch('clipscribe.extractors.multi_video_processor.genai') as mock_genai:

            mock_settings = MagicMock()
            mock_settings.google_api_key = "test-key"
            mock_settings_class.return_value = mock_settings

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            processor = MultiVideoProcessor(use_ai_validation=True)

            assert processor.use_ai_validation is True
            assert processor.ai_model == mock_model
            mock_genai.configure.assert_called_with(api_key="test-key")
            mock_genai.GenerativeModel.assert_called_with("gemini-2.5-pro")

    def test_init_ai_validation_failure(self):
        """Test initialization when AI validation setup fails."""
        with patch('clipscribe.extractors.multi_video_processor.EntityNormalizer'), \
             patch('clipscribe.extractors.multi_video_processor.SeriesDetector'), \
             patch('clipscribe.extractors.multi_video_processor.Settings') as mock_settings_class, \
             patch('clipscribe.extractors.multi_video_processor.genai') as mock_genai:

            mock_settings = MagicMock()
            mock_settings.google_api_key = "test-key"
            mock_settings_class.return_value = mock_settings

            # Make genai.configure raise an exception
            mock_genai.configure.side_effect = Exception("API key invalid")

            processor = MultiVideoProcessor(use_ai_validation=True)

            # Should fall back to disabled AI validation
            assert processor.use_ai_validation is False
            assert not hasattr(processor, 'ai_model')


class TestMultiVideoProcessorMainPipeline:
    """Test the main processing pipeline."""

    def test_process_video_collection_success(self, reset_multi_video_processor, mock_videos):
        """Test successful processing of video collection."""
        processor, mocks = reset_multi_video_processor

        # Mock all the pipeline steps
        with patch.object(processor, '_unify_entities_across_videos') as mock_unify, \
             patch.object(processor, '_extract_cross_video_relationships') as mock_extract, \
             patch.object(processor, '_generate_unified_knowledge_graph') as mock_generate_kg, \
             patch.object(processor, '_synthesize_information_flow_map') as mock_synthesize, \
             patch.object(processor, '_generate_collection_insights') as mock_insights, \
             patch('clipscribe.extractors.multi_video_processor.time.time', return_value=1234567890), \
             patch('clipscribe.extractors.multi_video_processor.MultiVideoIntelligence') as mock_mvi_class:

            # Setup mock returns
            mock_unify.return_value = [MagicMock(spec=CrossVideoEntity)]
            mock_extract.return_value = [MagicMock(spec=CrossVideoRelationship)]
            mock_generate_kg.return_value = {"nodes": [], "edges": []}
            mock_synthesize.return_value = MagicMock(spec=InformationFlowMap)
            mock_insights.return_value = ["Key insight 1", "Key insight 2"]

            mock_mvi = MagicMock(spec=MultiVideoIntelligence)
            mock_mvi_class.return_value = mock_mvi

            # Process collection
            result = asyncio.run(processor.process_video_collection(
                videos=mock_videos,
                collection_type=VideoCollectionType.SERIES,
                collection_title="Test Series",
                user_confirmed_series=True
            ))

            # Verify all pipeline steps were called
            mock_unify.assert_called_once_with(mock_videos, core_only=False)
            mock_extract.assert_called_once()
            mock_generate_kg.assert_called_once()
            mock_synthesize.assert_called_once()
            mock_insights.assert_called_once()

            # Verify MultiVideoIntelligence was created
            mock_mvi_class.assert_called_once()
            assert result == mock_mvi

    def test_process_video_collection_empty_videos(self, reset_multi_video_processor):
        """Test processing with empty video list."""
        processor, mocks = reset_multi_video_processor

        with pytest.raises(ValueError, match="At least one video required"):
            asyncio.run(processor.process_video_collection(
                videos=[],
                collection_type=VideoCollectionType.SERIES,
                collection_title="Empty Collection"
            ))

    def test_process_video_collection_core_only(self, reset_multi_video_processor, mock_videos):
        """Test processing with core_only flag."""
        processor, mocks = reset_multi_video_processor

        with patch.object(processor, '_unify_entities_across_videos') as mock_unify, \
             patch.object(processor, '_extract_cross_video_relationships') as mock_extract, \
             patch.object(processor, '_generate_unified_knowledge_graph') as mock_generate_kg, \
             patch.object(processor, '_synthesize_information_flow_map') as mock_synthesize, \
             patch.object(processor, '_generate_collection_insights') as mock_insights, \
             patch('clipscribe.extractors.multi_video_processor.time.time', return_value=1234567890), \
             patch('clipscribe.extractors.multi_video_processor.MultiVideoIntelligence') as mock_mvi_class:

            # Setup mock returns
            mock_unify.return_value = [MagicMock(spec=CrossVideoEntity)]
            mock_extract.return_value = [MagicMock(spec=CrossVideoRelationship)]
            mock_generate_kg.return_value = {"nodes": [], "edges": []}
            mock_synthesize.return_value = MagicMock(spec=InformationFlowMap)
            mock_insights.return_value = ["Key insight 1"]

            mock_mvi = MagicMock(spec=MultiVideoIntelligence)
            mock_mvi_class.return_value = mock_mvi

            # Process with core_only=True
            result = asyncio.run(processor.process_video_collection(
                videos=mock_videos,
                collection_type=VideoCollectionType.SERIES,
                collection_title="Test Series",
                core_only=True
            ))

            # Verify _unify_entities_across_videos was called with core_only=True
            mock_unify.assert_called_once_with(mock_videos, core_only=True)
            assert result == mock_mvi


@pytest.fixture
def processor():
    """Fixture to create a MultiVideoProcessor with mocked dependencies."""
    with (
        patch("clipscribe.extractors.multi_video_processor.EntityNormalizer"),
        patch("clipscribe.extractors.multi_video_processor.SeriesDetector"),
    ):
        return MultiVideoProcessor()


@pytest.mark.asyncio
async def test_process_video_collection(processor):
    """Test the main process_video_collection method."""
    videos = [create_mock_video_intelligence("vid1"), create_mock_video_intelligence("vid2")]

    with (
        patch.object(
            processor, "_unify_entities_across_videos", new_callable=AsyncMock
        ) as mock_unify,
        patch.object(
            processor, "_extract_cross_video_relationships", new_callable=AsyncMock
        ) as mock_extract,
        patch.object(
            processor, "_generate_unified_knowledge_graph", new_callable=AsyncMock
        ) as mock_graph,
        patch.object(
            processor, "_synthesize_information_flow_map", new_callable=AsyncMock
        ) as mock_flow,
        patch.object(
            processor, "_generate_collection_insights", new_callable=AsyncMock
        ) as mock_insights,
    ):

        mock_unify.return_value = []
        mock_extract.return_value = []
        mock_graph.return_value = {}
        mock_flow.return_value = Mock()
        mock_insights.return_value = []

        result = await processor.process_video_collection(
            videos, VideoCollectionType.SERIES, "Test Collection"
        )

        assert isinstance(result, MultiVideoIntelligence)
        assert result.collection_title == "Test Collection"
        mock_unify.assert_called_once()
        mock_extract.assert_called_once()


class TestMultiVideoProcessorEntityUnification:
    """Test entity unification across videos."""

    def test_unify_entities_across_videos(self, reset_multi_video_processor, mock_videos):
        """Test entity unification across videos."""
        processor, mocks = reset_multi_video_processor

        # Mock the normalizer to return unified entities
        mock_cross_entity = MagicMock(spec=CrossVideoEntity)
        mocks['normalizer'].unify_cross_video_entities.return_value = [mock_cross_entity]

        with patch.object(processor, '_calculate_entity_resolution_quality', return_value=0.85):
            result = asyncio.run(processor._unify_entities_across_videos(mock_videos))

            assert result == [mock_cross_entity]
            mocks['normalizer'].unify_cross_video_entities.assert_called_once()

    def test_unify_entities_across_videos_core_only(self, reset_multi_video_processor, mock_videos):
        """Test entity unification with core_only flag."""
        processor, mocks = reset_multi_video_processor

        # Mock the normalizer to return unified entities
        mock_cross_entity = MagicMock(spec=CrossVideoEntity)
        mocks['normalizer'].unify_cross_video_entities.return_value = [mock_cross_entity]

        with patch.object(processor, '_calculate_entity_resolution_quality', return_value=0.85):
            result = asyncio.run(processor._unify_entities_across_videos(mock_videos, core_only=True))

            assert result == [mock_cross_entity]
            # Verify core_only was passed to normalizer
            mocks['normalizer'].unify_cross_video_entities.assert_called_once()


class TestMultiVideoProcessorConceptAnalysis:
    """Test concept analysis functionality."""

    def test_is_conceptual_content(self, reset_multi_video_processor):
        """Test conceptual content detection."""
        processor, mocks = reset_multi_video_processor

        # Test conceptual content - use a term that matches the indicators
        assert processor._is_conceptual_content("Machine learning is a concept in AI") is True

        # Test non-conceptual content
        assert processor._is_conceptual_content("Hello world") is False

    def test_calculate_name_similarity(self, reset_multi_video_processor):
        """Test name similarity calculation."""
        processor, mocks = reset_multi_video_processor

        # Test identical names
        similarity = processor._calculate_name_similarity("AI", "AI")
        assert similarity == 1.0

        # Test different names
        similarity = processor._calculate_name_similarity("Machine Learning", "Deep Learning")
        assert 0 <= similarity <= 1

    def test_assess_concept_maturity(self, reset_multi_video_processor):
        """Test concept maturity assessment."""
        processor, mocks = reset_multi_video_processor

        # Test mature concept
        maturity = processor._assess_concept_maturity(
            "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed."
        )
        assert isinstance(maturity, ConceptMaturityLevel)

        # Test basic concept
        maturity = processor._assess_concept_maturity("AI is smart.")
        assert isinstance(maturity, ConceptMaturityLevel)


class TestMultiVideoProcessorUtilityMethods:
    """Test utility methods."""

    def test_calculate_entity_resolution_quality(self, reset_multi_video_processor, mock_videos):
        """Test entity resolution quality calculation."""
        processor, mocks = reset_multi_video_processor

        mock_entity = MagicMock(spec=CrossVideoEntity)
        mock_entity.mention_count = 5
        mock_entity.video_appearances = ["video1", "video2"]
        mock_entities = [mock_entity]

        quality = processor._calculate_entity_resolution_quality(mock_entities)
        assert isinstance(quality, float)
        assert 0 <= quality <= 1

    def test_calculate_narrative_coherence(self, reset_multi_video_processor, mock_videos):
        """Test narrative coherence calculation."""
        processor, mocks = reset_multi_video_processor

        mock_relationships = [MagicMock(spec=CrossVideoRelationship)]
        coherence = processor._calculate_narrative_coherence(mock_videos, mock_relationships)
        assert isinstance(coherence, float)
        assert 0 <= coherence <= 1

    def test_deduplicate_concepts(self, reset_multi_video_processor):
        """Test concept deduplication."""
        processor, mocks = reset_multi_video_processor

        # Create mock concept nodes
        concept1 = MagicMock(spec=ConceptNode)
        concept1.concept_name = "AI"
        concept1.confidence = 0.9
        concept1.video_id = "video1"

        concept2 = MagicMock(spec=ConceptNode)
        concept2.concept_name = "Artificial Intelligence"
        concept2.confidence = 0.7
        concept2.video_id = "video2"

        concepts = [concept1, concept2]

        with patch.object(processor, '_calculate_name_similarity', return_value=0.9):
            result = processor._deduplicate_concepts(concepts)

            # Should return the concept with higher confidence
            assert len(result) == 1
            assert result[0] == concept1
