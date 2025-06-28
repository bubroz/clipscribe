"""
Unit tests for Web Research Integration in Timeline Building Pipeline.

Tests the new v2.17.0 web research validation and timeline enrichment capabilities.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from clipscribe.utils.web_research import (
    WebResearchIntegrator,
    TimelineContextValidator,
    ResearchResult,
    TimelineEnrichment
)


@pytest.fixture
def sample_timeline_events():
    """Sample timeline events for testing."""
    return [
        {
            'event_id': 'evt_video1_100',
            'timestamp': datetime(2023, 12, 15, 10, 0, 0),
            'description': 'Iran announced new uranium enrichment activities',
            'involved_entities': ['Iran', 'Nuclear Program'],
            'confidence': 0.9,
            'source_video_id': 'video1'
        },
        {
            'event_id': 'evt_video1_200',
            'timestamp': datetime(2023, 12, 16, 14, 30, 0),
            'description': 'IAEA expresses concerns about compliance',
            'involved_entities': ['IAEA', 'Iran'],
            'confidence': 0.8,
            'source_video_id': 'video1'
        }
    ]


@pytest.fixture
def web_research_integrator():
    """Web research integrator with research disabled for testing."""
    return WebResearchIntegrator(enable_research=False)


@pytest.fixture
def timeline_validator():
    """Timeline context validator."""
    return TimelineContextValidator()


class TestWebResearchIntegrator:
    """Test cases for WebResearchIntegrator."""
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key."""
        integrator = WebResearchIntegrator(enable_research=False)
        assert not integrator.enable_research
        assert integrator.research_model is None
    
    def test_initialization_with_api_key(self):
        """Test initialization with API key but research disabled."""
        integrator = WebResearchIntegrator(api_key="test_key", enable_research=False)
        assert not integrator.enable_research
        assert integrator.research_model is None
    
    @pytest.mark.asyncio
    async def test_validate_timeline_events_disabled(self, web_research_integrator, sample_timeline_events):
        """Test timeline validation when research is disabled."""
        collection_context = "Test video collection about nuclear program"
        
        results = await web_research_integrator.validate_timeline_events(
            sample_timeline_events, collection_context
        )
        
        assert len(results) == 2
        for result in results:
            assert isinstance(result, ResearchResult)
            assert result.validation_status == "unverified"
            assert result.confidence == 0.6
            assert "web research disabled" in result.external_context
    
    @pytest.mark.asyncio
    async def test_enrich_timeline_disabled(self, web_research_integrator, sample_timeline_events):
        """Test timeline enrichment when research is disabled."""
        collection_theme = "nuclear program"
        
        # Create mock research results
        research_results = [
            ResearchResult(
                event_description="Test event",
                validation_status="unverified",
                confidence=0.6,
                external_context="Test context",
                sources_cited=["local_extraction"]
            )
            for _ in sample_timeline_events
        ]
        
        enrichments = await web_research_integrator.enrich_timeline_with_context(
            sample_timeline_events, research_results, collection_theme
        )
        
        assert len(enrichments) == 2
        for enrichment in enrichments:
            assert isinstance(enrichment, TimelineEnrichment)
            assert enrichment.confidence_boost == 0.0
            assert "local_extraction" in enrichment.validation_sources
    
    def test_create_research_query(self, web_research_integrator):
        """Test research query creation."""
        event_descriptions = [
            "Iran announced new uranium enrichment activities",
            "IAEA expresses concerns about compliance"
        ]
        context = "Nuclear program analysis"
        
        query = web_research_integrator._create_research_query(event_descriptions, context)
        
        assert "Nuclear program analysis" in query
        # Should extract proper nouns
        assert any(term in query for term in ["Iran", "IAEA"])
    
    def test_build_validation_prompt(self, web_research_integrator, sample_timeline_events):
        """Test validation prompt building."""
        collection_context = "Test collection"
        research_query = "Iran IAEA nuclear"
        
        prompt = web_research_integrator._build_validation_prompt(
            sample_timeline_events, collection_context, research_query
        )
        
        assert "Test collection" in prompt
        assert "Iran IAEA nuclear" in prompt
        assert "validation_status" in prompt
        assert "confidence" in prompt
    
    def test_create_local_validation_results(self, web_research_integrator, sample_timeline_events):
        """Test local validation result creation."""
        results = web_research_integrator._create_local_validation_results(sample_timeline_events)
        
        assert len(results) == 2
        for result in results:
            assert isinstance(result, ResearchResult)
            assert result.validation_status == "unverified"
            assert result.confidence == 0.6
            assert "local_extraction" in result.sources_cited


class TestTimelineContextValidator:
    """Test cases for TimelineContextValidator."""
    
    def test_validate_temporal_consistency_valid(self, timeline_validator, sample_timeline_events):
        """Test temporal consistency validation with valid timeline."""
        results = timeline_validator.validate_temporal_consistency(sample_timeline_events)
        
        assert len(results) == 2
        for result in results:
            assert result['temporal_consistency'] is True
            assert result['consistency_score'] == 1.0
            assert len(result['issues']) == 0
    
    def test_validate_temporal_consistency_negative_gap(self, timeline_validator):
        """Test temporal consistency with negative time gap."""
        events = [
            {
                'event_id': 'evt_1',
                'timestamp': datetime(2023, 12, 16, 10, 0, 0),
                'description': 'Second event'
            },
            {
                'event_id': 'evt_2',
                'timestamp': datetime(2023, 12, 15, 10, 0, 0),  # Earlier than first
                'description': 'First event'
            }
        ]
        
        results = timeline_validator.validate_temporal_consistency(events)
        
        # Should detect the temporal inconsistency
        assert len(results) == 2
        # Second event should have consistency issues
        assert results[1]['temporal_consistency'] is False
        assert results[1]['consistency_score'] == 0.3
        assert 'Negative time gap detected' in results[1]['issues']
    
    def test_validate_temporal_consistency_large_gap(self, timeline_validator):
        """Test temporal consistency with large time gap."""
        events = [
            {
                'event_id': 'evt_1',
                'timestamp': datetime(2020, 1, 1, 10, 0, 0),
                'description': 'First event'
            },
            {
                'event_id': 'evt_2',
                'timestamp': datetime(2023, 12, 15, 10, 0, 0),  # 3+ years later
                'description': 'Second event'
            }
        ]
        
        results = timeline_validator.validate_temporal_consistency(events)
        
        # Should detect large time gap
        assert len(results) == 2
        assert results[1]['consistency_score'] == 0.7  # Reduced but not failed
        assert 'Large time gap (>1 year)' in results[1]['issues']
    
    def test_calculate_time_gap(self, timeline_validator):
        """Test time gap calculation."""
        event1 = {'timestamp': datetime(2023, 12, 15, 10, 0, 0)}
        event2 = {'timestamp': datetime(2023, 12, 16, 10, 0, 0)}
        
        gap = timeline_validator._calculate_time_gap(event1, event2)
        
        assert gap == timedelta(days=1)
    
    def test_calculate_time_gap_invalid(self, timeline_validator):
        """Test time gap calculation with invalid timestamps."""
        event1 = {'timestamp': None}
        event2 = {'timestamp': "invalid"}
        
        gap = timeline_validator._calculate_time_gap(event1, event2)
        
        assert gap == timedelta(seconds=0)


class TestDataClasses:
    """Test the data classes used in web research."""
    
    def test_research_result_creation(self):
        """Test ResearchResult data class."""
        result = ResearchResult(
            event_description="Test event",
            validation_status="validated",
            confidence=0.9,
            external_context="External context",
            sources_cited=["source1", "source2"],
            timeline_adjustments={"corrected_date": "2023-12-15"},
            enrichment_data={"additional_info": "Extra details"}
        )
        
        assert result.event_description == "Test event"
        assert result.validation_status == "validated"
        assert result.confidence == 0.9
        assert len(result.sources_cited) == 2
        assert result.timeline_adjustments["corrected_date"] == "2023-12-15"
    
    def test_timeline_enrichment_creation(self):
        """Test TimelineEnrichment data class."""
        enrichment = TimelineEnrichment(
            original_event_id="evt_1",
            enhanced_description="Enhanced description",
            additional_context="Additional context",
            related_events=["evt_2", "evt_3"],
            confidence_boost=0.1,
            validation_sources=["source1"]
        )
        
        assert enrichment.original_event_id == "evt_1"
        assert enrichment.enhanced_description == "Enhanced description"
        assert enrichment.confidence_boost == 0.1
        assert len(enrichment.related_events) == 2
        assert "source1" in enrichment.validation_sources


@pytest.mark.asyncio
class TestWebResearchIntegrationMocked:
    """Test web research integration with mocked API calls."""
    
    @patch('clipscribe.utils.web_research.genai')
    async def test_validate_timeline_events_with_api(self, mock_genai, sample_timeline_events):
        """Test timeline validation with mocked API calls."""
        # Setup mock
        mock_model = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''
        {
            "results": [
                {
                    "event_description": "Iran announced new uranium enrichment activities",
                    "validation_status": "validated",
                    "confidence": 0.9,
                    "external_context": "Confirmed by IAEA reports",
                    "sources_cited": ["IAEA", "news reports"]
                },
                {
                    "event_description": "IAEA expresses concerns about compliance", 
                    "validation_status": "enhanced",
                    "confidence": 0.85,
                    "external_context": "IAEA issued statement on compliance",
                    "sources_cited": ["IAEA official statement"]
                }
            ]
        }
        '''
        mock_model.generate_content_async.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        # Test with research enabled
        integrator = WebResearchIntegrator(api_key="test_key", enable_research=True)
        integrator.research_model = mock_model
        
        results = await integrator.validate_timeline_events(
            sample_timeline_events, "Nuclear program analysis"
        )
        
        assert len(results) == 2
        assert results[0].validation_status == "validated"
        assert results[0].confidence == 0.9
        assert results[1].validation_status == "enhanced"
        assert "IAEA" in results[0].sources_cited
    
    @patch('clipscribe.utils.web_research.genai')
    async def test_api_failure_fallback(self, mock_genai, sample_timeline_events):
        """Test fallback behavior when API fails."""
        # Setup mock to raise exception
        mock_model = AsyncMock()
        mock_model.generate_content_async.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        integrator = WebResearchIntegrator(api_key="test_key", enable_research=True)
        integrator.research_model = mock_model
        
        results = await integrator.validate_timeline_events(
            sample_timeline_events, "Nuclear program analysis"
        )
        
        # Should fall back to local validation
        assert len(results) == 2
        for result in results:
            assert result.validation_status == "unverified"
            assert "local_extraction" in result.sources_cited


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 