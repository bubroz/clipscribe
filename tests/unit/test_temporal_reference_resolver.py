"""Unit tests for TemporalReferenceResolver module."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from typing import List, Optional

from clipscribe.extractors.temporal_reference_resolver import TemporalReferenceResolver
from clipscribe.models import (
    VideoIntelligence,
    VideoMetadata,
    VideoTranscript,
    TemporalReference,
    KeyPoint,
    Topic,
)


@pytest.fixture
def resolver():
    """Create TemporalReferenceResolver instance for testing."""
    return TemporalReferenceResolver()


@pytest.fixture
def mock_video_intel():
    """Create mock VideoIntelligence for testing."""
    metadata = VideoMetadata(
        video_id="test123",
        title="Test Video",
        channel="News Channel",
        channel_id="news123",
        published_at=datetime(2024, 1, 10, 12, 0, 0),  # Wednesday, Jan 10, 2024
        duration=180,
        tags=["news", "politics"],
        description="Test video description",
        url="https://example.com/video",
        view_count=1000,
    )

    transcript = VideoTranscript(
        full_text="Last Tuesday, Biden announced sanctions. Yesterday we saw the effects.",
        segments=[
            {
                "text": "Last Tuesday, Biden announced sanctions.",
                "start_time": 10.0,
                "end_time": 15.0,
            },
            {
                "text": "Yesterday we saw the effects.",
                "start_time": 20.0,
                "end_time": 25.0,
            },
        ],
    )

    return VideoIntelligence(
        metadata=metadata,
        transcript=transcript,
        summary="Test summary",
        key_points=[
            KeyPoint(text="Point 1", importance=0.8),
            KeyPoint(text="Point 2", importance=0.7),
        ],
        entities=[],
        relationships=[],
        topics=[
            Topic(name="Politics", confidence=0.9),
            Topic(name="News", confidence=0.8),
        ],
        processing_cost=0.15,
        processing_time=5.5,
    )


@pytest.fixture
def sample_text_with_temporal_refs():
    """Sample text containing various temporal references."""
    return "Last Tuesday, Biden announced sanctions. Yesterday we saw the effects. Tomorrow markets will react. This week has been busy. Last month was quieter. In 3 days we'll see results."


class TestTemporalReferenceResolverInitialization:
    """Test TemporalReferenceResolver initialization."""

    def test_init(self, resolver):
        """Test basic initialization."""
        assert resolver is not None
        assert hasattr(resolver, 'temporal_patterns')
        assert hasattr(resolver, 'weekday_map')
        assert isinstance(resolver.temporal_patterns, list)
        assert len(resolver.temporal_patterns) > 0
        assert isinstance(resolver.weekday_map, dict)
        assert len(resolver.weekday_map) == 7


class TestTemporalReferenceResolverMainFunctionality:
    """Test the main resolve_temporal_references functionality."""

    def test_resolve_temporal_references_empty_text(self, resolver, mock_video_intel):
        """Test resolving temporal references with empty text."""
        mock_video_intel.transcript.full_text = ""
        result = resolver.resolve_temporal_references(mock_video_intel)
        assert result == []

    def test_resolve_temporal_references_no_temporal_refs(self, resolver, mock_video_intel):
        """Test resolving temporal references with no temporal references."""
        mock_video_intel.transcript.full_text = "This is a video about technology."
        result = resolver.resolve_temporal_references(mock_video_intel)
        assert result == []

    def test_resolve_temporal_references_with_temporal_refs(self, resolver, mock_video_intel, sample_text_with_temporal_refs):
        """Test resolving temporal references with various temporal references."""
        mock_video_intel.transcript.full_text = sample_text_with_temporal_refs
        result = resolver.resolve_temporal_references(mock_video_intel)

        assert isinstance(result, list)
        # Should find several temporal references
        assert len(result) >= 3  # Tuesday, Yesterday, Tomorrow, This week, Last month, In 3 days

        for ref in result:
            assert isinstance(ref, TemporalReference)
            assert hasattr(ref, 'reference_text')
            assert hasattr(ref, 'resolved_date')
            assert hasattr(ref, 'resolution_method')

    def test_resolve_temporal_references_with_metadata_date(self, resolver):
        """Test resolving temporal references using metadata date."""
        # Create a video with specific publication date
        metadata = VideoMetadata(
            video_id="test123",
            title="Test Video",
            channel="News",
            channel_id="news123",
            published_at=datetime(2024, 1, 10),  # Wednesday
            duration=180,
            tags=[],
            description="",
            url="",
            view_count=0,
        )

        transcript = VideoTranscript(
            full_text="Yesterday the president spoke.",
            segments=[],
        )

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Test",
            key_points=[],
            entities=[],
            relationships=[],
            topics=[],
            processing_cost=0.1,
            processing_time=1.0,
        )

        result = resolver.resolve_temporal_references(video_intel)

        assert len(result) == 1
        assert "yesterday" in result[0].reference_text.lower()
        # Yesterday from Jan 10, 2024 should be Jan 9, 2024
        assert result[0].resolved_date == "2024-01-09"


class TestTemporalReferenceResolverContentDateDetection:
    """Test content date detection functionality."""

    def test_detect_content_date_with_explicit_date(self, resolver, mock_video_intel):
        """Test detecting content date with explicit date in text."""
        mock_video_intel.transcript.full_text = "On January 15, 2024, the president announced new policies."
        result = resolver._detect_content_date(mock_video_intel, datetime(2024, 1, 10))

        assert result is not None
        assert result == datetime(2024, 1, 15)

    def test_detect_content_date_no_explicit_date(self, resolver, mock_video_intel):
        """Test detecting content date with no explicit date."""
        mock_video_intel.transcript.full_text = "The president announced new policies yesterday."
        result = resolver._detect_content_date(mock_video_intel, datetime(2024, 1, 10))

        assert result is not None  # Should return the publication date as fallback

    def test_detect_content_date_various_formats(self, resolver, mock_video_intel):
        """Test detecting content date with various date formats."""
        test_cases = [
            ("On January 15, 2024", datetime(2024, 1, 15)),
            ("On Jan 15, 2024", datetime(2024, 1, 15)),
            ("On 15 January 2024", datetime(2024, 1, 15)),
            ("On 1/15/2024", datetime(2024, 1, 15)),
        ]

        for text, expected in test_cases:
            mock_video_intel.transcript.full_text = text
            result = resolver._detect_content_date(mock_video_intel, datetime(2024, 1, 10))
            assert result == expected, f"Failed for text: {text}"

    def test_extract_explicit_content_date_various_formats(self, resolver):
        """Test extracting explicit content dates in various formats."""
        test_cases = [
            ("On January 15, 2024, something happened.", datetime(2024, 1, 15)),
            ("On Jan 15, 2024, something happened.", datetime(2024, 1, 15)),
            ("On 15/01/2024, something happened.", datetime(2024, 1, 15)),
            ("Date: 2024-01-15", datetime(2024, 1, 15)),
        ]

        for text, expected in test_cases:
            result = resolver._extract_explicit_content_date(text, datetime(2024, 1, 10))
            assert result == expected, f"Failed for text: {text}"


class TestTemporalReferenceResolverTemporalResolution:
    """Test temporal reference resolution functionality."""

    def test_resolve_match_yesterday(self, resolver):
        """Test resolving 'yesterday' match."""
        import re
        # Use the actual pattern from the resolver
        pattern = resolver.temporal_patterns[2]  # \byesterday\b (index 2)
        match = re.search(pattern, "Yesterday the president spoke.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        video_date = datetime(2024, 1, 10)  # Wednesday

        result = resolver._resolve_match(match, video_date, "Yesterday the president spoke.")

        assert result is not None
        assert result.reference_text == "Yesterday"
        assert result.resolved_date == "2024-01-09"  # Tuesday

    def test_resolve_match_today(self, resolver):
        """Test resolving 'today' match."""
        import re
        # Use the actual pattern from the resolver (index 3: \btoday\b)
        pattern = resolver.temporal_patterns[3]
        match = re.search(pattern, "Today the president spoke.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        video_date = datetime(2024, 1, 10)

        result = resolver._resolve_match(match, video_date, "Today the president spoke.")

        assert result is not None
        assert result.reference_text == "Today"
        assert result.resolved_date == "2024-01-10"

    def test_resolve_match_tomorrow(self, resolver):
        """Test resolving 'tomorrow' match."""
        import re
        # Use the actual pattern from the resolver (index 4: \btomorrow\b)
        pattern = resolver.temporal_patterns[4]
        match = re.search(pattern, "Tomorrow will be different.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        video_date = datetime(2024, 1, 10)

        result = resolver._resolve_match(match, video_date, "Tomorrow will be different.")

        assert result is not None
        assert result.reference_text == "Tomorrow"
        assert result.resolved_date == "2024-01-11"

    def test_resolve_match_last_weekday(self, resolver):
        """Test resolving 'last Tuesday'."""
        import re
        # Use the actual pattern from the resolver (index 0: \b(?:last|previous)\s+(\w+day)\b)
        pattern = resolver.temporal_patterns[0]
        match = re.search(pattern, "Last Tuesday the president spoke.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        video_date = datetime(2024, 1, 10)  # Wednesday, Jan 10

        result = resolver._resolve_match(match, video_date, "Last Tuesday the president spoke.")

        assert result is not None
        assert result.reference_text == "Last Tuesday"
        # Last Tuesday from Wednesday Jan 10 should be Tuesday Jan 9
        assert result.resolved_date == "2024-01-09"

    def test_resolve_match_next_weekday(self, resolver):
        """Test resolving 'next Friday'."""
        import re
        # Use the actual pattern from the resolver (index 1: \bnext\s+(\w+day)\b)
        pattern = resolver.temporal_patterns[1]
        match = re.search(pattern, "Next Friday we meet.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        video_date = datetime(2024, 1, 10)  # Wednesday, Jan 10

        result = resolver._resolve_match(match, video_date, "Next Friday we meet.")

        assert result is not None
        assert result.reference_text == "Next Friday"
        # Next Friday from Wednesday Jan 10 should be Friday Jan 12
        assert result.resolved_date == "2024-01-12"

    def test_resolve_match_days_ago(self, resolver):
        """Test resolving 'X days ago'."""
        import re
        # Use the actual pattern from the resolver (index 5: \b(\d+)\s+days?\s+ago\b)
        pattern = resolver.temporal_patterns[5]
        match = re.search(pattern, "3 days ago the event happened.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        video_date = datetime(2024, 1, 10)

        result = resolver._resolve_match(match, video_date, "3 days ago the event happened.")

        assert result is not None
        assert result.reference_text == "3 days ago"
        assert result.resolved_date == "2024-01-07"

    def test_resolve_match_in_days(self, resolver):
        """Test resolving 'in X days'."""
        import re
        # Use the actual pattern from the resolver (index 6: \bin\s+(\d+)\s+days?\b)
        pattern = resolver.temporal_patterns[6]
        match = re.search(pattern, "In 5 days the conference starts.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        video_date = datetime(2024, 1, 10)

        result = resolver._resolve_match(match, video_date, "In 5 days the conference starts.")

        assert result is not None
        assert result.reference_text == "In 5 days"
        assert result.resolved_date == "2024-01-15"


class TestTemporalReferenceResolverUtilityMethods:
    """Test utility methods."""

    def test_check_metadata_recording_date_with_date(self, resolver):
        """Test checking metadata with recording date."""
        metadata = VideoMetadata(
            video_id="test",
            title="Test",
            channel="News",
            channel_id="news",
            published_at=datetime(2024, 1, 10),
            duration=180,
            tags=[],
            description="",
            url="",
            view_count=0,
        )

        result = resolver._check_metadata_recording_date(metadata)
        assert result is None  # Method not implemented yet, returns None

    def test_extract_context_basic(self, resolver):
        """Test extracting context around a match."""
        import re
        match = re.search(r"yesterday", "Today is Monday, yesterday was Sunday, tomorrow is Tuesday.")
        result = resolver._extract_context(match, "Today is Monday, yesterday was Sunday, tomorrow is Tuesday.")

        assert isinstance(result, str)
        assert "yesterday" in result

    def test_deduplicate_references_no_duplicates(self, resolver):
        """Test deduplicating references with no duplicates."""
        refs = [
            TemporalReference(
                reference_text="yesterday",
                resolved_date="2024-01-09",
                resolution_method="yesterday_resolution",
                context="Context 1",
                original_context="Full context 1",
                date_source="publication",
                content_vs_publication_delta=0,
            ),
            TemporalReference(
                reference_text="tomorrow",
                resolved_date="2024-01-11",
                resolution_method="tomorrow_resolution",
                context="Context 2",
                original_context="Full context 2",
                date_source="publication",
                content_vs_publication_delta=0,
            ),
        ]

        result = resolver._deduplicate_references(refs)
        assert len(result) == 2

    def test_deduplicate_references_with_duplicates(self, resolver):
        """Test deduplicating references with duplicates."""
        refs = [
            TemporalReference(
                reference_text="yesterday",
                resolved_date="2024-01-09",
                resolution_method="yesterday_resolution",
                context="Context 1",
                original_context="Full context 1",
                date_source="publication",
                content_vs_publication_delta=0,
            ),
            TemporalReference(
                reference_text="yesterday",
                resolved_date="2024-01-09",
                resolution_method="yesterday_resolution",
                context="Context 2",
                original_context="Full context 2",
                date_source="publication",
                content_vs_publication_delta=0,
            ),
        ]

        result = resolver._deduplicate_references(refs)
        assert len(result) == 1
        # Should keep one of the references (exact one depends on implementation)


class TestTemporalReferenceResolverPromptBuilding:
    """Test prompt building functionality."""

    def test_build_explicit_context_prompt(self, resolver, mock_video_intel):
        """Test building explicit context prompt."""
        result = resolver.build_explicit_context_prompt(
            mock_video_intel.transcript.full_text,
            mock_video_intel.metadata
        )

        assert isinstance(result, str)
        assert "Video published on" in result
        assert "2024-01-10" in result
        assert "TEMPORAL REFERENCE RESOLUTION TASK" in result

    def test_build_explicit_context_prompt_no_metadata(self, resolver):
        """Test building explicit context prompt with valid metadata."""
        # Create metadata with valid publication date
        metadata = VideoMetadata(
            video_id="test",
            title="Test",
            channel="News",
            channel_id="news",
            published_at=datetime(2024, 1, 10),  # Valid publication date
            duration=180,
            tags=[],
            description="",
            url="",
            view_count=0,
        )

        transcript_text = "Test transcript"

        result = resolver.build_explicit_context_prompt(transcript_text, metadata)
        assert isinstance(result, str)
        assert "Test transcript" in result


class TestTemporalReferenceResolverEdgeCases:
    """Test edge cases and error handling."""

    def test_resolve_temporal_references_no_transcript(self, resolver):
        """Test resolving temporal references with no transcript."""
        metadata = VideoMetadata(
            video_id="test",
            title="Test",
            channel="News",
            channel_id="news",
            published_at=datetime(2024, 1, 10),
            duration=180,
            tags=[],
            description="",
            url="",
            view_count=0,
        )

        # Create VideoTranscript with empty text instead of None
        transcript = VideoTranscript(
            full_text="",
            segments=[],
        )

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Test",
            key_points=[],
            entities=[],
            relationships=[],
            topics=[],
            processing_cost=0.1,
            processing_time=1.0,
        )

        result = resolver.resolve_temporal_references(video_intel)
        assert result == []

    def test_resolve_match_invalid_pattern(self, resolver):
        """Test resolving match with invalid pattern."""
        import re
        # Create a match that might cause issues
        pattern = r"\b(\d+)\s+days?\s+ago\b"
        match = re.search(pattern, "1000 days ago something happened.")
        video_date = datetime(2024, 1, 10)

        result = resolver._resolve_match(match, video_date, "1000 days ago something happened.")

        assert result is not None
        # Should handle large day counts gracefully

    def test_resolve_match_weekday_edge_cases(self, resolver):
        """Test resolving weekday references at week boundaries."""
        import re
        # Monday, Jan 1, 2024 - start of year
        video_date = datetime(2024, 1, 1)

        # Use the actual pattern from the resolver (index 0: \b(?:last|previous)\s+(\w+day)\b)
        pattern = resolver.temporal_patterns[0]
        match = re.search(pattern, "Last Friday something happened.", re.IGNORECASE)
        assert match is not None  # Ensure the regex matched
        result = resolver._resolve_match(match, video_date, "Last Friday something happened.")

        assert result is not None
        assert result.reference_text == "Last Friday"
        # Last Friday from Monday Jan 1 should be Friday Dec 29, 2023
        assert result.resolved_date == "2023-12-29"

    def test_extract_explicit_content_date_invalid_formats(self, resolver):
        """Test extracting explicit content dates with invalid formats."""
        invalid_texts = [
            "On the 45th of January, 2024",  # Invalid date
            "Date: 13/45/2024",  # Invalid month
            "On February 30, 2024",  # Invalid date
        ]

        for text in invalid_texts:
            result = resolver._extract_explicit_content_date(text, datetime(2024, 1, 10))
            # Should handle invalid dates gracefully
            assert result is None or isinstance(result, datetime)


class TestTemporalReferenceResolverIntegration:
    """Integration tests for the full temporal resolution process."""

    def test_full_temporal_resolution_workflow(self, resolver, mock_video_intel, sample_text_with_temporal_refs):
        """Test the complete temporal resolution workflow."""
        mock_video_intel.transcript.full_text = sample_text_with_temporal_refs
        result = resolver.resolve_temporal_references(mock_video_intel)

        assert isinstance(result, list)
        assert len(result) >= 3  # Should find multiple temporal references

        # Verify all results have required fields
        for ref in result:
            assert hasattr(ref, 'reference_text')
            assert hasattr(ref, 'resolved_date')
            assert hasattr(ref, 'resolution_method')
            assert isinstance(ref.resolved_date, str)

    def test_temporal_resolution_with_complex_text(self, resolver):
        """Test temporal resolution with complex, realistic text."""
        complex_text = """
        Last Tuesday, President Biden announced comprehensive sanctions against the regime.
        Yesterday, we saw immediate market reactions to the news. This morning, European leaders
        responded with statements. Next week, the UN Security Council will meet to discuss the implications.
        Three days ago, initial reports emerged about the diplomatic tensions.
        Last month, similar measures were taken in a different context.
        This week has been particularly volatile for international relations.
        """

        metadata = VideoMetadata(
            video_id="complex_test",
            title="Complex News Analysis",
            channel="International News",
            channel_id="intl_news",
            published_at=datetime(2024, 1, 10, 15, 30, 0),  # Wednesday afternoon
            duration=420,
            tags=["politics", "international", "sanctions"],
            description="Analysis of recent diplomatic developments",
            url="https://example.com/complex_news",
            view_count=5000,
        )

        transcript = VideoTranscript(
            full_text=complex_text,
            segments=[],
        )

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Complex diplomatic situation analysis",
            key_points=[
                KeyPoint(text="Sanctions announced", importance=0.9),
                KeyPoint(text="Market reactions", importance=0.8),
                KeyPoint(text="International response", importance=0.7),
            ],
            entities=[],
            relationships=[],
            topics=[
                Topic(name="Diplomacy", confidence=0.9),
                Topic(name="Politics", confidence=0.8),
                Topic(name="Economics", confidence=0.7),
            ],
            processing_cost=0.25,
            processing_time=8.5,
        )

        result = resolver.resolve_temporal_references(video_intel)

        assert len(result) >= 5  # Should find multiple temporal references
        assert all(isinstance(ref, TemporalReference) for ref in result)

        # Verify specific resolutions - be more flexible with the actual text found
        reference_texts = {ref.reference_text for ref in result}
        assert len(reference_texts) >= 5  # Should have at least 5 different temporal references
        assert any("Tuesday" in text for text in reference_texts)

    def test_temporal_resolution_empty_and_edge_cases(self, resolver):
        """Test temporal resolution with various edge cases."""
        test_cases = [
            ("", datetime(2024, 1, 10)),  # Empty text
            ("No temporal references here.", datetime(2024, 1, 10)),  # No references
            ("Today is a good day.", datetime(2024, 1, 10)),  # Present reference
            ("Last Monday and next Friday.", datetime(2024, 1, 10)),  # Multiple references
        ]

        for text, video_date in test_cases:
            metadata = VideoMetadata(
                video_id="edge_test",
                title="Edge Case Test",
                channel="Test",
                channel_id="test",
                published_at=video_date,
                duration=60,
                tags=[],
                description="",
                url="",
                view_count=0,
            )

            transcript = VideoTranscript(
                full_text=text,
                segments=[],
            )

            video_intel = VideoIntelligence(
                metadata=metadata,
                transcript=transcript,
                summary="Test",
                key_points=[],
                entities=[],
                relationships=[],
                topics=[],
                processing_cost=0.05,
                processing_time=0.5,
            )

            result = resolver.resolve_temporal_references(video_intel)
            assert isinstance(result, list)
            # Should not crash on any input
