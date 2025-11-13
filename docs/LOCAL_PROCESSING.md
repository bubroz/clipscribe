# Local Processing Guide

**Version:** v3.0.0  
**Last Updated:** November 13, 2025  
**Provider:** WhisperX Local

Complete guide to FREE local processing with ClipScribe on Apple Silicon or Intel CPU.

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Setup](#setup)
- [Performance](#performance)
- [Cost Analysis](#cost-analysis)
- [Troubleshooting](#troubleshooting)

---

## Overview

### WhisperX Local Provider

Run ClipScribe **entirely on your Mac** for FREE transcription with speaker diarization.

**Benefits:**
- 💰 **FREE transcription** (only Grok intelligence cost ~$0.005/30min)
- 🔒 **Privacy** (no data leaves your machine)
- 📶 **Offline** (works without internet for transcription)
- 🎯 **Speaker diarization** (identifies who said what)
- ✅ **Same quality** as cloud GPU

**How it works:**
- WhisperX large-v3 runs locally
- PyAnnote speaker diarization
- CPU processing (MPS/Metal not supported by faster-whisper yet)
- Models cached after first download (~8GB one-time)

---

## Requirements

### Hardware

**Minimum:**
- Mac with Apple Silicon (M1/M2/M3/M4) OR Intel CPU
- 16GB RAM
- 20GB free disk space (for models)

**Recommended:**
- Apple Silicon Mac (M-series)
- 32GB+ RAM (for long files or multi-speaker)
- SSD storage

**Performance:**
- Apple Silicon: 1-2x realtime (16min audio = ~10-20min processing)
- Intel CPU: 0.5-1x realtime (slower but works)

### Software

- macOS 11+ (Big Sur or later)
- Python 3.11-3.12
- Poetry (for installation)

---

## Setup

### Step 1: Install ClipScribe

```bash
# Clone repository
git clone https://github.com/bubroz/clipscribe
cd clipscribe

# Install dependencies
poetry install

# This installs:
# - whisperx (transcription engine)
# - pyannote-audio (speaker diarization)
# - torch (ML framework)
```

### Step 2: Get HuggingFace Token

WhisperX Local requires a HuggingFace token for speaker diarization models.

**Get token:**
1. Visit: https://huggingface.co/settings/tokens
2. Create new token (read access sufficient)
3. Copy the token

**Set token:**
```bash
# Method 1: Environment variable
export HUGGINGFACE_TOKEN=hf_your_token_here

# Method 2: .env file (recommended)
echo "HUGGINGFACE_TOKEN=hf_your_token_here" >> .env
```

### Step 3: Get Grok API Key

For intelligence extraction:

```bash
# Get key from: https://x.ai/api
export XAI_API_KEY=your_xai_key

# Or add to .env
echo "XAI_API_KEY=your_xai_key" >> .env
```

### Step 4: First Run (Model Download)

**First time only** - downloads models (~8GB):

```bash
clipscribe process test_audio.mp3 -t whisperx-local
```

**What downloads:**
- WhisperX large-v3 model (~3GB)
- PyAnnote diarization models (~4GB)
- Alignment models (~1GB)

**Cached to:** `~/.cache/whisperx/` and `~/.cache/huggingface/`

**Subsequent runs:** Models load from cache (10-15 seconds), no re-download

---

## Performance

### Expected Performance

**Processing Speed (Apple Silicon):**
- Short files (5-15 min): 1.5-2x realtime
- Medium files (15-45 min): 1-1.5x realtime
- Long files (60+ min): 0.8-1.2x realtime

**Example (16.3min medical audio, validated):**
- Processing time: 21 minutes
- Realtime factor: 1.3x
- CPU usage: 80-100% (single core)
- Memory: ~3GB peak

**Processing Speed (Intel CPU):**
- Expect 0.5-1x realtime (slower but functional)

### Resource Usage

**Memory:**
- Model loading: ~2GB
- Processing peak: ~3-4GB
- Recommended: 16GB total RAM (8GB minimum)

**CPU:**
- Single-core intensive (80-100% on one core)
- Duration: Matches processing time
- Other apps may slow down during processing

**Disk:**
- Models: ~8GB (cached, one-time)
- Temp files: ~100MB per file (auto-cleaned)

### Device Detection

WhisperX Local auto-detects device:

```
Apple Silicon detected - using CPU (MPS not yet supported by faster-whisper)
Loading WhisperX model: large-v3 on cpu
```

**Why CPU not GPU?**
- faster-whisper library (WhisperX's backend) doesn't support Metal/MPS yet
- CPU mode on Apple Silicon is still fast (efficient ARM cores)
- Performance is acceptable (1-2x realtime)

---

## Cost Analysis

### FREE Transcription!

**Cost breakdown (30min video):**
- Transcription: **$0.00** (runs locally)
- Intelligence (Grok): ~$0.005
- **Total: ~$0.005**

**Comparison:**
- Voxtral + Grok: $0.035 (7x more expensive)
- WhisperX Modal + Grok: $0.060 (12x more expensive)
- **WhisperX Local + Grok: $0.005 (cheapest!)**

**When is local worth it?**

**Use local if:**
- Processing >6 files per month (savings > Modal cost)
- Privacy requirements (data can't leave machine)
- Learning/experimentation (no cost concerns)
- Offline processing needed

**Use Modal if:**
- Speed critical (10x vs 1-2x realtime)
- Processing one-off files (no local setup time)
- Scalability needed (parallel processing)

### Actual Validated Costs

**16.3min medical file:**
- Transcription: $0.00
- Intelligence: $0.0018
- Total: **$0.0018**

**Estimate was $0.0094** - actual 81% cheaper!

---

## Troubleshooting

### "HUGGINGFACE_TOKEN required"

**Problem:** Token not set or not found

**Solution:**
```bash
# Check if set
echo $HUGGINGFACE_TOKEN

# Set it
export HUGGINGFACE_TOKEN=hf_your_token

# Or add to .env
echo "HUGGINGFACE_TOKEN=hf_your_token" >> .env

# Verify ClipScribe sees it
poetry run clipscribe utils check-auth
```

### Models Not Downloading

**Problem:** First run stuck or fails

**Solution:**
```bash
# Check internet connection
ping huggingface.co

# Check disk space
df -h ~/.cache

# Manual model download
poetry run python -c "
import whisperx
model = whisperx.load_model('large-v3', 'cpu')
print('Model downloaded successfully')
"
```

### Out of Memory

**Symptoms:** Process crashes, system freezes

**Solutions:**
1. **Close other applications** (free up RAM)
2. **Process shorter files** (split long files)
3. **Use WhisperX Modal** (cloud GPU has 24GB)

### Slow Performance

**Expected:** 1-2x realtime on Apple Silicon

**If slower (0.5x realtime or worse):**
- Check CPU usage in Activity Monitor
- Close background apps
- Check if using swap memory (RAM full)
- Consider upgrading RAM
- Or use WhisperX Modal (10x realtime)

### Speaker Diarization Not Working

**Problem:** All segments labeled "Unknown" or no speaker labels

**Solutions:**
1. **Check HUGGINGFACE_TOKEN is set**
2. **Ensure pyannote-audio installed:** `poetry install`
3. **Check logs for diarization errors**
4. **Try without diarization:** `--no-diarize` (faster, still works)

---

## Advanced Usage

### Processing Without Diarization (Faster)

If you don't need speakers:

```bash
clipscribe process lecture.mp3 -t whisperx-local --no-diarize
```

**Benefits:**
- ~30% faster (skips diarization step)
- Less memory usage
- No HUGGINGFACE_TOKEN needed

**Trade-off:** Can't identify who said what

### Batch Processing Locally

Process multiple files:

```bash
# Loop through files
for f in *.mp3; do
    clipscribe process "$f" -t whisperx-local
done

# Or use GNU parallel (faster)
parallel clipscribe process {} -t whisperx-local ::: *.mp3
```

**Cost:** Still FREE for transcription! Only Grok costs add up.

---

**For complete CLI reference, see [CLI.md](CLI.md)**  
**For provider comparison, see [PROVIDERS.md](PROVIDERS.md)**  
**For system architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)**

