# ARGOS Documentation

Welcome to the ARGOS documentation! This guide will help you get started with AI-powered video intelligence and enhanced temporal analysis.

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
poetry install

# Set API key securely
echo "GOOGLE_API_KEY=your-key-here" > .env

# Transcribe a video with relationship extraction
poetry run clipscribe transcribe "https://youtube.com/watch?v=..."

# Process multiple videos with knowledge synthesis
poetry run clipscribe process-collection "URL1" "URL2" --collection-title "My-Analysis"
```

## 💡 Key Features (v2.17.0 - Enhanced Temporal Intelligence COMPLETE!)

### ✅ **MAJOR MILESTONE: All 4/4 Core Components Complete! (2025-06-28)**

- **Enhanced Temporal Intelligence**: 300% more temporal intelligence for only 12-20% cost increase
- **Timeline Building Pipeline**: Web research integration for enhanced temporal event validation *(NEW - Just Completed!)*
- **Smart Video Retention**: Cost-optimized archival with automated retention policies
- **Direct Video Processing**: Eliminated audio extraction inefficiency for 10x performance improvement

### 🔧 **Timeline Building Pipeline Features (v2.17.0)**
- **Web Research Integration**: Validates timeline events against external sources
- **Temporal Consistency Validation**: Detects chronological anomalies and large time gaps
- **Smart Cost Control**: Research disabled by default, optional enrichment when API available
- **Graceful Degradation**: Full functionality maintained without external research
- **Comprehensive Testing**: 16/16 unit tests passing with 82% coverage

### ✨ **Enhanced Temporal Intelligence (v2.17.0)**
- **Visual Temporal Cues**: Extract dates from charts, graphs, documents, calendars
- **Enhanced Timeline Synthesis**: LLM-based date extraction with cross-video correlation
- **Video Retention System**: Smart storage vs reprocessing cost analysis
- **Complete Integration**: All components working together in unified pipeline

### 🚀 **Previous Major Features**
- **Information Flow Maps**: Track concept evolution across video sequences
- **Knowledge Panels**: Entity-centric intelligence synthesis (v2.15.0)
- **GEXF 1.3 Export**: Modern knowledge graph format for Gephi visualization
- **Mission Control**: Complete Streamlit web interface (v2.16.0)

### 🔥 **Core Capabilities**
- **1800+ Platforms**: YouTube, Twitter, TikTok, Vimeo, and many more
- **AI-Powered**: Uses Google's Gemini 2.5 Flash/Pro for accurate transcription
- **Cost-Effective**: 95% base savings through direct video processing
- **Fast**: Process 1 hour of video in just 2-5 minutes with model caching
- **Advanced Visualizations**: Interactive Plotly charts for comprehensive analysis
- **Excel Export**: Multi-sheet Excel exports with professional formatting
- **Performance Dashboards**: Real-time system monitoring and analytics
- **Multiple Formats**: TXT, JSON, CSV, Excel, Markdown reports, and GEXF graphs
- **Entity Source Tracking**: Track which extraction method found each entity
- **Professional Reports**: Auto-generated markdown intelligence reports with interactive charts

## 🔗 Links

- **GitHub**: https://github.com/bubroz/clipscribe
- **Issues**: https://github.com/bubroz/clipscribe/issues

## 📝 License

MIT License - see [LICENSE](../LICENSE) file for details. 