# ClipScribe CLI Reference

*Last Updated: 2025-10-12 - v2.54.0*

## Quick Start

```bash
# Process single video
clipscribe process video "https://youtube.com/watch?v=..."

# Monitor channel (async, 10 workers)
clipscribe monitor-async --channels UCxxx --interval 300 --workers 10

# Check stats
clipscribe stats
```

## Core Commands

### `process video`
Process a single video with full intelligence extraction.

```bash
clipscribe process video <URL> [OPTIONS]

Options:
  --output-dir PATH      Output directory
  --with-x-draft        Generate X/Twitter content draft
  --force               Reprocess even if already done
```

### `monitor-async`
Monitor YouTube channels with 10-worker async architecture.

```bash
clipscribe monitor-async --channels <CHANNEL_IDS> [OPTIONS]

Options:
  --channels TEXT       Comma-separated channel IDs (required)
  --interval INTEGER    Check interval in seconds (default: 60)
  --workers INTEGER     Concurrent workers (default: 10)
  --output-dir PATH     Output directory
```

**Features**:
- Concurrent processing (10 videos at once)
- Auto-detect new uploads via RSS
- Shorts filtering (multi-layer)
- Telegram notifications
- GCS mobile pages
- Crash-resistant (worker restart after 100 videos)

### `stats`
Show processing statistics and recent videos.

```bash
clipscribe stats
```

### `batch-process`
Process multiple videos with comprehensive analysis.

```bash
clipscribe batch-process --urls urls.txt
```

## Output Files

Each processed video creates:
- `core.json` - Entities, relationships, summary
- `knowledge_graph.json` - Graph data
- `transcript.txt` - Full transcript
- `report.md` - Formatted report
- `metadata.json` - Video metadata
- `x_draft/` - X/Twitter content (if `--with-x-draft`)

## Environment Variables

```bash
# Required for X content generation
XAI_API_KEY=your_xai_api_key

# Required for transcription
VOXTRAL_API_KEY=your_voxtral_key

# Optional: Telegram notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional: GCS uploads
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## Current Stack (v2.54.0)

- **Transcription**: Voxtral (uncensored, $0.002/min)
- **Intelligence**: Grok-4 (uncensored, dense extraction)
- **Tweet Generation**: 3 styles (Analyst, Alarm, Educator)
- **Architecture**: 10-worker async (processes 10 videos concurrently)
- **Reliability**: Comprehensive retry logic (Telegram, GCS, Grok)

## Support

See [STATUS.md](../STATUS.md) for current capabilities and known issues.
