# ClipScribe CLI Reference

*Last Updated: 2025-09-05 - v2.51.0*

Complete reference for all ClipScribe commands, groups, and options.

**Current Status**: Enterprise-ready CLI with 99% coverage and comprehensive validation. The system is in private alpha testing - not yet available for public use.

## Installation Options

```bash
# Core installation
poetry install

# For development, including all optional dependencies
poetry install --extras all --with dev
```

##  Key Features

- **Integrated Pipeline**: VideoIntelligenceRetrieverV2 with HybridProcessor (no more Gemini).
- **Consolidated Outputs**: 5 core files with Pydantic validation (reduced from 14+).
- **Output Validation**: Automatic detection and fixing of quality issues.
- **Uncensored Intelligence**: Voxtral transcription + Grok-4 extraction bypasses all safety filters.
- **Cost Optimized**: ~$0.02-0.04 per video with superior quality.
- **Bot Detection Bypass**: Automatic cookie fallback prevents YouTube download failures.
- **1800+ Platforms**: Supports YouTube, Twitter, TikTok, Vimeo, and more.
- **Enterprise Test Coverage**: 400+ unit tests passing with 83-99% coverage on critical infrastructure modules.

## Global Options

These options work with all commands:

```bash
clipscribe [GLOBAL OPTIONS] COMMAND [ARGS]...
```

| Option      | Description                               |
|-------------|-------------------------------------------|
| `--version` | Show ClipScribe version and exit.         |
| `--help`    | Show help message and exit.               |
| `--debug`   | Enable debug logging for detailed output. |

## Command Groups

### `process` - Process Single Media Files

Commands for processing a single video or media file.

#### `process video`

Process a single video from a URL to extract intelligence.

```bash
clipscribe process video [OPTIONS] URL
```

**Arguments:**

- `URL` (required) - The URL of the video to process.

**Options:**

*All options from the previous command set are available here, including `--output-dir`, `--mode`, `--use-flash`, etc.*

- `--cookies-from-browser BROWSER`: Use cookies from a specified browser (e.g., chrome, firefox) to access restricted content.

**Example:**

```bash
# Process a video with default (high-quality) settings
poetry run clipscribe process video "https://www.youtube.com/watch?v=VIDEO_ID"

# Process with faster, standard quality
poetry run clipscribe process video "https://www.youtube.com/watch?v=VIDEO_ID" --use-flash
```

---

### `collection` - Analyze Video Collections

Commands for processing multiple videos as a unified collection.

#### `collection series`

Process multiple related videos as a series with narrative flow analysis.

```bash
clipscribe collection series [OPTIONS] URLS...
```

**Arguments:**

- `URLS...` (required) - A list of video URLs in series order.

**Options:**

*Includes `--output-dir`, `--series-title`, `--use-flash`, etc.*

**Example:**

```bash
# Process a two-part documentary series
poetry run clipscribe collection series "URL_PART_1" "URL_PART_2"
```

#### `collection custom`

Process a custom collection of videos from various sources.

```bash
clipscribe collection custom [OPTIONS] COLLECTION_NAME URLS...
```

**Arguments:**

- `COLLECTION_NAME` (required) - A name for your custom collection.
- `URLS...` (required) - A list of video or playlist URLs.

**Options:**

*Includes `--output-dir`, `--collection-type`, `--limit`, `--use-flash`, etc.*

- `--core-only`: Unify only entities that appear in more than one video (Core Theme Analysis).
- `--cookies-from-browser BROWSER`: Use cookies from a specified browser to access restricted content.

**Example:**

```bash
# Analyze three videos about a specific topic
poetry run clipscribe collection custom "Market Research Q3" "URL1" "URL2" "URL3"
```

---

### `research` - Research by Topic

Search for and analyze multiple videos on a given topic.

```bash
clipscribe research [OPTIONS] QUERY
```

**Arguments:**

- `QUERY` (required) - The search term or a YouTube channel URL.

**Options:**

*Includes `--max-results`, `--period`, `--sort-by`, etc.*

**Example:**

```bash
# Research the latest 5 videos on a topic
poetry run clipscribe research "AI in biotechnology" --max-results 5
```

---

### `utils` - Utility Commands

Commands for project maintenance and utilities.

#### `utils clean-demo`

Clean up old demo and test collection folders.

```bash
clipscribe utils clean-demo [OPTIONS]
```

**Options:**

*Includes `--demo-dir`, `--dry-run`, `--keep-recent`.*

**Example:**

```bash
# See what would be deleted without actually deleting it
poetry run clipscribe utils clean-demo --dry-run
```

#### `utils check-auth`

Verify your API key or Vertex AI authentication.

```bash
clipscribe utils check-auth
```

## Web Interface

A static web interface is available for interacting with the deployed API. See the [Deployment Guide](advanced/deployment/DEPLOYMENT_GUIDE.md) for details.
