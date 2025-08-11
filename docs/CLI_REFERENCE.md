# ClipScribe CLI Reference

Last Updated: August 11, 2025 - v2.29.7

Complete reference for all ClipScribe commands, groups, and options.

**Current Status**: Core CLI fully functional. E2E networked tests are gated and run only with explicit credentials (Vertex ADC by default; AI Studio opt-in) to prevent accidental live-cost runs.

##  Key Features

- **Quality First**: Gemini 2.5 Pro is the default for the highest quality intelligence.
- **Speed Option**: Use `--use-flash` for a faster, lower-cost analysis.
- **Structured CLI**: Commands are organized into logical groups (`process`, `collection`, `research`, `utils`).
- **1800+ Platforms**: Supports YouTube, Twitter, TikTok, Vimeo, and more.

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
poetry run clipscribe --debug process video "https://www.youtube.com/watch?v=VIDEO_ID"

# Process with faster, standard quality
poetry run clipscribe --debug process video "https://www.youtube.com/watch?v=VIDEO_ID" --use-flash
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
poetry run clipscribe --debug collection series "URL_PART_1" "URL_PART_2"
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
poetry run clipscribe --debug collection custom "Market Research Q3" "URL1" "URL2" "URL3"
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
poetry run clipscribe --debug research "AI in biotechnology" --max-results 5
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
poetry run clipscribe --debug utils clean-demo --dry-run
```
