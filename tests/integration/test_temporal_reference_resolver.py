"""
Integration tests for TemporalReferenceResolver - Phase 3 implementation.

Tests temporal reference resolution, content date detection,
and integration with the VideoIntelligence model.
"""

import pytest
from datetime import datetime

from clipscribe.extractors.temporal_reference_resolver import TemporalReferenceResolver
from clipscribe.models import (
    VideoIntelligence,
    VideoTranscript,
    VideoMetadata,
    TemporalReference,
)


@pytest.fixture
def resolver():
    """Returns a TemporalReferenceResolver instance."""
    return TemporalReferenceResolver()


@pytest.fixture
def mock_video_intel():
    """Returns a mock VideoIntelligence object for testing."""
    transcript = VideoTranscript(
        full_text="Last Tuesday, Biden announced sanctions. Yesterday we saw the effects. Today markets reacted.",
        segments=[],
    )
    metadata = VideoMetadata(
        video_id="test123",
        title="Test Video",
        channel="News",
        channel_id="news123",
        published_at=datetime(2024, 1, 10),  # This is a Wednesday
        duration=180,
        tags=[],
        description="",
        url="",
        view_count=0,
    )
    return VideoIntelligence(
        metadata=metadata,
        transcript=transcript,
        summary="Test summary",
        key_points=[],
        entities=[],
        topics=[],
    )


def test_resolve_yesterday(resolver):
    reference_date = datetime(2024, 1, 10)
    resolved = resolver.resolve_temporal_references(
        VideoIntelligence(
            metadata=VideoMetadata(
                published_at=reference_date,
                video_id="1",
                title="t",
                channel="c",
                channel_id="ci",
                duration=1,
                tags=[],
                description="",
                url="",
                view_count=0,
            ),
            transcript=VideoTranscript(full_text="yesterday", segments=[]),
            summary="s",
            key_points=[],
            entities=[],
            topics=[],
        )
    )
    assert len(resolved) == 1
    assert resolved[0].resolved_date == "2024-01-09"


def test_resolve_today(resolver):
    reference_date = datetime(2024, 1, 10)
    resolved = resolver.resolve_temporal_references(
        VideoIntelligence(
            metadata=VideoMetadata(
                published_at=reference_date,
                video_id="1",
                title="t",
                channel="c",
                channel_id="ci",
                duration=1,
                tags=[],
                description="",
                url="",
                view_count=0,
            ),
            transcript=VideoTranscript(full_text="today", segments=[]),
            summary="s",
            key_points=[],
            entities=[],
            topics=[],
        )
    )
    assert len(resolved) == 1
    assert resolved[0].resolved_date == "2024-01-10"


def test_resolve_last_tuesday(resolver):
    # Reference date is a Wednesday
    reference_date = datetime(2024, 1, 10)
    resolved = resolver.resolve_temporal_references(
        VideoIntelligence(
            metadata=VideoMetadata(
                published_at=reference_date,
                video_id="1",
                title="t",
                channel="c",
                channel_id="ci",
                duration=1,
                tags=[],
                description="",
                url="",
                view_count=0,
            ),
            transcript=VideoTranscript(full_text="last Tuesday", segments=[]),
            summary="s",
            key_points=[],
            entities=[],
            topics=[],
        )
    )
    assert len(resolved) == 1
    # Last Tuesday was the 9th
    assert resolved[0].resolved_date == "2024-01-09"


def test_resolve_next_friday(resolver):
    # Reference date is a Wednesday
    reference_date = datetime(2024, 1, 10)
    resolved = resolver.resolve_temporal_references(
        VideoIntelligence(
            metadata=VideoMetadata(
                published_at=reference_date,
                video_id="1",
                title="t",
                channel="c",
                channel_id="ci",
                duration=1,
                tags=[],
                description="",
                url="",
                view_count=0,
            ),
            transcript=VideoTranscript(full_text="next Friday", segments=[]),
            summary="s",
            key_points=[],
            entities=[],
            topics=[],
        )
    )
    assert len(resolved) == 1
    # Next Friday is the 12th
    assert resolved[0].resolved_date == "2024-01-12"


def test_deduplicate_references(resolver):
    references = [
        TemporalReference(
            reference_text="yesterday",
            resolved_date="2024-01-09",
            confidence=0.9,
            resolution_method="test",
            context="test context",
        ),
        TemporalReference(
            reference_text="yesterday",
            resolved_date="2024-01-09",
            confidence=0.8,
            resolution_method="test",
            context="test context",
        ),
    ]
    deduplicated = resolver._deduplicate_references(references)
    assert len(deduplicated) == 1


def test_full_integration(resolver, mock_video_intel):
    resolved_references = resolver.resolve_temporal_references(mock_video_intel)

    assert len(resolved_references) == 3

    # Create a map for easy assertion
    results = {ref.reference_text: ref.resolved_date for ref in resolved_references}

    # Wednesday is Jan 10, 2024
    assert results["Last Tuesday"] == "2024-01-09"
    assert results["Yesterday"] == "2024-01-09"
    assert results["Today"] == "2024-01-10"
