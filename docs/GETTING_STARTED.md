# Getting Started with ClipScribe

*Last Updated: August 11, 2025*
*Related: [CLI Reference](CLI_REFERENCE.md) | [Output Formats](OUTPUT_FORMATS.md)*

##  What's New: v2.29.3 — Stability, Chunked Uploads, and Clean CLI Groups

**ClipScribe v2.29.7** highlights:
- **Pro by default, Flash available**: Gemini 2.5 Pro for complex analysis; `--use-flash` for standard/high-volume tasks.
- **Resilience**: Chunked MP3 uploads, throttled concurrency, and configurable timeouts for long videos.
- **Exports**: GEXF export upgraded (stable IDs, idtype, node attrs, edge labels, viz colors).
- **CLI**: Structured command groups (`process`, `collection`, `research`, `utils`).

## Prerequisites

- Python 3.11+ (3.12+ for optimal performance)
- Poetry ([install](https://python-poetry.org/docs/#installation)) for dependency management
- Google API key ([free tier](https://makersuite.google.com/app/apikey)) or Vertex AI ADC (enterprise)
- FFmpeg (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Ubuntu)

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
# Should output: ClipScribe, version 2.29.7

poetry run clipscribe --help
```

### Python API (For Data Scientists)

```python
import asyncio
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever

async def analyze_video(url: str, use_flash: bool = False):
    retriever = VideoIntelligenceRetriever(use_pro=not use_flash)
    result = await retriever.process_url(url)
    
    # Access structured data
    print(f"Entities: {len(result.entities)}")
    print(f"Relationships: {len(result.relationships)}")
    print(f"Cost: ${result.processing_cost:.4f}")
    
    # Custom analysis example
    people = [e for e in result.entities if e.type == 'PERSON']
    print(f"People mentioned: {len(people)}")

asyncio.run(analyze_video("https://youtube.com/watch?v=..."))
```

## Basic Usage

### Process a Single Video (Pro by Default)

```bash
# High quality (Gemini 2.5 Pro, DEFAULT)
poetry run clipscribe --debug process video "https://www.youtube.com/watch?v=7sWj6D2i4eU"

# Optional: Faster, standard quality (Gemini 2.5 Flash) 
poetry run clipscribe --debug process video "https://www.youtube.com/watch?v=7sWj6D2i4eU" --use-flash

# With additional processing options
poetry run clipscribe process video "https://vimeo.com/123456789" \
  --enhance-transcript \
  --clean-graph \
  --output-dir analysis/
```

### Validated Output (v2.22.2)

After processing, you'll get these verified working files:
```
output/YYYYMMDD_youtube_videoID/
├── entities.json          #  24-59 entities saved
├── relationships.json     #  53+ relationships with evidence
├── knowledge_graph.gexf   #  60 nodes, 53 edges for Gephi
├── transcript.json        #  Complete analysis
├── report.md             #  Human-readable report
└── 6+ more formats...    #  All working
```

### Process Multiple Videos (Collection Analysis)

```bash
# Process a collection of videos as a series
poetry run clipscribe collection series \
  "https://youtube.com/watch?v=video1" \
  "https://youtube.com/watch?v=video2"

# Process a custom collection with a name
poetry run clipscribe collection custom \
  "My Research Collection" \
  "https://youtube.com/watch?v=video3" \
  "https://youtube.com/watch?v=video4"

# Process a playlist automatically
poetry run clipscribe collection custom \
  "CNBC Market Analysis" \
  "https://www.youtube.com/playlist?list=PLVbP054jv0Ko..."
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
poetry run clipscribe process video "https://youtube.com/watch?v=..." \
  --format all \
  --clean-graph
```

### Launch Mission Control

```bash
# Launch the comprehensive web interface
poetry run streamlit run streamlit_app/ClipScribe_Mission_Control.py
```

Access features:
-  Video processing monitor
-  Entity and relationship visualization
-  Collection management
-  Information flow analysis
-  Export and integration tools 

## Understanding Entity & Relationship Extraction

ClipScribe's extraction targets **100% completeness** - extracting ALL entities and relationships from videos:

- **Entities**: People, organizations, locations, events, products, etc.
- **Relationships**: Who interacts with whom, what happened where, etc.
- **Evidence**: Direct quotes and timestamps backing every claim
- **Knowledge Graphs**: Visual network of all connections

### What's Improved:
- No longer filters out 70% of valid entities (quality filter was too aggressive)
- Actually uses all 50+ Gemini-extracted relationships (they were being ignored!)
- Dynamic confidence scoring based on context (not hardcoded 0.85)
- Results: 16+ entities and 52+ relationships per video (was 0-10 entities, 0 relationships)

## Common Use Cases

### 1. News Analysis
```bash
poetry run clipscribe process video "https://youtube.com/watch?v=news_video" \
  --format all \
  --clean-graph \
  -o news-analysis/
```

### 2. Multi-Video Investigation
```bash
poetry run clipscribe collection series \
  "https://youtube.com/watch?v=investigation_pt1" \
  "https://youtube.com/watch?v=investigation_pt2" \
  --format all
```

### 3. Market Analysis Demo
```bash
# Process CNBC playlist for analyst demo
poetry run clipscribe collection custom \
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

### "API Key Not Found"
- Confirm .env file exists and is loaded (or export GOOGLE_API_KEY)
- Test: `poetry run python -c "import os; print(os.getenv('GOOGLE_API_KEY'))"`

### "Import Errors"
- Run `poetry install --with dev`
- Check Python version: `poetry run python --version`

### "Low Entity Counts"
- Use --use-pro for better quality (this is now the default)
- Update to v2.20.4+: `poetry update clipscribe`

Full guide: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

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

Remember: ClipScribe now targets **100% extraction completeness**, not arbitrary numbers!  

## Enterprise Use
For large-scale deployment, see docs/advanced/deployment/DEPLOYMENT_GUIDE.md


