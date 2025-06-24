# Getting Started with ClipScribe

ClipScribe is an AI-powered tool that transcribes videos from 1800+ platforms including YouTube, Twitter, TikTok, and more. This guide will get you up and running in 5 minutes.

## Prerequisites

You'll need:
- Python 3.11, 3.12, or 3.13 installed
- Poetry package manager ([Install instructions](https://python-poetry.org/docs/#installation))
- A Google API key for Gemini ([Get one free](https://makersuite.google.com/app/apikey))
- ffmpeg installed (`brew install ffmpeg` on macOS)

## Quick Installation

### 1. Install ClipScribe

```bash
# Clone the repository
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# Install with Poetry
poetry install
```

### 2. Set Your API Key

```bash
# Option 1: Export as environment variable
export GOOGLE_API_KEY="your-api-key-here"

# Option 2: Create a .env file
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```

### 3. Test Installation

```bash
poetry run clipscribe --version
poetry run clipscribe --help
```

## Basic Usage

### Transcribe a Video

```bash
# Transcribe any video URL
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Save to specific directory
poetry run clipscribe transcribe "https://vimeo.com/123456789" -o transcripts/

# Get subtitles in SRT format
poetry run clipscribe transcribe "https://twitter.com/user/status/123456" -f srt

# Enable AI enhancement for better formatting
poetry run clipscribe transcribe "https://tiktok.com/@user/video/123" --enhance
```

### Output Formats

ClipScribe supports multiple output formats:

- **txt** - Plain text transcript (default)
- **json** - Structured data with metadata
- **srt** - Subtitle format with timestamps
- **vtt** - WebVTT subtitle format
- **all** - Generate all formats

```bash
# Get all formats
poetry run clipscribe transcribe "https://youtube.com/watch?v=..." -f all
```

### Check Platform Support

```bash
# List all supported platforms
poetry run clipscribe platforms

# This shows popular platforms, but ClipScribe actually supports 1800+ sites!
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
  -f srt \
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

## What's Next?

- Read the [CLI Reference](CLI_REFERENCE.md) for all commands
- Check [Supported Platforms](PLATFORMS.md) for a full list
- See [Development Guide](DEVELOPMENT.md) to contribute

## Getting Help

- **Documentation**: https://github.com/bubroz/clipscribe
- **Issues**: https://github.com/bubroz/clipscribe/issues
- **Discussions**: https://github.com/bubroz/clipscribe/discussions

Happy transcribing! 🎥✨ 