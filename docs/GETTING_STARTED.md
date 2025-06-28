# Getting Started with ARGOS

ARGOS (formerly ClipScribe) is an AI-powered video intelligence tool that analyzes videos from 1800+ platforms including YouTube, Twitter, TikTok, and more. This guide will get you up and running in 5 minutes.

## Prerequisites

You'll need:
- Python 3.12+ installed (3.13 supported)
- Poetry package manager ([Install instructions](https://python-poetry.org/docs/#installation))
- A Google API key for Gemini ([Get one free](https://makersuite.google.com/app/apikey))
- ffmpeg installed (`brew install ffmpeg` on macOS)

## Quick Installation

### 1. Install ARGOS

```bash
# Clone the repository
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# Install with Poetry
poetry install
```

### 2. Set Your API Key Securely

```bash
# RECOMMENDED: Create a .env file (secure)
echo "GOOGLE_API_KEY=your-api-key-here" > .env

# Alternative: Export as environment variable
export GOOGLE_API_KEY="your-api-key-here"
```

### 3. Test Installation

```bash
poetry run clipscribe --version
poetry run clipscribe --help
```

## Basic Usage

### Process a Single Video

```bash
# Basic video intelligence extraction
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Save to specific directory
poetry run clipscribe transcribe "https://vimeo.com/123456789" -o analysis/

# Enhanced temporal intelligence (v2.17.0)
poetry run clipscribe transcribe "https://twitter.com/user/status/123456" --enhanced-temporal

# Full intelligence extraction with relationship analysis
poetry run clipscribe transcribe "https://tiktok.com/@user/video/123" --use-advanced-extraction
```

### Process Multiple Videos (Collection Analysis)

```bash
# NEW in v2.17.0: Process multiple videos with Timeline Building Pipeline
poetry run clipscribe process-collection "my-collection" \
  "https://youtube.com/watch?v=video1" \
  "https://youtube.com/watch?v=video2" \
  --enhanced-temporal
```

### Research Command

```bash
# Research a topic across multiple videos
poetry run clipscribe research "machine learning tutorials" --max-results 5
```

### Output Formats

ARGOS supports comprehensive intelligence extraction with multiple formats:

- **txt** - Plain text transcript
- **json** - Structured intelligence data with entities, relationships, and timelines
- **csv** - Entity and relationship data for analysis
- **gexf** - Knowledge graph for Gephi visualization
- **markdown** - Professional reports with visualizations

```bash
# Get all formats with full intelligence extraction
poetry run clipscribe transcribe "https://youtube.com/watch?v=..." -f all --use-advanced-extraction
```

### Launch Mission Control Web Interface

```bash
# Launch the comprehensive web interface
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

### Check Platform Support

```bash
# List all supported platforms (1800+)
poetry run clipscribe platforms
```

## Common Use Cases

### 1. Transcribe a YouTube Tutorial

```bash
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --enhance \
  --include-timestamps \
  -o youtube-tutorials/
```

### 2. Extract Subtitles from a Movie Clip

```bash
poetry run clipscribe transcribe "https://vimeo.com/12345" \
  -f json \
  -o subtitles/
```

### 3. Analyze Multiple Videos

```bash
# Create a list of URLs
cat > videos.txt << EOF
https://youtube.com/watch?v=video1
https://twitter.com/user/status/video2
https://tiktok.com/@user/video/video3
EOF

# Process them all
while read url; do
  poetry run clipscribe transcribe "$url" -o batch-output/
done < videos.txt
```

### 4. Research a Topic (Coming Soon)

```bash
# Search and analyze multiple videos on a topic
poetry run clipscribe research "machine learning tutorials" -n 10
```

## Understanding Costs

ClipScribe uses Google's Gemini API which is extremely cost-effective:

- **5-minute video**: ~$0.01
- **30-minute video**: ~$0.06  
- **1-hour video**: ~$0.12

This is 92% cheaper than traditional transcription services!

## Tips and Tricks

### Speed Up Processing
- Shorter videos process faster
- Use `--language en` if you know the video is in English
- Videos under 10 minutes typically process in under 1 minute

### Better Accuracy
- Use `--enhance` for AI-improved formatting
- Specify the language with `--language` if known
- Clear audio quality gives better results

### Manage Output
- Use `-o` to organize transcripts by project
- Use `-f json` to get structured data for programming
- JSON format includes metadata, entities, and key points

## Troubleshooting

### "API key not found"
Make sure your GOOGLE_API_KEY is set:
```bash
echo $GOOGLE_API_KEY  # Should show your key
```

### "Video not supported"
While rare, some videos might not work. Try:
- Checking if the video is public
- Using a different video from the same platform
- Updating ClipScribe: `poetry update`

### "ffmpeg not found"
Install ffmpeg for your system:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Configuration

ClipScribe uses environment variables for configuration. Create a `.env` file in the project root:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional - Timeout for long videos (default: 14400 seconds / 4 hours)
GEMINI_REQUEST_TIMEOUT=14400

# Optional - Cost warning threshold (default: $1.00)
COST_WARNING_THRESHOLD=1.0

# Optional - Default output directory (default: output)
OUTPUT_DIR=output
```

### Long Video Support

ClipScribe can process videos up to 4 hours long. If you're getting timeout errors with long videos:

1. Ensure `GEMINI_REQUEST_TIMEOUT` is set in your `.env` file
2. The default timeout is 14400 seconds (4 hours)
3. For shorter videos, you can reduce this value to fail faster if needed

Example for 1-hour timeout:
```bash
GEMINI_REQUEST_TIMEOUT=3600
```

## 5. Running ClipScribe

You can now run ClipScribe using two methods:

### Via Command-Line

To transcribe a single video, use the `transcribe` command:

```bash
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=your_video_id"
```

To research a topic across multiple videos, use the `research` command:

```bash
poetry run clipscribe research "your search query"
```

### Via Web UI (New in v2.8.0)

To launch the interactive web application, run the following command from the project root:

```bash
poetry run streamlit run app.py
```

This will open a new tab in your web browser where you can paste a video URL and see the results interactively.

## What's Next?

- Explore the different output formats in the [Output Formats Guide](OUTPUT_FORMATS.md).
- See all available commands in the [CLI Reference](CLI_REFERENCE.md).
- Check out the `examples/` directory for more advanced use cases.

## Getting Help

- **Documentation**: https://github.com/bubroz/clipscribe
- **Issues**: https://github.com/bubroz/clipscribe/issues
- **Discussions**: https://github.com/bubroz/clipscribe/discussions

Happy transcribing! 🎥✨ 