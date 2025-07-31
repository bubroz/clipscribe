# ClipScribe Comprehensive Testing Plan

*Last Updated: July 30, 2025*
*Status: v2.21.0 - Pro-First Architecture Implemented. Next priority: CLI Integration Test Suite.*

## Executive Summary

ClipScribe has successfully transitioned to a "Pro-First" architecture, making Gemini 2.5 Pro the default for all intelligence extraction. This decision, driven by comprehensive benchmarking, ensures the highest quality output for users. With this architectural shift and numerous bug fixes complete, the next critical step is to build a robust, automated integration test suite to ensure long-term stability and prevent regressions.

## Recently Resolved Issues (v2.20.1 & v2.21.0)

- **✅ Pro-Model by Default**: Addressed user feedback on quality by making Gemini 2.5 Pro the default model.
- **✅ Multi-Video Command Bugs**: Fixed `TypeError` and `AttributeError` issues that blocked `process-series` and `process-collection`.
- **✅ API Timeout Errors**: Increased timeout to 60 minutes to handle long-form video content successfully.
- **✅ Performance Reporting**: Fixed a bug to ensure accurate `processing_time` is captured.
- **✅ CLI Clarity**: Improved UX by adding a completion message and clarifying multi-video result tables.

## Next Priority: CLI Integration Test Suite

Our recent development cycles, while successful, have been characterized by manual, iterative debugging of the CLI. To professionalize our workflow and ensure stability, an automated integration test suite is the highest priority.

### Phase 1: Core Functionality Testing (Backend)

#### 1.1 Single Video Processing
- [ ] Test `transcribe` command with a standard video URL.
- [ ] Test with `--use-flash` flag to ensure the optional model is correctly invoked.
- [ ] Test with `--no-cache` to verify non-cached execution.
- [ ] Assert that all expected output files are generated in the correct directory.
- [ ] Assert that the `performance_report.json` contains valid, non-zero data.

#### 1.2 Multi-Video Collection Processing
- [ ] Test `process-series` with multiple video URLs.
- [ ] Test `process-collection` with multiple video URLs.
- [ ] Test both commands with the `--use-flash` flag.
- [ ] Assert that both individual and unified collection directories and files are created.
- [ ] Assert that the final summary table in the CLI output is rendered correctly.

#### 1.3 Error Handling & Edge Cases
- [ ] Test with an invalid video URL and assert a graceful error message.
- [ ] Test with a known private/deleted video and assert a clear user message.
- [ ] Test timeout functionality with an extremely long (mocked) processing time.

### Phase 2: Test Implementation

#### 2.1 Test Framework
- We will use `pytest` as our testing framework.
- Tests will be located in the `tests/integration/` directory.
- We will use a dedicated test video from the `MASTER_TEST_VIDEO_TABLE.md` for consistency.

#### 2.2 Test Structure
A new test file, `tests/integration/test_cli_workflow.py`, will be created to house these tests. Each test will use Python's `subprocess` module to run the `clipscribe` CLI command and will then inspect the filesystem and command output to assert the expected outcome.

```python
# Example Test Structure in test_cli_workflow.py
import subprocess
import json
from pathlib import Path

def run_clipscribe_command(command: list[str]) -> subprocess.CompletedProcess:
    """Helper function to run a clipscribe command."""
    base_command = ["poetry", "run", "clipscribe"]
    full_command = base_command + command
    return subprocess.run(full_command, capture_output=True, text=True)

def test_transcribe_default_pro_model():
    """Tests the default transcribe command (should use Pro model)."""
    video_url = "https://www.youtube.com/watch?v=..." # Test video
    output_dir = Path("output/test_transcribe_pro")
    
    # Run command
    result = run_clipscribe_command(["transcribe", video_url, "--output-dir", str(output_dir)])
    
    # Assertions
    assert result.returncode == 0
    assert "Intelligence extraction complete!" in result.stdout
    assert (output_dir / "report.md").exists()
    # ... more assertions
```

## Success Criteria

- **Test Coverage**: The new test suite should cover all major CLI commands and their primary options.
- **Reliability**: Tests must be reliable and produce consistent results.
- **CI Integration**: The test suite should be added to our Continuous Integration pipeline to run on every commit, preventing future regressions.
- **Confidence**: The successful implementation of this test suite will give us high confidence to refactor and add new features in the future without breaking existing functionality. 