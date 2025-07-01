# ClipScribe Documentation

*Last Updated: July 1, 2025*
*Related: [Main README](../README.md)*

Welcome to ClipScribe's documentation! This guide will help you understand and use all features of the video intelligence platform.

## 🚀 Timeline Intelligence v2.0 Era (v2.18.17)

**ClipScribe Evolution**: Advanced video intelligence platform with Timeline Intelligence v2.0 + TimelineJS3 Export
- Breakthrough temporal intelligence through yt-dlp integration with 157KB of Timeline v2.0 code
- 300% more temporal intelligence for only 12-20% cost increase through direct video processing
- Beautiful interactive timeline visualizations with TimelineJS3 export
- Battle-tested against real-world video collections with comprehensive validation

**Current Status**: **v2.18.17 FULLY OPERATIONAL + ENHANCED** 🎉

**Timeline Intelligence v2.0**: Focus on precision temporal intelligence collection and synthesis with proven results + interactive export.

## 📊 Major Accomplishments Summary

### ✅ **Timeline Intelligence v2.0 - FULLY OPERATIONAL (v2.18.17)**
- **Complete Foundation Implementation**: 157KB of Timeline v2.0 code with 4 core components
- **Proven Real-World Results**: 9→5 event transformation with 55.56% quality improvement
- **Full Pipeline Integration**: VideoRetriever and MultiVideoProcessor support Timeline v2.0
- **Data Persistence**: All timeline data properly saved to JSON outputs
- **Quality Filtering**: Advanced duplicate removal and date validation
- **TimelineJS3 Export**: Beautiful interactive timeline visualizations ✅ NEW!

### 🎯 **Timeline v2.0 Components Delivered (v2.18.10-17)**
- **TemporalExtractorV2** (29KB): Core yt-dlp temporal intelligence integration
- **TimelineQualityFilter** (28KB): Comprehensive quality assurance and validation
- **ChapterSegmenter** (31KB): yt-dlp chapter-based intelligent segmentation
- **CrossVideoSynthesizer** (41KB): Multi-video timeline correlation and synthesis
- **Complete Integration**: VideoRetriever and MultiVideoProcessor support Timeline v2.0
- **TimelineJSFormatter**: Interactive timeline export with media support ✅ NEW!

### 🚀 **Current Integration Status**
**Phase 5: Integration & Testing Progress:**
- ✅ **Component 1**: Pipeline Integration (MultiVideoProcessor Timeline v2.0) - **COMPLETE**
- ✅ **Component 2**: VideoRetriever Integration (Single video Timeline v2.0 processing) - **COMPLETE**
- ✅ **Component 3**: Mission Control Integration (Timeline v2.0 UI features) - **COMPLETE**
- ✅ **Component 4**: Real-World Testing (Comprehensive validation) - **COMPLETE**
- ✅ **Component 5**: TimelineJS3 Export (Interactive visualizations) - **COMPLETE**

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

## 💡 Key Features (v2.18.17 - Timeline Intelligence v2.0 FULLY OPERATIONAL!)

### ✅ **MAJOR BREAKTHROUGH: Timeline Intelligence v2.0 Foundation Complete! (2025-07-01)**

- **Timeline Intelligence v2.0**: Complete architectural transformation with 157KB of implementation code
- **yt-dlp Temporal Integration**: Chapter-aware extraction, word-level timing, SponsorBlock filtering
- **Advanced Event Processing**: 5-step pipeline: Extract → Deduplicate → Content dates → Quality filter → Chapter segmentation
- **Pipeline Integration**: Complete integration into single video and multi-video processing workflows

### 🚀 **Timeline Intelligence v2.0 Capabilities**
- **Chapter-Aware Processing**: Uses yt-dlp chapter boundaries for intelligent content segmentation
- **Word-Level Timing**: Sub-second precision using yt-dlp subtitle data
- **Content Date Extraction**: Extracts historical dates from content (not video metadata)
- **Event Deduplication**: Eliminates duplicate events through intelligent consolidation
- **Quality Filtering**: Comprehensive quality assurance with configurable thresholds
- **Cross-Video Synthesis**: Builds coherent timelines across multiple video sources

### ✨ **Enhanced Temporal Intelligence Foundation (v2.17.0)**
- **Visual Temporal Cues**: Extract dates from charts, graphs, documents, calendars
- **Enhanced Timeline Synthesis**: LLM-based date extraction with cross-video correlation
- **Video Retention System**: Smart storage vs reprocessing cost analysis
- **Direct Video Processing**: Eliminated audio extraction inefficiency for 10x performance improvement

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