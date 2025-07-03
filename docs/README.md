# ClipScribe Documentation

*Last Updated: July 3, 2025*
*Related: [Main README](../README.md)*

Welcome to ClipScribe's documentation! This guide will help you understand and use all features of the advanced video intelligence extraction platform.

## 🎯 Core Intelligence Extraction Focus (v2.18.23)

**ClipScribe Evolution**: Advanced video intelligence platform focused on world-class entity extraction, relationship mapping, and cross-video intelligence analysis.

**Strategic Direction**: ClipScribe now focuses exclusively on **core function enhancement** rather than feature expansion. We're making our proven strengths (95%+ entity extraction, 90%+ relationship accuracy) industry-leading.

**Current Status**: **v2.18.23 - STRATEGIC PIVOT COMPLETE** 🎯

## 🚀 What ClipScribe Does Exceptionally Well

### ✅ **Entity Extraction (95%+ Accuracy)**
- **Hybrid Approach**: SpaCy + GLiNER + REBEL multi-source validation
- **26K+ Line Intelligence**: Rich entity extraction from complex video content
- **Multi-Platform**: 1800+ video platforms supported
- **Cost Leadership**: $0.002/minute processing cost (92% reduction vs competitors)

### ✅ **Relationship Mapping (90%+ Accuracy)**
- **Complex Connections**: Subject-predicate-object relationships with high accuracy
- **Factual Verification**: Cross-validated relationship claims
- **Rich Context**: Relationship extraction with confidence scoring

### ✅ **Cross-Video Intelligence**
- **Collection Analysis**: Advanced multi-video insight synthesis
- **Entity Consistency**: Cross-video entity resolution and deduplication
- **Comprehensive Reports**: Professional intelligence summaries

### ✅ **Knowledge Graph Generation**
- **Multiple Formats**: JSON, GEXF, GraphML for different visualization tools
- **Interactive Visualization**: Gephi-compatible network graphs
- **Professional Output**: Research-grade knowledge extraction

## 📈 Strategic Roadmap: Core Excellence & User Value

**🚫 ENHANCED RELATIONSHIP ANALYSIS CANCELLED**: Determined to be additive feature that distracts from core value. Current 90%+ relationship accuracy is sufficient for users.

### Phase 1: Core Excellence & User Experience (Q3 2025)
- **Performance Optimization**: 25% faster processing while maintaining cost leadership
- **User Experience Improvements**: <100ms CLI feedback response times, clear error messages
- **Documentation Excellence**: 100% use case coverage with working examples
- **Bug Fixes & Edge Cases**: 99%+ successful video processing rate

### Phase 2: Proven Feature Enhancement (Q4 2025)
- **Video Format Support**: Better handling of edge cases and platform-specific content
- **Export Improvements**: Better output formats based on actual user requests
- **Cost Transparency**: Real-time cost tracking and clearer estimates
- **Platform Optimization**: Better handling of platform-specific video processing

### Phase 3: Market-Driven Features (Q1 2026)
- **User-Requested Features**: Build what users actually ask for, not theoretical improvements
- **Real-World Use Cases**: Focus on solving actual problems users face
- **Competitive Advantages**: Strengthen areas where we already excel
- **Performance Leadership**: Maintain cost and speed advantages while improving reliability

## 🚫 Discontinued Features

### ~~Enhanced Relationship Analysis~~ (CANCELLED July 3, 2025)
- **Reason**: Additive feature that distracts from core value; current 90%+ accuracy sufficient for users
- **Impact**: Focus redirected to core stability, user experience, and performance optimization
- **Replacement**: Core excellence in existing entity extraction and relationship mapping

### ~~Timeline Intelligence~~ (DISCONTINUED July 2, 2025)
- **Reason**: Only 24.66% accuracy - insufficient for production use
- **Impact**: 85 development hours/month redirected to core excellence
- **Replacement**: Focus on proven video intelligence extraction strengths

ClipScribe now focuses exclusively on what it does exceptionally well: video intelligence extraction with practical improvements based on user needs.

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

9. **[Strategic Pivot Document](STRATEGIC_PIVOT_2025_07_02.md)** - Strategic direction
   - Why timeline development was discontinued
   - New focus on core function enhancement
   - Implementation roadmap and success metrics

## 🗺️ Quick Navigation

- **Just want to process a video?** → Start with [Getting Started](GETTING_STARTED.md)
- **Need command details?** → Check [CLI Reference](CLI_REFERENCE.md)
- **Having issues?** → See [Troubleshooting](TROUBLESHOOTING.md)
- **Want to contribute?** → Read [Development Guide](DEVELOPMENT.md)
- **Understand the strategic direction?** → Review [Strategic Pivot Document](STRATEGIC_PIVOT_2025_07_02.md)

## 🚀 Quick Start

```bash
# Install
poetry install

# Set API key securely
echo "GOOGLE_API_KEY=your-key-here" > .env

# Extract intelligence from a video
poetry run clipscribe transcribe "https://youtube.com/watch?v=..."

# Process multiple videos with enhanced intelligence
poetry run clipscribe process-collection "URL1" "URL2" --collection-title "My-Analysis"
```

## 💡 Key Features (v2.18.23 - Core Intelligence Focus!)

### 🎯 **Core Intelligence Extraction**
- **Entity Extraction**: 95%+ accuracy with hybrid multi-source approach
- **Relationship Mapping**: 90%+ accuracy with complex factual connections
- **Cross-Video Analysis**: Advanced multi-video intelligence synthesis
- **Knowledge Graphs**: Professional-grade relationship network generation

### 🚀 **Platform & Performance Excellence**
- **1800+ Platforms**: YouTube, Twitter, TikTok, Vimeo, and many more
- **AI-Powered**: Uses Google's Gemini 2.5 Flash/Pro for accurate processing
- **Cost Leadership**: $0.002/minute (92% reduction vs competitors)
- **Fast Processing**: Process 1 hour of video in 2-5 minutes with model caching

### 🔥 **Professional Output**
- **Multiple Formats**: JSON, CSV, Excel, Markdown, GEXF graphs
- **Interactive Visualization**: Gephi-compatible knowledge graphs
- **Professional Reports**: Auto-generated intelligence summaries
- **Entity Source Tracking**: Full traceability of extraction methods

### 📊 **Advanced Analysis**
- **Mission Control**: Complete Streamlit web interface
- **Performance Dashboards**: Real-time system monitoring
- **Information Flow Maps**: Track concept evolution across videos
- **Excel Export**: Multi-sheet professional formatting

## 📋 Documentation Standards

All documentation follows these standards:

1. **Focus on Core Strengths** - Document what ClipScribe does exceptionally well
2. **Clear Examples** - Every feature includes working examples
3. **Updated Regularly** - Docs are updated with each feature change
4. **Cross-Referenced** - Related documents are linked appropriately

## 🔄 Keeping Docs Current

When making changes to ClipScribe:

1. Update relevant documentation immediately
2. Test all code examples to ensure they work
3. Update the "Last Updated" date at the top of modified files
4. Add new documents to this README when created

Remember: ClipScribe dominates video intelligence extraction by doing fewer things exceptionally well :-)

## 🔗 Links

- **GitHub**: https://github.com/bubroz/clipscribe
- **Issues**: https://github.com/bubroz/clipscribe/issues
- **Strategic Pivot**: [STRATEGIC_PIVOT_2025_07_02.md](STRATEGIC_PIVOT_2025_07_02.md)

## 📝 License

MIT License - see [LICENSE](../LICENSE) file for details. 