# ClipScribe Troubleshooting Guide

*Last Updated: July 31, 2025*

This guide helps you resolve common issues with ClipScribe.

## Table of Contents
- [Installation Issues](#installation-issues)
- [API Key Problems](#api-key-problems)
- [Video Processing Errors](#video-processing-errors)
- [503 Socket Closed Errors](#503-socket-closed-errors)
- [Performance Issues](#performance-issues)
- [Output Problems](#output-problems)
- [Platform-Specific Issues](#platform-specific-issues)
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

## Entity & Relationship Extraction Issues (v2.19.0 Fixed)

### Poor Extraction Quality
**Problem**: Only getting 0-10 generic entities like "Revenue", "This Morning" and 0-1 relationships

**Cause**: Quality filters were too aggressive (removing 70% of valid entities)

**Solution**: Update to v2.19.0+

```bash
# Check your version
poetry run clipscribe --version

# Update if needed
poetry update clipscribe
```

**What v2.19.0 Fixed**:
- Language filter was removing common English words (de, la, en, etc.)
- Confidence threshold was too high (0.6), now 0.4
- Gemini's 50+ relationships were extracted but ignored (bug)
- False positive detection was too aggressive

**Expected Results After Fix**:
- 16+ meaningful entities (people, orgs, locations)
- 52+ relationships with evidence chains
- 88+ node knowledge graphs
- Still only $0.0083 per video!

### Python Version Warning
**Problem**: You see a warning like:

```text
The currently activated Python version 3.13.5 is not supported by the project (^3.12,<3.13).
Trying to find and use a compatible version. 
Using python3.12 (3.12.11)
```

**Solution**: This is normal behavior. ClipScribe requires Python 3.12+ and Poetry will automatically find and use a compatible version. No action needed.

**To avoid the warning**: Use Python 3.12 explicitly:

```bash
pyenv install 3.12.11
pyenv local 3.12.11
poetry install
```

### Tokenizer Warning
**Problem**: You see repeated warnings about sentencepiece tokenizer:

```text
UserWarning: The sentencepiece tokenizer that you are converting to a fast tokenizer uses the byte fallback option which is not implemented in the fast tokenizers.
```

**Solution**: This warning is harmless and has been suppressed in v2.10.0+. If you're still seeing it, update to the latest version:

```bash
poetry update
```
The warning comes from the GLiNER model loading and doesn't affect functionality.

## API Key Problems

### API Errors (500, 503, etc.)
- **Symptom**: The CLI exits with an error mentioning `500 Internal Server Error`, `503 Service Unavailable`, or a `grpc` error.
- **Cause**: These are transient (temporary) errors from the upstream Google Gemini API. They are not bugs in ClipScribe.
- **Solution**: ClipScribe v2.23.0 and later includes automatic retry logic with exponential backoff. The application will automatically retry the request up to 3 times. If the problem persists after multiple retries, it may indicate a wider outage with the Google API. Check Google Cloud Status dashboard for more information.

### Missing Google API Key

```bash
# Option 1: Set in .env file
echo "GOOGLE_API_KEY=your_key_here" >> .env

# Option 2: Export in shell
export GOOGLE_API_KEY="your_key_here"

# Option 3: Pass via CLI
clipscribe process video "URL" --api-key "your_key_here"
```

### Invalid API Key
- Ensure key starts with "AIza"
- Check key has Gemini API enabled in Google Cloud Console
- Verify billing is enabled for the project

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

## 503 Socket Closed Errors
### Problem: "Premature close" or "Socket closed" errors

**New in v2.19.2**: Use Vertex AI SDK for better reliability

```bash
# Enable Vertex AI mode
export USE_VERTEX_AI=true
export VERTEX_AI_PROJECT_ID=your-project-id

# Set up GCS bucket (one-time)
poetry run python scripts/setup_vertex_ai.py

# Process videos with improved reliability
poetry run clipscribe process video "URL"
```

Benefits of Vertex AI:
- Enterprise-grade infrastructure
- Automatic retry logic
- Better error handling
- Same pricing as Google AI SDK
- Minimal GCS storage costs (auto-cleanup)

### "No Transcript Available"
This happens when:
1. Video has no captions
2. Video is age-restricted
3. Video is private/deleted

**Solution**: Use enhanced temporal intelligence processing for optimal performance
```bash
clipscribe process video "URL" --force-transcribe
```

### Download Failed
Common causes:
- Rate limiting
- Geographic restrictions
- Authentication required

**Solutions**:
```bash
# Slow down requests
clipscribe process video "URL" --rate-limit 50k

# Skip certificate check (use carefully)
clipscribe process video "URL" --no-check-certificate
```

### Large Video Memory Issues
For videos over 2 hours:
```bash
# Process in chunks (coming in v2.3)
# For now, download and process manually:
yt-dlp "URL" -o video.mp4
clipscribe process video video.mp4
```

### Video Not Found
```
ERROR: Video unavailable
```

**Solutions:**
- Check if the video is private or age-restricted
- Try using cookies file for authentication
- Verify the URL is correct

### Timeout Errors with Long Videos
```
ERROR: 504 Deadline Exceeded
```
**This happens when processing videos longer than ~15 minutes with default settings.**

**Solutions:**
1. Set the `GEMINI_REQUEST_TIMEOUT` environment variable:
   ```bash
   # In your .env file
   GEMINI_REQUEST_TIMEOUT=14400  # 4 hours
   ```

2. For very long videos, consider:
   - Using `--start-time` and `--end-time` to process segments
   - Using enhanced temporal intelligence for optimal processing
   - Breaking into smaller chunks

**Example for processing a segment:**
```bash
clipscribe process video "URL" --start-time 0 --end-time 1800  # First 30 minutes
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

# Enable caching
export CLIPSCRIBE_CACHE=true
```

### High API Costs
Monitor costs with:
```bash
# Check estimated cost before processing
clipscribe estimate "URL"

# Use enhanced temporal intelligence
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
- Re-run with `--force` to overwrite

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
Run with debug logging:
```bash
# Via environment
export CLIPSCRIBE_LOG_LEVEL=DEBUG

# Via CLI
clipscribe --debug process video "URL"
```

### Quick Test
Verify installation:
```bash
# Test with known-good video
clipscribe --debug process video "https://www.youtube.com/watch?v=7sWj6D2i4eU"
```

### Reset Everything
Nuclear option:
```bash
# Full reset
rm -rf ~/.cache/clipscribe
rm -rf .venv poetry.lock
poetry install
poetry run pytest
```

### Report Issues
1. Check existing issues: https://github.com/bubroz/clipscribe/issues
2. Include:
   - ClipScribe version (`clipscribe --version`)
   - Python version (`python --version`)
   - Full error message
   - Debug log output
   - Video URL (if not sensitive)

### Common Error Messages
| Error | Cause | Solution |
|---|---|---|
| `TranscriptNotAvailable` | No captions | Use `--force-transcribe` |
| `VideoUnavailable` | Private/deleted | Check URL is accessible |
| `APIQuotaExceeded` | Hit API limits | Wait or upgrade quota |
| `ModelNotFound` | Models not downloaded | Run `clipscribe download-models` |
| `PermissionError` | Can't write output | Check directory permissions |

## Development and Testing Best Practices

###  CRITICAL: Validation Before Deployment
To prevent issues like import errors, broken functionality, or incomplete features:

#### 1. **Always Test Imports First**
```bash
# Before declaring any feature complete
poetry run python -c "from module import function; print(' Import successful')"
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
poetry run python -c "import streamlit as st; from src.module import component"
poetry run streamlit run app.py --server.port 8501 &
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501  # Should return 200
pkill -f streamlit
```

#### 4. **Common Validation Patterns**
**For CLI Commands:**
```bash
poetry run clipscribe --help  # Should show help without errors
poetry run clipscribe process video "test_url"  # Should process successfully
```

**For Python Modules:**
```bash
poetry run python -c "from clipscribe.config import settings; print(settings.google_api_key[:8])"
```

**For Web Interfaces:**
```bash
poetry run streamlit run app.py &
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

Remember: When in doubt, run with `--debug`  

### Vertex AI Failures
- **Symptom**: The application crashes with errors related to `vertexai` or Google Cloud permissions, especially during batch processing.
- **Solution**: As of v2.19.7, the system has a **graceful fallback mechanism**. If Vertex AI processing fails for any reason (e.g., incorrect configuration, quota limits), ClipScribe will automatically log a warning and switch to the standard Gemini API to complete the job. This ensures that your processing can continue even if the Vertex AI setup is not perfect. To force the use of the standard Gemini API, you can set `USE_VERTEX_AI=False` in your `.env` file. 

## Enterprise Issues
For scaling problems, check Vertex quotas