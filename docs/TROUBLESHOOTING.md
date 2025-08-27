# ClipScribe Troubleshooting Guide

*Last Updated: 2025-08-26*

This guide helps you resolve common issues with ClipScribe.

## Table of Contents

- [Installation Issues](#installation-issues)
- [API Key Problems](#api-key-problems)
- [Video Processing Errors](#video-processing-errors)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

## Installation Issues

### Poetry Not Found

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

### Python Version Mismatch

```bash
# Install Python 3.11 or 3.12
pyenv install 3.12.0
pyenv local 3.12.0

# Tell Poetry to use correct version
poetry env use 3.12.0
poetry install
```

### Dependency Conflicts

```bash
# Clear and reinstall
poetry cache clear . --all
rm -rf poetry.lock
poetry install --no-cache
```

## API Key Problems

### Missing Google API Key

```bash
# Option 1: Set in .env file (recommended)
echo "GOOGLE_API_KEY=your_key_here" >> .env

# Option 2: Export in shell
export GOOGLE_API_KEY="your_key_here"
```

### Invalid API Key

- Ensure your key starts with "AIza".
- Check that the Gemini API is enabled in your Google Cloud Console.
- Verify that billing is enabled for the associated project.
- Use the `check-auth` utility to verify your setup:
  ```bash
  poetry run clipscribe utils check-auth
  ```

### API Errors (500, 503, etc.)

- **Symptom**: The CLI exits with an error mentioning `500 Internal Server Error` or `503 Service Unavailable`.
- **Cause**: These are typically transient errors from the Google Gemini API.
- **Solution**: ClipScribe includes automatic retry logic. If the problem persists, check the Google Cloud Status dashboard.

## Video Processing Errors

### YouTube Authentication Errors (Age/Login Gates)

- **Symptom**: `yt-dlp` fails with an error like `Sign in to confirm your age` or `This video may be inappropriate for some users`.
- **Cause**: The video is age-restricted or requires a login to view.
- **Solution**: Use the `--cookies-from-browser` flag to allow ClipScribe to securely use your browser's existing login session.

```bash
# Example for a user logged into YouTube on Chrome
clipscribe process video "URL_HERE" --cookies-from-browser chrome

# Supported browsers: chrome, firefox, brave, edge, opera, safari, vivaldi
```

### Video Not Found or Unavailable

- **Symptom**: `yt-dlp` returns an error like `Video unavailable`.
- **Cause**: The video may be private, deleted, or geographically restricted.
- **Solution**:
  - Verify the URL is correct and accessible in your browser.
  - For restricted content, use the `--cookies-from-browser` option.

### Download Failed

Common causes:

- Rate limiting
- Geographic restrictions
- Authentication required

**Solutions**:

```bash
# These options are not available
# clipscribe process video "URL" --rate-limit 50k
# clipscribe process video "URL" --no-check-certificate
```

### Large Video Memory Issues

For videos over 2 hours:

```bash
# Processing uses chunked uploads automatically (v2.25.0+)
# If needed, you can download and process manually:
yt-dlp "URL" -o video.mp4
clipscribe process video video.mp4
```

### Timeout Errors with Long Videos

```text
ERROR: 504 Deadline Exceeded
```

**This happens when processing videos longer than ~15 minutes with default settings.**

**Solutions:**

1.  Set the `GEMINI_REQUEST_TIMEOUT` environment variable:

    ```bash
    # In your .env file
    GEMINI_REQUEST_TIMEOUT=14400  # 4 hours
    ```

2.  For very long videos, consider:
    - Using `--start-time` and `--end-time` to process segments (not yet implemented)
    - Breaking into smaller chunks locally before processing

**Example for processing a segment (future feature):**

```bash
# Not yet implemented
# clipscribe process video "URL" --start-time 0 --end-time 1800  # First 30 minutes
```

## Performance Issues

### Slow Processing

Check these factors:

1. Internet speed
2. API quota limits
3. Model download status

**Optimizations**:

```bash
# Use faster model
clipscribe process video "URL" --use-flash
```

### High API Costs

Monitor costs with:

```bash
# The estimate command is not yet available.
# clipscribe estimate "URL"

# Use audio-only mode for cost savings
clipscribe process video "URL" --mode audio

# Set cost limit
export COST_WARNING_THRESHOLD=1.0
```

## Output Problems

### Encoding Issues

If you see garbled text:

```bash
# Force UTF-8 encoding
export PYTHONIOENCODING=utf-8
clipscribe process video "URL"
```

### Missing Output Files

Check:

1. Write permissions in output directory
2. Disk space available
3. Look in `output/` subdirectories

### Corrupted JSON

If JSON files are corrupted:

- Check for incomplete processing (Ctrl+C)
- Look for `.tmp` files in output directory
- Re-run with `--force` to overwrite (not yet implemented)

## Platform-Specific Issues

### YouTube

- **Playlist URLs**: Process individual videos or use batch mode
- **Live Streams**: Not supported yet
- **Premieres**: Wait until video is fully available

### Twitter/X

- May require authentication
- Some videos are region-locked
- Check if video is still available

### TikTok

- URLs change frequently
- Use the share URL, not the web URL
- Some regions block access

## Getting Help

### Debug Mode

Run with debug logging for more detailed output:

```bash
# Via environment variable
export CLIPSCRIBE_LOG_LEVEL=DEBUG
clipscribe process video "URL"

# Via CLI flag
clipscribe --debug process video "URL"
```

### Quick Test

Verify your installation with a known-good video:

```bash
clipscribe process video "https://www.youtube.com/watch?v=7sWj6D2i4eU"
```

### Report Issues

1.  Check existing issues: [GitHub Issues](https://github.com/bubroz/clipscribe/issues)
2.  Include:
    - ClipScribe version (`clipscribe --version`)
    - Python version (`python --version`)
    - Full error message
    - Debug log output
    - Video URL (if not sensitive)

### Common Error Messages

| Error | Cause | Solution |
|---|---|---|
| `TranscriptNotAvailable` | No captions | Transcription is automatic |
| `VideoUnavailable` | Private/deleted | Check URL is accessible |
| `APIQuotaExceeded` | Hit API limits | Wait or upgrade quota |
| `ModelNotFound` | Models not downloaded | Not applicable |
| `PermissionError` | Can't write output | Check directory permissions |

## Development and Testing Best Practices

### CRITICAL: Validation Before Deployment

To prevent issues like import errors, broken functionality, or incomplete features:

#### 1. **Always Test Imports First**

```bash
# Before declaring any feature complete
poetry run python -c "from path.to.module import YourClass; print('Import successful')"
```

#### 2. **Follow Incremental Testing**

- **Step 1**: Test imports in isolation
- **Step 2**: Test core functionality
- **Step 3**: Test component integration
- **Step 4**: Test full application
- **Step 5**: Verify external connectivity

#### 3. **Validate Before Success Declaration**

```bash
# Example for Streamlit apps
poetry run python -c "import streamlit as st; from src.clipscribe.tui.app import main"
poetry run streamlit run src/clipscribe/tui/app.py --server.port 8501 &
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501  # Should return 200
pkill -f streamlit
```

#### 4. **Common Validation Patterns**

**For CLI Commands:**

```bash
poetry run clipscribe --help  # Should show help without errors
poetry run clipscribe process video "https://www.youtube.com/watch?v=7sWj6D2i4eU" # Test URL
```

**For Python Modules:**

```bash
poetry run python -c "from clipscribe.config import settings; print(settings.google_api_key[:8] if settings.google_api_key else 'Not Set')"
```

**For Web Interfaces:**

```bash
poetry run streamlit run src/clipscribe/tui/app.py &
sleep 5 # Give it time to start
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
pkill -f streamlit
```

#### 5. **Error Diagnosis Protocol**

When errors occur:

1. **Read the full error message** - don't skip details
2. **Identify the root cause** - not just symptoms
3. **Fix the underlying issue** - avoid workarounds
4. **Test the fix** - verify it actually works
5. **Test related functionality** - ensure no regressions

This prevents deploying broken code and saves debugging time later.

Remember: When in doubt, run with `--debug`.

### Vertex AI Failures

- **Symptom**: The application crashes with errors related to `vertexai` or Google Cloud permissions, especially during batch processing.
- **Solution**: As of v2.19.7, the system has a **graceful fallback mechanism**. If Vertex AI processing fails for any reason (e.g., incorrect configuration, quota limits), ClipScribe will automatically log a warning and switch to the standard Gemini API to complete the job. This ensures that your processing can continue even if the Vertex AI setup is not perfect. To force the use of the standard Gemini API, you can set `USE_VERTEX_AI=False` in your `.env` file.

## Enterprise Issues

For scaling problems, check Vertex quotas.
