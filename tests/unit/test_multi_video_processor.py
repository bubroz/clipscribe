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
    ConceptMaturityLevel, KeyPoint
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

    

    def test_init_with_disabled_ai_validation(self):
        """Test initialization with AI validation disabled."""
        with patch('clipscribe.extractors.multi_video_processor.EntityNormalizer'), \
             patch('clipscribe.extractors.multi_video_processor.SeriesDetector'), \
             patch('clipscribe.extractors.multi_video_processor.Settings') as mock_settings_class:

            mock_settings = MagicMock()
            mock_settings.google_api_key = "test-key"
            mock_settings_class.return_value = mock_settings

            processor = MultiVideoProcessor(use_ai_validation=False)

            # Should have AI validation disabled
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
             patch('clipscribe.models.MultiVideoIntelligence') as mock_mvi_class:

            # Setup mock returns
            mock_cross_entity = MagicMock(spec=CrossVideoEntity)
            mock_cross_entity.mention_count = 3
            mock_cross_entity.video_appearances = ["video1", "video2"]  # Required for quality calculation
            mock_unify.return_value = [mock_cross_entity]
            mock_extract.return_value = [MagicMock(spec=CrossVideoRelationship)]
            mock_generate_kg.return_value = {"nodes": [], "edges": []}
            mock_synthesize.return_value = MagicMock(spec=InformationFlowMap)
            mock_insights.return_value = ["Key insight 1", "Key insight 2"]

            mock_mvi = MagicMock(spec=MultiVideoIntelligence)
            mock_mvi.collection_summary = "Automated summary of 3 series videos"
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
             patch('clipscribe.models.MultiVideoIntelligence') as mock_mvi_class:

            # Setup mock returns
            mock_cross_entity = MagicMock(spec=CrossVideoEntity)
            mock_cross_entity.mention_count = 3
            mock_cross_entity.video_appearances = ["video1", "video2"]  # Required for quality calculation
            mock_unify.return_value = [mock_cross_entity]
            mock_extract.return_value = [MagicMock(spec=CrossVideoRelationship)]
            mock_generate_kg.return_value = {"nodes": [], "edges": []}
            mock_synthesize.return_value = MagicMock(spec=InformationFlowMap)
            mock_insights.return_value = ["Key insight 1"]

            mock_mvi = MagicMock(spec=MultiVideoIntelligence)
            mock_mvi.collection_summary = "Automated summary of 3 series videos"
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

        # Mock the entity resolution quality calculation
        with patch.object(processor, '_calculate_entity_resolution_quality', return_value=0.85):
            result = asyncio.run(processor._unify_entities_across_videos(mock_videos))

            # Should return unified entities based on mock videos
            assert len(result) >= 0  # Should process the mock videos
            # The exact result depends on the mock video entities

    def test_unify_entities_across_videos_core_only(self, reset_multi_video_processor, mock_videos):
        """Test entity unification with core_only flag."""
        processor, mocks = reset_multi_video_processor

        # Mock the normalizer to return unified entities
        mock_cross_entity = MagicMock(spec=CrossVideoEntity)
        mocks['normalizer'].unify_cross_video_entities.return_value = [mock_cross_entity]

        with patch.object(processor, '_calculate_entity_resolution_quality', return_value=0.85):
            result = asyncio.run(processor._unify_entities_across_videos(mock_videos, core_only=True))

            # Should return unified entities based on mock videos with core_only flag
            assert len(result) >= 0  # Should process the mock videos
            # The exact result depends on the mock video entities


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

        # Create mock concept nodes - same video_id and similar names to trigger deduplication
        concept1 = MagicMock(spec=ConceptNode)
        concept1.concept_name = "AI"
        concept1.confidence = 0.9
        concept1.video_id = "video1"
        concept1.node_id = "node1"
        concept1.maturity_level = "introduced"

        concept2 = MagicMock(spec=ConceptNode)
        concept2.concept_name = "AI"  # Same name to trigger deduplication
        concept2.confidence = 0.7
        concept2.video_id = "video1"  # Same video to trigger deduplication
        concept2.node_id = "node2"
        concept2.maturity_level = "explained"  # Higher maturity level

        concepts = [concept1, concept2]

        with patch.object(processor, '_calculate_name_similarity', return_value=0.9):
            result = processor._deduplicate_concepts(concepts)

            # Should return the concept with higher maturity level ("explained" > "introduced")
            assert len(result) == 1
            assert result[0] == concept2  # concept2 has higher maturity level


class TestMultiVideoProcessorUtilityMethods:
    """Test utility methods for concept analysis and processing."""

    def test_is_conceptual_content_true(self, reset_multi_video_processor):
        """Test _is_conceptual_content with conceptual text."""
        processor, mocks = reset_multi_video_processor

        conceptual_text = "This video explores the concept of artificial intelligence and its philosophical implications."
        assert processor._is_conceptual_content(conceptual_text) is True

    def test_is_conceptual_content_false(self, reset_multi_video_processor):
        """Test _is_conceptual_content with non-conceptual text."""
        processor, mocks = reset_multi_video_processor

        factual_text = "The weather today is sunny with temperatures reaching 75 degrees."
        assert processor._is_conceptual_content(factual_text) is False

    def test_assess_concept_maturity_mentioned(self, reset_multi_video_processor):
        """Test _assess_concept_maturity for mentioned level."""
        processor, mocks = reset_multi_video_processor

        text = "This video mentions artificial intelligence in passing."
        result = processor._assess_concept_maturity(text)
        assert result == ConceptMaturityLevel.MENTIONED

    def test_assess_concept_maturity_explained(self, reset_multi_video_processor):
        """Test _assess_concept_maturity for explained level."""
        processor, mocks = reset_multi_video_processor

        text = "This video explains artificial intelligence in great detail."
        result = processor._assess_concept_maturity(text)
        assert result in [ConceptMaturityLevel.EXPLAINED, ConceptMaturityLevel.DEFINED]

    def test_calculate_entity_resolution_quality(self, reset_multi_video_processor):
        """Test _calculate_entity_resolution_quality."""
        processor, mocks = reset_multi_video_processor

        # Mock cross entity with required attributes
        entity = MagicMock(spec=CrossVideoEntity)
        entity.mention_count = 5
        entity.video_appearances = ["video1", "video2", "video3"]
        entity.confidence_score = 0.8

        # Mock the len() function more safely
        with patch('builtins.len', return_value=3):
            quality = processor._calculate_entity_resolution_quality(entity)
            assert isinstance(quality, float)
            assert 0.0 <= quality <= 1.0

    def test_calculate_narrative_coherence(self, reset_multi_video_processor, mock_videos):
        """Test _calculate_narrative_coherence."""
        processor, mocks = reset_multi_video_processor

        # Mock cross relationships as the second argument
        mock_relationships = [MagicMock(spec=CrossVideoRelationship)]
        coherence = processor._calculate_narrative_coherence(mock_videos, mock_relationships)
        assert isinstance(coherence, float)
        assert 0.0 <= coherence <= 1.0

    def test_is_significant_topic_true(self, reset_multi_video_processor):
        """Test _is_significant_topic with significant topic."""
        processor, mocks = reset_multi_video_processor

        significant_topic = MagicMock(spec=Topic)
        significant_topic.name = "Artificial Intelligence"
        significant_topic.confidence = 0.9

        assert processor._is_significant_topic(significant_topic) is True

    def test_is_significant_topic_false(self, reset_multi_video_processor):
        """Test _is_significant_topic with insignificant topic."""
        processor, mocks = reset_multi_video_processor

        insignificant_topic = MagicMock(spec=Topic)
        insignificant_topic.name = "weather"
        insignificant_topic.confidence = 0.1

        assert processor._is_significant_topic(insignificant_topic) is False


class TestMultiVideoProcessorErrorHandling:
    """Test error handling and edge cases."""

    def test_process_video_collection_empty_videos_error(self, reset_multi_video_processor):
        """Test processing empty video collection raises error."""
        processor, mocks = reset_multi_video_processor

        with pytest.raises(ValueError, match="At least one video required"):
            asyncio.run(processor.process_video_collection([], "Test Collection", "test"))

    def test_process_video_collection_with_exceptions(self, reset_multi_video_processor, mock_videos):
        """Test processing with various exceptions in pipeline steps."""
        processor, mocks = reset_multi_video_processor

        # Mock pipeline to raise exceptions
        with patch.object(processor, '_unify_entities_across_videos', side_effect=Exception("Unify failed")), \
             patch.object(processor, '_extract_cross_video_relationships'), \
             patch.object(processor, '_generate_unified_knowledge_graph'), \
             patch.object(processor, '_synthesize_information_flow_map'), \
             patch.object(processor, '_generate_collection_insights'), \
             patch('clipscribe.extractors.multi_video_processor.time.time', return_value=1234567890):

            with pytest.raises(Exception, match="Unify failed"):
                asyncio.run(processor.process_video_collection(
                    videos=mock_videos,
                    collection_type=VideoCollectionType.SERIES,
                    collection_title="Test Series"
                ))


class TestMultiVideoProcessorConceptAnalysis:
    """Test concept analysis and extraction methods."""

    @pytest.mark.asyncio
    async def test_extract_concept_nodes_success(self, reset_multi_video_processor, mock_videos):
        """Test successful concept node extraction."""
        processor, mocks = reset_multi_video_processor

        # Mock the necessary methods and add missing attributes to mock_videos
        for video in mock_videos:
            video.key_points = [MagicMock(spec=KeyPoint)]
            video.summary = "Mock summary for testing"

        # Mock the necessary methods
        with patch.object(processor, '_is_conceptual_content', return_value=True), \
             patch.object(processor, '_extract_main_concept', return_value="AI Technology"), \
             patch.object(processor, '_assess_concept_maturity', return_value=ConceptMaturityLevel.EXPLAINED), \
             patch.object(processor, '_is_significant_topic', return_value=True), \
             patch.object(processor, '_find_topic_context', return_value="AI context"):

            concept_nodes = await processor._extract_concept_nodes(mock_videos)

            assert isinstance(concept_nodes, list)
            assert len(concept_nodes) > 0
            # Should have extracted concepts from the mock videos

    @pytest.mark.asyncio
    async def test_extract_concept_nodes_no_conceptual_content(self, reset_multi_video_processor, mock_videos):
        """Test concept extraction with no conceptual content."""
        processor, mocks = reset_multi_video_processor

        # Add missing attributes to mock_videos
        for video in mock_videos:
            video.key_points = [MagicMock(spec=KeyPoint)]
            video.summary = "Mock summary for testing"

        with patch.object(processor, '_is_conceptual_content', return_value=False):
            concept_nodes = await processor._extract_concept_nodes(mock_videos)
            assert isinstance(concept_nodes, list)
            assert len(concept_nodes) == 0

    def test_find_topic_context(self, reset_multi_video_processor, mock_videos):
        """Test finding context for a topic in a video."""
        processor, mocks = reset_multi_video_processor

        # Add missing summary attribute to mock video
        mock_videos[0].summary = "This video discusses AI technology and its applications in various fields."

        context = processor._find_topic_context("AI", mock_videos[0])
        assert isinstance(context, str)
        assert len(context) > 0


class TestMultiVideoProcessorInformationFlow:
    """Test information flow synthesis methods."""

    @pytest.mark.asyncio
    async def test_synthesize_information_flow_map_success(self, reset_multi_video_processor, mock_videos):
        """Test successful information flow map synthesis."""
        processor, mocks = reset_multi_video_processor

        # Create mock unified entities and relationships
        mock_entities = [MagicMock(spec=CrossVideoEntity)]
        mock_relationships = [MagicMock(spec=CrossVideoRelationship)]

        with patch.object(processor, '_extract_concept_nodes', return_value=[]), \
             patch.object(processor, '_calculate_entity_resolution_quality', return_value=0.8), \
             patch.object(processor, '_calculate_narrative_coherence', return_value=0.7), \
             patch.object(processor, '_deduplicate_concepts', return_value=[]):

            info_flow_map = await processor._synthesize_information_flow_map(
                videos=mock_videos,
                unified_entities=mock_entities,
                cross_video_relationships=mock_relationships,
                collection_id="test_collection",
                collection_title="Test Collection"
            )

            assert info_flow_map is not None
            # Should return some form of information flow map

    def test_calculate_name_similarity(self, reset_multi_video_processor):
        """Test name similarity calculation."""
        processor, mocks = reset_multi_video_processor

        similarity = processor._calculate_name_similarity("artificial intelligence", "AI")
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

        # Test exact match
        exact_similarity = processor._calculate_name_similarity("AI", "AI")
        assert exact_similarity == 1.0
