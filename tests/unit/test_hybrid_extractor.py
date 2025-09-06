"""Unit tests for HybridEntityExtractor module."""
import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from typing import List, Tuple

from clipscribe.extractors.hybrid_extractor import HybridEntityExtractor
from clipscribe.models import Entity, VideoMetadata, VideoTranscript

# DEPRECATED: Skip all tests in this file
pytest.skip("These tests are deprecated - HybridExtractor now uses Voxtral-Grok pipeline, Gemini validation removed", allow_module_level=True)
from clipscribe.config.settings import Settings


@pytest.fixture
def mock_entity():
    """Create a mock entity for testing."""
    return Entity(
        entity="John Doe",
        type="PERSON",
        properties={"source": "spacy"}
    )


@pytest.fixture
def mock_video_metadata():
    """Create mock video metadata."""
    return VideoMetadata(
        video_id="test_123",
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="test_channel",
        published_at=datetime(2024, 1, 15, 14, 30, 0),
        duration=300,
        view_count=1000,
        description="Test description",
        tags=["test"]
    )


@pytest.fixture
def mock_video_intelligence(mock_video_metadata):
    """Create mock video intelligence."""
    from clipscribe.models import VideoTranscript
    vi = VideoIntelligence(
        metadata=mock_video_metadata,
        transcript=VideoTranscript(full_text="Test transcript", segments=[]),
        summary="Test summary",
        entities=[],
        relationships=[],
        key_points=[],
        topics=[]
    )
    return vi


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.google_api_key = "test-api-key"
    settings.gemini_request_timeout = 30.0
    return settings


@pytest.fixture
def mock_spacy_extractor():
    """Create mock SpaCy extractor."""
    extractor = MagicMock()
    return extractor


@pytest.fixture
def mock_gemini_transcriber():
    """Create mock Gemini transcriber."""
    transcriber = MagicMock()
    transcriber.model = MagicMock()
    transcriber.model.generate_content_async = AsyncMock()
    return transcriber


class TestHybridEntityExtractor:
    """Test HybridEntityExtractor functionality."""

    @pytest.fixture
    def extractor(self, mock_settings):
        """Create a HybridEntityExtractor instance for testing."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor', mock_spacy_extractor), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber', mock_gemini_transcriber), \
             patch('clipscribe.extractors.hybrid_extractor.Settings', return_value=mock_settings):
            return HybridEntityExtractor()

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings') as mock_settings_class:

            mock_settings = MagicMock()
            mock_settings.gemini_request_timeout = 30.0
            mock_settings_class.return_value = mock_settings

            extractor = HybridEntityExtractor()

            assert extractor.confidence_threshold == 0.8
            assert extractor.batch_size == 20
            assert extractor.enable_cost_tracking is True
            assert extractor.total_cost == 0.0
            assert extractor.entities_processed == 0
            assert extractor.llm_validations == 0
            assert extractor.request_timeout == 30.0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings') as mock_settings_class:

            mock_settings = MagicMock()
            mock_settings.gemini_request_timeout = 30.0
            mock_settings_class.return_value = mock_settings

            extractor = HybridEntityExtractor(
                confidence_threshold=0.9,
                batch_size=10,
                enable_cost_tracking=False
            )

            assert extractor.confidence_threshold == 0.9
            assert extractor.batch_size == 10
            assert extractor.enable_cost_tracking is False

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_extract_entities_empty_spacy_results(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test extraction when SpaCy finds no entities."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_spacy = MagicMock()
        mock_spacy.extract_entities.return_value = []  # No entities found
        mock_spacy_class.return_value = mock_spacy

        mock_transcriber = MagicMock()
        mock_transcriber.model = MagicMock()
        mock_transcriber.model.generate_content_async = AsyncMock()
        mock_transcriber_class.return_value = mock_transcriber

        # Setup LLM response for fallback
        mock_response = MagicMock()
        mock_response.text = '[{"name": "Apple Inc.", "type": "ORGANIZATION"}]'
        mock_transcriber.model.generate_content_async.return_value = mock_response

        extractor = HybridEntityExtractor()

        # Run extraction
        result = asyncio.run(extractor.extract_entities("This is a test text with no obvious entities."))

        # Verify fallback was used
        assert len(result) == 1
        assert result[0].entity == "Apple Inc."
        assert result[0].type == "ORGANIZATION"
        mock_transcriber.model.generate_content_async.assert_called_once()

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_extract_entities_high_confidence_only(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test extraction with only high-confidence entities (no LLM validation needed)."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_spacy = MagicMock()
        high_conf_entity = Entity(entity="John Doe", type="PERSON", properties={})
        mock_spacy.extract_entities.return_value = [(high_conf_entity, 0.9)]
        mock_spacy_class.return_value = mock_spacy

        mock_transcriber = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber

        extractor = HybridEntityExtractor(confidence_threshold=0.8)

        # Run extraction
        result = asyncio.run(extractor.extract_entities("John Doe is a person."))

        # Verify results
        assert len(result) == 1
        assert result[0].name == "John Doe"
        assert result[0].type == "PERSON"

        # Verify no LLM calls were made
        mock_transcriber.model.generate_content_async.assert_not_called()

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_extract_entities_with_llm_validation(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test extraction with LLM validation for low-confidence entities."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_spacy = MagicMock()
        high_conf_entity = Entity(entity="John Doe", type="PERSON", properties={})
        low_conf_entity = Entity(entity="Apple Corp", type="ORG", properties={})
        mock_spacy.extract_entities.return_value = [
            (high_conf_entity, 0.9),
            (low_conf_entity, 0.5)
        ]
        mock_spacy_class.return_value = mock_spacy

        mock_transcriber = MagicMock()
        mock_transcriber.model = MagicMock()
        mock_transcriber.model.generate_content_async = AsyncMock()
        mock_transcriber_class.return_value = mock_transcriber

        # Setup LLM response
        mock_response = MagicMock()
        mock_response.text = '[{"name": "Apple Corp", "type": "ORGANIZATION", "confidence": 0.9, "correct": true}]'
        mock_transcriber.model.generate_content_async.return_value = mock_response

        extractor = HybridEntityExtractor(confidence_threshold=0.8)

        # Run extraction
        result = asyncio.run(extractor.extract_entities("John Doe works at Apple Corp."))

        # Verify results
        assert len(result) == 2
        entities = [e.entity for e in result]
        assert "John Doe" in entities
        assert "Apple Corp" in entities

        # Verify LLM was called for validation
        mock_transcriber.model.generate_content_async.assert_called_once()

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_extract_entities_force_llm_validation(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test extraction with forced LLM validation."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_spacy = MagicMock()
        high_conf_entity = Entity(entity="John Doe", type="PERSON", properties={})
        mock_spacy.extract_entities.return_value = [(high_conf_entity, 0.9)]
        mock_spacy_class.return_value = mock_spacy

        mock_transcriber = MagicMock()
        mock_transcriber.model = MagicMock()
        mock_transcriber.model.generate_content_async = AsyncMock()
        mock_transcriber_class.return_value = mock_transcriber

        # Setup LLM response
        mock_response = MagicMock()
        mock_response.text = '[{"name": "John Doe", "type": "PERSON", "confidence": 0.95, "correct": true}]'
        mock_transcriber.model.generate_content_async.return_value = mock_response

        extractor = HybridEntityExtractor()

        # Run extraction with forced validation
        result = asyncio.run(extractor.extract_entities("John Doe is a person.", force_llm_validation=True))

        # Verify LLM was called despite high confidence
        mock_transcriber.model.generate_content_async.assert_called_once()
        assert len(result) == 1

    def test_create_validation_prompt(self):
        """Test prompt creation for entity validation."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()

            entities = [
                (Entity(entity="Apple Inc.", type="ORG", properties={}), 0.6),
                (Entity(entity="Microsoft", type="ORG", properties={}), 0.7)
            ]

            prompt = extractor._create_validation_prompt(entities, "Apple Inc. and Microsoft are tech companies.")

            assert "Apple Inc." in prompt
            assert "Microsoft" in prompt
            assert '"name": "Apple Inc."' in prompt
            assert '"name": "Microsoft"' in prompt
            assert "tech companies" in prompt
            assert "validate" in prompt.lower()
            assert "confidence" in prompt.lower()

    def test_get_entity_context(self):
        """Test entity context extraction."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()

            text = "Apple Inc. is a technology company based in Cupertino, California."
            context = extractor._get_entity_context("Apple Inc.", text, window=50)

            assert "Apple Inc." in context
            assert "**Apple Inc.**" in context  # Should be highlighted

    def test_get_entity_context_not_found(self):
        """Test entity context extraction when entity not found."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()

            text = "This text doesn't contain the entity."
            context = extractor._get_entity_context("Missing Entity", text)

            assert context == ""

    def test_parse_validation_response_valid(self):
        """Test parsing valid LLM validation response."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()

            response_text = '''
            Here is the validation result:
            [
                {
                    "name": "Apple Inc.",
                    "type": "ORGANIZATION",
                    "confidence": 0.95,
                    "correct": true
                }
            ]
            '''

            entities = [(Entity(entity="Apple Inc.", type="ORG", properties={}), 0.6)]
            result = extractor._parse_validation_response(response_text, entities)

            assert len(result) == 1
            assert result[0].entity == "Apple Inc."
            assert result[0].type == "ORGANIZATION"
            assert result[0].confidence == 0.95

    def test_parse_validation_response_invalid_json(self):
        """Test parsing invalid LLM response."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()

            response_text = "This is not JSON at all"
            entities = [(Entity(entity="Test Entity", type="PERSON", properties={}), 0.6)]
            result = extractor._parse_validation_response(response_text, entities)

            # Should return original entities
            assert len(result) == 1
            assert result[0].name == "Test Entity"

    def test_parse_validation_response_no_json_array(self):
        """Test parsing response without JSON array."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()

            response_text = '{"message": "No entities found"}'
            entities = [(Entity(entity="Test Entity", type="PERSON", properties={}), 0.6)]
            result = extractor._parse_validation_response(response_text, entities)

            # Should return original entities
            assert len(result) == 1
            assert result[0].name == "Test Entity"

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_llm_only_extraction_success(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test successful LLM-only extraction."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_transcriber = MagicMock()
        mock_transcriber.model = MagicMock()
        mock_transcriber.model.generate_content_async = AsyncMock()
        mock_transcriber_class.return_value = mock_transcriber

        # Setup successful LLM response
        mock_response = MagicMock()
        mock_response.text = '[{"name": "Google", "type": "ORGANIZATION", "confidence": 0.9}]'
        mock_transcriber.model.generate_content_async.return_value = mock_response

        extractor = HybridEntityExtractor()

        # Run LLM-only extraction
        result = asyncio.run(extractor._llm_only_extraction("Google is a search engine."))

        assert len(result) == 1
        assert result[0].entity == "Google"
        assert result[0].type == "ORGANIZATION"
        assert result[0].properties["source"] == "llm"

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_llm_only_extraction_failure(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test LLM-only extraction failure."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_transcriber = MagicMock()
        mock_transcriber.model = MagicMock()
        mock_transcriber.model.generate_content_async = AsyncMock(side_effect=Exception("LLM error"))
        mock_transcriber_class.return_value = mock_transcriber

        extractor = HybridEntityExtractor()

        # Run LLM-only extraction
        result = asyncio.run(extractor._llm_only_extraction("Test text."))

        # Should return empty list on failure
        assert len(result) == 0

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_validate_with_llm_batch_processing(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test LLM validation with batch processing."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_transcriber = MagicMock()
        mock_transcriber.model = MagicMock()
        mock_transcriber.model.generate_content_async = AsyncMock()
        mock_transcriber_class.return_value = mock_transcriber

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = '[{"name": "Entity1", "type": "PERSON", "confidence": 0.9, "correct": true}]'
        mock_transcriber.model.generate_content_async.return_value = mock_response

        extractor = HybridEntityExtractor(batch_size=2)

        # Create test entities
        entities = [
            (Entity(entity="Entity1", type="PERSON", properties={}), 0.6),
            (Entity(entity="Entity2", type="PERSON", properties={}), 0.7),
            (Entity(entity="Entity3", type="PERSON", properties={}), 0.5)
        ]

        # Run validation
        result = asyncio.run(extractor._validate_with_llm(entities, "Test context"))

        # Should process in batches of 2
        assert mock_transcriber.model.generate_content_async.call_count == 2
        assert len(result) == 1  # Only valid entities returned

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_validate_with_llm_error_handling(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test LLM validation error handling."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_transcriber = MagicMock()
        mock_transcriber.model = MagicMock()
        mock_transcriber.model.generate_content_async = AsyncMock(side_effect=Exception("API error"))
        mock_transcriber_class.return_value = mock_transcriber

        extractor = HybridEntityExtractor()

        entities = [(Entity(name="Test Entity", type="PERSON", properties={}), 0.6)]
        result = asyncio.run(extractor._validate_with_llm(entities, "Test context"))

        # Should return original entity with reduced confidence
        assert len(result) == 1
        assert result[0].entity == "Test Entity"
        assert result[0].confidence == 0.6 * 0.8  # Reduced confidence

    def test_get_total_cost(self):
        """Test getting total cost."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()
            extractor.total_cost = 1.23

            assert extractor.get_total_cost() == 1.23

    def test_get_statistics(self):
        """Test getting extraction statistics."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'):

            extractor = HybridEntityExtractor()
            extractor.entities_processed = 100
            extractor.llm_validations = 25
            extractor.total_cost = 0.50
            extractor.confidence_threshold = 0.8

            stats = extractor.get_statistics()

            assert stats["entities_processed"] == 100
            assert stats["llm_validations"] == 25
            assert stats["validation_rate"] == 25.0
            assert stats["total_cost"] == 0.50
            assert stats["confidence_threshold"] == 0.8

    def test_log_cost_metrics_no_entities(self):
        """Test cost metrics logging with no entities."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'), \
             patch('clipscribe.extractors.hybrid_extractor.logger') as mock_logger:

            extractor = HybridEntityExtractor()
            extractor.entities_processed = 0

            extractor._log_cost_metrics()

            mock_logger.info.assert_called_once()
            # Should handle division by zero gracefully

    def test_log_cost_metrics_with_entities(self):
        """Test cost metrics logging with entities."""
        with patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor'), \
             patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber'), \
             patch('clipscribe.extractors.hybrid_extractor.Settings'), \
             patch('clipscribe.extractors.hybrid_extractor.logger') as mock_logger:

            extractor = HybridEntityExtractor()
            extractor.entities_processed = 100
            extractor.llm_validations = 20
            extractor.total_cost = 0.75

            extractor._log_cost_metrics()

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "100" in call_args  # entities processed
            assert "20" in call_args   # llm validations
            assert "0.75" in call_args # total cost

    @patch('clipscribe.extractors.hybrid_extractor.SpacyEntityExtractor')
    @patch('clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('clipscribe.extractors.hybrid_extractor.Settings')
    def test_extract_entities_deduplication(self, mock_settings_class, mock_transcriber_class, mock_spacy_class):
        """Test entity deduplication in final results."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.gemini_request_timeout = 30.0
        mock_settings_class.return_value = mock_settings

        mock_spacy = MagicMock()
        # Create entities that will be deduplicated
        entity1 = Entity(name="Apple Inc.", type="ORGANIZATION", confidence=0.9, properties={})
        entity2 = Entity(name="Apple Inc.", type="ORGANIZATION", confidence=0.8, properties={})
        mock_spacy.extract_entities.return_value = [
            (entity1, 0.9),
            (entity2, 0.8)
        ]
        mock_spacy_class.return_value = mock_spacy

        mock_transcriber = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber

        extractor = HybridEntityExtractor(confidence_threshold=0.95)  # Force validation

        # Setup LLM response
        mock_response = MagicMock()
        mock_response.text = '[{"name": "Apple Inc.", "type": "ORGANIZATION", "confidence": 0.85, "correct": true}]'
        mock_transcriber.model.generate_content_async = AsyncMock(return_value=mock_response)

        # Run extraction
        result = asyncio.run(extractor.extract_entities("Apple Inc. is a company.", force_llm_validation=True))

        # Should have only one entity after deduplication
        assert len(result) == 1
        assert result[0].entity == "Apple Inc."
