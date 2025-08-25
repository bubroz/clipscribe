"""Unit tests for ClipScribe CLI commands."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from pathlib import Path
from click.testing import CliRunner
from datetime import datetime, timezone

from clipscribe.commands.cli import (
    cli,
    process_video,
    collection_series,
    research,
    clean_demo,
    check_auth,
    run_processing_logic,
)
from clipscribe.models import VideoMetadata, VideoIntelligence, VideoTranscript


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.google_api_key = "test-api-key"
    settings.use_vertex_ai = False
    return settings


@pytest.fixture
def mock_video_metadata():
    """Create mock video metadata."""
    return VideoMetadata(
        video_id="test_123",
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="test_channel",
        published_at=datetime.now(timezone.utc),
        duration=300,
        view_count=1000,
        description="Test description",
        tags=["test"]
    )


@pytest.fixture
def mock_video_intelligence(mock_video_metadata):
    """Create mock video intelligence."""
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


class TestCLIMain:
    """Test main CLI functionality."""

    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ClipScribe - AI-powered video transcription and analysis" in result.output
        assert "process" in result.output
        assert "collection" in result.output
        assert "research" in result.output
        assert "utils" in result.output

    def test_cli_version(self, cli_runner):
        """Test CLI version command."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "ClipScribe" in result.output

    def test_cli_debug_flag(self, cli_runner):
        """Test CLI debug flag."""
        # Test that the debug flag doesn't break the CLI
        result = cli_runner.invoke(cli, ["--debug", "--help"])
        assert result.exit_code == 0
        assert "--debug" in result.output


class TestProcessVideoCommand:
    """Test the process video command."""

    @patch('clipscribe.commands.cli.run_processing_logic')
    @patch('asyncio.run')
    def test_process_video_command_basic(self, mock_asyncio_run, mock_run_logic, cli_runner):
        """Test process video command with basic options."""
        result = cli_runner.invoke(cli, ["process", "video", "https://example.com/video"])

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
        # Check that run_processing_logic was called with correct arguments
        mock_run_logic.assert_called_once_with(
            "https://example.com/video",
            False,  # use_flash
            True,   # use_cache
            "output",  # output_dir
            "auto",  # mode
            None    # cookies_from_browser
        )

    @patch('clipscribe.commands.cli.run_processing_logic')
    @patch('asyncio.run')
    def test_process_video_command_with_options(self, mock_asyncio_run, mock_run_logic, cli_runner):
        """Test process video command with all options."""
        result = cli_runner.invoke(cli, [
            "process", "video", "https://example.com/video",
            "--output-dir", "/tmp/test",
            "--mode", "video",
            "--no-cache",
            "--use-flash",
            "--cookies-from-browser", "chrome"
        ])

        assert result.exit_code == 0
        mock_run_logic.assert_called_once_with(
            "https://example.com/video",
            True,   # use_flash
            False,  # use_cache
            "/tmp/test",  # output_dir
            "video",  # mode
            "chrome"    # cookies_from_browser
        )

    @patch('clipscribe.commands.cli.run_processing_logic')
    @patch('asyncio.run')
    def test_process_video_command_invalid_mode(self, mock_asyncio_run, mock_run_logic, cli_runner):
        """Test process video command with invalid mode."""
        result = cli_runner.invoke(cli, [
            "process", "video", "https://example.com/video",
            "--mode", "invalid"
        ])

        assert result.exit_code != 0
        assert "Invalid value for" in result.output

    def test_process_video_help(self, cli_runner):
        """Test process video help."""
        result = cli_runner.invoke(cli, ["process", "video", "--help"])
        assert result.exit_code == 0
        assert "Process a single video" in result.output
        assert "--output-dir" in result.output
        assert "--mode" in result.output
        assert "--use-flash" in result.output


class TestRunProcessingLogic:
    """Test the core processing logic function."""

    @patch('clipscribe.commands.cli.VideoIntelligenceRetriever')
    @patch('clipscribe.commands.cli.Settings')
    def test_run_processing_logic_success(self, mock_settings_class, mock_retriever_class, mock_video_intelligence):
        """Test successful processing logic."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        mock_retriever = MagicMock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.process_url = AsyncMock(return_value=mock_video_intelligence)
        mock_retriever.save_all_formats = MagicMock(return_value={"directory": "/tmp/test"})

        # Mock the logger
        with patch('clipscribe.commands.cli.logging.getLogger') as mock_logger:
            mock_log_instance = MagicMock()
            mock_logger.return_value = mock_log_instance

            # Run the function
            asyncio.run(run_processing_logic(
                url="https://example.com/video",
                use_flash=False,
                use_cache=True,
                output_dir="/tmp/test",
                mode="auto",
                cookies_from_browser=None
            ))

            # Verify calls
            mock_retriever_class.assert_called_once_with(
                use_cache=True,
                use_advanced_extraction=True,
                mode="auto",
                output_dir="/tmp/test",
                use_flash=False,
                cookies_from_browser=None,
                settings=mock_settings
            )

            mock_retriever.process_url.assert_called_once_with("https://example.com/video")
            mock_retriever.save_all_formats.assert_called_once()

            # Verify logging
            mock_log_instance.info.assert_any_call("Title: Test Video")
            mock_log_instance.info.assert_any_call("Channel: Test Channel")

    @patch('clipscribe.commands.cli.VideoIntelligenceRetriever')
    @patch('clipscribe.commands.cli.Settings')
    def test_run_processing_logic_failure(self, mock_settings_class, mock_retriever_class):
        """Test processing logic when processing fails."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        mock_retriever = MagicMock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.process_url = AsyncMock(return_value=None)  # Simulate failure

        # Mock the logger
        with patch('clipscribe.commands.cli.logging.getLogger') as mock_logger:
            mock_log_instance = MagicMock()
            mock_logger.return_value = mock_log_instance

            # Run the function
            asyncio.run(run_processing_logic(
                url="https://example.com/video",
                use_flash=False,
                use_cache=True,
                output_dir="/tmp/test",
                mode="auto",
                cookies_from_browser=None
            ))

            # Verify error logging
            mock_log_instance.error.assert_called_with("Processing failed. Please check the log for details.")

    @patch('clipscribe.commands.cli.VideoIntelligenceRetriever')
    @patch('clipscribe.commands.cli.Settings')
    def test_run_processing_logic_exception(self, mock_settings_class, mock_retriever_class):
        """Test processing logic when exception occurs."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        mock_retriever = MagicMock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.process_url = AsyncMock(side_effect=Exception("Test error"))

        # Mock the logger
        with patch('clipscribe.commands.cli.logging.getLogger') as mock_logger:
            mock_log_instance = MagicMock()
            mock_logger.return_value = mock_log_instance

            # Run the function
            asyncio.run(run_processing_logic(
                url="https://example.com/video",
                use_flash=False,
                use_cache=True,
                output_dir="/tmp/test",
                mode="auto",
                cookies_from_browser=None
            ))

            # Verify error logging
            mock_log_instance.error.assert_called_with("A fatal error occurred: Test error", exc_info=True)


class TestCollectionSeriesCommand:
    """Test the collection series command."""

    @patch('clipscribe.commands.cli.MultiVideoProcessor')
    @patch('clipscribe.commands.cli.VideoIntelligenceRetriever')
    @patch('clipscribe.commands.cli.Settings')
    @patch('asyncio.run')
    def test_collection_series_command(self, mock_asyncio_run, mock_settings_class, mock_retriever_class, mock_mvp_class, cli_runner, mock_video_intelligence):
        """Test collection series command."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        mock_retriever = MagicMock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.process_url = AsyncMock(return_value=mock_video_intelligence)
        mock_retriever.save_collection_outputs = MagicMock()

        mock_mvp = MagicMock()
        mock_mvp_class.return_value = mock_mvp
        mock_mvp.process_video_collection = AsyncMock(return_value=mock_video_intelligence)

        result = cli_runner.invoke(cli, [
            "collection", "series",
            "https://example.com/video1",
            "https://example.com/video2"
        ])

        assert result.exit_code == 0
        # Verify that asyncio.run was called (the actual logic is in the async function)
        mock_asyncio_run.assert_called_once()

    def test_collection_series_help(self, cli_runner):
        """Test collection series help."""
        result = cli_runner.invoke(cli, ["collection", "series", "--help"])
        assert result.exit_code == 0
        assert "Process multiple related videos" in result.output
        assert "--output-dir" in result.output
        assert "--use-flash" in result.output


class TestResearchCommand:
    """Test the research command."""

    @patch('clipscribe.commands.cli.VideoIntelligenceRetriever')
    @patch('clipscribe.commands.cli.Settings')
    @patch('asyncio.run')
    def test_research_command(self, mock_asyncio_run, mock_settings_class, mock_retriever_class, cli_runner, mock_video_intelligence):
        """Test research command."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        mock_retriever = MagicMock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.search = AsyncMock(return_value=[mock_video_intelligence])
        mock_retriever.save_all_formats = MagicMock()

        result = cli_runner.invoke(cli, [
            "research", "test query",
            "--max-results", "3"
        ])

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    def test_research_help(self, cli_runner):
        """Test research help."""
        result = cli_runner.invoke(cli, ["research", "--help"])
        assert result.exit_code == 0
        assert "Search for and analyze multiple videos" in result.output
        assert "--max-results" in result.output


class TestUtilsCommands:
    """Test utility commands."""

    def test_clean_demo_command_basic(self, cli_runner, tmp_path):
        """Test clean-demo command with basic options."""
        # Create test directories
        demo_dir = tmp_path / "demos"
        demo_dir.mkdir()
        (demo_dir / "old_demo1").mkdir()
        (demo_dir / "old_demo2").mkdir()

        result = cli_runner.invoke(cli, [
            "utils", "clean-demo",
            "--demo-dir", str(demo_dir)
        ])

        assert result.exit_code == 0
        assert "Demo cleanup complete" in result.output

        # Check that directories were deleted
        assert not (demo_dir / "old_demo1").exists()
        assert not (demo_dir / "old_demo2").exists()

    def test_clean_demo_command_dry_run(self, cli_runner, tmp_path):
        """Test clean-demo command with dry-run option."""
        # Create test directories
        demo_dir = tmp_path / "demos"
        demo_dir.mkdir()
        (demo_dir / "old_demo1").mkdir()
        (demo_dir / "old_demo2").mkdir()

        result = cli_runner.invoke(cli, [
            "utils", "clean-demo",
            "--demo-dir", str(demo_dir),
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Would delete:" in result.output

        # Check that directories were NOT deleted (dry run)
        assert (demo_dir / "old_demo1").exists()
        assert (demo_dir / "old_demo2").exists()

    def test_clean_demo_command_keep_recent(self, cli_runner, tmp_path):
        """Test clean-demo command with keep-recent option."""
        import time

        # Create test directories with different modification times
        demo_dir = tmp_path / "demos"
        demo_dir.mkdir()

        # Create directories with different timestamps
        old_dir = demo_dir / "old_demo"
        old_dir.mkdir()
        time.sleep(0.01)  # Small delay

        recent_dir = demo_dir / "recent_demo"
        recent_dir.mkdir()

        result = cli_runner.invoke(cli, [
            "utils", "clean-demo",
            "--demo-dir", str(demo_dir),
            "--keep-recent", "1"
        ])

        assert result.exit_code == 0

        # Check that old directory was deleted but recent one was kept
        assert not old_dir.exists()
        assert recent_dir.exists()

    def test_clean_demo_command_no_dir(self, cli_runner, tmp_path):
        """Test clean-demo command when directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"

        result = cli_runner.invoke(cli, [
            "utils", "clean-demo",
            "--demo-dir", str(nonexistent_dir)
        ])

        assert result.exit_code == 0
        assert "Nothing to clean" in result.output

    def test_clean_demo_command_with_deletion_error(self, cli_runner):
        """Test clean demo command when deletion fails."""
        with cli_runner.isolated_filesystem():
            # Create the output directory and a demo subdirectory inside it
            import os
            output_dir = "output"
            demo_dir = os.path.join(output_dir, "20250101_demo")
            os.makedirs(demo_dir)
            with open(os.path.join(demo_dir, "test.txt"), "w") as f:
                f.write("test")

            # Mock shutil.rmtree to raise an exception
            with patch('shutil.rmtree', side_effect=OSError("Permission denied")):
                result = cli_runner.invoke(cli, ["utils", "clean-demo"])

                assert result.exit_code == 0
                assert "Failed to delete" in result.output
                assert "Permission denied" in result.output
                assert "Demo cleanup complete" in result.output


class TestCheckAuthCommand:
    """Test the check-auth command."""

    @patch('clipscribe.commands.cli.Settings')
    @patch('os.environ.get')
    def test_check_auth_google_ai_studio(self, mock_env_get, mock_settings_class, cli_runner):
        """Test check-auth command with Google AI Studio configuration."""
        # Mock settings for Google AI Studio mode
        mock_settings = MagicMock()
        mock_settings.google_api_key = "test-api-key-123456789"
        mock_settings.use_vertex_ai = False
        mock_settings_class.return_value = mock_settings

        mock_env_get.return_value = None

        result = cli_runner.invoke(cli, ["utils", "check-auth"])

        assert result.exit_code == 0
        assert "Auth: Google AI Studio API key detected" in result.output
        assert "test-a" in result.output  # Masked API key (first 6 chars + ...)

    @patch('clipscribe.commands.cli.Settings')
    @patch('os.environ.get')
    def test_check_auth_vertex_ai(self, mock_env_get, mock_settings_class, cli_runner):
        """Test check-auth command with Vertex AI configuration."""
        # Mock settings for Vertex AI mode
        mock_settings = MagicMock()
        mock_settings.use_vertex_ai = True
        mock_settings.VERTEX_AI_PROJECT = "test-project"
        mock_settings_class.return_value = mock_settings

        mock_env_get.side_effect = lambda key, default=None: {
            "VERTEX_AI_LOCATION": "us-central1",
            "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json"
        }.get(key, default)

        with patch('pathlib.Path.exists', return_value=True):
            result = cli_runner.invoke(cli, ["utils", "check-auth"])

            assert result.exit_code == 0
            assert "Auth: Vertex AI mode enabled" in result.output
            assert "test-project" in result.output
            assert "us-central1" in result.output
            assert "exists" in result.output

    @patch('clipscribe.commands.cli.Settings')
    def test_check_auth_misconfigured(self, mock_settings_class, cli_runner):
        """Test check-auth command when configuration is invalid."""
        mock_settings_class.side_effect = Exception("Invalid configuration")

        result = cli_runner.invoke(cli, ["utils", "check-auth"])

        assert result.exit_code == 0
        assert "Auth status: Misconfigured" in result.output
        assert "Invalid configuration" in result.output

    @patch('clipscribe.commands.cli.Settings')
    @patch('os.environ.get')
    def test_check_auth_missing_keys(self, mock_env_get, mock_settings_class, cli_runner):
        """Test check-auth command when API keys are missing."""
        # Mock settings with no API key
        mock_settings = MagicMock()
        mock_settings.google_api_key = ""
        mock_settings.use_vertex_ai = False
        mock_settings_class.return_value = mock_settings

        mock_env_get.return_value = None

        result = cli_runner.invoke(cli, ["utils", "check-auth"])

        assert result.exit_code == 0
        assert "Auth: Missing GOOGLE_API_KEY" in result.output


class TestCommandGroups:
    """Test command group structure and help."""

    def test_process_group_help(self, cli_runner):
        """Test process command group help."""
        result = cli_runner.invoke(cli, ["process", "--help"])
        assert result.exit_code == 0
        assert "Process single media" in result.output
        assert "video" in result.output

    @patch('os.environ.get')
    @patch('clipscribe.commands.cli.Settings')
    def test_check_auth_vertex_ai_no_credentials_file(self, mock_settings_class, mock_env_get, cli_runner):
        """Test check-auth command with Vertex AI but no credentials file set."""
        # Mock settings for Vertex AI mode
        mock_settings = MagicMock()
        mock_settings.use_vertex_ai = True
        mock_settings.VERTEX_AI_PROJECT = "test-project"
        mock_settings_class.return_value = mock_settings

        mock_env_get.side_effect = lambda key, default=None: {
            "VERTEX_AI_LOCATION": "us-central1"
            # Deliberately omit GOOGLE_APPLICATION_CREDENTIALS
        }.get(key, default)

        result = cli_runner.invoke(cli, ["utils", "check-auth"])

        assert result.exit_code == 0
        assert "Auth: Vertex AI mode enabled" in result.output
        assert "test-project" in result.output
        assert "us-central1" in result.output
        assert "GOOGLE_APPLICATION_CREDENTIALS: not set" in result.output

    def test_collection_group_help(self, cli_runner):
        """Test collection command group help."""
        result = cli_runner.invoke(cli, ["collection", "--help"])
        assert result.exit_code == 0
        assert "Analyze video collections" in result.output
        assert "series" in result.output

    def test_utils_group_help(self, cli_runner):
        """Test utils command group help."""
        result = cli_runner.invoke(cli, ["utils", "--help"])
        assert result.exit_code == 0
        assert "Utility commands" in result.output
        assert "clean-demo" in result.output
        assert "check-auth" in result.output
