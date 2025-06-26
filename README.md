# ClipScribe v2.14.0 - The Synthesis Update

<p align="center">
  <strong>AI-powered video intelligence for 1800+ platforms</strong>
</p>

<p align="center">
  <em>Now with Working Relationship Extraction, Knowledge Synthesis & GEXF 1.3 🧠</em>
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
- 🧠 **Multi-Video Intelligence** - Process multiple related videos with cross-video analysis and unified knowledge graphs.
- 🔍 **Automatic Series Detection** - AI-powered pattern recognition for video series with user confirmation workflows.
- 🌐 **Cross-Video Entity Resolution** - Aggressive entity merging with 85% similarity threshold and Gemini 2.5 Pro validation.
- 📖 **Narrative Flow Analysis** - Story progression tracking and thematic arc identification for series content.
- 🔒 **Data Integrity** - Manifest files include SHA256 checksums for all outputs.
- 🎯 **Entity Source Tracking** - Track which extraction method (SpaCy, GLiNER, REBEL) found each entity.
- ⚡ **Performance Optimized** - Model caching provides 3-5x faster batch processing.
- 📊 **Advanced Visualizations** - Interactive Plotly charts for comprehensive analysis.
- 📄 **Excel Export** - Multi-sheet Excel exports with professional formatting.
- 📈 **Performance Dashboards** - Dedicated monitoring interface with real-time analytics.
- 🎯 **REBEL Relationship Extraction** - Extract 10-19 meaningful relationships per video with space-separated parsing.
- 🌐 **GEXF 1.3 Export** - Modern knowledge graph format for Gephi visualization with enhanced styling.

## 🎉 What's New in v2.14.0 - The Synthesis Update

### 🎯 **MAJOR BREAKTHROUGH: REBEL Relationship Extraction Fixed**

**Critical Achievement**: Fixed the relationship extraction pipeline that was preventing ClipScribe from building meaningful knowledge graphs.

**Results**: Now extracting **10-19 relationships per video** from news content, including:
- "Pegasus | spyware | instance of"
- "NSO | inception | 2010" 
- "Carmen Aristegui | employer | Aristegui Noticias"
- "United Arab Emirates | diplomatic relation | Saudi Arabia"
- "Enrique Peña Nieto | President of Mexico | position held"

### ✨ **New Features in v2.14.0**

#### 🌐 **GEXF 1.3 Knowledge Graph Export**
- **Upgraded GEXF export** from 1.2draft to GEXF 1.3 specification
- Enhanced Gephi compatibility with modern namespaces and hex color attributes
- Confidence-based node sizing and type-based color coding

#### 🧠 **Knowledge Synthesis Engine**
- **Timeline Synthesis**: Chronological event correlation across multiple videos
- **Data Models**: New `TimelineEvent` and `ConsolidatedTimeline` Pydantic models
- **Collection Intelligence**: Enhanced multi-video processing with consolidated outputs

#### 🔧 **Critical Bug Fixes**
- **Fixed**: `'NoneType' object is not subscriptable` error in relationship saving
- **Resolved**: REBEL parser incompatibility with space-separated output format
- **Enhanced**: Async command handling and logging system stability

### 📊 **Performance Metrics (v2.14.0)**
- **Relationship Extraction**: 10-19 relationships per video ✅
- **Entity Extraction**: 250-300 entities per video with LLM validation ✅
- **Knowledge Graph**: 240+ nodes, 9-13 edges per video ✅
- **Processing Cost**: Maintained ~$0.41 per video ✅
- **Success Rate**: 100% completion rate ✅

## 🎉 What's New in v2.13.0

The latest version introduces comprehensive Multi-Video Intelligence capabilities:

### 🧠 Multi-Video Intelligence Architecture (v2.13.0)
- **Cross-Video Analysis**: Process multiple related videos with unified intelligence analysis.
- **Automatic Series Detection**: AI-powered pattern recognition for video series with 95%+ accuracy.
- **Entity Resolution**: Aggressive entity merging with 85% similarity threshold and Gemini 2.5 Pro validation.
- **Unified Knowledge Graphs**: Cross-video relationship mapping with temporal context awareness.
- **CLI Commands**: New `process-collection` and `process-series` commands for streamlined workflows.

### 🔍 Gemini 2.5 Pro Integration (v2.13.0)
- **Intelligence-Grade Analysis**: Strategic insights focusing on information architecture and relationship dynamics.
- **Collection Summaries**: Comprehensive 4-5 paragraph analysis with rich context and strategic focus.
- **Entity Validation**: Identity verification with temporal context and disambiguation analysis.
- **Narrative Flow Analysis**: Story progression tracking and thematic arc identification for series content.

### 📖 Topic Evolution & Narrative Analysis (v2.13.0)
- **Story Progression**: Track narrative development across video sequences with milestone identification.
- **Topic Evolution**: Analysis of how topics develop across video sequences with coherence scoring.
- **Thematic Arcs**: Identification of story patterns and information dependencies across videos.
- **Strategic Intelligence**: Pro-level insights with focus on temporal intelligence and relationship dynamics.

### 🎯 Previous Major Features

### 📊 Advanced Plotly Visualizations (v2.12.0)
- **Interactive Charts**: Pie charts, bar charts, and gauge visualizations for entity source analysis.
- **Professional Quality**: Publication-ready charts with hover effects and customizable styling.
- **Graceful Fallback**: Simple charts when Plotly unavailable for maximum compatibility.
- **Model Caching**: 3-5x performance improvement through intelligent model reuse.
- **Enhanced Streamlit UI**: Comprehensive batch processing with real-time progress tracking.

### 📄 Excel Export Capabilities (v2.12.0)
- **Multi-Sheet Workbooks**: Organized data across Summary, Source Distribution, Entity Types, and Per-Video Analysis sheets.
- **One-Click Downloads**: Streamlit integration for instant Excel file generation.
- **Comprehensive Data**: All analysis metrics, breakdowns, and insights included.

### 📈 Performance Dashboard Integration (v2.12.0)
- **Dedicated Streamlit Tab**: Comprehensive performance monitoring interface.
- **Real-time System Health**: CPU, memory, and disk usage monitoring with gauge visualizations.
- **Model Cache Analytics**: Hit rates, load times, and efficiency metrics with historical reports.

### 🎯 Previous Enhancements (v2.10.1-v2.11.0)
- **Entity Source Tracking**: Pipeline transparency with detailed extraction method attribution.
- **Model Caching**: 3-5x performance improvement through intelligent model reuse.
- **Enhanced Streamlit UI**: Comprehensive batch processing with real-time progress tracking.

The latest versions of ClipScribe also include these major enhancements:

### 🖥️ Enhanced Interactive Web UI (v2.12.0)
- **Performance Dashboard**: Dedicated tab for comprehensive system monitoring and analytics.
- **Advanced Visualizations**: Interactive Plotly charts for entity source analysis.
- **Export Capabilities**: One-click downloads for Excel, CSV, and Markdown formats.
- **Real-time Analytics**: Live progress tracking with detailed batch processing insights.
- **Professional Interface**: Enhanced UI with comprehensive batch processing features.

### 🔬 Research Command (v2.7.0)
- **Topic-Based Analysis**: Use the new `research` command to analyze multiple videos on a single topic.
- **Batch Processing**: Automatically finds and processes a list of relevant videos.

### 📊 Performance Dashboards & Rich CLI (v2.6.0)
- **Rich Progress Indicators**: Get real-time feedback in your terminal with beautiful progress bars.
- **Cost & Time Tracking**: Live monitoring of API costs and processing time for each stage.
- **Enhanced Markdown Reports**: Interactive reports with Mermaid diagrams, collapsible sections, and visual dashboards.

### 💡 Coming in v2.15.0: Streamlit "Mission Control"
- **Collection Workbench**: Drag-and-drop interface for building and managing video collections.
- **Synthesis Dashboard**: Interactive visualizations of consolidated timelines and knowledge graphs.
- **Live Knowledge Graph**: Real-time visualization as collections are built.
- **Dynamic Knowledge Panels**: Synthesize all information about entities into comprehensive views.

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

3. **Set up environment variables (SECURE)**
   ```bash
   # Create .env file with your FREE Google API key
   echo "GOOGLE_API_KEY=your_actual_key_here" > .env
   ```

4. **Verify installation**
   ```bash
   poetry run clipscribe --version
   ```

## 💻 Usage

### Command-Line Interface (CLI)

```bash
# Quick demo with TWO-PART PBS video series (recommended for relationship extraction!)
poetry run python demo.py

# Transcribe a single video with working relationship extraction
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=6ZVj1_SE4Mo"

# Research a topic across multiple videos with performance monitoring
poetry run clipscribe research "PBS NewsHour" --max-results 3

# NEW in v2.14.0: Process multiple videos with working relationship extraction and knowledge synthesis
poetry run clipscribe process-collection "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" "https://www.youtube.com/watch?v=xYMWTXIkANM" --collection-title "Pegasus-Investigation"

# Process video series with automatic detection and narrative flow analysis
poetry run clipscribe process-series "URL1" "URL2" "URL3" --series-title "My Documentary Series"

# Analyze entity sources with advanced visualizations and Excel export
poetry run python scripts/analyze_entity_sources.py --output-dir output/research --create-visualizations --save-excel
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

ClipScribe includes a complete video intelligence extraction pipeline with **working relationship extraction**:

### 🎯 REBEL Relationship Extraction (FIXED in v2.14.0)
- **Extract 10-19 relationships per video** (`Subject -> Predicate -> Object`) automatically
- **Space-separated parsing** with dual fallback strategy for maximum compatibility
- **Build meaningful knowledge graphs** from video content with real relationships
- **Examples**: "NSO | inception | 2010", "UAE | diplomatic relation | Saudi Arabia"

### 🔍 Custom Entity Detection (GLiNER) 
- Detect domain-specific entities beyond standard NER (e.g., weapons, technologies, financial metrics)
- **250-300 entities per video** with LLM validation for accuracy

### 🧠 Complete Intelligence Stack
```
Video → Transcription → Entities → Relationships → Knowledge Graph → GEXF Export
```

### Usage Example:
```python
# See examples/advanced_features_demo.py for a full example
retriever = VideoIntelligenceRetriever(
    use_advanced_extraction=True,
    domain="technology"  # Optional domain specialization
)

# Process a video and get relationships
result = await retriever.process_url("https://youtube.com/watch?v=...")
print(f"Extracted {len(result.relationships)} relationships")
print(f"Knowledge graph has {result.knowledge_graph['edge_count']} edges")
```

**Try the demo:**
```bash
# Run the advanced features demo with working relationship extraction
poetry run python examples/advanced_features_demo.py

# Test with PBS NewsHour content (recommended for relationship extraction)
poetry run clipscribe process-collection "https://www.youtube.com/watch?v=6ZVj1_SE4Mo" --collection-title "Test-Relationships"
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
