# ClipScribe Examples

This directory contains example scripts demonstrating various features and use cases of ClipScribe.

## 🚀 Quick Start

The easiest way to get started:

```bash
python examples/quick_start.py
```

## 📚 Available Examples

### 1. **quick_start.py** - Simple Transcription
The simplest way to transcribe a video in just a few lines of code.
- Basic video transcription
- Saving outputs to files
- Error handling

### 2. **structured_output_demo.py** - Machine-Readable Output
Creates structured output with multiple formats for Chimera integration.
- Machine-readable directory structure
- Multiple output formats (TXT, JSON, plus knowledge graphs)
- Metadata and entity extraction
- Manifest file with checksums
- Chimera-compatible format

### 3. **batch_processing.py** - Multiple Videos
Process multiple videos efficiently with parallel processing.
- Parallel video processing
- Progress tracking
- Cost summaries
- Error recovery

### 4. **cost_optimization.py** - Managing Costs
Strategies for minimizing transcription costs.
- Cost preview before processing
- Budget-aware processing
- Video chunking for long content
- Cost comparison tables

### 5. **output_formats.py** - Export Options
All available output formats and custom export examples.
- Standard formats: TXT, JSON, plus knowledge graph formats
- Custom formats: CSV, HTML
- Format selection guide

### 6. **cli_usage.py** - Command Line Guide
Complete reference for using ClipScribe from the terminal.
- 60+ command examples
- Advanced options
- Integration patterns
- Tips and tricks

### 7. **multi_platform_demo.py** - 1800+ Platforms
Demonstrates support for various video platforms.
- Platform detection
- URL validation
- Multi-source processing
- Search capabilities

### 8. **video_intelligence_demo.py** - Advanced Features
Advanced analysis and intelligence extraction.
- Entity extraction
- Key points detection
- Cost analysis
- Metadata processing

### 9. **test_improvements.py** - Test Improvements
Demonstrates the hybrid entity extraction and proper segment generation.

```bash
poetry run python examples/test_improvements.py
```

Shows:
- SpaCy entity extraction (zero cost)
- Hybrid extraction with selective LLM validation
- Proper transcript segmentation for readability
- Cost metrics and performance stats

### 10. **advanced_extraction_demo.py** - 🔥 NEW v2.2 Intelligence Extraction
Complete intelligence extraction with relationships and knowledge graphs.

```bash
poetry run python examples/advanced_extraction_demo.py "VIDEO_URL" [domain]
```

Features:
- **REBEL** relationship extraction (subject → predicate → object)
- **GLiNER** custom entity detection
- Knowledge graph generation with NetworkX
- Domain-specific extraction (military, tech, finance, medical)
- Fact extraction from relationships
- Processing statistics and visualization

Example:
```bash
# Extract military intelligence from a defense video
poetry run python examples/advanced_extraction_demo.py "https://youtube.com/..." military

# Extract tech entities from a programming tutorial
poetry run python examples/advanced_extraction_demo.py "https://youtube.com/..." tech
```

Output includes:
- Entity distribution by type
- Top relationships with confidence scores
- Key facts extracted
- Knowledge graph statistics
- All output formats including relationships.json and knowledge_graph.json

**Note**: First run downloads ~3GB of ML models. Subsequent runs use cached models.

### 11. **multi_video_collection_demo.py** - 🧠 NEW v2.13.0 Multi-Video Intelligence
Comprehensive multi-video collection processing with cross-video analysis.

```bash
poetry run python examples/multi_video_collection_demo.py
```

Features:
- **Automatic Series Detection**: AI-powered pattern recognition for video series
- **Cross-Video Entity Resolution**: Aggressive entity merging with 85% similarity threshold
- **Unified Knowledge Graphs**: Cross-video relationship mapping with temporal context
- **Narrative Flow Analysis**: Story progression tracking for series content
- **Topic Evolution Tracking**: Analysis of how topics develop across video sequences
- **Gemini 2.5 Pro Integration**: Intelligence-grade analysis with strategic insights

Example output:
- Multi-video intelligence analysis with unified entities and relationships
- Collection summary with strategic insights and quality metrics
- Topic evolution reports and narrative flow analysis
- Cross-video knowledge graphs and entity resolution reports

**Use cases**: Documentary series, educational content, news coverage analysis, multi-part investigations

## 🛠️ Prerequisites

Before running the examples:

1. **Install ClipScribe**:
   ```bash
   poetry install
   ```

2. **Set up API key**:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   # Or create a .env file
   ```

3. **Install FFmpeg** (for audio extraction):
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

## 💡 Usage Tips

1. **Start with quick_start.py** to understand the basics
2. **Try structured_output_demo.py** for machine-readable output
3. **Use batch_processing.py** for multiple videos
4. **Check cost_optimization.py** before processing long videos
5. **Refer to cli_usage.py** for command-line options
6. **Explore output_formats.py** for different export needs

## 🎯 Common Patterns

### Process a Single Video
```python
from clipscribe.retrievers import UniversalVideoClient

client = UniversalVideoClient()
result = await client.transcribe_video("https://youtube.com/watch?v=...")
print(result.transcript.full_text)
```

### Process with Cost Limit
```python
# Preview cost first
info = await client.extract_video_info(url)
cost = (info['duration'] / 60) * 0.002

if cost <= budget:
    result = await client.transcribe_video(url)
```

### Export Multiple Formats
```python
result = await client.transcribe_video(
    url,
    save_outputs=True,
    output_formats=['txt', 'json']
)
```

## 📊 Performance Expectations

- **Speed**: 2-5 minutes to transcribe 1 hour of video
- **Cost**: $0.002/minute ($0.12/hour)
- **Accuracy**: High accuracy with Gemini 2.5 Flash
- **Platforms**: 1800+ supported sites

## 🤝 Contributing

Found a useful pattern? Feel free to contribute new examples!

1. Create a new example file
2. Add clear documentation
3. Update this README
4. Submit a pull request

## 📚 More Resources

- [Main Documentation](../docs/README.md)
- [API Reference](../docs/DEVELOPMENT.md)
- [CLI Reference](../docs/CLI_REFERENCE.md)
- [Supported Platforms](../docs/PLATFORMS.md)

---

*Happy transcribing! 🎉* 