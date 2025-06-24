# ClipScribe 2.2

<p align="center">
  <strong>AI-powered video transcription and analysis for 1800+ platforms</strong>
</p>

<p align="center">
  <em>v2.2 with Advanced Intelligence Extraction - Now Fully Functional! 🎉</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#api">API</a> •
  <a href="#contributing">Contributing</a>
</p>

---

ClipScribe is a modern video transcription tool that leverages Google's Gemini 2.5 Flash to provide fast, accurate, and cost-effective video intelligence. It supports **1800+ video platforms** through yt-dlp integration.

## ✨ Features

- 🌍 **Universal Platform Support** - YouTube, TikTok, Twitter/X, Vimeo, and 1800+ more sites
- 🚀 **Gemini 2.5 Flash** - Native audio transcription with 92% cost reduction
- ⚡ **10x Faster** - Process 1 hour of video in 2-5 minutes
- 🎯 **High Accuracy** - Native audio understanding outperforms traditional ASR
- 📊 **Multiple Formats** - Export as TXT or JSON, plus GEXF for knowledge graphs
- 💰 **Cost Tracking** - Real-time cost calculation per video
- 🔄 **Async Processing** - Handle multiple videos concurrently
- 🎨 **Beautiful CLI** - Modern terminal interface with Rich

## 📋 Requirements

- Python 3.11 or higher
- Google Cloud API key with Gemini access
- FFmpeg (for audio extraction)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bubroz/clipscribe.git
   cd clipscribe
   ```

2. **Install with Poetry**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

4. **Verify installation**
   ```bash
   poetry run clipscribe --version
   ```

## 💻 Usage

### Basic Transcription

```bash
# Transcribe a YouTube video
poetry run clipscribe transcribe "https://youtube.com/watch?v=..."

# Transcribe from any supported platform
poetry run clipscribe transcribe "https://vimeo.com/123456789"

# With options
poetry run clipscribe transcribe "https://tiktok.com/@user/video/..." \
  --output-dir transcripts \
  --format json \
  --enhance
```

### Research Mode (Coming Soon)

```bash
# Analyze multiple videos on a topic
poetry run clipscribe research "machine learning tutorials" --max-results 10
```

### Configuration

```bash
# View current configuration
poetry run clipscribe config

# List supported platforms
poetry run clipscribe platforms
```

## 📚 Examples

We provide comprehensive examples to help you get started:

- **[Quick Start](examples/quick_start.py)** - Simplest way to transcribe a video
- **[Batch Processing](examples/batch_processing.py)** - Process multiple videos efficiently
- **[Cost Optimization](examples/cost_optimization.py)** - Strategies to minimize costs
- **[Output Formats](examples/output_formats.py)** - Export in various formats (TXT, SRT, JSON, etc.)
- **[CLI Usage](examples/cli_usage.py)** - Complete command-line reference
- **[Multi-Platform Demo](examples/multi_platform_demo.py)** - Working with 1800+ platforms
- **[Video Intelligence Demo](examples/video_intelligence_demo.py)** - Advanced analysis features

Run any example:
```bash
poetry run python examples/quick_start.py
```

## 🐍 Python API

```python
from clipscribe.chimera_video.retrievers.video import VideoIntelligenceRetriever

# Initialize retriever
retriever = VideoIntelligenceRetriever(
    query="Transcribe this video",
    output_dir="output"
)

# Process any video URL
result = await retriever.process_url("https://youtube.com/watch?v=...")

# Access results
print(f"Title: {result['title']}")
print(f"Transcript: {result['transcript']}")
print(f"Cost: ${result['cost']:.4f}")
```

## 📁 Project Structure

```
clipscribe/
├── src/
│   └── clipscribe/           # Main package
│       ├── commands/         # CLI implementation
│       ├── config/           # Configuration management
│       ├── extractors/       # Entity & relationship extraction
│       ├── retrievers/       # Video processing core
│       └── utils/            # Utilities and helpers
├── tests/                    # Test suite
├── docs/                     # Documentation
├── examples/                 # Usage examples
├── .cursor/rules/            # AI assistant rules & patterns
└── output/                   # Generated transcripts & graphs
```

## 🔧 Configuration

Create a `.env` file with:

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional
OUTPUT_DIR=output
LOG_LEVEL=INFO
DEFAULT_LANGUAGE=en
```

See [docs/guides/configuration.md](docs/guides/configuration.md) for all options.

## 🔥 NEW in v2.2: Advanced Intelligence Extraction

ClipScribe now includes complete video intelligence extraction:

### Relationship Extraction (REBEL)
- Extract facts and relationships from videos automatically
- Build knowledge graphs from video content
- Example: "Elon Musk → founded → SpaceX"

### Custom Entity Detection (GLiNER) 
- Detect domain-specific entities beyond standard NER
- Specialized domains: Military, Technology, Finance, Medical
- Custom entity types: weapons, operations, technologies, diseases

### Complete Intelligence Stack
```
Video → Transcription → Entities → Relationships → Knowledge Graph → Facts
```

### New Features in v2.2:
- **98% Cost Reduction** - Hybrid approach using SpaCy + selective LLM validation
- **3 Extraction Levels** - Basic (SpaCy), Enhanced (SpaCy+LLM), Advanced (SpaCy+GLiNER+REBEL+LLM)
- **Knowledge Graphs** - NetworkX-compatible graph format
- **Fact Extraction** - Top facts from relationships
- **Domain Optimization** - Specialized extraction for specific domains

### Usage Example:
```python
# Advanced extraction with domain specialization
retriever = VideoIntelligenceRetriever(
    use_advanced_extraction=True,
    domain="military"  # or: tech, finance, medical
)

result = await retriever.process_url("https://youtube.com/watch?v=...")

# Access advanced features
print(f"Entities: {len(result.entities)}")
print(f"Relationships: {len(result.relationships)}")
print(f"Knowledge Graph Nodes: {result.knowledge_graph['node_count']}")
```

**Try it now:**
```bash
poetry run python examples/advanced_extraction_demo.py "VIDEO_URL" military
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Run tests
poetry run pytest

# Format code
poetry run black src tests
poetry run isort src tests

# Type check
poetry run mypy src
```

## 🛠️ Development

**ClipScribe was developed 100% in [Cursor](https://cursor.sh/)** - an AI-powered code editor. Every line of code, documentation, and example was written with AI assistance, demonstrating the power of AI-augmented development.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for universal video platform support
- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI transcription
- [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/) for the CLI

---

<p align="center">
  Made with ❤️ for the Chimera Researcher project
</p>
