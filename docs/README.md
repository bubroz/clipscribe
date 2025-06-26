# ClipScribe Documentation

Welcome to the ClipScribe documentation! This guide will help you get started with AI-powered video transcription and analysis.

## 📚 Documentation Index

### Getting Started
- [**Quick Start Guide**](GETTING_STARTED.md) - Get up and running in 5 minutes
- [**CLI Reference**](CLI_REFERENCE.md) - Complete command-line documentation
- [**Supported Platforms**](PLATFORMS.md) - List of 1800+ supported video platforms

### Features & Guides
- [**Output Formats**](OUTPUT_FORMATS.md) - Understanding all output formats: TXT, JSON, CSV, Markdown reports, and GEXF graphs
- [**Visualizing Knowledge Graphs**](VISUALIZING_GRAPHS.md) - View extracted relationships with Gephi
- [**Extraction Technology**](EXTRACTION_TECHNOLOGY.md) - Deep dive into entity and relationship extraction methods
- [**Development Guide**](DEVELOPMENT.md) - Architecture, API reference, and contribution guidelines
- [**Troubleshooting**](TROUBLESHOOTING.md) - Common issues and solutions

## 🚀 Quick Start

```bash
# Install
pip install clipscribe

# Set API key
export GOOGLE_API_KEY="your-key-here"

# Transcribe a video with relationship extraction
clipscribe transcribe "https://youtube.com/watch?v=..."

# Process multiple videos with knowledge synthesis
clipscribe process-collection "URL1" "URL2" --collection-title "My-Analysis"
```

## 💡 Key Features (v2.14.0 - The Synthesis Update)

### 🎯 **MAJOR BREAKTHROUGH: Working Relationship Extraction**
- **REBEL Model Fixed**: Extract 10-19 meaningful relationships per video
- **Knowledge Graphs**: Build connected graphs with real relationship data
- **Space-Separated Parsing**: Dual parsing strategy for maximum compatibility

### ✨ **New in v2.14.0**
- **Knowledge Synthesis Engine**: Timeline synthesis across multiple videos
- **GEXF 1.3 Export**: Modern knowledge graph format for Gephi visualization
- **Collection Intelligence**: Enhanced multi-video processing with consolidated outputs
- **Critical Bug Fixes**: Resolved async handling and relationship saving issues

### 🔥 **Core Capabilities**
- **1800+ Platforms**: YouTube, Twitter, TikTok, Vimeo, and many more
- **AI-Powered**: Uses Google's Gemini 2.5 Flash/Pro for accurate transcription
- **Cost-Effective**: 92% base savings with intelligent API batching
- **Fast**: Process 1 hour of video in just 2-5 minutes with model caching
- **Advanced Visualizations**: Interactive Plotly charts for comprehensive analysis
- **Excel Export**: Multi-sheet Excel exports with professional formatting
- **Performance Dashboards**: Real-time system monitoring and analytics
- **Multiple Formats**: TXT, JSON, CSV, Excel, Markdown reports, and GEXF graphs
- **Entity Source Tracking**: Track which extraction method found each entity
- **Professional Reports**: Auto-generated markdown intelligence reports with interactive charts

## 🔗 Links

- **GitHub**: https://github.com/yourusername/clipscribe
- **Issues**: https://github.com/yourusername/clipscribe/issues
- **PyPI**: https://pypi.org/project/clipscribe/

## 📝 License

MIT License - see [LICENSE](../LICENSE) file for details. 