# tests/helpers.py
from datetime import datetime
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript, EnhancedEntity


def create_mock_video_metadata(video_id="test_vid", title="Test Video", channel_id="test_chan"):
    """
    Creates a valid VideoMetadata object for testing.
    """
    return VideoMetadata(
        video_id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        title=title,
        channel="Test Channel",
        channel_id=channel_id,
        published_at=datetime.now(),
        duration=300,
        view_count=1000,
        description="A test video description.",
        tags=["test", "video"],
    )


def create_mock_video_intelligence(video_id="test_vid", title="Test Video", channel_id="test_chan", processing_cost=0.0):
    """
    Creates a valid VideoIntelligence object with all required fields for testing.
    """
    metadata = VideoMetadata(
        video_id=video_id,
        url=f"https://test.com/video/{video_id}",
        title=title,
        channel="Test Channel",
        channel_id=channel_id,
        published_at=datetime.now(),
        duration=300,
        view_count=1000,
        description="A test video description.",
        tags=["test", "video"],
    )

    transcript = VideoTranscript(
        full_text="This is a test transcript.",
        segments=[{"text": "This is a test transcript.", "start": 0.0, "end": 5.0}],
    )

    entities = [
        EnhancedEntity(
            name="Test Entity",
            type="TEST",
            mention_count=1,
            extraction_sources=["test_source"],
            canonical_form="Test Entity",
            context_windows=[],
            aliases=[],
            temporal_distribution=[],
        )
    ]

    return VideoIntelligence(
        metadata=metadata,
        transcript=transcript,
        summary="This is a test summary.",
        entities=entities,
        relationships=[],
        key_points=[],
        topics=[],
        processing_cost=processing_cost,
    )
