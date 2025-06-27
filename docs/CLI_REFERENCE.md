# ClipScribe CLI Reference (v2.15.0 - The Synthesis Complete Update)

Complete reference for all ClipScribe commands and options, featuring **working relationship extraction** and knowledge synthesis capabilities.

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

### `transcribe` - Transcribe a video with relationship extraction

Transcribe videos from 1800+ supported platforms using Gemini 2.5 Flash/Pro with **working REBEL relationship extraction** (10-19 relationships per video).

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

# Test relationship extraction with PBS NewsHour content
clipscribe transcribe "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" --no-cache
# Extracts relationships like: "NSO | inception | 2010", "UAE | diplomatic relation | Saudi Arabia"
```

**Output:**
- Creates comprehensive output directory with multiple formats
- **Working relationship extraction**: 10-19 relationships per video with REBEL
- **Knowledge graphs**: Connected graphs with real relationship data
- **GEXF 1.3 export**: Modern format for Gephi visualization
- CSV files for data analysis with relationship data
- Markdown report with statistics and relationship metrics
- Shows cost estimate and processing time (~$0.41 per video)

### `research` - Research a Topic or Channel

Search and analyze multiple videos to gather broad insights on a topic or from a specific YouTube channel. This command processes videos concurrently and provides a clean, dashboard-like progress view in your terminal.

```bash
clipscribe research [OPTIONS] QUERY
```

**Arguments:**
- `QUERY` (required) - A search term (e.g., "James Webb Telescope") or a full YouTube channel URL (e.g., "https://www.youtube.com/@pbsnewshour").

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--max-results` | `-n` | `2` | Maximum videos to analyze. **Use with caution**, high numbers can be resource-intensive. |
| `--period` | | None | Filter topic search by time. Options: `hour`, `day`, `week`, `month`, `year`. |
| `--sort-by` | | `relevance` | Sort order for channel search. Options: `relevance`, `newest`, `oldest`, `popular`. |
| `--output-dir` | `-o` | `output/research` | Base directory for research results. Each video gets its own subdirectory. |
| `--mode` | `-m` | `audio` | Processing mode for each video: `audio`, `video`, `auto`. |
| `--no-cache` | | False | Disable caching and force fresh processing for all videos. |

**Examples:**

```bash
# Research the 3 most recent videos about AI from the last week
clipscribe research "latest on AI" -n 3 --period week

# Get the 5 most popular videos from the PBS NewsHour channel
clipscribe research "https://www.youtube.com/@pbsnewshour" -n 5 --sort-by popular

# Get the 2 newest videos from a channel and process them in video mode
clipscribe research "https://www.youtube.com/@mkbhd" -n 2 --sort-by newest --mode video
```

### `process-collection` - Process Multiple Videos as Collection (ENHANCED in v2.15.0)

Process multiple videos as a unified collection with **working relationship extraction**, knowledge synthesis, timeline generation, and unified knowledge graph creation.

```bash
clipscribe process-collection [OPTIONS] URL1 URL2 [URL3...]
```

**Arguments:**
- `URL1 URL2 [URL3...]` (required) - Multiple video URLs to process as a collection

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--collection-title` | `-t` | Auto-generated | Title for the video collection |
| `--collection-type` | | `custom_collection` | Collection type: `series`, `topic_research`, `channel_analysis`, `cross_source_topic`, `custom_collection` |
| `--auto-detect-series` | | False | Automatically detect if videos form a series |
| `--user-confirmed-series` | | False | User confirms this is a series (skips detection) |
| `--output-dir` | `-o` | `output/collections` | Output directory for collection analysis |
| `--mode` | `-m` | `audio` | Processing mode: `audio`, `video`, `auto` |
| `--use-cache/--no-cache` | | True | Use cached results if available |
| `--enhance-transcript` | | False | Add speaker diarization and timestamps |
| `--clean-graph` | | False | Clean knowledge graph with AI |
| `--performance-report` | | False | Generate detailed performance report |

**Examples:**

```bash
# Process a video series with automatic detection
clipscribe process-collection \
  "https://youtube.com/watch?v=part1" \
  "https://youtube.com/watch?v=part2" \
  "https://youtube.com/watch?v=part3" \
  --collection-type series \
  --auto-detect-series

# Process cross-source topic research
clipscribe process-collection \
  "https://youtube.com/watch?v=cnn_climate" \
  "https://youtube.com/watch?v=bbc_climate" \
  "https://youtube.com/watch?v=pbs_climate" \
  --collection-type cross_source_topic \
  --collection-title "Climate Change Coverage"

# Process channel analysis with custom settings
clipscribe process-collection \
  "https://youtube.com/watch?v=video1" \
  "https://youtube.com/watch?v=video2" \
  --collection-type channel_analysis \
  --mode video \
  --enhance-transcript \
  --clean-graph
```

**Output (v2.15.0):**
- Individual video outputs with **working relationship extraction** (10-19 per video)
- **Knowledge synthesis**: Complete with Knowledge Panels and Information Flow Maps
- **Knowledge Panels**: Entity-centric profiles in `knowledge_panels.json` and `entity_panels/`
- **Information Flow Maps**: Concept evolution in `information_flow_map.json` and `concept_flows/`
- **Human-Readable Summaries**: `knowledge_panels_summary.md` and `information_flow_summary.md`
- **GEXF 1.3 export**: Unified knowledge graph for Gephi visualization
- **Enhanced Timeline**: LLM-based temporal intelligence with date extraction
- Collection intelligence in `collection_intelligence.json` with all synthesis features
- Performance metrics and cost tracking (~$0.41 per video)

### `process-series` - Process Video Series (NEW in v2.13.0)

Specialized command for processing videos as a series with automatic detection, narrative flow analysis, and story progression tracking.

```bash
clipscribe process-series [OPTIONS] URL1 URL2 [URL3...]
```

**Arguments:**
- `URL1 URL2 [URL3...]` (required) - Video URLs to process as a series

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output-dir` | `-o` | `output/series` | Output directory for series analysis |
| `--series-title` | `-t` | Auto-detected | Title for the video series |
| `--mode` | `-m` | `audio` | Processing mode: `audio`, `video`, `auto` |
| `--use-cache/--no-cache` | | True | Use cached results if available |
| `--enhance-transcript` | | False | Add speaker diarization and timestamps |
| `--clean-graph` | | False | Clean knowledge graph with AI |
| `--performance-report` | | False | Generate detailed performance report |

**Examples:**

```bash
# Process a documentary series
clipscribe process-series \
  "https://youtube.com/watch?v=documentary_pt1" \
  "https://youtube.com/watch?v=documentary_pt2" \
  "https://youtube.com/watch?v=documentary_pt3" \
  --series-title "Climate Change Documentary Series"

# Process educational series with enhanced transcripts
clipscribe process-series \
  "https://youtube.com/watch?v=lesson1" \
  "https://youtube.com/watch?v=lesson2" \
  --enhance-transcript \
  --clean-graph \
  --performance-report
```

**Output:**
- All features of `process-collection` with series-specific enhancements
- Automatic series detection and validation
- Narrative flow analysis with story progression tracking
- Topic evolution tracking across episodes
- Thematic arc identification and coherence scoring

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

## Entity Source Analysis Tools (NEW in v2.12.0)

### `analyze_entity_sources.py` - Analyze extraction method effectiveness

Comprehensive analysis tool for understanding which extraction methods (SpaCy, GLiNER, REBEL) are most effective for your content.

```bash
python scripts/analyze_entity_sources.py [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--output-dir OUTPUT_DIR` | Directory containing ClipScribe outputs |
| `--single-video SINGLE_VIDEO` | Analyze a single video directory |
| `--compare-methods` | Compare extraction method effectiveness |
| `--save-csv` | Save results as CSV file |
| `--save-excel` | Save results as Excel file (NEW in v2.12.0) |
| `--save-markdown` | Save results as Markdown report |
| `--create-visualizations` | Create interactive Plotly visualizations (default: True) |

**Examples:**

```bash
# Analyze all videos in research output with Excel export and visualizations
python scripts/analyze_entity_sources.py \
  --output-dir output/research \
  --create-visualizations \
  --save-excel \
  --save-csv \
  --save-markdown

# Analyze a single video with method comparison
python scripts/analyze_entity_sources.py \
  --single-video output/20250126_youtube_UjDpW_SOrlw \
  --compare-methods \
  --save-excel

# Batch analysis with comprehensive reporting
python scripts/analyze_entity_sources.py \
  --output-dir output/research \
  --compare-methods \
  --save-excel \
  --create-visualizations
```

**Output:**
- **Interactive Visualizations**: Pie charts, bar charts, and gauge visualizations (when Plotly available)
- **Excel Reports**: Multi-sheet analysis with Summary, Source Distribution, Entity Types, and Per-Video Analysis
- **CSV Reports**: Spreadsheet-friendly data for further analysis
- **Markdown Reports**: Human-readable analysis with insights and recommendations
- **Quality Insights**: Automated recommendations based on extraction performance

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
   - **NEW in v2.10.1**: Model caching provides 3-5x faster batch processing

2. **Better Quality**
   - Use `--enhance` for cleaner transcripts
   - Original video quality affects accuracy
   - Avoid videos with heavy background music

3. **Storage Management**
   - JSON format includes all data but uses more space
   - Text format is most compact
   - Use `-o` to organize by project
   - **NEW in v2.10.1**: Entity source tracking files (`entity_sources.json/csv`) help analyze extraction quality

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