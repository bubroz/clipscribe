# ClipScribe Mission Control

*Last Updated: July 20, 2025*

Interactive web interface for managing and visualizing ClipScribe video intelligence collections with **enhanced extraction quality**.

##  v2.19.0 Extraction Quality!

**ClipScribe Mission Control** features dramatically improved extraction:
- **Entity Visualization**: 16+ entities per video with source tracking
- **Relationship Mapping**: 52+ relationships with evidence chains
- **Knowledge Graph Explorer**: 88+ nodes and 52+ edges visualization
- **Performance Monitoring**: Real-time processing tracking
- **Cross-Video Synthesis**: Multi-video entity correlation interface

##  Quick Start

### Launch the Interface
```bash
# From the project root
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

The interface will open in your browser at `http://localhost:8501`

### Prerequisites
- ClipScribe v2.19.0+ installed with `poetry install`
- Google API key configured (`GOOGLE_API_KEY` environment variable)
- Some processed videos or collections (optional for demo)

##  Interface Overview

###  Dashboard
The main landing page provides:
- **Quick Stats**: Collection and video counts with processing indicators
- **Feature Cards**: Overview of Collections, Analytics, and Information Flows
- **Recent Activity**: Shows your 5 most recently processed videos/collections
- **System Status**: API key configuration and cost tracking

###  Collections
Browse and manage multi-video collections:

**Overview Tab**:
- Collection metrics and statistics
- Entity/relationship synthesis status
- Collection summary with key insights

**Videos Tab**:
- Complete list of videos in collection
- Individual video entity/relationship counts
- Processing status and metadata

**Entities Tab**:
- Cross-video entity analysis
- Entity resolution and deduplication
- Entity frequency and importance

**Knowledge Synthesis Tab**:
- Unified knowledge graph visualization
- Cross-video relationship mapping
- Information flow analysis

###  Information Flows
Track concept evolution across videos:

**Overview Tab**:
- Flow statistics and metrics
- Concept maturity tracking
- Cross-video concept analysis

**Concept Explorer Tab**:
- Individual concept details
- Evolution across videos
- Related entities and relationships

**Evolution Paths Tab**:
- Concept progression visualization
- Introduction and development tracking
- Cross-video concept correlation

###  Analytics
Enhanced monitoring and insights:

**Cost Overview Tab**:
- Processing cost analysis
- Cost per video/collection tracking
- Budget monitoring

**Performance Tab**:
- System resource monitoring
- Processing speed metrics
- API usage statistics

**Quality Tab**:
- Entity extraction quality metrics
- Relationship confidence tracking
- Knowledge graph density analysis

##  Key Features

###  Data Integration
- **Automatic Detection**: Finds all processed videos and collections
- **Enhanced JSON Loading**: Loads complete extraction data
- **Quality Metrics**: Real-time extraction quality tracking
- **Performance Monitoring**: Processing efficiency metrics

###  Intelligence Visualization
- **Interactive Charts**: Entity/relationship visualization
- **Knowledge Graphs**: Network visualization with filtering
- **Performance Graphs**: Processing efficiency metrics
- **Quality Analysis**: Extraction confidence distributions

###  Download Options
- **Complete Exports**: All extraction data formats
- **Research Formats**: Academic-compatible exports
- **Performance Reports**: Processing analytics
- **Quality Analysis**: Extraction metrics documentation

###  User Experience
- **Modern Interface**: Clean, intuitive design
- **Interactive Elements**: Expandable sections and filters
- **Real-time Feedback**: Processing status updates
- **Quality Indicators**: Visual extraction quality tracking

###  Security
- **Local Processing**: All data stays on your system
- **API Key Protection**: Secure credential handling
- **Performance Monitoring**: Resource usage tracking
- **Error Handling**: Graceful error recovery

##  Troubleshooting

### "No data found"
- Process videos first:
  ```bash
  poetry run clipscribe process "VIDEO_URL" --format all
  ```

### "Loading errors"
- Check that extraction JSON data is valid
- Ensure ClipScribe v2.19.0+ is installed
- Verify processing completed successfully

### Version issues
- Ensure you're running ClipScribe v2.19.0+:
  ```bash
  poetry run clipscribe --version  # Should show v2.19.0+
  ```

##  Future Enhancements

### Advanced Visualizations
- Interactive knowledge graph exploration
- Entity timeline visualization
- Relationship evidence browser

### Real-time Processing
- Live progress monitoring for CLI commands
- WebSocket integration for status updates
- Queue management for batch processing

### Enhanced Analytics
- Extraction quality trend charts
- Performance benchmarking
- Cross-collection analysis

### Export Hub
- Multiple export format templates
- Automated report generation
- Integration with research tools

##  Best Practices

### For Best Performance
1. **Process in batches**: Use collection processing for multiple videos
2. **Monitor costs**: Track API usage in Analytics
3. **Use caching**: Enable cache for repeated processing

### For Better Analysis
1. **Clean graphs**: Use --clean-graph flag for cleaner visualizations
2. **Process collections**: Related videos provide better cross-video insights
3. **Review quality**: Check extraction quality metrics regularly

##  Support

For issues or questions:
- Check documentation in `docs/`
- Review error messages in the interface
- Ensure ClipScribe CLI is working correctly first
- Report issues on GitHub

---

**ClipScribe Mission Control** - Comprehensive video intelligence visualization!  