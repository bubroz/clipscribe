# Getting Started with ClipScribe

*Last Updated: 2025-08-26*
*Related: [CLI Reference](CLI_REFERENCE.md) | [Output Formats](OUTPUT_FORMATS.md)*

## What's New: v2.44.0 — Private Alpha Release

**ClipScribe v2.44.0** is deployed to Google Cloud Run in private alpha testing mode.

- **🔒 Private Alpha**: Services are deployed but access is restricted to alpha testers only
- **🔧 Infrastructure Ready**: API, web UI, and worker services configured for beta testing
- **📦 Optimized Architecture**: Hybrid Cloud Run + Compute Engine for cost-effective processing
- **⏳ Beta Timeline**: Public launch planned for Month 6+ after thorough testing

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


