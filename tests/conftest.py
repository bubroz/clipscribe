"""Pytest configuration and shared fixtures for ClipScribe tests."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_google_api_key():
    """Automatically mock Google API key for all tests."""
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-api-key"}):
        yield


@pytest.fixture
def temp_directory():
    """Create a temporary directory that's automatically cleaned up."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


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
