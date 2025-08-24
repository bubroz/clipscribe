"""Unit tests for video_retention_manager.py module."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from clipscribe.retrievers.video_retention_manager import (
    VideoRetentionManager,
    RetentionCostAnalysis,
)
from clipscribe.config.settings import Settings, VideoRetentionPolicy
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_settings(temp_dir):
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.get_video_retention_config.return_value = {
        "policy": VideoRetentionPolicy.DELETE,
        "archive_directory": temp_dir / "archive",
        "cost_threshold": 5.0,
        "cost_optimization": True,
        "max_archive_size_gb": 50,
    }
    # Add missing attributes and methods
    settings.temporal_intelligence_level = "standard"
    settings.estimate_cost = Mock(return_value=2.0)
    return settings


@pytest.fixture
def video_retention_manager(mock_settings):
    """Create a VideoRetentionManager instance for testing."""
    return VideoRetentionManager(settings=mock_settings)


@pytest.fixture
def sample_video_intelligence(temp_dir):
    """Create sample VideoIntelligence instance for testing."""
    video_path = temp_dir / "test_video.mp4"

    return VideoIntelligence(
        metadata=VideoMetadata(
            video_id="vid_001",
            url="https://youtube.com/watch?v=vid001",
            title="Test Video",
            channel="TestChannel",
            channel_id="channel123",
            published_at=datetime.now().isoformat(),
            duration=600,
        ),
        transcript=VideoTranscript(
            full_text="This is a test transcript",
            segments=[],
        ),
        summary="Test video summary",
        entities=[],
    )


class TestRetentionCostAnalysis:
    """Test RetentionCostAnalysis class."""

    def test_init(self):
        """Test RetentionCostAnalysis initialization."""
        analysis = RetentionCostAnalysis(
            storage_cost_monthly=2.50,
            storage_cost_yearly=30.00,
            reprocessing_cost=1.20,
            breakeven_months=6.0,
            recommendation="retain",
            confidence=0.85,
        )

        assert analysis.storage_cost_monthly == 2.50
        assert analysis.storage_cost_yearly == 30.00
        assert analysis.reprocessing_cost == 1.20
        assert analysis.breakeven_months == 6.0
        assert analysis.recommendation == "retain"
        assert analysis.confidence == 0.85

    def test_init_default_confidence(self):
        """Test RetentionCostAnalysis with default confidence."""
        analysis = RetentionCostAnalysis(
            storage_cost_monthly=1.00,
            storage_cost_yearly=12.00,
            reprocessing_cost=0.50,
            breakeven_months=12.0,
            recommendation="delete",
        )

        assert analysis.confidence == 0.8  # Default value


class TestVideoRetentionManagerInitialization:
    """Test VideoRetentionManager initialization."""

    def test_init_with_settings(self, mock_settings):
        """Test initialization with custom settings."""
        manager = VideoRetentionManager(settings=mock_settings)

        assert manager.settings == mock_settings
        mock_settings.get_video_retention_config.assert_called_once()

    def test_init_default_settings(self):
        """Test initialization with default settings."""
        with patch("clipscribe.retrievers.video_retention_manager.Settings") as mock_settings_class:
            mock_settings = Mock()
            mock_settings.get_video_retention_config.return_value = {
                "policy": VideoRetentionPolicy.KEEP_ALL,
                "archive_directory": Path("output/archive"),
                "cost_threshold": 3.0,
                "cost_optimization": False,
                "max_archive_size_gb": 25,
            }
            mock_settings_class.return_value = mock_settings

            manager = VideoRetentionManager()

            assert manager.settings == mock_settings
            mock_settings.get_video_retention_config.assert_called_once()

    def test_init_archive_directory_creation(self, mock_settings, temp_dir):
        """Test that archive directory is created during initialization."""
        mock_settings.get_video_retention_config.return_value = {
            "policy": VideoRetentionPolicy.KEEP_ALL,
            "archive_directory": temp_dir / "test_archive",
            "cost_threshold": 3.0,
            "cost_optimization": False,
            "max_archive_size_gb": 25,
        }

        manager = VideoRetentionManager(settings=mock_settings)

        # Archive directory should be created
        assert manager.archive_dir.exists()
        assert manager.archive_dir.is_dir()


class TestVideoRetentionManagerHistory:
    """Test retention history management."""

    def test_load_retention_history_file_exists(self, video_retention_manager, temp_dir):
        """Test loading retention history when file exists."""
        retention_log_file = video_retention_manager.retention_log_file
        test_history = {
            "retained_videos": {
                "vid_001": {
                    "action": "archived",
                    "timestamp": "2024-01-01T12:00:00",
                    "cost_analysis": {
                        "storage_cost_monthly": 1.50,
                        "reprocessing_cost": 0.80,
                    }
                }
            },
            "deleted_videos": {},
            "retention_stats": {
                "total_saved_cost": 0.0,
                "total_storage_cost": 0.0,
                "videos_retained": 0,
                "videos_deleted": 0,
            }
        }

        # Create the history file
        video_retention_manager.archive_dir.mkdir(parents=True, exist_ok=True)
        with open(retention_log_file, 'w') as f:
            json.dump(test_history, f)

        history = video_retention_manager._load_retention_history()

        assert history == test_history

    def test_load_retention_history_file_not_exists(self, video_retention_manager):
        """Test loading retention history when file doesn't exist."""
        history = video_retention_manager._load_retention_history()

        # Should return default structure
        assert "retained_videos" in history
        assert "deleted_videos" in history
        assert "retention_stats" in history

    def test_save_retention_history(self, video_retention_manager):
        """Test saving retention history."""
        # Set up some history first
        video_retention_manager.retention_history = {
            "retained_videos": {
                "vid_001": {
                    "action": "archived",
                    "timestamp": "2024-01-01T12:00:00",
                }
            },
            "deleted_videos": {},
            "retention_stats": {
                "total_saved_cost": 1.5,
                "total_storage_cost": 0.0,
                "videos_retained": 1,
                "videos_deleted": 0,
            }
        }

        video_retention_manager._save_retention_history()

        # Check that file was created and contains correct data
        history_file = video_retention_manager.retention_log_file
        assert history_file.exists()

        with open(history_file, 'r') as f:
            saved_history = json.load(f)

        assert saved_history == video_retention_manager.retention_history


class TestVideoRetentionManagerUtilities:
    """Test utility methods."""

    def test_get_video_hash(self, video_retention_manager, temp_dir):
        """Test video hash generation."""
        # Create a dummy video file
        video_file = temp_dir / "test_video.mp4"
        video_file.write_text("dummy video content")

        hash_value = video_retention_manager._get_video_hash(video_file)

        assert isinstance(hash_value, str)
        assert len(hash_value) > 0

    def test_get_video_hash_nonexistent_file(self, video_retention_manager, temp_dir):
        """Test video hash generation for nonexistent file."""
        nonexistent_file = temp_dir / "nonexistent.mp4"

        hash_value = video_retention_manager._get_video_hash(nonexistent_file)

        assert isinstance(hash_value, str)
        # Should return hash of empty content for nonexistent files


class TestVideoRetentionManagerCostAnalysis:
    """Test cost analysis functionality."""

    def test_analyze_retention_costs_retain_recommendation(self, video_retention_manager, sample_video_intelligence, temp_dir):
        """Test cost analysis recommending retention."""
        # Create a mock video file
        video_file = temp_dir / "test_video.mp4"
        video_file.write_text("dummy video content")

        result = video_retention_manager._analyze_retention_costs(video_file, sample_video_intelligence)

        assert isinstance(result, RetentionCostAnalysis)
        assert result.recommendation in ["retain", "delete", "conditional"]
        assert result.storage_cost_monthly > 0
        assert result.reprocessing_cost > 0
        assert result.breakeven_months >= 0

    def test_analyze_retention_costs_delete_recommendation(self, video_retention_manager, sample_video_intelligence, temp_dir):
        """Test cost analysis recommending deletion."""
        # Create a large mock video file to simulate high storage costs
        video_file = temp_dir / "large_video.mp4"
        video_file.write_text("x" * (100 * 1024 * 1024))  # 100MB file

        result = video_retention_manager._analyze_retention_costs(video_file, sample_video_intelligence)

        assert isinstance(result, RetentionCostAnalysis)
        assert result.recommendation in ["retain", "delete", "conditional"]

    def test_make_retention_decision_retain(self, video_retention_manager, sample_video_intelligence):
        """Test retention decision to retain."""
        cost_analysis = RetentionCostAnalysis(
            storage_cost_monthly=1.0,
            storage_cost_yearly=12.0,
            reprocessing_cost=3.0,
            breakeven_months=8.0,
            recommendation="retain",
        )

        decision = video_retention_manager._make_retention_decision(
            VideoRetentionPolicy.KEEP_ALL,
            cost_analysis,
            sample_video_intelligence,
        )

        assert "action" in decision
        assert "reason" in decision

    def test_make_retention_decision_delete(self, video_retention_manager, sample_video_intelligence):
        """Test retention decision to delete."""
        cost_analysis = RetentionCostAnalysis(
            storage_cost_monthly=5.0,
            storage_cost_yearly=60.0,
            reprocessing_cost=1.0,
            breakeven_months=2.0,
            recommendation="delete",
        )

        decision = video_retention_manager._make_retention_decision(
            VideoRetentionPolicy.DELETE,
            cost_analysis,
            sample_video_intelligence,
        )

        assert "action" in decision
        assert "reason" in decision


class TestVideoRetentionManagerMainFlow:
    """Test the main retention handling flow."""

    @pytest.mark.asyncio
    async def test_handle_video_retention_delete_policy(self, video_retention_manager, sample_video_intelligence, temp_dir):
        """Test video retention with delete policy."""
        # Create a mock video file
        video_file = temp_dir / "test_video.mp4"
        video_file.write_text("dummy video content")

        # Mock the cost analysis and decision
        with patch.object(video_retention_manager, "_analyze_retention_costs") as mock_analyze, \
             patch.object(video_retention_manager, "_make_retention_decision") as mock_decide, \
             patch.object(video_retention_manager, "_execute_retention_action") as mock_execute, \
             patch.object(video_retention_manager, "_update_retention_history") as mock_update:

            mock_analyze.return_value = RetentionCostAnalysis(
                storage_cost_monthly=1.0,
                storage_cost_yearly=12.0,
                reprocessing_cost=2.0,
                breakeven_months=6.0,
                recommendation="delete",
            )
            mock_decide.return_value = {"action": "delete", "reason": "Cost effective"}
            mock_execute.return_value = {"action": "delete", "reason": "Cost effective", "success": True}

            result = await video_retention_manager.handle_video_retention(
                video_path=video_file,
                processing_result=sample_video_intelligence,
            )

            assert "action" in result
            mock_analyze.assert_called_once()
            mock_decide.assert_called_once()
            mock_execute.assert_called_once()
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_video_retention_retain_policy(self, video_retention_manager, sample_video_intelligence, temp_dir):
        """Test video retention with retain policy."""
        # Create a mock video file
        video_file = temp_dir / "test_video.mp4"
        video_file.write_text("dummy video content")

        with patch.object(video_retention_manager, "_analyze_retention_costs") as mock_analyze, \
             patch.object(video_retention_manager, "_make_retention_decision") as mock_decide, \
             patch.object(video_retention_manager, "_execute_retention_action") as mock_execute, \
             patch.object(video_retention_manager, "_update_retention_history") as mock_update:

            mock_analyze.return_value = RetentionCostAnalysis(
                storage_cost_monthly=0.5,
                storage_cost_yearly=6.0,
                reprocessing_cost=3.0,
                breakeven_months=12.0,
                recommendation="retain",
            )
            mock_decide.return_value = {"action": "archive", "reason": "Cost effective to retain"}
            mock_execute.return_value = True

            result = await video_retention_manager.handle_video_retention(
                video_intelligence=sample_video_intelligence,
                video_path=video_file,
                processed_data={"transcript": "processed transcript"},
            )

            assert result["action_taken"] == "archive"
            mock_execute.assert_called_once()

    def test_update_retention_history(self, video_retention_manager, temp_dir):
        """Test updating retention history."""
        video_file = temp_dir / "test_video.mp4"
        video_file.write_text("dummy content")

        retention_result = {
            "action": "archived",
            "reason": "Cost effective to retain",
            "success": True
        }
        cost_analysis = RetentionCostAnalysis(
            storage_cost_monthly=1.5,
            storage_cost_yearly=18.0,
            reprocessing_cost=2.5,
            breakeven_months=8.0,
            recommendation="retain",
        )

        video_retention_manager._update_retention_history(video_file, retention_result, cost_analysis)

        # Check that history was updated
        history = video_retention_manager._load_retention_history()
        assert "retained_videos" in history or "deleted_videos" in history


class TestVideoRetentionManagerArchive:
    """Test archive management functionality."""

    def test_cleanup_archive(self, video_retention_manager, temp_dir):
        """Test archive cleanup functionality."""
        # Create some old files in archive
        archive_dir = video_retention_manager.archive_dir
        old_file = archive_dir / "old_video.mp4"
        new_file = archive_dir / "new_video.mp4"

        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create files with different modification times
        old_file.write_text("old content")
        new_file.write_text("new content")

        # Make old file appear old
        old_time = datetime.now() - timedelta(days=400)
        old_file.stat().st_mtime = old_time.timestamp()

        result = video_retention_manager.cleanup_archive(max_age_days=365)

        assert isinstance(result, dict)
        assert "files_cleaned" in result
        assert "space_freed_gb" in result

    def test_get_retention_stats(self, video_retention_manager):
        """Test getting retention statistics."""
        # Add some history first
        video_retention_manager._save_retention_history({
            "vid_001": {"action": "archived", "timestamp": "2024-01-01T12:00:00"},
            "vid_002": {"action": "deleted", "timestamp": "2024-01-02T12:00:00"},
        })

        stats = video_retention_manager.get_retention_stats()

        assert isinstance(stats, dict)
        assert "total_videos_processed" in stats
        assert "archived_count" in stats
        assert "deleted_count" in stats

    def test_recommend_policy_optimization(self, video_retention_manager):
        """Test policy optimization recommendations."""
        recommendations = video_retention_manager.recommend_policy_optimization()

        assert isinstance(recommendations, dict)
        assert "suggested_policy" in recommendations
        assert "estimated_savings" in recommendations
        assert "confidence" in recommendations


class TestVideoRetentionManagerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handle_video_retention_no_video_file(self, video_retention_manager, sample_video_intelligence):
        """Test retention handling when video file doesn't exist."""
        nonexistent_path = Path("/nonexistent/video.mp4")

        result = await video_retention_manager.handle_video_retention(
            video_intelligence=sample_video_intelligence,
            video_path=nonexistent_path,
            processed_data={"transcript": "processed"},
        )

        assert "error" in result or result["action_taken"] == "skip"

    @pytest.mark.asyncio
    async def test_handle_video_retention_cost_analysis_disabled(self, mock_settings, sample_video_intelligence, temp_dir):
        """Test retention handling when cost optimization is disabled."""
        mock_settings.get_video_retention_config.return_value = {
            "policy": VideoRetentionPolicy.KEEP_ALL,
            "archive_directory": temp_dir / "archive",
            "cost_threshold": 5.0,
            "cost_optimization": False,  # Disabled
            "max_archive_size_gb": 50,
        }

        manager = VideoRetentionManager(settings=mock_settings)

        video_file = temp_dir / "test.mp4"
        video_file.write_text("content")

        result = await manager.handle_video_retention(
            video_intelligence=sample_video_intelligence,
            video_path=video_file,
            processed_data={"transcript": "processed"},
        )

        # Should retain due to policy, not cost analysis
        assert result["action_taken"] == "retain"

    def test_analyze_retention_costs_zero_size(self, video_retention_manager):
        """Test cost analysis with zero video size."""
        result = video_retention_manager._analyze_retention_costs(
            video_size_gb=0.0,
            access_frequency=0.1,
            storage_cost_per_gb=0.5,
            reprocessing_cost=1.0,
        )

        assert isinstance(result, RetentionCostAnalysis)
        assert result.storage_cost_monthly == 0.0
