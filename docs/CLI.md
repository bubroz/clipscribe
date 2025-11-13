# ClipScribe CLI Reference

**Version:** v3.0.0  
**Last Updated:** November 13, 2025

Complete command-line interface reference for ClipScribe.

---

## Table of Contents

- [Installation](#installation)
- [Main Command: `process`](#main-command-process)
- [Utility Commands](#utility-commands)
- [Environment Variables](#environment-variables)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

---

## Installation

```bash
# Clone repository
git clone https://github.com/bubroz/clipscribe
cd clipscribe

# Install with Poetry
poetry install

# Verify installation
poetry run clipscribe --version
# Output: ClipScribe v3.0.0
```

---

## Main Command: `process`

Process audio/video file to extract intelligence.

### Syntax

```bash
clipscribe process AUDIO_FILE [OPTIONS]
```

### Arguments

**AUDIO_FILE** (required)
- Path to audio or video file
- Formats: MP3, MP4, WAV, M4A, WEBM, OGG
- Example: `test_videos/interview.mp3`

### Options

**`-t, --transcription-provider`** (default: `whisperx-local`)
- Choose transcription provider
- Options: `voxtral` | `whisperx-modal` | `whisperx-local`
- Example: `-t voxtral`

**`-i, --intelligence-provider`** (default: `grok`)
- Choose intelligence provider
- Options: `grok` (only option currently)
- Example: `-i grok`

**`--diarize / --no-diarize`** (default: `--diarize`)
- Enable/disable speaker diarization
- Only works with providers that support it
- Example: `--no-diarize`

**`--formats`** (default: `json`, `docx`, `csv`)
- Choose output formats to generate
- Options: `json`, `docx`, `csv`, `pptx`, `markdown`, `all`
- Can specify multiple: `--formats json docx pptx`
- Use `all` for all 5 formats
- Example: `--formats json docx csv`

**`-o, --output-dir`** (default: `output`)
- Output directory for results
- Example: `-o my_results`

### Examples

**Single-speaker, cheap (Mistral API):**
```bash
clipscribe process lecture.mp3 -t voxtral --no-diarize
```

**Multi-speaker, FREE (local Apple Silicon/CPU):**
```bash
clipscribe process interview.mp3 -t whisperx-local
```

**Multi-speaker, cloud quality (Modal GPU):**
```bash
clipscribe process podcast.mp3 -t whisperx-modal
```

**Custom output directory:**
```bash
clipscribe process audio.mp3 -o my_research/results
```

**Multi-format export:**
```bash
# Generate all 5 formats
clipscribe process video.mp3 --formats all

# Select specific formats
clipscribe process video.mp3 --formats json docx pptx

# Just JSON (minimal)
clipscribe process video.mp3 --formats json
```

### Output

Processing creates timestamped directory with selected formats:
```
output/
└── 20251113_001556_filename/
    ├── transcript.json                   # Complete data (always generated)
    ├── intelligence_report.docx          # Professional report (if --formats docx)
    ├── executive_summary.pptx            # 7-slide deck (if --formats pptx)
    ├── report.md                         # Markdown report (if --formats markdown)
    └── csv/                              # Data tables (if --formats csv)
        ├── entities.csv
        ├── relationships.csv
        ├── topics.csv
        ├── key_moments.csv
        └── segments.csv
```

**transcript.json structure:**
```json
{
  "transcript": {
    "segments": [...],
    "language": "en",
    "speakers": 2,
    "cost": 0.0
  },
  "intelligence": {
    "entities": [...],
    "relationships": [...],
    "topics": [...],
    "key_moments": [...],
    "sentiment": {...},
    "cost": 0.0018,
    "cost_breakdown": {...},
    "cache_stats": {...}
  },
  "file_metadata": {
    "filename": "interview.mp3",
    "total_cost": 0.0018
  }
}
```

---

## Command: `process-series`

Process multiple videos as a series to extract cross-video intelligence patterns.

**NEW in v3.0.0** - Analyze entity frequency, relationship patterns, and topic evolution across multiple videos.

### Syntax

```bash
clipscribe process-series FILES_LIST --series-name NAME [OPTIONS]
```

### Arguments

**FILES_LIST** (required)
- Path to text file containing audio/video file paths (one per line)
- Example: `video_list.txt`

**--series-name** (required)
- Name for this video series
- Used in output directory and reports
- Example: `--series-name "Q1-Earnings-Calls"`

### Options

Same options as `process` command:
- `-t, --transcription-provider` (default: `whisperx-local`)
- `-i, --intelligence-provider` (default: `grok`)
- `--diarize / --no-diarize` (default: `--diarize`)
- `--formats` (default: `json`, `docx`, `csv`, `pptx`)
- `-o, --output-dir` (default: `output`)

### Examples

**Analyze earnings calls series:**
```bash
# Create file list
echo "call1.mp3" > earnings_calls.txt
echo "call2.mp3" >> earnings_calls.txt
echo "call3.mp3" >> earnings_calls.txt

# Process series
clipscribe process-series earnings_calls.txt --series-name "Q1-Q4-2024"
```

**Process multi-part investigation:**
```bash
clipscribe process-series interviews.txt --series-name "Cartel-Investigation"
```

### Output

Creates series directory with individual + aggregate analysis:
```
output/collections/
└── 20251113_series_Q1-Q4-2024/
    ├── call1/
    │   ├── transcript.json
    │   ├── intelligence_report.docx
    │   └── [other formats]
    ├── call2/
    │   └── [same structure]
    ├── call3/
    │   └── [same structure]
    └── series_analysis/
        ├── series_report.json          # Aggregate intelligence
        ├── series_summary.docx          # Cross-video findings
        ├── series_presentation.pptx     # Executive brief
        └── aggregate_data.csv           # Combined statistics
```

### Series Analysis Features

**Cross-Video Intelligence:**
- **Entity frequency tracking:** Which entities appear across multiple videos
- **Relationship patterns:** Connections that span videos
- **Topic evolution:** How themes develop across the series
- **Aggregate statistics:** Combined metrics and insights

**Series Report Includes:**
- Top entities by frequency (appeared in X of Y videos)
- Recurring relationships (patterns across corpus)
- Topic timeline (how themes evolved)
- Cross-video insights and patterns

---

## Utility Commands

### `clipscribe utils check-auth`

Verify API key configuration.

```bash
clipscribe utils check-auth
```

**Output:**
```
Auth: Mistral API key detected
MISTRAL_API_KEY: abc123...

Auth: xAI API key detected
XAI_API_KEY: xyz789...
```

### `clipscribe utils clean-demo`

Clean up old test/demo output directories.

```bash
# Dry run (show what would be deleted)
clipscribe utils clean-demo --dry-run

# Keep 5 most recent, delete rest
clipscribe utils clean-demo --keep-recent 5

# Delete all
clipscribe utils clean-demo
```

---

## Environment Variables

### Required for Each Provider

**Voxtral:**
```bash
export MISTRAL_API_KEY=your_mistral_api_key
```
Get from: https://console.mistral.ai

**WhisperX Local:**
```bash
export HUGGINGFACE_TOKEN=your_hf_token
```
Get from: https://huggingface.co/settings/tokens

**WhisperX Modal:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export GCS_BUCKET=your-gcs-bucket-name
```

**Grok Intelligence:**
```bash
export XAI_API_KEY=your_xai_api_key
```
Get from: https://x.ai/api

### Using .env File

```bash
# Create .env file
cp .env.example .env

# Edit .env
MISTRAL_API_KEY=your_key
XAI_API_KEY=your_key
HUGGINGFACE_TOKEN=your_token

# ClipScribe automatically loads .env
clipscribe process file.mp3
```

---

## Common Workflows

### Workflow 1: Budget-Conscious Single-Speaker

```bash
# Get audio file
yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=..."

# Process with cheap Mistral API (no speakers)
clipscribe process video.mp3 -t voxtral --no-diarize

# Cost: ~$0.03 for 30min
```

### Workflow 2: FREE Multi-Speaker (Local)

```bash
# Get audio file
yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=..."

# Process locally (FREE transcription, speakers included!)
clipscribe process video.mp3 -t whisperx-local

# Cost: ~$0.005 for 30min (only Grok)
# Time: ~30-60min processing for 30min audio (1-2x realtime on CPU)
```

### Workflow 3: Professional Quality (Cloud GPU)

```bash
# Get audio file
yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=..."

# Process on Modal GPU (best quality, speakers, fast)
clipscribe process video.mp3 -t whisperx-modal

# Cost: ~$0.06 for 30min
# Time: ~3min processing for 30min audio (10x realtime on GPU)
```

### Workflow 4: Batch Processing Multiple Files

```bash
# Get multiple files
yt-dlp -x --audio-format mp3 -a urls.txt

# Process each (use loop for now, batch coming in v3.1.0)
for f in *.mp3; do
    clipscribe process "$f" -t whisperx-local
done

# Or use GNU parallel for speed
parallel clipscribe process {} -t whisperx-local ::: *.mp3
```

---

## Troubleshooting

### "Missing or invalid bearer token"

**Problem:** API key not set

**Solution:**
```bash
# Check which keys are set
clipscribe utils check-auth

# Set missing keys
export MISTRAL_API_KEY=your_key
export XAI_API_KEY=your_key
```

### "Voxtral does not support speaker diarization"

**Problem:** Requested `--diarize` with Voxtral

**Solution:** Use WhisperX for multi-speaker:
```bash
clipscribe process file.mp3 -t whisperx-local  # FREE
# or
clipscribe process file.mp3 -t whisperx-modal  # Cloud GPU
```

### "HUGGINGFACE_TOKEN required"

**Problem:** WhisperX Local needs token for diarization

**Solution:**
```bash
# Get token from HuggingFace
# https://huggingface.co/settings/tokens

export HUGGINGFACE_TOKEN=your_token

# Or disable diarization
clipscribe process file.mp3 -t whisperx-local --no-diarize
```

### Slow Processing

**WhisperX Local expected speed:** 1-2x realtime on Apple Silicon CPU

**If slower:**
- Close other CPU-intensive applications
- Check RAM available (16GB minimum recommended)
- Monitor CPU usage in Activity Monitor
- Consider WhisperX Modal for faster processing (10x realtime on GPU)

### "Could not connect to Modal app"

**Problem:** WhisperX Modal app not deployed

**Solution:**
```bash
# Deploy Modal app
cd clipscribe
modal deploy deploy/station10_modal.py

# Verify
modal app list
# Should show: clipscribe-transcription
```

---

## Advanced Usage

### Cost Estimation Before Processing

ClipScribe shows cost estimates before processing:

```
File: interview.mp3
Duration: 16.3 minutes
Estimated cost: $0.0094
  Transcription (whisperx-local): $0.0000
  Intelligence (grok): $0.0094
```

Actual costs displayed after completion.

### Provider Comparison

Test same file with different providers:

```bash
# Compare costs and quality
clipscribe process test.mp3 -t voxtral --no-diarize  # Cheap, no speakers
clipscribe process test.mp3 -t whisperx-local        # FREE, speakers
clipscribe process test.mp3 -t whisperx-modal        # GPU quality, speakers
```

Compare results in `output/` directories.

---

**For provider selection guide, see [PROVIDERS.md](PROVIDERS.md)**  
**For system architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)**  
**For API usage, see [API.md](API.md)**

