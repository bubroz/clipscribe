# ClipScribe v2.10.1

<p align="center">
  <strong>AI-powered video intelligence for 1800+ platforms</strong>
</p>

<p align="center">
  <em>Now with Entity Source Tracking, Model Caching & Enhanced Performance 🚀</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#api">API</a> •
  <a href="#contributing">Contributing</a>
</p>

---

ClipScribe is a modern video intelligence tool that leverages Google's Gemini to provide fast, accurate, and cost-effective analysis. It supports **1800+ video platforms** through yt-dlp integration.

## ✨ Features

- 🖥️ **Interactive Web UI** - An easy-to-use Streamlit app for running analysis in your browser.
- 🌍 **Universal Platform Support** - YouTube, TikTok, Twitter/X, Vimeo, and 1800+ more.
- 🚀 **Gemini Powered** - Native audio/video understanding for high accuracy.
- 🔬 **Research Command** - Analyze multiple videos on a single topic to gather broad insights.
- 📊 **Rich Interactive Reports** - Auto-generated markdown reports with:
  - 📈 **Mermaid.js Diagrams** for knowledge graphs and entity distributions.
  - 🗂️ **Collapsible Sections** for easy navigation.
  -  dashboards with visual statistics.
- 🎨 **Beautiful CLI** - Modern terminal interface with Rich progress indicators, live cost tracking, and phase timing.
- 💰 **Cost Optimized** - Intelligent API batching reduces costs by 50-60%.
- 📈 **Multiple Data Formats** - Export to TXT, JSON, CSV, GEXF, and interactive Markdown.
- 🔗 **Full Knowledge Extraction** - Extracts entities, relationships, topics, and key points to build a complete knowledge graph.
- 🔒 **Data Integrity** - Manifest files include SHA256 checksums for all outputs.
- 🎯 **Entity Source Tracking** - Track which extraction method (SpaCy, GLiNER, REBEL) found each entity.
- ⚡ **Performance Optimized** - Model caching provides 3-5x faster batch processing.

## 🎉 What's New in v2.10.1

The latest version introduces major performance improvements and transparency features:

### 🎯 Entity Source Tracking (v2.10.1)
- **Pipeline Transparency**: New `entity_sources.json` and `entity_sources.csv` files show which extraction method found each entity.
- **Quality Analysis**: Understand the contribution of SpaCy (basic NER), GLiNER (custom entities), and REBEL (relationships).
- **Performance Insights**: Identify which extractors work best for different content types.

### ⚡ Performance Optimizations (v2.10.1)
- **Model Caching**: Singleton pattern prevents repeated model loading in batch processing (3-5x performance improvement).
- **Retry Logic**: Automatic retry for ffmpeg errors with exponential backoff.
- **Warning Suppression**: Cleaned up console output by suppressing harmless tokenizer warnings.

The latest versions of ClipScribe also include these major enhancements:

### 🖥️ Interactive Web UI (v2.8.0)
- **Run in Browser**: A new Streamlit-based web app (`app.py`) provides a graphical interface for ClipScribe.
- **Live Progress**: See real-time updates as your video is processed.
- **Download Results**: Get all output files directly from the UI.
- **Full Configuration**: Control processing mode, caching, and graph cleaning directly from the sidebar.

### 🔬 Research Command (v2.7.0)
- **Topic-Based Analysis**: Use the new `research` command to analyze multiple videos on a single topic.
- **Batch Processing**: Automatically finds and processes a list of relevant videos.

### 📊 Performance Dashboards & Rich CLI (v2.6.0)
- **Rich Progress Indicators**: Get real-time feedback in your terminal with beautiful progress bars.
- **Cost & Time Tracking**: Live monitoring of API costs and processing time for each stage.
- **Enhanced Markdown Reports**: Interactive reports with Mermaid diagrams, collapsible sections, and visual dashboards.

## 📋 Requirements

- Python 3.12+ (3.13 supported)
- A Google API key with Gemini access enabled.
- [FFmpeg](https://ffmpeg.org/download.html) installed on your system.

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

### Command-Line Interface (CLI)

```bash
# Transcribe a single video
poetry run clipscribe transcribe "https://youtube.com/watch?v=..."

# Research a topic across multiple videos
poetry run clipscribe research "James Webb Telescope" --max-results 3
```

### Web UI

To launch the interactive web interface, run:

```bash
poetry run streamlit run app.py
```

This will open the application in your web browser.

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
- **[Advanced Features Demo](examples/advanced_features_demo.py)** - A menu-driven demo of all advanced features.
- **[Batch Processing](examples/batch_processing.py)** - Process multiple videos efficiently
- **[Cost Optimization](examples/cost_optimization.py)** - Strategies to minimize costs
- **[Output Formats](examples/output_formats.py)** - Export in various formats (TXT, JSON, CSV, GEXF, etc.)
- **[CLI Usage](examples/cli_usage.py)** - Complete command-line reference
- **[Multi-Platform Demo](examples/multi_platform_demo.py)** - Working with 1800+ platforms
- **[Video Intelligence Demo](examples/video_intelligence_demo.py)** - Advanced analysis features
- **[Video Mode Demo](examples/video_mode_demo.py)** - Demonstrates audio vs. video processing modes.

Run any example:
```bash
poetry run python examples/quick_start.py
```

## 🐍 Python API

```python
import asyncio
from clipscribe.retrievers import VideoIntelligenceRetriever

async def main():
    # Initialize retriever
    retriever = VideoIntelligenceRetriever()

    # Process any video URL
    result = await retriever.process_url("https://youtube.com/watch?v=...")

    if result:
        # Access results
        print(f"Title: {result.metadata.title}")
        print(f"Summary: {result.summary}")
        print(f"Cost: ${result.processing_cost:.4f}")
        print(f"Entities found: {len(result.entities)}")

if __name__ == "__main__":
    asyncio.run(main())
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

Create a `.env` file in the project root:

```env
# Required
GOOGLE_API_KEY="your_gemini_api_key_here"

# Optional (defaults shown)
# OUTPUT_DIR=output
# LOG_LEVEL=INFO
# DEFAULT_LANGUAGE=en
```

## 🔥 Advanced Intelligence Extraction

ClipScribe includes a complete video intelligence extraction pipeline:

### Relationship Extraction (REBEL)
- Extract facts and relationships (`Subject -> Predicate -> Object`) from videos automatically.
- Build knowledge graphs from video content.

### Custom Entity Detection (GLiNER) 
- Detect domain-specific entities beyond standard NER (e.g., weapons, technologies, financial metrics).

### Complete Intelligence Stack
```
Video → Transcription → Entities → Relationships → Knowledge Graph → Facts
```

### Usage Example:
```python
# See examples/advanced_features_demo.py for a full example
retriever = VideoIntelligenceRetriever(
    use_advanced_extraction=True,
    domain="technology"
)
```

**Try the demo:**
```bash
# Run the advanced features demo
poetry run python examples/advanced_features_demo.py
```

## 🛠️ Development

**ClipScribe was developed 100% in [Cursor](https://cursor.sh/)** - an AI-powered code editor. Every line of code, documentation, and example was written with AI assistance, demonstrating the power of AI-augmented development.

## Versioning

This project follows [Semantic Versioning](https://semver.org). The current version is maintained in `pyproject.toml` and `src/clipscribe/version.py`. All changes are documented in `CHANGELOG.md`.

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
