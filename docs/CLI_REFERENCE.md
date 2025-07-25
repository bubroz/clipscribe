# ClipScribe CLI Reference

*Last Updated: July 25, 2025 - v2.20.4 with Critical Bug Fixes & Quality Control*

Complete reference for all ClipScribe commands and options.

## ✨ Key Features

- **Quality Control** - Choose Flash ($0.003) vs Pro ($0.017) models via --use-pro flag
- **Fixed Pipeline** - Entities/relationships now properly saved to output files ✅
- **1800+ platforms** - YouTube, Twitter, TikTok, Vimeo, and more
- **Knowledge Graphs** - GEXF generation working (validated 60 nodes, 53 edges)
- **Cost-effective** - $0.0122-0.0167 per video with validated processing

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
- `URL` (required) - Video URL to process (supports 1800+ platforms via yt-dlp)

**Options:**

| Option | Short | Default | Description | Tech Notes |
|--------|-------|---------|-------------|------------|
| `--output-dir` | `-o` | `output` | Directory to save outputs | Creates timestamped subdir |
| `--mode` | `-m` | `auto` | Processing mode: audio, video, auto | 'video' enables visual analysis, adds ~20% time |
| `--use-pro` | | False | Use Gemini 2.5 Pro (~$0.017/video) | Improves entity accuracy by 30-50% (benchmarked) |
| `--use-cache/--no-cache` | | True | Use cached results | Reduces repeat costs by 100% |
| `--enhance-transcript` | | False | Add diarization/timestamps | Adds $0.001-0.002, enables temporal features |
| `--clean-graph` | | False | AI-clean knowledge graph | Adds 5-10s, improves graph quality |
| `--skip-cleaning` | | False | Skip cleaning for raw results | Useful for debugging extractors |
| `--visualize` | | False | Generate interactive viz | Outputs HTML graph, requires pyvis |
| `--performance-report` | | False | Generate report | Includes timings, costs, metrics |

**Examples:**

```bash
# High-quality analysis for data science
clipscribe transcribe "https://youtube.com/watch?v=6ZVj1_SE4Mo" --use-pro --performance-report

# Extend with custom mode
# See Contributing for subclassing VideoIntelligenceRetriever
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