import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from clipscribe.extractors.multi_video_processor import MultiVideoProcessor
from clipscribe.models import (
    VideoIntelligence, 
    VideoMetadata, 
    KeyPoint, 
    ExtractedDate, 
    ConsolidatedTimeline, 
    TimelineEvent,
    VideoTranscript
)

@pytest.fixture
def processor():
    """Provides a MultiVideoProcessor instance for testing."""
    return MultiVideoProcessor(use_ai_validation=True)

@pytest.fixture
def base_video_intelligence():
    """Provides a base VideoIntelligence object for tests."""
    return VideoIntelligence(
        metadata=VideoMetadata(
            video_id="video1",
            title="A video about an event in 1999",
            channel="Test Channel",
            channel_id="UC123",
            duration=60,
            url="http://test.com/video1",
            published_at=datetime(2024, 1, 1, 12, 0, 0),
        ),
        transcript=VideoTranscript(full_text="mock transcript", segments=[]),
        summary="Test summary",
        key_points=[] # Key points will be added per test
    )

@pytest.mark.asyncio
async def test_timeline_uses_date_from_key_point(processor, base_video_intelligence):
    """Verify timeline uses date extracted directly from key point text."""
    base_video_intelligence.key_points = [
        KeyPoint(timestamp=10, text="The main event happened on Christmas Day 2023.", importance=0.9)
    ]
    
    async def side_effect(text, source_type):
        if "Christmas Day 2023" in text:
            return ExtractedDate(parsed_date=datetime(2023, 12, 25), original_text="Christmas Day 2023", confidence=0.95, source=source_type)
        return None
    processor._extract_date_from_text = AsyncMock(side_effect=side_effect)

    timeline = await processor._synthesize_event_timeline([base_video_intelligence], [], "collection1")
    
    assert len(timeline.events) == 1
    event = timeline.events[0]
    assert event.timestamp == datetime(2023, 12, 25)
    assert event.date_source == "key_point_content"
    assert event.extracted_date.original_text == "Christmas Day 2023"

@pytest.mark.asyncio
async def test_timeline_falls_back_to_title_date(processor, base_video_intelligence):
    """Verify timeline falls back to video title's date if key point has no date."""
    base_video_intelligence.key_points = [
        KeyPoint(timestamp=20, text="Another thing happened.", importance=0.8)
    ]
    
    async def side_effect(text, source_type):
        if source_type == 'video_title':
            return ExtractedDate(parsed_date=datetime(1999, 1, 1), original_text="1999", confidence=0.9, source=source_type)
        return None
    processor._extract_date_from_text = AsyncMock(side_effect=side_effect)

    timeline = await processor._synthesize_event_timeline([base_video_intelligence], [], "collection1")
    
    assert len(timeline.events) == 1
    event = timeline.events[0]
    assert event.timestamp == datetime(1999, 1, 1)
    assert event.date_source == "video_title"
    assert event.extracted_date.original_text == "1999"

@pytest.mark.asyncio
async def test_timeline_falls_back_to_publication_date(processor, base_video_intelligence):
    """Verify timeline falls back to publication date when no other date is found."""
    base_video_intelligence.key_points = [
        KeyPoint(timestamp=30, text="A final point.", importance=0.7)
    ]
    
    # Mock returns None for all calls
    processor._extract_date_from_text = AsyncMock(return_value=None)

    timeline = await processor._synthesize_event_timeline([base_video_intelligence], [], "collection1")
    
    assert len(timeline.events) == 1
    event = timeline.events[0]
    expected_fallback_date = base_video_intelligence.metadata.published_at + timedelta(seconds=30)
    assert event.timestamp == expected_fallback_date
    assert event.date_source == "video_published_date"
    assert event.extracted_date is None 