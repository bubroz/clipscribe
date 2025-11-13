# Troubleshooting Guide

**Version:** v3.0.0  
**Last Updated:** November 13, 2025

Common issues and solutions for ClipScribe.

---

## API Key Issues

### Missing MISTRAL_API_KEY

**Symptom:**
```
ValueError: Mistral API key required (set MISTRAL_API_KEY)
```

**Cause:** MISTRAL_API_KEY environment variable not set

**Solution:**
```bash
# Get API key from Mistral
open https://console.mistral.ai

# Set environment variable
export MISTRAL_API_KEY=your_key_here

# Or add to .env file
echo "MISTRAL_API_KEY=your_key" >> .env

# Verify
poetry run clipscribe utils check-auth
```

### Missing XAI_API_KEY

**Symptom:**
```
ConfigurationError: XAI_API_KEY required.
Get key from: https://x.ai/api
```

**Cause:** XAI_API_KEY not set (needed for Grok intelligence)

**Solution:**
```bash
# Get API key
open https://x.ai/api

# Set it
export XAI_API_KEY=your_key

# Or .env
echo "XAI_API_KEY=your_key" >> .env
```

### Missing HUGGINGFACE_TOKEN

**Symptom:**
```
ConfigurationError: HUGGINGFACE_TOKEN required for speaker diarization.
```

**Cause:** Token not set (needed for WhisperX Local speaker diarization)

**Solution:**
```bash
# Get token
open https://huggingface.co/settings/tokens

# Set it
export HUGGINGFACE_TOKEN=hf_your_token

# Or .env
echo "HUGGINGFACE_TOKEN=hf_your_token" >> .env

# Or disable diarization
clipscribe process file.mp3 --no-diarize
```

---

## Provider Errors

### "Voxtral does not support speaker diarization"

**Symptom:**
```
WARNING: voxtral does not support speaker diarization. 
Processing without speakers. Use -t whisperx-modal or -t whisperx-local 
for multi-speaker content.
```

**Cause:** Requested `--diarize` with Voxtral provider

**Behavior:** Graceful - shows warning and continues without speakers

**Solution:**
```bash
# For multi-speaker content, use:
clipscribe process file.mp3 -t whisperx-local  # FREE
# or
clipscribe process file.mp3 -t whisperx-modal  # Cloud GPU
```

### "Could not connect to Modal app"

**Symptom:**
```
ConfigurationError: Could not connect to Modal app
Deploy the app first:
  poetry run modal deploy deploy/station10_modal.py
```

**Cause:** Modal app not deployed

**Solution:**
```bash
# Deploy Modal app
cd /path/to/clipscribe
poetry run modal deploy deploy/station10_modal.py

# Verify deployment
poetry run modal app list
# Should show: clipscribe-transcription

# Then retry
clipscribe process file.mp3 -t whisperx-modal
```

### "GCS credentials required"

**Symptom:**
```
ConfigurationError: GCS credentials required for Modal provider.
Set one of:
  export SERVICE_ACCOUNT_JSON='{...}'
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

**Cause:** Google Cloud Storage credentials not configured

**Solution:**
```bash
# Set path to service account JSON
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Or add to .env
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json" >> .env
```

---

## File Issues

### File Not Found

**Symptom:**
```
Error: Invalid value for 'AUDIO_FILE': Path 'nonexistent.mp3' does not exist.
```

**Cause:** File path incorrect or file doesn't exist

**Solution:**
```bash
# Check file exists
ls -lh path/to/file.mp3

# Use absolute path
clipscribe process /full/path/to/file.mp3

# Or relative from project root
clipscribe process test_videos/file.mp3
```

### Unsupported Format (Voxtral)

**Symptom:**
```
tenacity.RetryError: RetryError[...]
```

**Cause:** Voxtral may not support some video formats (like MP4)

**Solution:**
```bash
# Convert to MP3 first
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3

# Or use WhisperX Local (handles more formats)
clipscribe process video.mp4 -t whisperx-local
```

---

## Performance Issues

### Slow WhisperX Local Processing

**Expected:** 1-2x realtime on Apple Silicon CPU

**If slower (0.5x or worse):**

**Solutions:**
1. **Close other applications** (free up CPU/RAM)
2. **Check Activity Monitor** → CPU tab (should show high usage)
3. **Disable diarization** if not needed:
   ```bash
   clipscribe process file.mp3 --no-diarize  # ~30% faster
   ```
4. **Use WhisperX Modal** for faster processing (10x realtime on GPU)

### Out of Memory

**Symptom:** Process crashes, system freezes, swap memory high

**Solutions:**
1. **Free up RAM** (close browsers, apps)
2. **Process shorter files** (split long files)
3. **Use WhisperX Modal** (cloud GPU, 24GB VRAM)

### Model Download Slow/Failing

**Symptom:** First run takes very long or hangs

**Cause:** Downloading ~8GB of models

**Solutions:**
```bash
# Check internet connection
ping huggingface.co

# Check disk space
df -h ~/.cache

# If stuck, delete cache and retry
rm -rf ~/.cache/whisperx ~/.cache/huggingface
clipscribe process file.mp3 -t whisperx-local
```

---

## Modal-Specific Issues

### Modal Processing Timeout

**Symptom:** Modal processing takes >1 hour

**Cause:** Very long file or GPU issues

**Solution:**
- Check Modal logs: `poetry run modal app logs clipscribe-transcription`
- Verify GPU allocation in Modal dashboard
- For very long files (2+ hours), consider splitting

### GCS Upload Failures

**Symptom:** 404 or upload errors

**Solutions:**
1. **Verify credentials:**
   ```bash
   gsutil ls gs://your-bucket-name
   ```
2. **Check bucket exists**
3. **Verify service account has Storage Admin role**

---

## Output Issues

### Missing Output Files

**Expected output:**
```
output/timestamp_filename/
└── transcript.json  (comprehensive data)
```

**If missing:**
1. Check for errors in log
2. Verify output directory writable
3. Check disk space

### Speaker Labels Missing

**WhisperX Local:**
- Requires HUGGINGFACE_TOKEN
- First run downloads diarization models
- If fails, continues without speakers (check logs)

**Voxtral:**
- Does NOT support speakers (expected)
- Use WhisperX for multi-speaker

---

## Common Warnings (Safe to Ignore)

### TorchAudio MP3 Warnings

**Warning:**
```
UserWarning: The MPEG_LAYER_III subtype is unknown to TorchAudio.
bits_per_sample will be set to 0.
```

**Impact:** None - cosmetic warning, MP3 processes fine

### PyAnnote Version Mismatch

**Warning:**
```
Model was trained with pyannote.audio 0.0.1, yours is 3.4.0
```

**Impact:** Minimal - speaker diarization still works well

### MPS Not Supported

**Message:**
```
Apple Silicon detected - using CPU (MPS not yet supported by faster-whisper)
```

**Impact:** Expected - faster-whisper library doesn't support Metal yet  
**Performance:** Still good (1-2x realtime on Apple Silicon CPU)

---

## Getting Help

**Check configuration:**
```bash
poetry run clipscribe utils check-auth
```

**Check logs:**
```bash
ls -lth output/*.log
tail -100 output/v3_*.log
```

**Verify installation:**
```bash
poetry run clipscribe --version
poetry run python -c "import whisperx, torch; print('OK')"
```

**For Modal issues:**
```bash
poetry run modal app list
poetry run modal app logs clipscribe-transcription
```

