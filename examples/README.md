# ClipScribe Examples (v3.0.0)

**Last Updated:** November 13, 2025  
**Architecture:** Provider-based, file-first processing

---

## Quick Start

```bash
# Update quick_start.py with your file path
python examples/quick_start.py
```

---

## Available Examples (v3.0.0)

### ✅ quick_start.py - Basic Provider Usage

Simplest way to use ClipScribe v3.0.0 providers.

**Features:**
- Provider selection (Voxtral, WhisperX Local, WhisperX Modal)
- Basic transcription
- Intelligence extraction
- Cost tracking

**Usage:**
```bash
# Edit file path in quick_start.py
python examples/quick_start.py
```

---

## Prerequisites

**Install ClipScribe:**
```bash
poetry install
```

**Set API Keys:**
```bash
export MISTRAL_API_KEY=your_key     # For Voxtral
export XAI_API_KEY=your_key         # For Grok
export HUGGINGFACE_TOKEN=your_token # For local diarization
```

**Get an audio file:**
```bash
# Use yt-dlp to obtain files
yt-dlp -x --audio-format mp3 "https://youtube.com/..."

# Or use existing test files
ls test_videos/*.mp3
```

---

## Common Patterns (v3.0.0)

### Process with FREE Local Provider

```python
import asyncio
from clipscribe.providers.factory import get_transcription_provider, get_intelligence_provider

async def main():
    # FREE local processing on Apple Silicon
    transcriber = get_transcription_provider("whisperx-local")
    extractor = get_intelligence_provider("grok")
    
    transcript = await transcriber.transcribe("audio.mp3")
    intelligence = await extractor.extract(transcript)
    
    print(f"Cost: ${transcript.cost + intelligence.cost:.4f}")  # Only Grok!
    print(f"Speakers: {transcript.speakers}")
    print(f"Entities: {len(intelligence.entities)}")

asyncio.run(main())
```

### Compare Providers

```python
# Test all 3 providers with same file
for provider in ["voxtral", "whisperx-local", "whisperx-modal"]:
    transcriber = get_transcription_provider(provider)
    result = await transcriber.transcribe("audio.mp3")
    print(f"{provider}: ${result.cost:.4f}")
```

### Provider Cost Comparison

```python
providers = {
    "voxtral": get_transcription_provider("voxtral"),
    "whisperx-local": get_transcription_provider("whisperx-local"),
    "whisperx-modal": get_transcription_provider("whisperx-modal"),
}

duration = 1800  # 30 minutes

for name, provider in providers.items():
    cost = provider.estimate_cost(duration)
    print(f"{name}: ${cost:.4f} for 30min")

# Output:
# voxtral: $0.0300
# whisperx-local: $0.0000 (FREE!)
# whisperx-modal: $0.0600
```

---

## Migration from v2.x

**Old (v2.x):**
```python
from clipscribe.retrievers import VideoIntelligenceRetriever

retriever = VideoIntelligenceRetriever()
result = await retriever.process_url("https://youtube.com/...")
```

**New (v3.0.0):**
```python
from clipscribe.providers.factory import get_transcription_provider, get_intelligence_provider

# Step 1: Obtain file (use yt-dlp separately)
# yt-dlp -x --audio-format mp3 "URL"

# Step 2: Process file with providers
transcriber = get_transcription_provider("whisperx-local")
extractor = get_intelligence_provider("grok")

transcript = await transcriber.transcribe("file.mp3")
intelligence = await extractor.extract(transcript)
```

---

## More Resources

- **[CLI Reference](../docs/CLI.md)** - Complete command reference
- **[Provider Guide](../docs/PROVIDERS.md)** - Provider selection
- **[API Reference](../docs/API.md)** - API usage
- **[Troubleshooting](../docs/TROUBLESHOOTING.md)** - Common issues

---

**ClipScribe v3.0.0** - Provider-based intelligence extraction
