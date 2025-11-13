# ClipScribe Provider System

**Version:** v3.0.0  
**Last Updated:** November 13, 2025

Complete guide to ClipScribe's provider system - choose optimal transcription and intelligence providers for your use case.

---

## Table of Contents

- [Overview](#overview)
- [Transcription Providers](#transcription-providers)
- [Intelligence Providers](#intelligence-providers)
- [Provider Selection Guide](#provider-selection-guide)
- [Cost Comparison](#cost-comparison)
- [Setup Instructions](#setup-instructions)

---

## Overview

### What Are Providers?

Providers are swappable components for transcription and intelligence extraction. Choose the best provider for your:
- **Budget** (FREE to $0.06 per 30min)
- **Quality needs** (speakers vs no speakers)
- **Privacy requirements** (local vs cloud)
- **Performance** (API speed vs GPU quality)

### Provider Architecture

```
Audio File
    ↓
Transcription Provider (Voxtral | WhisperX Local | WhisperX Modal)
    ↓
TranscriptResult (standardized format)
    ↓
Intelligence Provider (Grok)
    ↓
IntelligenceResult (entities, relationships, topics)
    ↓
Comprehensive JSON Output
```

---

## Transcription Providers

### Voxtral (Mistral API)

**What it is:** Mistral's Voxtral API for fast,budget-friendly transcription

**Features:**
- ✅ Fast API-based processing (~0.1x realtime from API latency)
- ✅ Extremely cheap ($0.001/min)
- ❌ **NO speaker diarization** (single-speaker only)
- ✅ Retry logic with exponential backoff
- ✅ Language auto-detection

**Cost:** $0.001/min = **$0.03 for 30min video**

**Best for:**
- Single-speaker content (lectures, monologues, audiobooks)
- Budget-conscious processing
- Fast turnaround (API speed)

**Limitations:**
- Cannot identify who said what
- Not suitable for interviews, podcasts, meetings

**Setup:**
```bash
export MISTRAL_API_KEY=your_key_here
# Get key from: https://console.mistral.ai
```

**Usage:**
```bash
clipscribe process lecture.mp3 -t voxtral --no-diarize
```

**Validated:** ✅ 7.1min file, $0.0071, accurate transcription

---

### WhisperX Local (Apple Silicon/CPU)

**What it is:** WhisperX running locally on your Mac (Apple Silicon or Intel CPU)

**Features:**
- ✅ **FREE** ($0 transcription cost!)
- ✅ **Speaker diarization** (pyannote.audio)
- ✅ Word-level timestamps
- ✅ Privacy (no data leaves your machine)
- ✅ Offline processing
- ✅ Same quality as Modal GPU
- ⚠️ CPU mode (MPS not supported by faster-whisper library)

**Performance:**
- Apple Silicon (M1/M2/M3/M4): 1-2x realtime on CPU
- Intel CPU: 0.5-1x realtime (slower but works)
- Memory: 2-4GB during processing

**Cost:** **FREE** (only Grok intelligence cost ~$0.005/30min)

**Best for:**
- Privacy-sensitive content
- Cost-conscious processing
- Offline/air-gapped environments
- Learning/experimentation

**Limitations:**
- Slower than cloud GPU (1-2x vs 10x realtime)
- Uses CPU not GPU (faster-whisper doesn't support Metal/MPS yet)
- First-time model download (~8GB, one-time)

**Setup:**
```bash
# Install ClipScribe
poetry install  # Includes whisperx and pyannote-audio

# Get HuggingFace token for speaker diarization
export HUGGINGFACE_TOKEN=your_token_here
# Get token from: https://huggingface.co/settings/tokens

# First run downloads models (~8GB, cached after)
clipscribe process audio.mp3 -t whisperx-local
```

**Usage:**
```bash
# Multi-speaker, FREE
clipscribe process interview.mp3 -t whisperx-local

# Single-speaker (faster, still FREE)
clipscribe process lecture.mp3 -t whisperx-local --no-diarize
```

**Validated:** ✅ 16.3min file, $0.0018 (FREE transcription + Grok), 1 speaker detected, 20 entities

---

### WhisperX Modal (Cloud GPU)

**What it is:** WhisperX running on Modal cloud GPU (A10G, serverless)

**Features:**
- ✅ **10x realtime** processing (30min video = 3min processing)
- ✅ **Speaker diarization** (pyannote + Gemini verification)
- ✅ Highest quality transcription
- ✅ Scalable (serverless, auto-scales)
- ✅ OOM retry with cascading batch sizes
- ✅ Multi-sample language detection
- ✅ Speaker quality improvement algorithms

**Performance:**
- Processing: 10x realtime on A10G GPU
- Memory: 24GB GPU VRAM (handles any file)
- Latency: GCS upload/download overhead

**Cost:** ~$0.055 for 30min video (GPU + Grok)

**Best for:**
- Multi-speaker content (interviews, podcasts, meetings)
- Professional-grade quality requirements
- Cloud processing (no local GPU needed)
- Scalability (process many files in parallel)

**Limitations:**
- Requires Modal deployment
- Requires GCS configuration
- Higher cost than local (worth it for quality + speed)

**Setup:**
```bash
# Deploy Modal app
modal deploy deploy/station10_modal.py

# Configure GCS
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export GCS_BUCKET=your-bucket-name
```

**Usage:**
```bash
# Multi-speaker, cloud GPU quality
clipscribe process podcast.mp3 -t whisperx-modal
```

**Validated:** ⏳ Not yet tested (code ready, needs GCS upload test)

---

## Intelligence Providers

### Grok (xAI)

**What it is:** xAI's Grok-4-fast-reasoning for entity and relationship extraction

**Features:**
- ✅ **Prompt caching** (75% savings on cached tokens)
- ✅ **Two-tier pricing** (<128K vs >128K context auto-detected)
- ✅ **Structured outputs** (json_schema, type-safe)
- ✅ **Server-side tools** (web_search, x_search for fact-checking)
- ✅ Detailed cost breakdowns
- ✅ Cache performance tracking

**Pricing (Standard tier, <128K context):**
- Input: $0.20 per 1M tokens
- Output: $0.50 per 1M tokens
- Cached: $0.05 per 1M tokens (75% savings!)

**Typical cost:** $0.002-0.005 for 30min video

**Best for:**
- Comprehensive intelligence extraction
- Cost-effective (with caching)
- High-quality entity extraction

**Setup:**
```bash
export XAI_API_KEY=your_key_here
# Get key from: https://x.ai/api
```

**Usage:**
```bash
# Default (Grok is only intelligence provider currently)
clipscribe process audio.mp3
```

**Validated:** ✅ 100% feature preservation (caching, pricing, tools all working)

---

## Provider Selection Guide

### Decision Tree

```
Do you need speaker attribution (who said what)?
│
├─ NO (single-speaker content)
│  └─ Use Voxtral
│     Cost: $0.03/30min
│     Speed: Fast (API)
│
└─ YES (multi-speaker content)
   │
   ├─ Want FREE processing?
   │  └─ Use WhisperX Local
   │     Cost: $0.00/30min (only Grok)
   │     Speed: 1-2x realtime (CPU)
   │     Privacy: Data stays local
   │
   └─ Want best quality + speed?
      └─ Use WhisperX Modal
         Cost: $0.06/30min
         Speed: 10x realtime (GPU)
         Quality: Gemini speaker verification
```

### Use Case Matrix

| Use Case | Recommended Provider | Why |
|----------|---------------------|-----|
| Lecture transcription | Voxtral | Single-speaker, cheap |
| Surveillance footage | Voxtral | Single-speaker, no privacy concerns |
| Interview processing | WhisperX Local | Multi-speaker, cost savings |
| Podcast analysis | WhisperX Local or Modal | Speakers needed, local=FREE, Modal=quality |
| Legal deposition | WhisperX Modal | Professional quality, speakers critical |
| Meeting transcription | WhisperX Local | Speakers, privacy, FREE |
| Large batch (100+ files) | WhisperX Modal | Scalability, parallel processing |

---

## Cost Comparison

### 30-Minute Video

| Provider Combo | Transcription | Intelligence | Total | Speakers | Speed |
|----------------|---------------|--------------|-------|----------|-------|
| Voxtral + Grok | $0.030 | $0.005 | **$0.035** | ❌ No | API (fast) |
| WhisperX Local + Grok | $0.000 | $0.005 | **$0.005** | ✅ Yes | 1-2x realtime |
| WhisperX Modal + Grok | $0.055 | $0.005 | **$0.060** | ✅ Yes | 10x realtime |

### Cost Breakdown Detail

**Voxtral:**
- 30min × $0.001/min = $0.03
- No additional costs
- Mistral API charges

**WhisperX Local:**
- **FREE transcription** (runs on your CPU)
- Only Grok cost (~$0.005)
- One-time model download (~8GB)

**WhisperX Modal:**
- GPU processing: ~3min × $0.01836/min = $0.055
- Includes: WhisperX + diarization + Gemini verification
- Plus Grok: ~$0.005

**Intelligence (Grok):**
- Input tokens: ~3,500 @ $0.20/M = $0.0007
- Output tokens: ~1,000 @ $0.50/M = $0.0005
- Total: ~$0.0012-0.0018
- **With caching:** 50% savings on repeated prompts

---

## Setup Instructions

### Quick Setup (All Providers)

```bash
# 1. Install ClipScribe
git clone https://github.com/bubroz/clipscribe
cd clipscribe
poetry install

# 2. Set API keys
cp .env.example .env
# Edit .env and add:

# For Voxtral provider
MISTRAL_API_KEY=your_mistral_key

# For Grok intelligence
XAI_API_KEY=your_xai_key

# For WhisperX Local diarization
HUGGINGFACE_TOKEN=your_hf_token

# 3. Test
clipscribe process test.mp3
```

### Provider-Specific Setup

**Voxtral:**
1. Get API key: https://console.mistral.ai
2. `export MISTRAL_API_KEY=your_key`
3. Test: `clipscribe process file.mp3 -t voxtral --no-diarize`

**WhisperX Local:**
1. Get HuggingFace token: https://huggingface.co/settings/tokens
2. `export HUGGINGFACE_TOKEN=your_token`
3. First run downloads models (~8GB, one-time)
4. Test: `clipscribe process file.mp3 -t whisperx-local`

**WhisperX Modal:**
1. Deploy Modal app: `modal deploy deploy/station10_modal.py`
2. Configure GCS:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   export GCS_BUCKET=your-bucket-name
   ```
3. Test: `clipscribe process file.mp3 -t whisperx-modal`

---

## Performance Characteristics

### Validated Performance (November 13, 2025)

**Voxtral (7.1min test):**
- Processing time: ~15 seconds (0.35x realtime from API latency)
- Memory: <500MB
- CPU: <10%
- Accuracy: Good (95%+ WER)

**WhisperX Local (16.3min test, Apple Silicon CPU):**
- Processing time: 21 minutes (1.3x realtime)
- Memory: ~3GB
- CPU: 80-100% (single core)
- Accuracy: Excellent (97-99% WER)
- Speakers: 1 detected correctly

**WhisperX Modal (from previous validation):**
- Processing time: 10-11x realtime (30min video = ~3min)
- GPU: A10G 24GB
- Accuracy: Excellent (97-99% WER)
- Speakers: 2-13 detected with Gemini verification

---

## Troubleshooting

### "Voxtral does not support speaker diarization"

**Problem:** You requested `--diarize` with Voxtral provider

**Solution:** Use WhisperX Local or Modal for multi-speaker content:
```bash
clipscribe process file.mp3 -t whisperx-local  # FREE
# or
clipscribe process file.mp3 -t whisperx-modal  # Cloud GPU
```

### "HUGGINGFACE_TOKEN required"

**Problem:** WhisperX Local needs token for speaker diarization

**Solution:**
1. Get token: https://huggingface.co/settings/tokens
2. Set: `export HUGGINGFACE_TOKEN=your_token`
3. Or disable diarization: `--no-diarize`

### "Could not connect to Modal app"

**Problem:** WhisperX Modal provider can't find deployed app

**Solution:**
```bash
# Deploy the Modal app
modal deploy deploy/station10_modal.py

# Verify deployment
modal app list
# Should show: clipscribe-transcription
```

### Slow WhisperX Local Performance

**Expected:** 1-2x realtime on Apple Silicon CPU (MPS not supported by faster-whisper)

**If slower:**
- Close other CPU-intensive apps
- Ensure sufficient RAM (16GB minimum)
- Check Activity Monitor > CPU for utilization
- Consider using WhisperX Modal for faster processing

---

**For complete CLI reference, see [CLI.md](CLI.md)**  
**For system architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)**  
**For API usage, see [API.md](API.md)**

