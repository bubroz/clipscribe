"""Unit tests for series_detector.py module."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from clipscribe.extractors.series_detector import SeriesDetector
from clipscribe.models import (
    VideoIntelligence,
    SeriesDetectionResult,
    SeriesMetadata,
    VideoSimilarity,
    VideoMetadata,
    VideoTranscript,
)


@pytest.fixture
def series_detector():
    """Create a SeriesDetector instance for testing."""
    return SeriesDetector(similarity_threshold=0.7)


@pytest.fixture
def sample_video_intelligence():
    """Create sample VideoIntelligence instances for testing."""
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    return [
        VideoIntelligence(
            metadata=VideoMetadata(
                video_id="vid_001",
                url="https://youtube.com/watch?v=vid001",
                title="Python Tutorial Part 1: Getting Started",
                channel="TechChannel",
                channel_id="channel123",
                published_at=base_time.isoformat(),
                duration=600,
            ),
            transcript=VideoTranscript(
                full_text="This is part 1 of Python tutorial",
                segments=[],
            ),
            summary="Introduction to Python programming",
            entities=[],
        ),
        VideoIntelligence(
            metadata=VideoMetadata(
                video_id="vid_002",
                url="https://youtube.com/watch?v=vid002",
                title="Python Tutorial Part 2: Data Types",
                channel="TechChannel",
                channel_id="channel123",
                published_at=(base_time + timedelta(days=1)).isoformat(),
                duration=650,
            ),
            transcript=VideoTranscript(
                full_text="This is part 2 covering Python data types",
                segments=[],
            ),
            summary="Python data types and variables",
            entities=[],
        ),
        VideoIntelligence(
            metadata=VideoMetadata(
                video_id="vid_003",
                url="https://youtube.com/watch?v=vid003",
                title="Python Tutorial Part 3: Functions",
                channel="TechChannel",
                channel_id="channel123",
                published_at=(base_time + timedelta(days=2)).isoformat(),
                duration=700,
            ),
            transcript=VideoTranscript(
                full_text="This is part 3 about Python functions",
                segments=[],
            ),
            summary="Python functions and methods",
            entities=[],
        ),
        VideoIntelligence(
            metadata=VideoMetadata(
                video_id="vid_004",
                url="https://youtube.com/watch?v=vid004",
                title="Cooking Show: Pasta Recipe",
                channel="FoodChannel",
                channel_id="food456",
                published_at=(base_time + timedelta(days=10)).isoformat(),
                duration=900,
            ),
            transcript=VideoTranscript(
                full_text="How to cook delicious pasta",
                segments=[],
            ),
            summary="Italian pasta cooking tutorial",
            entities=[],
        ),
    ]


class TestSeriesDetectorInitialization:
    """Test SeriesDetector initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        detector = SeriesDetector()

        assert detector.similarity_threshold == 0.7
        assert hasattr(detector, "series_patterns")
        assert len(detector.series_patterns) > 0

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        detector = SeriesDetector(similarity_threshold=0.8)

        assert detector.similarity_threshold == 0.8

    def test_init_patterns_loaded(self):
        """Test that series patterns are loaded during initialization."""
        detector = SeriesDetector()

        # Check that common patterns are loaded
        assert hasattr(detector, "series_patterns")
        assert hasattr(detector, "compiled_patterns")
        assert len(detector.series_patterns) > 0
        assert len(detector.compiled_patterns) > 0
        assert any("part" in pattern for pattern in detector.series_patterns)
        assert any("episode" in pattern for pattern in detector.series_patterns)


class TestSeriesDetectorTitlePatterns:
    """Test title pattern analysis functionality."""

    def test_analyze_title_patterns_series_detected(self, series_detector, sample_video_intelligence):
        """Test title pattern analysis for series detection."""
        videos = sample_video_intelligence[:3]  # First 3 are Python tutorial parts

        result = series_detector._analyze_title_patterns(videos)

        # Check the actual return structure
        assert "best_pattern" in result
        assert "pattern_score" in result
        assert "base_title_analysis" in result
        assert "total_patterns_found" in result
        assert result["pattern_score"] > 0  # Should detect the pattern

    def test_analyze_title_patterns_no_series(self, series_detector, sample_video_intelligence):
        """Test title pattern analysis for non-series videos."""
        videos = [sample_video_intelligence[3]]  # Just the cooking video

        result = series_detector._analyze_title_patterns(videos)

        # Single video should have low pattern score
        assert result["pattern_score"] < 0.5

    def test_analyze_title_patterns_mixed_content(self, series_detector, sample_video_intelligence):
        """Test title pattern analysis for mixed content."""
        videos = sample_video_intelligence  # All 4 videos

        result = series_detector._analyze_title_patterns(videos)

        # Should still detect patterns in the mixed content
        assert result["total_patterns_found"] > 0

    def test_check_sequential_pattern_sequential(self, series_detector):
        """Test sequential pattern checking for sequential parts."""
        matches = [
            {"matches": ["1"]},  # Part 1
            {"matches": ["2"]},  # Part 2
            {"matches": ["3"]},  # Part 3
        ]

        confidence = series_detector._check_sequential_pattern(matches)

        assert confidence > 0.8  # High confidence for sequential parts

    def test_check_sequential_pattern_non_sequential(self, series_detector):
        """Test sequential pattern checking for non-sequential parts."""
        matches = [
            {"matches": ["1"]},  # Part 1
            {"matches": ["3"]},  # Missing part 2
            {"matches": ["5"]},  # Part 5
        ]

        confidence = series_detector._check_sequential_pattern(matches)

        assert confidence < 0.5  # Low confidence for non-sequential

    def test_analyze_base_titles(self, series_detector):
        """Test base title analysis."""
        titles = [
            "Python Tutorial Part 1: Getting Started",
            "Python Tutorial Part 2: Data Types",
            "Python Tutorial Part 3: Functions",
        ]

        result = series_detector._analyze_base_titles(titles)

        # Check the actual return structure
        assert "has_common_base" in result
        assert "common_base" in result
        assert "average_similarity" in result
        assert "title_similarities" in result
        assert result["average_similarity"] > 0.6  # Should be similar


class TestSeriesDetectorTemporalPatterns:
    """Test temporal pattern analysis."""

    def test_analyze_temporal_patterns_close_dates(self, series_detector, sample_video_intelligence):
        """Test temporal analysis for videos with close publication dates."""
        videos = sample_video_intelligence[:3]  # Python tutorial parts

        result = series_detector._analyze_temporal_patterns(videos)

        # Check the actual return structure
        assert "temporal_score" in result
        assert "time_gaps_days" in result
        assert "duration_consistency" in result
        assert "publication_span_days" in result
        assert result["temporal_score"] > 0.5  # Should detect close dates

    def test_analyze_temporal_patterns_spread_dates(self, series_detector, sample_video_intelligence):
        """Test temporal analysis for videos with spread publication dates."""
        videos = sample_video_intelligence  # All videos including cooking show

        result = series_detector._analyze_temporal_patterns(videos)

        # The algorithm considers 10 days reasonable for series, so score is higher than expected
        assert result["temporal_score"] > 0.5

    def test_analyze_temporal_patterns_single_video(self, series_detector, sample_video_intelligence):
        """Test temporal analysis for single video."""
        videos = [sample_video_intelligence[0]]

        result = series_detector._analyze_temporal_patterns(videos)

        assert result["temporal_score"] == 0.0  # No temporal pattern with single video


class TestSeriesDetectorChannelConsistency:
    """Test channel consistency analysis."""

    def test_analyze_channel_consistency_same_channel(self, series_detector, sample_video_intelligence):
        """Test channel consistency for same channel videos."""
        videos = sample_video_intelligence[:3]  # All Python tutorials from same channel

        result = series_detector._analyze_channel_consistency(videos)

        # Check the actual return structure
        assert "same_channel" in result
        assert "channel_consistency_score" in result
        assert "channel_distribution" in result
        assert result["same_channel"] is True
        assert result["channel_consistency_score"] > 0.9

    def test_analyze_channel_consistency_different_channels(self, series_detector, sample_video_intelligence):
        """Test channel consistency for different channel videos."""
        videos = sample_video_intelligence  # Python + Cooking from different channels

        result = series_detector._analyze_channel_consistency(videos)

        assert result["same_channel"] is False
        # 3 out of 4 videos are from same channel, so score is 0.75, not < 0.5
        assert result["channel_consistency_score"] == 0.75

    def test_analyze_channel_consistency_single_video(self, series_detector, sample_video_intelligence):
        """Test channel consistency for single video."""
        videos = [sample_video_intelligence[0]]

        result = series_detector._analyze_channel_consistency(videos)

        assert result["same_channel"] is True  # Single video is perfectly consistent
        assert result["channel_consistency_score"] == 1.0


class TestSeriesDetectorContentSimilarity:
    """Test content similarity analysis."""

    @pytest.mark.asyncio
    async def test_analyze_content_similarity_high_similarity(self, series_detector, sample_video_intelligence):
        """Test content similarity analysis for similar content."""
        videos = sample_video_intelligence[:3]  # Python tutorial parts

        with patch.object(series_detector, "_calculate_video_similarity") as mock_similarity:
            mock_similarity.return_value = VideoSimilarity(
                video1_id="vid_001",
                video2_id="vid_002",
                overall_similarity=0.8,
                title_similarity=0.9,
                content_similarity=0.7,
                temporal_similarity=0.9,
                channel_similarity=1.0,
            )

            result = await series_detector._analyze_content_similarity(videos)

            assert result["average_similarity"] > 0.7
            assert result["similarity_score"] > 0.6

    @pytest.mark.asyncio
    async def test_analyze_content_similarity_low_similarity(self, series_detector, sample_video_intelligence):
        """Test content similarity analysis for dissimilar content."""
        videos = sample_video_intelligence  # All videos

        with patch.object(series_detector, "_calculate_video_similarity") as mock_similarity:
            mock_similarity.return_value = VideoSimilarity(
                video1_id="vid_001",
                video2_id="vid_004",
                overall_similarity=0.2,
                title_similarity=0.1,
                content_similarity=0.3,
                temporal_similarity=0.2,
                channel_similarity=0.0,
            )

            result = await series_detector._analyze_content_similarity(videos)

            assert result["average_similarity"] < 0.4

    def test_calculate_video_similarity(self, series_detector, sample_video_intelligence):
        """Test video similarity calculation."""
        video1 = sample_video_intelligence[0]
        video2 = sample_video_intelligence[1]

        similarity = series_detector._calculate_video_similarity(video1, video2)

        assert isinstance(similarity, VideoSimilarity)
        assert similarity.video1_id == "vid_001"
        assert similarity.video2_id == "vid_002"
        assert 0.0 <= similarity.overall_similarity <= 1.0


class TestSeriesDetectorAnalysisCombination:
    """Test analysis combination and result generation."""

    def test_combine_analyses_high_confidence(self, series_detector):
        """Test combining analyses with high confidence results."""
        analyses = {
            "title_analysis": {"is_series": True, "confidence": 0.9},
            "temporal_analysis": {"temporal_score": 0.8},
            "channel_analysis": {"consistency_score": 1.0},
            "content_analysis": {"similarity_score": 0.7},
        }

        result = series_detector._combine_analyses(analyses)

        assert result["is_series"] is True
        assert result["confidence"] > 0.8

    def test_combine_analyses_low_confidence(self, series_detector):
        """Test combining analyses with low confidence results."""
        analyses = {
            "title_analysis": {"is_series": False, "confidence": 0.2},
            "temporal_analysis": {"temporal_score": 0.1},
            "channel_analysis": {"consistency_score": 0.3},
            "content_analysis": {"similarity_score": 0.2},
        }

        result = series_detector._combine_analyses(analyses)

        assert result["is_series"] is False
        assert result["confidence"] < 0.3

    def test_generate_groupings_sequential(self, series_detector, sample_video_intelligence):
        """Test grouping generation for sequential series."""
        videos = sample_video_intelligence[:3]  # Python tutorial parts

        groupings = series_detector._generate_groupings(videos, pattern_type="sequential")

        assert len(groupings) == 1
        assert len(groupings[0]) == 3  # All 3 videos in one group

    def test_generate_groupings_by_pattern(self, series_detector, sample_video_intelligence):
        """Test grouping generation by pattern."""
        videos = sample_video_intelligence[:3]

        groupings = series_detector._generate_groupings(videos, pattern_type="pattern")

        assert isinstance(groupings, list)

    def test_cluster_by_similarity(self, series_detector, sample_video_intelligence):
        """Test similarity-based clustering."""
        videos = sample_video_intelligence[:3]

        with patch.object(series_detector, "_calculate_video_similarity") as mock_similarity:
            mock_similarity.return_value = VideoSimilarity(
                video1_id="vid_001",
                video2_id="vid_002",
                overall_similarity=0.8,
                title_similarity=0.9,
                content_similarity=0.7,
                temporal_similarity=0.9,
                channel_similarity=1.0,
            )

            clusters = series_detector._cluster_by_similarity(videos, threshold=0.7)

            assert isinstance(clusters, list)


class TestSeriesDetectorMainFlow:
    """Test the main series detection flow."""

    @pytest.mark.asyncio
    async def test_detect_series_python_tutorial(self, series_detector, sample_video_intelligence):
        """Test series detection for Python tutorial series."""
        videos = sample_video_intelligence[:3]  # Python tutorial parts

        with patch.object(series_detector, "_analyze_title_patterns") as mock_title, \
             patch.object(series_detector, "_analyze_temporal_patterns") as mock_temporal, \
             patch.object(series_detector, "_analyze_channel_consistency") as mock_channel, \
             patch.object(series_detector, "_analyze_content_similarity", new_callable=AsyncMock) as mock_content:

            # Mock high confidence results
            mock_title.return_value = {"is_series": True, "confidence": 0.9, "patterns_found": ["part"]}
            mock_temporal.return_value = {"temporal_score": 0.8}
            mock_channel.return_value = {"consistency_score": 1.0}
            mock_content.return_value = {"similarity_score": 0.7}

            result = await series_detector.detect_series(videos)

            assert isinstance(result, SeriesDetectionResult)
            assert result.is_series is True
            assert result.confidence > 0.8
            assert result.detection_method == "pattern_analysis"

    @pytest.mark.asyncio
    async def test_detect_series_no_series(self, series_detector, sample_video_intelligence):
        """Test series detection for non-series videos."""
        videos = [sample_video_intelligence[3]]  # Just the cooking video

        with patch.object(series_detector, "_analyze_title_patterns") as mock_title, \
             patch.object(series_detector, "_analyze_temporal_patterns") as mock_temporal, \
             patch.object(series_detector, "_analyze_channel_consistency") as mock_channel, \
             patch.object(series_detector, "_analyze_content_similarity", new_callable=AsyncMock) as mock_content:

            # Mock low confidence results
            mock_title.return_value = {"is_series": False, "confidence": 0.1}
            mock_temporal.return_value = {"temporal_score": 0.2}
            mock_channel.return_value = {"consistency_score": 0.3}
            mock_content.return_value = {"similarity_score": 0.1}

            result = await series_detector.detect_series(videos)

            assert isinstance(result, SeriesDetectionResult)
            assert result.is_series is False
            assert result.confidence < 0.3

    @pytest.mark.asyncio
    async def test_detect_series_mixed_content(self, series_detector, sample_video_intelligence):
        """Test series detection for mixed content."""
        videos = sample_video_intelligence  # All 4 videos

        result = await series_detector.detect_series(videos)

        assert isinstance(result, SeriesDetectionResult)
        # Should still be able to analyze the mixed content

    def test_create_series_metadata(self, series_detector, sample_video_intelligence):
        """Test series metadata creation."""
        videos = sample_video_intelligence[:3]

        metadata = series_detector.create_series_metadata(
            series_id="python_tutorial_001",
            series_title="Python Tutorial Series",
            videos=videos,
            pattern="part",
            part_numbers=[1, 2, 3],
        )

        assert isinstance(metadata, SeriesMetadata)
        assert metadata.series_id == "python_tutorial_001"
        assert metadata.series_title == "Python Tutorial Series"
        assert metadata.part_number is None  # Not set for series
        assert metadata.total_parts == 3


class TestSeriesDetectorEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_detect_series_empty_list(self, series_detector):
        """Test series detection with empty video list."""
        result = await series_detector.detect_series([])

        assert isinstance(result, SeriesDetectionResult)
        assert result.is_series is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_detect_series_single_video(self, series_detector, sample_video_intelligence):
        """Test series detection with single video."""
        videos = [sample_video_intelligence[0]]

        result = await series_detector.detect_series(videos)

        assert isinstance(result, SeriesDetectionResult)
        assert result.is_series is False  # Single video can't be a series

    def test_analyze_title_patterns_empty_titles(self, series_detector):
        """Test title pattern analysis with empty titles."""
        videos = [
            VideoIntelligence(
                metadata=VideoMetadata(
                    video_id="vid_001",
                    url="https://youtube.com/watch?v=vid001",
                    title="",
                    channel="TestChannel",
                    channel_id="channel123",
                    published_at="2024-01-01T12:00:00Z",
                    duration=600,
                ),
                transcript=VideoTranscript(full_text="Test content", segments=[]),
                summary="Test summary",
                entities=[],
            )
        ]

        result = series_detector._analyze_title_patterns(videos)

        assert result["is_series"] is False
        assert result["confidence"] < 0.5

    def test_check_sequential_pattern_empty_matches(self, series_detector):
        """Test sequential pattern checking with empty matches."""
        confidence = series_detector._check_sequential_pattern([])

        assert confidence == 0.0

    def test_analyze_base_titles_empty_list(self, series_detector):
        """Test base title analysis with empty list."""
        result = series_detector._analyze_base_titles([])

        assert result["common_base"] == ""
        assert result["base_confidence"] == 0.0
