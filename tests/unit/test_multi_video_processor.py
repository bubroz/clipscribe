# tests/unit/test_multi_video_processor.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from clipscribe.extractors.multi_video_processor import MultiVideoProcessor
from clipscribe.models import MultiVideoIntelligence, VideoCollectionType
from tests.helpers import create_mock_video_intelligence

@pytest.fixture
def processor():
    """Fixture to create a MultiVideoProcessor with mocked dependencies."""
    with patch('clipscribe.extractors.multi_video_processor.EntityNormalizer'), \
         patch('clipscribe.extractors.multi_video_processor.SeriesDetector'):
        return MultiVideoProcessor()

@pytest.mark.asyncio
async def test_process_video_collection(processor):
    """Test the main process_video_collection method."""
    videos = [
        create_mock_video_intelligence('vid1'),
        create_mock_video_intelligence('vid2')
    ]
    
    with patch.object(processor, '_unify_entities_across_videos', new_callable=AsyncMock) as mock_unify, \
         patch.object(processor, '_extract_cross_video_relationships', new_callable=AsyncMock) as mock_extract, \
         patch.object(processor, '_generate_unified_knowledge_graph', new_callable=AsyncMock) as mock_graph, \
         patch.object(processor, '_synthesize_information_flow_map', new_callable=AsyncMock) as mock_flow, \
         patch.object(processor, '_generate_collection_insights', new_callable=AsyncMock) as mock_insights:

        mock_unify.return_value = []
        mock_extract.return_value = []
        mock_graph.return_value = {}
        mock_flow.return_value = Mock()
        mock_insights.return_value = []

        result = await processor.process_video_collection(videos, VideoCollectionType.SERIES, 'Test Collection')

        assert isinstance(result, MultiVideoIntelligence)
        assert result.collection_title == 'Test Collection'
        mock_unify.assert_called_once()
        mock_extract.assert_called_once()
