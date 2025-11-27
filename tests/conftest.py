"""Pytest configuration and shared fixtures for ClipScribe tests."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


# Removed custom event_loop fixture to avoid conflicts with pytest-asyncio
# pytest-asyncio will handle event loop creation automatically


@pytest.fixture(autouse=True)
def mock_google_api_key(request):
    """Automatically mock Google API key for all tests except performance tests."""
    # Skip mocking for performance tests - they need real API keys
    if "performance" in request.keywords:
        yield
    else:
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-api-key"}):
            yield


@pytest.fixture(autouse=True)
def mock_api_authentication():
    """Mock API authentication for tests."""
    with patch.dict("os.environ", {"VALID_TOKENS": "test-token"}):
        yield


@pytest.fixture
def temp_directory():
    """Create a temporary directory that's automatically cleaned up."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def mock_video_urls():
    """Common test video URLs."""
    return {
        "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "vimeo": "https://vimeo.com/123456789",
        "twitter": "https://twitter.com/user/status/1234567890",
        "tiktok": "https://www.tiktok.com/@user/video/1234567890",
        "dailymotion": "https://www.dailymotion.com/video/x123456",
        "instagram": "https://www.instagram.com/reel/ABC123/",
    }


@pytest.fixture(autouse=True)
def mock_subprocess_and_external_deps():
    """Mock subprocess calls and external dependencies for all tests."""
    with (
        patch("subprocess.run") as mock_subprocess,
        patch("google.generativeai.configure") as mock_genai_configure,
        patch("google.generativeai.GenerativeModel") as mock_genai_model,
        patch("google.generativeai.upload_file") as mock_upload_file,
        patch("google.generativeai.delete_file") as mock_delete_file,
        patch("subprocess.Popen") as mock_popen,
        patch("os.system") as mock_system,
        patch.dict(
            "sys.modules", {"google.cloud": MagicMock(), "google.cloud.tasks_v2": MagicMock()}
        ),
        patch("clipscribe.api.task_queue.get_task_queue_manager") as mock_task_manager,
    ):

        # Mock subprocess for CLI commands with smart responses
        def mock_subprocess_run(cmd, **kwargs):
            # Check if this is a clipscribe help command
            if len(cmd) >= 3 and cmd[0] == "poetry" and cmd[1] == "run" and cmd[2] == "clipscribe":
                if "--help" in cmd:
                    # Return realistic CLI help output
                    return MagicMock(
                        returncode=0,
                        stdout="Usage: clipscribe [OPTIONS] COMMAND [ARGS]...\n\n  Video intelligence extraction and analysis.\n\nOptions:\n  --help  Show this message and exit.\n\nCommands:\n  process     Process videos from URLs\n  collection  Process collections of videos\n  research    Research and analyze topics\n  utils       Utility commands\n",
                        stderr="",
                        check=False,
                    )
                elif len(cmd) >= 4 and cmd[3] == "process":
                    # Return realistic error for invalid URL
                    return MagicMock(
                        returncode=1,
                        stdout="",
                        stderr="ERROR: URL not supported by yt-dlp\n",
                        check=False,
                    )
                else:
                    # Default success response
                    return MagicMock(
                        returncode=0, stdout="Command executed successfully", stderr="", check=False
                    )
            else:
                # Non-clipscribe commands
                return MagicMock(
                    returncode=0, stdout="Command executed successfully", stderr="", check=False
                )

        mock_subprocess.side_effect = mock_subprocess_run

        # Mock Popen for yt-dlp and other subprocess calls
        mock_popen.return_value = MagicMock(
            communicate=MagicMock(return_value=(b"mock output", b"")),
            returncode=0,
            stdout=b"mock stdout",
            stderr=b"",
        )

        # Mock os.system calls
        mock_system.return_value = 0

        # Mock Gemini API calls
        mock_genai_model.return_value = MagicMock()

        # Mock task queue manager
        mock_task_manager_instance = MagicMock()
        mock_task_manager_instance.enqueue_job.return_value = ("test-task-name", "test-task-path")
        mock_task_manager.return_value = mock_task_manager_instance
        mock_genai_model.return_value.generate_content_async = AsyncMock()
        mock_genai_model.return_value.generate_content_async.return_value = MagicMock()
        mock_genai_model.return_value.generate_content_async.return_value.text = '{"summary": "Mock response", "key_points": [], "entities": [], "topics": [], "relationships": [], "dates": []}'

        yield


@pytest.fixture
def sample_transcript_text():
    """Sample transcript text for testing."""
    return """Hello and welcome to this ClipScribe demo video.
    Today we're going to test the amazing transcription capabilities
    of our AI-powered video intelligence tool.
    
    ClipScribe uses Google's Gemini 2.5 Flash model to provide
    high-accuracy transcriptions at 92% lower cost than traditional
    speech-to-text services.
    
    Let's see it in action!"""


# Test markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "requires_api: marks tests that require real API access")


# Skip slow tests by default in CI
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    if config.getoption("--ci"):
        skip_slow = pytest.mark.skip(reason="Slow test skipped in CI")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--ci", action="store_true", default=False, help="Run in CI mode (skip slow tests)"
    )
    parser.addoption(
        "--integration", action="store_true", default=False, help="Run integration tests only"
    )
