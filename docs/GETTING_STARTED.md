# Getting Started with ClipScribe

*Last Updated: 2025-08-26*
*Related: [CLI Reference](CLI_REFERENCE.md) | [Output Formats](OUTPUT_FORMATS.md)*

## What's New: v2.44.0 — Production Deployment Live!

**ClipScribe v2.44.0** is now live on Google Cloud Run with a stable, automated deployment pipeline.

- **🚀 Live Services**: API and web front end are now live and serving traffic.
- **🔧 Stable Build Pipeline**: A robust multi-stage `Dockerfile` provides reliable and efficient builds.
- **🐛 Core Functionality is Solid**: All critical bugs that were blocking deployment have been resolved.
- **✅ Enterprise-Ready**: Comprehensive test coverage and a stable production environment.

## Prerequisites

- Python 3.12+
- Poetry for dependency management
- A Google API key or configured Vertex AI environment
- FFmpeg for video/audio processing

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
# Create a .env file (recommended)
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```

### 3. Test Installation

```bash
poetry run clipscribe --version
# Should output: ClipScribe, version 2.44.0

poetry run clipscribe --help
```

## Basic Usage

### Process a Single Video

```bash
# High-quality analysis with Gemini 2.5 Pro (default)
poetry run clipscribe process video "https://www.youtube.com/watch?v=VIDEO_ID"

# Faster analysis with Gemini 2.5 Flash
poetry run clipscribe process video "https://www.youtube.com/watch?v=VIDEO_ID" --use-flash
```

### Process Multiple Videos

```bash
# Process a collection of videos as a series
poetry run clipscribe collection series "URL1" "URL2" "URL3"
```

## What's Next?

- Learn about all output formats in the [Output Formats Guide](OUTPUT_FORMATS.md)
- Explore advanced CLI options in the [CLI Reference](CLI_REFERENCE.md)
- Check the [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues
- See the [Deployment Guide](advanced/deployment/DEPLOYMENT_GUIDE.md) for production setup.


