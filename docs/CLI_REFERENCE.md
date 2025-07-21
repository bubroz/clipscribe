# ClipScribe CLI Reference

*Last Updated: July 20, 2025 - v2.19.3 with Vertex AI integration*

Complete reference for all ClipScribe commands and options.

## ✨ Key Features

- **Lightning-fast CLI** - 0.4s startup time
- **1800+ platforms** - YouTube, Twitter, TikTok, Vimeo, and more
- **Enhanced extraction** - 16+ entities and 52+ relationships per video
- **Cost-effective** - $0.002-0.0035/minute processing
- **Multiple outputs** - JSON, CSV, GEXF, Markdown formats

## Global Options

These options work with all commands:

```bash
clipscribe [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--version` | Show ClipScribe version and exit |
| `--help` | Show help message and exit |
| `--debug` | Enable debug logging |

## Commands

### `transcribe` - Extract Video Intelligence

Process videos to extract entities, relationships, and generate knowledge graphs.

```bash
clipscribe transcribe [OPTIONS] URL
```

**Arguments:**
- `URL` (required) - Video URL to process

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output-dir` | `-o` | `output` | Directory to save outputs |
| `--mode` | `-m` | `audio` | Processing mode: audio, video, auto |
| `--use-cache/--no-cache` | | True | Use cached results if available |
| `--enhance-transcript` | | False | Add speaker diarization and timestamps |
| `--clean-graph` | | False | Clean knowledge graph with AI |
| `--skip-cleaning` | | False | Skip graph cleaning to see raw results |
| `--visualize` | | False | Generate interactive visualization |
| `--performance-report` | | False | Generate performance report |

**Examples:**

```bash
# Basic video processing
clipscribe transcribe "https://youtube.com/watch?v=6ZVj1_SE4Mo"

# Process with visualization
clipscribe transcribe "https://youtube.com/watch?v=6ZVj1_SE4Mo" \
  --clean-graph \
  --visualize

# Use video mode for visual content
clipscribe transcribe "https://vimeo.com/123456" \
  --mode video \
  --enhance-transcript
```

### `research` - Research Videos by Topic

Search and analyze multiple videos on a topic.

```bash
clipscribe research [OPTIONS] QUERY
```

**Arguments:**
- `QUERY` (required) - Search term or YouTube channel URL

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--max-results` | `-n` | `2` | Maximum videos to analyze |
| `--period` | | None | Filter: hour, day, week, month, year |
| `--sort-by` | | `relevance` | Sort: relevance, newest, oldest, popular |
| `--output-dir` | `-o` | `output/research` | Output directory |

**Examples:**

```bash
# Research a topic
clipscribe research "climate change solutions" --max-results 5

# Analyze a YouTube channel
clipscribe research "https://www.youtube.com/@pbsnewshour" \
  --max-results 10 \
  --sort-by newest
```

### `process-collection` - Analyze Video Collections

Process multiple videos as a unified collection.

```bash
clipscribe process-collection [OPTIONS] TITLE URL1 URL2 [URL3...]
```

**Arguments:**
- `TITLE` (required) - Collection title
- `URLs` (required) - Video URLs or playlist URL

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--collection-type` | | `custom` | Type: series, topic_research, channel |
| `--output-dir` | `-o` | `output/collections` | Output directory |
| `--limit` | `-l` | None | Limit videos from playlists |
| `--skip-confirmation` | | False | Skip confirmation prompt |

**Examples:**

```bash
# Process a video series
clipscribe process-collection \
  "Investigation Series" \
  "https://youtube.com/watch?v=part1" \
  "https://youtube.com/watch?v=part2" \
  "https://youtube.com/watch?v=part3"

# Process YouTube playlist
clipscribe process-collection \
  "CNBC Market Analysis" \
  "https://www.youtube.com/playlist?list=PLVbP054..." \
  --limit 20
```

### `process-series` - Process Related Videos

Process multiple related videos as a series.

```bash
clipscribe process-series [OPTIONS] URL1 URL2 [URL3...]
```

**Arguments:**
- `URLs` (required) - Video URLs in series order

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--series-title` | `-t` | Auto | Title for the series |
| `--output-dir` | `-o` | `output` | Output directory |
| `--mode` | `-m` | `audio` | Processing mode |

**Examples:**

```bash
# Process documentary series
clipscribe process-series \
  "https://youtube.com/watch?v=doc_pt1" \
  "https://youtube.com/watch?v=doc_pt2" \
  --series-title "Nature Documentary"
```

### `clean-demo` - Clean Demo Folders

Clean up old demo and test folders.

```bash
clipscribe clean-demo [OPTIONS]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--demo-dir` | `-d` | `demo` | Demo directory |
| `--dry-run` | | False | Show what would be deleted |
| `--keep-recent` | `-k` | `3` | Keep N recent collections |

**Examples:**

```bash
# Preview cleanup
clipscribe clean-demo --dry-run

# Clean keeping last 5
clipscribe clean-demo --keep-recent 5
```

## Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GOOGLE_API_KEY` | Yes | Google AI Studio API key | None |
| `VERTEX_AI_PROJECT` | No | Google Cloud project ID | None |
| `VERTEX_AI_LOCATION` | No | Vertex AI location | `us-central1` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `COST_WARNING_THRESHOLD` | No | Cost warning threshold | `1.0` |

## Output Files

Each processed video creates:

- `transcript.txt` - Plain text transcript
- `transcript.json` - Full structured data with all analysis
- `metadata.json` - Processing metadata
- `entities.json` - Extracted entities with confidence scores
- `entities.csv` - Entities in spreadsheet format
- `relationships.json` - Entity relationships with evidence
- `relationships.csv` - Relationships in spreadsheet format
- `knowledge_graph.json` - Graph structure (nodes and edges)
- `knowledge_graph.gexf` - Gephi-compatible visualization
- `report.md` - Markdown intelligence report
- `manifest.json` - File checksums

## Advanced Usage

### Batch Processing
```bash
# Process multiple videos from file
while read url; do
  clipscribe transcribe "$url" -o batch-output/
done < video_urls.txt
```

### Using with Vertex AI
```bash
# First pre-upload videos to GCS
python scripts/pre_upload_videos.py

# Then process using GCS URIs
clipscribe transcribe "gs://bucket/videos/video.mp4" \
  --mode video
```

### Pipeline Integration
```bash
# Extract and analyze
clipscribe transcribe "$URL" | \
  jq '.entities[] | select(.confidence > 0.8)' > high_confidence_entities.json
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | API key not found |
| 4 | Network error |
| 5 | Unsupported video URL |

## Performance Tips

1. **Use caching** - Avoid reprocessing the same videos
2. **Audio mode** - Faster for speech-only content
3. **Video mode** - Better for visual information
4. **Batch collections** - More efficient than individual processing

## Cost Management

- **5-minute video**: ~$0.008
- **30-minute video**: ~$0.048
- **1-hour video**: ~$0.096

Use `COST_WARNING_THRESHOLD` to get alerts before processing expensive videos.

---

For more information, see the [full documentation](README.md). 