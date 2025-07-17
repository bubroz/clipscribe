"""
Integration tests for TemporalReferenceResolver - Phase 3 implementation.

Tests temporal reference resolution, content date detection,
and integration with the VideoIntelligence model.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List
from datetime import datetime

from clipscribe.extractors.temporal_reference_resolver import TemporalReferenceResolver, TemporalReference
from clipscribe.models import VideoIntelligence, VideoTranscript, VideoMetadata


class TestTemporalReferenceResolver:
    """Test temporal reference resolution functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = TemporalReferenceResolver()
        
        # Create mock video intelligence with transcript containing temporal references
        self.mock_transcript = VideoTranscript(
            full_text="Last Tuesday, Biden announced sanctions. Yesterday we saw the effects. Today markets reacted.",
            segments=[
                {"text": "Last Tuesday, Biden announced sanctions.", "timestamp": "00:01:30"},
                {"text": "Yesterday we saw the effects.", "timestamp": "00:02:15"},
                {"text": "Today markets reacted.", "timestamp": "00:02:45"}
            ]
        )
        
        self.mock_metadata = VideoMetadata(
            video_id="test123",
            title="Test Video",
            channel="News",
            channel_id="news123",
            published_at=datetime(2024, 1, 10),  # Wednesday
            duration=180
        )
        
        self.mock_video_intel = VideoIntelligence(
            metadata=self.mock_metadata,
            transcript=self.mock_transcript,
            summary="Test summary"
        )
    
    def test_resolver_initialization(self):
        """Test that the resolver initializes correctly."""
        assert self.resolver is not None
        assert len(self.resolver.temporal_patterns) > 0
        assert len(self.resolver.weekday_map) == 7
    
    def test_detect_content_date_explicit(self):
        """Test explicit content date detection."""
        transcript_text = "This is June 27, 2025"
        publication_date = datetime(2025, 7, 1)
        content_date = self.resolver._detect_content_date(Mock(transcript=Mock(full_text=transcript_text)), publication_date)
        assert content_date == datetime(2025, 6, 27)
    
    def test_detect_content_date_gemini(self):
        """Test Gemini-extracted content date."""
        mock_video_intel = Mock(dates=[{'normalized_date': '2025-06-27T00:00:00', 'context': 'today'}])
        publication_date = datetime(2025, 7, 1)
        content_date = self.resolver._detect_content_date(mock_video_intel, publication_date)
        assert content_date == datetime(2025, 6, 27)
    
    def test_resolve_yesterday(self):
        match = Mock(group=lambda i: 'yesterday' if i==0 else None, start=lambda: 0, end=lambda: 9)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2024-01-09'
    
    def test_resolve_today(self):
        match = Mock(group=lambda i: 'today' if i==0 else None, start=lambda: 0, end=lambda: 4)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2024-01-10'
    
    def test_resolve_tomorrow(self):
        match = Mock(group=lambda i: 'tomorrow' if i==0 else None, start=lambda: 0, end=lambda: 6)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2024-01-11'
    
    def test_resolve_last_weekday(self):
        match = Mock(group=lambda i: 'last_weekday' if i==0 else None, start=lambda: 0, end=lambda: 12)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2024-01-09'
    
    def test_resolve_next_weekday(self):
        match = Mock(group=lambda i: 'next_weekday' if i==0 else None, start=lambda: 0, end=lambda: 12)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2024-01-11'
    
    def test_resolve_days_ago(self):
        match = Mock(group=lambda i: 'days_ago' if i==0 else None, start=lambda: 0, end=lambda: 8)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2024-01-02'
    
    def test_resolve_last_week(self):
        match = Mock(group=lambda i: 'last_week' if i==0 else None, start=lambda: 0, end=lambda: 7)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2023-12-27'
    
    def test_resolve_last_month(self):
        match = Mock(group=lambda i: 'last_month' if i==0 else None, start=lambda: 0, end=lambda: 8)
        resolved = self.resolver._resolve_match(match, datetime(2024, 1, 10), 'test text')
        assert resolved.resolved_date == '2023-12-10'
    
    def test_deduplicate_references(self):
        references = [
            TemporalReference(resolved_date='2024-01-09', confidence=0.9),
            TemporalReference(resolved_date='2024-01-09', confidence=0.8)
        ]
        deduplicated = self.resolver._deduplicate_references(references)
        assert len(deduplicated) == 1
        assert deduplicated[0].resolved_date == '2024-01-09'
        assert deduplicated[0].confidence == 0.9
    
    def test_extract_context(self):
        match = Mock(group=lambda i: 'yesterday' if i==0 else None, start=lambda: 0, end=lambda: 9)
        context = self.resolver._extract_context(match, self.mock_video_intel)
        assert context == '2024-01-09'
    
    def test_resolve_temporal_references(self):
        resolved_references = self.resolver.resolve_temporal_references(self.mock_video_intel)
        assert len(resolved_references) == 3
        assert resolved_references[0].resolved_date == '2024-01-09'
        assert resolved_references[1].resolved_date == '2024-01-10'
        assert resolved_references[2].resolved_date == '2024-01-10'
    
    def test_integration_with_video_intelligence(self):
        resolved_references = self.resolver.resolve_temporal_references(self.mock_video_intel)
        assert len(resolved_references) == 3
        assert resolved_references[0].resolved_date == '2024-01-09'
        assert resolved_references[1].resolved_date == '2024-01-10'
        assert resolved_references[2].resolved_date == '2024-01-10'

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 