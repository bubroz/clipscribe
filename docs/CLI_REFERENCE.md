# ClipScribe CLI Reference

Complete reference for all ClipScribe commands and options.

## Global Options

These options work with all commands:

```bash
clipscribe [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--version` | Show ClipScribe version and exit |
| `--debug` | Enable debug logging for troubleshooting |
| `--help` | Show help message and exit |

## Commands

### `transcribe` - Transcribe a video

Transcribe videos from 1800+ supported platforms using Gemini 2.5 Flash.

```bash
clipscribe transcribe [OPTIONS] URL
```

**Arguments:**
- `URL` (required) - Video URL to transcribe

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output-dir` | `-o` | `output` | Directory to save transcripts |
| `--format` | `-f` | `txt` | Output format: txt, json, md, all |
| `--language` | `-l` | `en` | Language code (e.g., en, es, fr) |
| `--include-timestamps` | | False | Include word-level timestamps |
| `--enhance` | | False | Enable AI enhancement for better formatting |
| `--mode` | `-m` | `auto` | Processing mode: auto, audio, video |
| `--skip-cleaning` | | False | Skip AI graph cleaning (v2.5+) |
| `--clean-graph` | | False | Force AI graph cleaning (v2.5+) |
| `--no-cache` | | False | Skip cache and force fresh processing |
| `--visualize` | | False | Auto-open knowledge graph visualization |

**Examples:**

```bash
# Basic transcription
clipscribe transcribe "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Save to specific directory with JSON format
clipscribe transcribe "https://vimeo.com/123456" -o my-project/ -f json

# Transcribe Spanish video with enhancement
clipscribe transcribe "https://youtube.com/watch?v=..." -l es --enhance

# Get all output formats with timestamps
clipscribe transcribe "https://twitter.com/i/status/..." -f all --include-timestamps

# Skip graph cleaning for raw extraction results (v2.5+)
clipscribe transcribe "https://youtube.com/watch?v=..." --skip-cleaning

# Force fresh processing without cache (v2.5+)
clipscribe transcribe "https://youtube.com/watch?v=..." --no-cache

# Audio-only mode for faster processing (v2.5+)
clipscribe transcribe "https://youtube.com/watch?v=..." --mode audio
```

**Output:**
- Creates comprehensive output directory with multiple formats
- Includes transcript, entities, relationships, knowledge graph
- CSV files for data analysis (v2.5.1+)
- Markdown report with statistics (v2.5.1+)
- Shows cost estimate and processing time

### `research` - Research a topic (Coming Soon)

Search and analyze multiple videos on a topic.

```bash
clipscribe research [OPTIONS] QUERY
```

**Arguments:**
- `QUERY` (required) - Search query for video research

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--max-results` | `-n` | `5` | Maximum videos to analyze |
| `--output-dir` | `-o` | `output/research` | Output directory |
| `--platforms` | `-p` | all | Specific platforms to search |

**Examples:**

```bash
# Research AI tutorials
clipscribe research "machine learning tutorials"

# Analyze 10 videos from specific platforms
clipscribe research "cooking recipes" -n 10 -p youtube -p vimeo

# Save research to custom directory
clipscribe research "climate change" -o research/climate/
```

### `config` - Show configuration

Display current ClipScribe configuration.

```bash
clipscribe config [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--full` | Show full configuration including API keys |

**Examples:**

```bash
# Show configuration (API keys masked)
clipscribe config

# Show full configuration
clipscribe config --full
```

**Output:**
- Output directory location
- Default language setting
- AI model being used
- API key status (masked unless --full)

### `platforms` - List supported platforms

Show all video platforms supported by ClipScribe.

```bash
clipscribe platforms
```

**Examples:**

```bash
clipscribe platforms
```

**Output:**
- Lists popular platforms
- Notes that 1800+ total platforms are supported
- Link to complete list

## Environment Variables

ClipScribe uses these environment variables:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GOOGLE_API_KEY` | Yes | Google API key for Gemini | None |
| `CLIPSCRIBE_OUTPUT_DIR` | No | Default output directory | `./output` |
| `CLIPSCRIBE_LANGUAGE` | No | Default language | `en` |
| `CLIPSCRIBE_MODEL` | No | Gemini model | `gemini-2.5-flash` |
| `MAX_VIDEO_DURATION` | No | Max video length (seconds) | `3600` |

## Output Formats

### Text Format (.txt)
Plain text transcript, optionally enhanced with AI formatting.

```
This is the transcript of the video.
It contains what was said in the video.
```

### JSON Format (.json)
Structured data with metadata, transcript, entities, and key points.

```json
{
  "metadata": {
    "title": "Video Title",
    "duration": 300,
    "url": "https://...",
    "channel": "Channel Name"
  },
  "transcript": {
    "text": "Full transcript...",
    "segments": [...]
  },
  "entities": [
    {"name": "John Doe", "type": "PERSON", "count": 3}
  ],
  "key_points": [
    {"text": "Important point", "timestamp": 45.2}
  ]
}
```

### CSV Format (.csv) - NEW in v2.5.1
Spreadsheet-compatible data files for analysis.

**entities.csv:**
```csv
name,type,confidence,source,timestamp
John Doe,PERSON,0.95,SpaCy,
Acme Corp,ORGANIZATION,0.92,GLiNER,
```

**relationships.csv:**
```csv
subject,predicate,object,confidence,context
John Doe,founded,Acme Corp,0.89,"In 2020, John Doe founded..."
```

### Markdown Report (.md) - NEW in v2.5.1
Professional intelligence report with statistics.

```markdown
# Video Intelligence Report: [Title]

**Processing Cost**: 🟢 $0.0842

## Executive Summary
[Summary of video content]

## Key Statistics
| Metric | Count |
|--------|-------|
| Entities | 125 |
| Relationships | 87 |
```

### GEXF Format (.gexf)
Gephi-compatible graph format for advanced visualization.

### Note on Subtitle Formats
As of v2.3, SRT and VTT subtitle formats have been removed to focus on intelligence extraction rather than captioning.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | API key not found |
| 4 | Network error |
| 5 | Unsupported video URL |

## Advanced Usage

### Batch Processing

Process multiple videos using shell scripting:

```bash
# From a file
while read url; do
  clipscribe transcribe "$url" -o batch/
done < urls.txt

# From search results
clipscribe research "topic" --json | \
  jq -r '.videos[].url' | \
  xargs -I {} clipscribe transcribe {} -o results/
```

### Integration with Other Tools

```bash
# Pipe to translation
clipscribe transcribe "$URL" -f txt | \
  translate-cli -t spanish > spanish.txt

# Extract just entities
clipscribe transcribe "$URL" -f json | \
  jq '.entities'

# Create word cloud
clipscribe transcribe "$URL" -f txt | \
  wordcloud_cli --imagefile wordcloud.png
```

### Monitoring Costs

```bash
# Track costs across multiple videos
for url in "${urls[@]}"; do
  clipscribe transcribe "$url" -f json | \
    jq -r '.cost' >> costs.log
done

# Sum total costs
awk '{sum += $1} END {print "Total: $" sum}' costs.log
```

## Performance Tips

1. **Faster Processing**
   - Videos under 10 minutes process quickest
   - Specify language if known: `-l en`
   - Use multiple terminal sessions for parallel processing

2. **Better Quality**
   - Use `--enhance` for cleaner transcripts
   - Original video quality affects accuracy
   - Avoid videos with heavy background music

3. **Storage Management**
   - JSON format includes all data but uses more space
   - Text format is most compact
   - Use `-o` to organize by project

## Troubleshooting

### Debug Mode

Enable debug logging to troubleshoot issues:

```bash
clipscribe --debug transcribe "URL"
```

### Common Issues

**"Command not found"**
```bash
# Ensure clipscribe is in PATH
which clipscribe

# Or use poetry
poetry run clipscribe
```

**"SSL Certificate Error"**
```bash
# Update certificates
pip install --upgrade certifi
```

**"Rate limit exceeded"**
- Wait a few minutes
- Check API quotas in Google Cloud Console
- Consider upgrading API limits

## Updates

Keep ClipScribe updated for new features and platform support:

```bash
# Update via pip
pip install -U clipscribe

# Update from source
cd clipscribe
git pull
pip install -e .

# Update just yt-dlp for new platforms
pip install -U yt-dlp
``` 