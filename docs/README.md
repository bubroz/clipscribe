# ClipScribe Documentation

*Last Updated: June 29, 2025*
*Related: [Main README](../README.md)*

Welcome to the ClipScribe documentation! This directory contains comprehensive guides for using and developing ClipScribe.

## 🎯 Strategic Positioning (v2.18.3)

**ClipScribe Role**: Video intelligence collector and triage analyst
- Extracts structured intelligence from video content with 95% cost reduction
- Provides reliable video processing and initial intelligence extraction  
- Designed to feed structured data to advanced analysis engines (future Chimera integration)

**NOT a complete analysis engine** - focuses on reliable collection and triage rather than deep analytical correlation.

## 🚀 What's New

### 🔧 **Timeline Intelligence - Simplified Approach (v2.18.3)**
- **Key Event Extraction**: Extract important facts and events mentioned in video content
- **Video Timestamp Context**: Precise reference points ("At 5:23, speaker mentions X")
- **Mentioned Date Detection**: Attempt to find actual dates referenced in content
- **No Complex Temporal Correlation**: Simplified approach focused on reliable intelligence collection
- **Future-Ready**: Designed for eventual integration with advanced temporal analysis systems

### 🚧 **Current Status: Critical Bug Fixes in Progress**
- Timeline date extraction logic being repaired
- Information Flow Maps crashes being resolved
- Mission Control stability improvements underway

### 🚧 **Current Status: Timeline Feature Fundamentally Broken** (Updated 2025-06-29)
- **CRITICAL**: Timeline feature creates 44 duplicates of same event with entity combinations
- **Wrong Dates**: 90% of events use video publish date instead of actual historical dates
- **No Temporal Intelligence**: Extracts entity mentions, not actual temporal events
- **Complete Redesign Required**: See [Timeline Intelligence v2.0](TIMELINE_INTELLIGENCE_V2.md) for architecture
- **Mission Control UI**: Fixed all duplicate element issues - fully operational (v2.18.7)

## 📚 Documentation Overview

### For Users

1. **[Getting Started](GETTING_STARTED.md)** - Quick start guide for new users
   - Installation instructions
   - Basic usage examples
   - First video processing

2. **[CLI Reference](CLI_REFERENCE.md)** - Complete command-line interface documentation
   - All available commands
   - Options and parameters
   - Advanced usage patterns

3. **[Supported Platforms](PLATFORMS.md)** - Video platform compatibility
   - YouTube, Twitter/X, TikTok, and more
   - Platform-specific features
   - Authentication requirements

4. **[Output Formats](OUTPUT_FORMATS.md)** - All supported output formats
   - JSON, CSV, Markdown formats
   - Knowledge graph exports (GEXF, GraphML)
   - Chimera integration format

5. **[Visualizing Knowledge Graphs](VISUALIZING_GRAPHS.md)** - Graph visualization guide
   - Using Gephi for network analysis
   - Python visualization scripts
   - Interactive graph exploration

6. **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
   - API key configuration
   - Platform-specific issues
   - Performance optimization

### For Developers

7. **[Development Guide](DEVELOPMENT.md)** - Developer setup and guidelines
   - Development environment setup
   - Code organization
   - Testing procedures
   - Contributing guidelines

8. **[Extraction Technology](EXTRACTION_TECHNOLOGY.md)** - Entity extraction details
   - Hybrid extraction approach
   - Model configurations
   - Cost optimization strategies

9. **[Timeline Intelligence v2.0](TIMELINE_INTELLIGENCE_V2.md)** ⚠️ **CRITICAL REDESIGN**
   - Current timeline feature is fundamentally broken
   - Complete v2.0 architecture specification
   - Implementation roadmap for fixing timeline extraction
   - Quality metrics and testing strategy

## 🗺️ Quick Navigation

- **Just want to process a video?** → Start with [Getting Started](GETTING_STARTED.md)
- **Need command details?** → Check [CLI Reference](CLI_REFERENCE.md)
- **Having issues?** → See [Troubleshooting](TROUBLESHOOTING.md)
- **Want to contribute?** → Read [Development Guide](DEVELOPMENT.md)
- **Interested in timeline features?** → Review [Timeline Intelligence v2.0](TIMELINE_INTELLIGENCE_V2.md)

## 📋 Documentation Standards

All documentation in this directory follows these standards:

1. **Markdown Format** - All docs use GitHub-flavored Markdown
2. **Clear Examples** - Every feature includes working examples
3. **Updated Regularly** - Docs are updated with each feature change
4. **Cross-Referenced** - Related documents are linked appropriately

## 🔄 Keeping Docs Current

When making changes to ClipScribe:

1. Update relevant documentation immediately
2. Test all code examples to ensure they work
3. Update the "Last Updated" date at the top of modified files
4. Add new documents to this README when created

Remember: Good documentation is as important as good code :-)

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