# ClipScribe Troubleshooting Guide

*Last Updated: December 2024*

This guide helps you resolve common issues with ClipScribe.

## Table of Contents
- [Installation Issues](#installation-issues)
- [API Key Problems](#api-key-problems)
- [Video Processing Errors](#video-processing-errors)
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

### Python Version Warning

**Problem**: You see a warning like:
```
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
```
UserWarning: The sentencepiece tokenizer that you are converting to a fast tokenizer uses the byte fallback option which is not implemented in the fast tokenizers.
```

**Solution**: This warning is harmless and has been suppressed in v2.10.0+. If you're still seeing it, update to the latest version:
```bash
poetry update
```

The warning comes from the GLiNER model loading and doesn't affect functionality.

## API Key Problems

### Missing Google API Key
```bash
# Option 1: Set in .env file
echo "GOOGLE_API_KEY=your_key_here" >> .env

# Option 2: Export in shell
export GOOGLE_API_KEY="your_key_here"

# Option 3: Pass via CLI
clipscribe process "URL" --api-key "your_key_here"
```

### Invalid API Key
- Ensure key starts with "AIza"
- Check key has Gemini API enabled in Google Cloud Console
- Verify billing is enabled for the project

## Video Processing Errors

### "No Transcript Available"
This happens when:
1. Video has no captions
2. Video is age-restricted
3. Video is private/deleted

**Solution**: Use audio transcription mode
```bash
clipscribe process "URL" --force-transcribe
```

### Download Failed
Common causes:
- Rate limiting
- Geographic restrictions
- Authentication required

**Solutions**:
```bash
# Slow down requests
clipscribe process "URL" --rate-limit 50k

# Skip certificate check (use carefully)
clipscribe process "URL" --no-check-certificate
```

### Large Video Memory Issues
For videos over 2 hours:
```bash
# Process in chunks (coming in v2.3)
# For now, download and process manually:
yt-dlp "URL" -o video.mp4
clipscribe process video.mp4
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
   - Processing in audio mode (faster than video mode)
   - Breaking into smaller chunks

**Example for processing a segment:**
```bash
clipscribe transcribe "URL" --start-time 0 --end-time 1800  # First 30 minutes
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
clipscribe process "URL" --model flash

# Enable caching
export CLIPSCRIBE_CACHE=true
```

### High API Costs
Monitor costs with:
```bash
# Check estimated cost before processing
clipscribe estimate "URL"

# Use audio-only mode
clipscribe process "URL" --mode audio

# Set cost limit
export COST_WARNING_THRESHOLD=1.0
```

## Output Problems

### Encoding Issues
If you see garbled text:
```bash
# Force UTF-8 encoding
export PYTHONIOENCODING=utf-8
clipscribe process "URL"
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
clipscribe process "URL" --log-level DEBUG
```

### Quick Test
Verify installation:
```bash
# Test with known-good video
clipscribe process "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
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
|-------|-------|----------|
| `TranscriptNotAvailable` | No captions | Use `--force-transcribe` |
| `VideoUnavailable` | Private/deleted | Check URL is accessible |
| `APIQuotaExceeded` | Hit API limits | Wait or upgrade quota |
| `ModelNotFound` | Models not downloaded | Run `clipscribe download-models` |
| `PermissionError` | Can't write output | Check directory permissions |

Remember: When in doubt, run with `--log-level DEBUG` :-) 