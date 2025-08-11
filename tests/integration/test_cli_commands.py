import subprocess
import json
from pathlib import Path
import shutil
import os
from pathlib import Path
import pytest

# --- Test Constants ---
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # "Me at the zoo" - short and reliable
TEST_VIDEO_ID = "jNQXAC9IVRw"
OUTPUT_DIR = Path("output/test_suite")

# --- Helper Functions ---

def run_clipscribe_command(command: list[str]) -> subprocess.CompletedProcess:
    """Helper function to run a clipscribe command via poetry."""
    base_command = ["poetry", "run", "clipscribe"]
    full_command = base_command + command
    return subprocess.run(full_command, capture_output=True, text=True, check=False)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Fixture to clear cache and output before and after test module runs."""
    # Setup: Clear cache and old test outputs
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    run_clipscribe_command(["utils", "clean-demo"]) # Use the app's own cleaner
    
    yield # This is where the tests will run
    
    # Teardown: Clean up created files
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

# --- Test Suite ---

def test_cli_help():
    """Tests that the main help command works and shows the new groups."""
    result = run_clipscribe_command(["--help"])
    assert result.returncode == 0
    assert "Usage: clipscribe [OPTIONS] COMMAND [ARGS]..." in result.stdout
    assert "process" in result.stdout
    assert "collection" in result.stdout
    assert "research" in result.stdout
    assert "utils" in result.stdout

def _should_run_e2e() -> bool:
    return os.environ.get("CLIPSCRIBE_RUN_E2E", "").lower() in ("1", "true", "yes")


def _auth_configured() -> bool:
    """Require Vertex ADC by default; allow API key only with explicit opt-in."""
    try:
        from clipscribe.config.settings import Settings
        s = Settings()
        # Prefer Vertex ADC path
        if getattr(s, 'use_vertex_ai', False) or os.environ.get("USE_VERTEX_AI"):
            cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            proj = os.environ.get("VERTEX_AI_PROJECT") or getattr(s, 'vertex_ai_project', None)
            if cred and Path(cred).exists() and proj:
                return True
        # Allow AI Studio only if explicitly opted in to avoid accidental billing/limits
        if os.environ.get("CLIPSCRIBE_RUN_E2E_ALLOW_AISTUDIO", "").lower() in ("1", "true", "yes"):
            if getattr(s, 'google_api_key', '') and os.environ.get("GOOGLE_API_KEY", "") not in ("", "your_key_here"):
                return True
        return False
    except Exception:
        return False


@pytest.mark.skipif(not (_should_run_e2e() and _auth_configured()), reason="Requires CLIPSCRIBE_RUN_E2E=1 and configured GOOGLE_API_KEY or Vertex creds")
def test_process_video_default_pro_model():
    """Tests the default `process video` command which should use the Pro model."""
    output_path = OUTPUT_DIR / "process_video_default"
    command = ["process", "video", TEST_VIDEO_URL, "--output-dir", str(output_path)]
    
    result = run_clipscribe_command(command)
    
    assert result.returncode == 0, f"CLI command failed: {result.stderr}"
    assert "Intelligence extraction complete!" in result.stdout
    
                # Verify that output files were created
    output_subdirs = list(output_path.glob("*"))
    assert len(output_subdirs) > 0, "No output subdirectory was created."
    expected_report = output_subdirs[0] / "report.md"
    assert expected_report.exists(), "The output report.md was not created."

@pytest.mark.skipif(not (_should_run_e2e() and _auth_configured()), reason="Requires CLIPSCRIBE_RUN_E2E=1 and configured GOOGLE_API_KEY or Vertex creds")
def test_process_video_use_flash():
    """Tests the `process video` command with the --use-flash flag."""
    output_path = OUTPUT_DIR / "process_video_flash"
    command = ["process", "video", TEST_VIDEO_URL, "--output-dir", str(output_path), "--use-flash"]
    
    result = run_clipscribe_command(command)
    
    assert result.returncode == 0, f"CLI command failed: {result.stderr}"
    assert "Intelligence extraction complete!" in result.stdout
    assert "Model: gemini-2.5-flash" in result.stderr or "Model: gemini-2.5-flash" in result.stdout
    
                # Verify that output files were created
    output_subdirs = list(output_path.glob("*"))
    assert len(output_subdirs) > 0, "No output subdirectory was created."
    expected_report = output_subdirs[0] / "report.md"
    assert expected_report.exists(), "The output report.md was not created for flash run."

@pytest.mark.skipif(not (_should_run_e2e() and _auth_configured()), reason="Requires CLIPSCRIBE_RUN_E2E=1 and configured GOOGLE_API_KEY or Vertex creds")
def test_collection_series_command():
    """Tests the `collection series` command with two videos."""
    output_path = OUTPUT_DIR / "collection_series"
    urls = [TEST_VIDEO_URL, "https://www.youtube.com/watch?v=dQw4w9WgXcQ"] # Using two short videos
    command = ["collection", "series", "--output-dir", str(output_path)] + urls
    
    result = run_clipscribe_command(command)
    
    assert result.returncode == 0, f"CLI command failed: {result.stderr}"
    assert "Multi-video collection processing complete!" in result.stdout
    
                # Check that a collection directory was created
    collection_dirs = list(output_path.glob("collection_*"))
    assert len(collection_dirs) > 0, "No collection output directory was created."

    # Check for a unified graph in the collection directory
    # The actual files are in a subdirectory within the collection directory
    collection_subdirs = list(collection_dirs[0].glob("collection_*"))
    assert len(collection_subdirs) > 0, "No collection subdirectory was created."

    unified_gexf = collection_subdirs[0] / "unified_knowledge_graph.gexf"
    assert unified_gexf.exists(), f"Unified knowledge graph was not created for the series. Contents of dir: {list(collection_subdirs[0].iterdir())}"

@pytest.mark.skipif(not (_should_run_e2e() and _auth_configured()), reason="Requires CLIPSCRIBE_RUN_E2E=1 and configured GOOGLE_API_KEY or Vertex creds")
def test_research_command():
    """Tests the `research` command."""
    output_path = OUTPUT_DIR / "research"
    query = "Jawed Karim" # The user in the test video
    command = ["research", query, "--output-dir", str(output_path), "--max-results", "1"]
    
    result = run_clipscribe_command(command)
    
    assert result.returncode == 0, f"CLI command failed: {result.stderr}"
    assert "Research complete!" in result.stdout or "Research complete!" in result.stderr
    
    # Check that output files were created in a subdirectory
    research_outputs = list(output_path.glob("youtube_*"))
    assert len(research_outputs) > 0, "No output directories were created for the research command."

def test_invalid_url_error_handling():
    """Tests that the CLI handles an invalid URL gracefully."""
    command = ["process", "video", "not-a-real-url"]
    
    result = run_clipscribe_command(command)
    
    # It should not crash, but might exit with a non-zero code after logging an error
    assert "URL not supported by yt-dlp" in result.stderr or "ERROR" in result.stderr
