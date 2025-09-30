# Getting Started with ClipScribe

*Last Updated: 2025-09-30*
*Related: [CLI Reference](CLI_REFERENCE.md) | [Output Formats](OUTPUT_FORMATS.md)*

## What's New: v2.51.1 — Bot Detection Fixed!

**ClipScribe v2.51.1** solves video download failures with automatic curl-cffi browser impersonation.

- **🛡️ Bot Detection Bypass**: 100% download success rate with automatic TLS/JA3/HTTP2 fingerprinting
- **🔒 Private Alpha**: Services are deployed but access is restricted to alpha testers only
- **🎯 Zero Configuration**: curl-cffi impersonation works automatically for all platforms
- **📦 Clean Codebase**: Repository cleaned from 4.9GB to 3.4GB (-31%)
- **⏳ Beta Timeline**: Public launch planned for Month 6+ after thorough testing

**Key Fix**: No more "Requested format is not available" or "Sign in to confirm you're not a bot" errors!

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
# Should output: ClipScribe, version 2.51.1

poetry run clipscribe --help
```

## Basic Usage

### Process a Single Video

```bash
# Process any video URL (YouTube, Vimeo, TikTok, etc.)
poetry run clipscribe process video "https://www.youtube.com/watch?v=VIDEO_ID"

# Bot detection bypass works automatically - no configuration needed!
# Supports 1800+ platforms via yt-dlp with curl-cffi impersonation
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


