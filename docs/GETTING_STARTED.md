# Getting Started with ClipScribe

*Last Updated: July 20, 2025*
*Related: [CLI Reference](mdc:CLI_REFERENCE.md) | [Output Formats](mdc:OUTPUT_FORMATS.md)*

## 🚀 What's New: v2.19.0 Extraction Quality!

**ClipScribe v2.19.0** features dramatically improved extraction quality:
- **Comprehensive Entity Extraction**: Targets 100% completeness (16+ entities per video)
- **Evidence-Based Relationships**: 52+ relationships with direct quotes and timestamps
- **Fixed Quality Filters**: No longer removes 70% of valid entities
- **Knowledge Graphs**: 88+ nodes and 52+ edges for rich intelligence
- **Still Cost-Effective**: Only $0.0083 per video!

## Prerequisites

You'll need:
- Python 3.11+ installed (3.12+ recommended)
- Poetry package manager ([Install instructions](https://python-poetry.org/docs/#installation))
- A Google API key for Gemini ([Get one free](https://makersuite.google.com/app/apikey))
- ffmpeg installed (`brew install ffmpeg` on macOS)

## Quick Installation

### 1. Install ClipScribe

```bash
# Clone the repository
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# Install with Poetry
poetry install
```

### 2. Set Your API Key Securely

```bash
# RECOMMENDED: Create a .env file (secure)
echo "GOOGLE_API_KEY=your-api-key-here" > .env

# Alternative: Export as environment variable
export GOOGLE_API_KEY="your-api-key-here"
```

### 3. Test Installation

```bash
poetry run clipscribe --version
poetry run clipscribe --help
```

## Basic Usage

### Process a Single Video

```bash
# Basic video intelligence extraction
poetry run clipscribe process "https://www.youtube.com/watch?v=6ZVj1_SE4Mo"

# Full extraction with all output formats
poetry run clipscribe process "https://vimeo.com/123456789" \
  --format all \
  --clean-graph \
  -o analysis/

# Process with cost tracking
poetry run clipscribe process "https://twitter.com/user/status/123456" \
  --show-cost \
  --format json,markdown
```

### Process Multiple Videos (Collection Analysis)

```bash
# Process collection with automatic synthesis
poetry run clipscribe process-collection \
  "My Research Collection" \
  "https://youtube.com/watch?v=video1" \
  "https://youtube.com/watch?v=video2" \
  "https://youtube.com/watch?v=video3"

# Process playlist automatically
poetry run clipscribe process-collection \
  "CNBC Market Analysis" \
  "https://www.youtube.com/playlist?list=PLVbP054jv0Ko..." \
  --format all
```

### Research Command

```bash
# Research a topic across multiple videos
poetry run clipscribe research "climate change reports" \
  --max-results 5 \
  --format markdown
```

### Output Formats

ClipScribe supports comprehensive intelligence extraction:

- **json** - Complete structured data with entities, relationships, and metadata
- **csv** - Entities and relationships in spreadsheet format
- **gexf** - Knowledge graphs for Gephi visualization
- **markdown** - Professional reports with summaries and insights
- **all** - Generate all available formats

```bash
# Get all formats
poetry run clipscribe process "https://youtube.com/watch?v=..." \
  --format all \
  --clean-graph
```

### Launch Mission Control

```bash
# Launch the comprehensive web interface
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

Access features:
- 🎬 Video processing monitor
- 📊 Entity and relationship visualization
- 🔧 Collection management
- 🎞️ Information flow analysis
- 💾 Export and integration tools 

## Understanding Entity & Relationship Extraction (v2.19.0 Enhanced)

ClipScribe's extraction targets **100% completeness** - extracting ALL entities and relationships from videos:

- **Entities**: People, organizations, locations, events, products, etc.
- **Relationships**: Who interacts with whom, what happened where, etc.
- **Evidence**: Direct quotes and timestamps backing every claim
- **Knowledge Graphs**: Visual network of all connections

### What v2.19.0 Fixed:
- No longer filters out 70% of valid entities (quality filter was too aggressive)
- Actually uses all 50+ Gemini-extracted relationships (they were being ignored!)
- Dynamic confidence scoring based on context (not hardcoded 0.85)
- Results: 16+ entities and 52+ relationships per video (was 0-10 entities, 0 relationships)

## Common Use Cases

### 1. News Analysis
```bash
poetry run clipscribe process "https://youtube.com/watch?v=news_video" \
  --format all \
  --clean-graph \
  -o news-analysis/
```

### 2. Multi-Video Investigation
```bash
poetry run clipscribe process-collection \
  "Pegasus Investigation" \
  "https://youtube.com/watch?v=investigation_pt1" \
  "https://youtube.com/watch?v=investigation_pt2" \
  --format all
```

### 3. Market Analysis Demo
```bash
# Process CNBC playlist for analyst demo
poetry run clipscribe process-collection \
  "CNBC Market Analysis" \
  "https://www.youtube.com/playlist?list=PLVbP054jv0Ko..." \
  --output-dir demo/cnbc_analysis \
  --skip-confirmation
```

## Understanding Costs

ClipScribe provides comprehensive intelligence extraction at industry-leading costs:

- **5-minute video**: ~$0.008
- **30-minute video**: ~$0.048  
- **1-hour video**: ~$0.096

Cost includes full entity extraction, relationship mapping, and knowledge graph generation.

## Configuration

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional optimization
CONFIDENCE_THRESHOLD=0.4  # v2.19.0 lowered for completeness
LANGUAGE_CONFIDENCE_THRESHOLD=0.3  # v2.19.0 less aggressive
ENABLE_LLM_VALIDATION=false  # Set true for critical applications
```

## Troubleshooting

### "Poor extraction quality" (Fixed in v2.19.0)
If you're seeing only 0-10 entities and 0 relationships:
```bash
# Update to v2.19.0
poetry update clipscribe
poetry run clipscribe --version  # Should show 2.19.0+
```

### "Memory issues with large collections"
```bash
# Process in smaller batches
poetry run clipscribe process-collection \
  "Large Collection" \
  "url1" "url2" "url3" \
  --batch-size 5
```

### "Slow processing"
```bash
# Enable caching for repeated processing
poetry run clipscribe process "URL" \
  --format json \
  --use-cache
```

## What's Next?

- Learn about all output formats in the [Output Formats Guide](OUTPUT_FORMATS.md)
- Explore advanced CLI options in the [CLI Reference](CLI_REFERENCE.md)
- Launch Mission Control web interface for visual exploration
- Check [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues

## Getting Help

- **Documentation**: Complete documentation in `docs/`
- **Mission Control**: Web interface at http://localhost:8501
- **GitHub Issues**: Report bugs or request features
- **Examples**: See `examples/` directory for working code

Remember: ClipScribe now targets **100% extraction completeness**, not arbitrary numbers! 🎯 