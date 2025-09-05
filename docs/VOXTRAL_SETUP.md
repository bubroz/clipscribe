# Voxtral Setup Guide

## Overview

Voxtral is Mistral's speech-to-text model that provides uncensored, high-accuracy transcription at 70% lower cost than Gemini.

## Key Benefits

- **No Content Filters**: Transcribes all content without censorship
- **Superior Accuracy**: 1.8% WER vs Gemini's 2.3% WER  
- **70% Cost Savings**: $0.001/minute vs Gemini's $0.0035/minute
- **Long-Form Support**: Handles 30-40 minute chunks natively

## Setup Instructions

### 1. Get Mistral API Key

1. Visit [Mistral AI Console](https://console.mistral.ai/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `msk_`)

### 2. Configure Environment

Add to your `.env` file:
```bash
MISTRAL_API_KEY=msk_your_key_here
```

Or export temporarily:
```bash
export MISTRAL_API_KEY='msk_your_key_here'
```

### 3. Enable Voxtral

#### Option A: Environment Variable (Recommended)
```bash
export USE_VOXTRAL=true
```

#### Option B: Command Line Flag
```bash
poetry run clipscribe process --use-voxtral <video_url>
```

#### Option C: Programmatic
```python
from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber

transcriber = GeminiFlashTranscriber(use_voxtral=True)
```

## Usage Modes

### 1. Voxtral Primary (Recommended for Production)
All transcription goes through Voxtral:
```bash
USE_VOXTRAL=true poetry run clipscribe process <url>
```

### 2. Smart Fallback (Conservative)
Try Gemini first, fall back to Voxtral if blocked:
```bash
# This is the default behavior when Voxtral is configured
poetry run clipscribe process <url>
```

### 3. Force Gemini Only
Disable Voxtral completely:
```bash
USE_VOXTRAL=false poetry run clipscribe process <url>
```

## Testing

### Quick Test
```bash
poetry run python scripts/test_voxtral_quick.py
```

### PBS Frontline Test
```bash
poetry run python scripts/test_voxtral_pbs.py
```

### Compare Models
```bash
poetry run python scripts/test_voxtral_comparison.py
```

## Cost Analysis

For a 94-minute PBS Frontline documentary:

| Service | Cost | Success Rate | Notes |
|---------|------|--------------|-------|
| Gemini Only | $0.33 | 0% | Blocked by safety filters |
| Voxtral Only | $0.094 | 100% | No content filters |
| Hybrid (Voxtral + Gemini extraction) | $0.10 | 100% | Best approach |

## Migration Path

### Phase 1: Testing (Current)
- Voxtral as fallback for blocked content
- Monitor accuracy and performance

### Phase 2: Hybrid Production
- Voxtral for all transcription
- Gemini for entity extraction from text

### Phase 3: Full Migration
- Replace all Gemini transcription with Voxtral
- 70% cost reduction across the board

## Troubleshooting

### "MISTRAL_API_KEY not set"
- Ensure the key is in your `.env` file
- Or export it: `export MISTRAL_API_KEY='msk_...'`

### "Failed to initialize Voxtral"
- Check your API key is valid
- Verify internet connectivity
- Check Mistral API status

### "Transcription failed"
- Check audio file format (MP3, MP4, WAV supported)
- Verify file size (< 200MB)
- Check API quota/credits

## API Documentation

- [Mistral API Docs](https://docs.mistral.ai/api/)
- [Voxtral Models](https://mistral.ai/news/voxtral)
- [Pricing](https://mistral.ai/pricing)
