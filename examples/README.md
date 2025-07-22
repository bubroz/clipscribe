# ClipScribe Examples

*Last Updated: July 20, 2025*

This directory contains example scripts demonstrating various features and use cases of ClipScribe with **enhanced entity and relationship extraction**.

## 🚀 v2.19.0 Extraction Quality

**ClipScribe v2.19.0** features dramatically improved extraction:
- **Entity Completeness**: Targets 100% extraction (16+ entities per video)
- **Relationship Mapping**: 52+ relationships with evidence chains
- **Knowledge Graphs**: 88+ nodes and 52+ edges with rich metadata
- **Fixed Quality Filters**: No longer removes 70% of valid entities
- **Cost Effective**: Still only $0.0083 per video

## 🚀 Quick Start

The easiest way to get started:

```bash
python examples/quick_start.py
```

## 📚 Available Examples

### 1. **quick_start.py** - Simple Processing
The simplest way to process a video and extract intelligence.
- Basic video processing
- Entity and relationship extraction
- Knowledge graph generation
- Error handling

### 2. **structured_output_demo.py** - Machine-Readable Output
Creates structured output for research integration.
- JSON/CSV data structures
- Knowledge graph formats
- Entity source tracking
- Chimera-compatible format

### 3. **batch_processing.py** - Multiple Videos
Process multiple videos efficiently.
- Parallel video processing
- Cross-video entity resolution
- Collection synthesis
- Performance optimization

### 4. **cost_optimization.py** - Cost Management
Strategies for minimizing costs while maximizing extraction quality.
- Cost preview and tracking
- Processing optimization

### 5. **output_formats.py** - Export Options
All available output formats with enhanced extraction metadata.
- JSON format with entities and relationships
- CSV exports for spreadsheet analysis
- Knowledge graph formats (GEXF)
- Research-compatible exports

### 6. **cli_usage.py** - Command Line Guide
Complete reference for using ClipScribe from the terminal.
- Command examples and options
- Performance optimization flags
- Batch processing
- Quality filtering options

### 7. **multi_platform_demo.py** - 1800+ Platforms
Demonstrates support across various video platforms.
- Platform detection capabilities
- YouTube, Twitter/X, TikTok, Vimeo
- Multi-source processing
- Cross-platform intelligence

### 8. **video_intelligence_demo.py** - Advanced Features
Advanced intelligence analysis and extraction.
- Entity extraction with source tracking
- Relationship evidence chains
- Knowledge graph generation
- Performance optimization

### 9. **extraction_comparison.py** - Extraction Methods
Compare different extraction methods and their results.
- SpaCy vs GLiNER vs REBEL
- Hybrid extraction benefits
- Quality metrics comparison
- Source attribution analysis

### 10. **multi_video_collection_demo.py** - 🧠 Multi-Video Intelligence
Enhanced multi-video collection processing with entity correlation.

```bash
poetry run python examples/multi_video_collection_demo.py
```

Features:
- **Collection Processing**: Cross-video entity resolution
- **Performance Optimization**: Batch processing for large collections
- **Entity Synthesis**: Collection-wide entity deduplication
- **Relationship Correlation**: Cross-video relationship validation
- **Information Flow**: Track concepts across videos

Example output:
- Collection-wide entity synthesis
- Cross-video relationship mapping
- Performance optimization metrics
- Information flow analysis

### 11. **performance_optimization_demo.py** - ⚡ NEW Timeline v2.0 Performance
Demonstrates Timeline Intelligence v2.0 performance optimization capabilities.

```bash
poetry run python examples/performance_optimization_demo.py
```

Features:
- **Streaming Mode**: Memory-efficient processing for 100+ video collections
- **Performance Monitoring**: Real-time system monitoring and optimization
- **Cache Intelligence**: 85%+ hit rates with Timeline v2.0 data
- **Resource Management**: Configurable memory limits and batch sizing
- **Optimization Analytics**: Performance metrics and efficiency tracking

## 🛠️ Prerequisites

Before running the examples:

1. **Install ClipScribe**:
   ```bash
   poetry install
   ```

2. **Verify installation**:
   ```bash
   poetry run clipscribe --version  # Should show v2.19.0+
   ```

3. **Set up API key**:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   # Or create a .env file
   ```

4. **Install FFmpeg** (for audio extraction):
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

## 💡 Usage Tips

1. **Start with quick_start.py** to understand basic extraction
2. **Try multi_video_collection_demo.py** for cross-video intelligence
3. **Use batch_processing.py** for large collections
4. **Check cost_optimization.py** for cost/benefit analysis
5. **Explore output_formats.py** for export options

## 🎯 Common Patterns

### Process a Single Video
```python
from clipscribe.retrievers import VideoIntelligenceRetriever

retriever = VideoIntelligenceRetriever()
result = await retriever.process_url(
    "https://youtube.com/watch?v=..."
)

# Access extracted data
entities = result.entities  # 16+ entities with metadata
relationships = result.relationships  # 52+ relationships with evidence
knowledge_graph = result.knowledge_graph  # 88+ nodes, 52+ edges
```

### Process Collection
```python
from clipscribe.extractors import MultiVideoProcessor

processor = MultiVideoProcessor()
collection = await processor.process_collection(
    urls=["url1", "url2", "url3"],
    collection_title="My Research"
)

# Access cross-video synthesis
unified_entities = collection.unified_entities
cross_video_relationships = collection.cross_video_relationships
information_flow = collection.information_flow_map
```

### Performance Optimization
```python
# Large collection with batch processing
result = await processor.process_collection(
    urls=large_url_list,
    batch_size=10,
    max_concurrent=3
)
```

## 📊 Performance Expectations (v2.19.0)

- **Speed**: 2-4 minutes to process 1 hour of video
- **Cost**: $0.002/minute ($0.0083 per 5-minute video)
- **Extraction**: 52-92+ entities, 70-106+ relationships per video
- **Memory**: <2GB for typical usage
- **Platforms**: 1800+ supported sites

## 🚀 v2.19.0 Success Metrics

**Entity Completeness**: Targets 100% extraction (was filtering 70%)
**Relationship Quality**: 52+ relationships with evidence chains
**Knowledge Graphs**: 88+ nodes, 52+ edges with rich metadata
**Cost Efficiency**: Still only $0.0083 per video
**Quality Filters**: Fixed to keep valid entities

## 🤝 Contributing

Found a useful pattern? Feel free to contribute new examples!

1. Create a new example file
2. Add clear documentation
3. Include extraction examples
4. Update this README
5. Submit a pull request

## 📚 More Resources

- [Getting Started Guide](../docs/GETTING_STARTED.md)
- [Output Formats](../docs/OUTPUT_FORMATS.md)
- [Main Documentation](../docs/README.md)
- [API Reference](../docs/DEVELOPMENT.md)
- [CLI Reference](../docs/CLI_REFERENCE.md)

---

**ClipScribe v2.19.0**: Comprehensive video intelligence extraction! 🎯 