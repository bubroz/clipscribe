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
- `URL` (required) - Video URL to process

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output-dir` | `-o` | `output` | Directory to save outputs |
| `--mode` | `-m` | `auto` | Processing mode: audio, video, auto |
| `--use-pro` | | False | **NEW**: Use Gemini 2.5 Pro for highest quality (~$0.017/video) |
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