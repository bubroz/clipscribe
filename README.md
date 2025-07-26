# ClipScribe

**Video Intelligence Collection, Analysis, and Reporting**

*Transform video content into structured, searchable, and reportable intelligence*

[Features](#features) | [Installation](#installation) | [Quick Start](#quick-start) | [Use Cases](#use-cases) | [Documentation](#documentation)

---

ClipScribe extracts and analyzes structured data from video content through entity recognition, relationship mapping, and key insight identification. Built for students, researchers, analysts, content creators, and organizations requiring reliable video intelligence.

## v2.20.4 - FIXES & IMPROVEMENTS

**FIXES**: Fixed critical output pipeline issue where entities/relationships weren't saved to final files. All extraction features now work end-to-end.

**IMPROVEMENTS**: --use-pro FLAG**: Choose between cost-optimized (Gemini 2.5 Flash, ~$0.003/video) and quality-optimized (Gemini 2.5 Pro, ~$0.017/video) processing.

## Features

### Single Video Analysis
- **Entity Extraction**: People, Organizations, Locations, and Concepts
- **Relationship Mapping**: Relationships with evidence chains and context
- **Key Points**: Executive summaries
- **Multiple Formats**: JSON, CSV, GEXF, Markdown for any workflow
- **Quality Control**: Choose Flash ($0.003) vs Pro ($0.017) models based on needs

### Multi-Video Collections
- **Unified Intelligence**: Cross-video entity resolution and alias detection
- **Information Flows**: Track concept evolution across video series
- **Collection Analysis**: Synthesis reports spanning multiple videos
- **Knowledge Graphs**: Unified graphs for collections
- **Professional Reports**: Analyst-grade documentation

### Platform Support
- **Universal Access**: YouTube, TikTok, X, Vimeo + 1800 platforms via yt-dlp
- **Audio/Video Modes**: Optimized processing for different content types
- **Enterprise Scale**: Vertex AI integration for high-volume processing
- **Cost Control**: Budget limits and usage tracking

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
```

### 2. Install Dependencies
```bash
# Using Poetry (recommended for reproducible environments)
poetry install --with dev  # Includes dev tools for testing/extending

# Or using pip (for quick setup)
pip install -e .[dev]
```

### 3. Configure API Access
```bash
# Create .env file (git-ignored)
echo "GOOGLE_API_KEY=your_actual_key_here" > .env

# For Vertex AI (optional, for scale)
echo "VERTEX_AI_PROJECT=your-project-id" >> .env
echo "VERTEX_AI_LOCATION=us-central1" >> .env
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json" >> .env
```

### 4. Verify Installation
```bash
poetry run clipscribe --version
# Expected: ClipScribe v2.20.4

# Test imports for extension
poetry run python -c "from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever; print('Imports working')"
```

## Quick Start

### Single Video Analysis
```bash
# Standard quality processing (Gemini 2.5 Flash, ~$0.003/video)
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID"

# High quality processing (Gemini 2.5 Pro, ~$0.017/video)
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID" --use-pro

# Results saved to: output/YYYYMMDD_youtube_VIDEO_ID/
```

### Multi-Video Collection
```bash
# Process a 3-video series with unified intelligence
poetry run clipscribe process-collection "MySeries" \
  "URL1" "URL2" "URL3" \
  --collection-type series \
  --enhance-transcript \
  --clean-graph

# Results: Unified intelligence in output/collections/collection_TIMESTAMP_3/
```

### Python API
```python
import asyncio
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever

async def analyze_video():
    # Standard quality (Flash model)
    retriever = VideoIntelligenceRetriever()
    
    # Or high quality (Pro model)
    retriever = VideoIntelligenceRetriever(use_pro=True)
    
    result = await retriever.process_url("https://youtube.com/watch?v=...")
    
    if result:
        print(f"Title: {result.metadata.title}")
        print(f"Key Points: {len(result.key_points)}")
        print(f"Entities: {len(result.entities)}")
        print(f"Relationships: {len(result.relationships)}")
        print(f"Processing Cost: ${result.processing_cost:.4f}")

asyncio.run(analyze_video())
```

## Output Structure

### Single Video Output (v2.20.4 Validated)
```
output/YYYYMMDD_platform_videoID/
├── transcript.txt                 # Plain text transcript
├── transcript.json                # Complete analysis with metadata
├── entities.json                  # Entities with sources
├── entities.csv                   # Spreadsheet format
├── relationships.json             # Relationships with evidence
├── relationships.csv              # Spreadsheet format
├── knowledge_graph.gexf           # Gephi-compatible
├── report.md                      # Human-readable intelligence report
├── entity_sources.json            # Source attribution and normalization
├── chimera_format.json            # Integration format
└── manifest.json                  # File inventory and metadata
```

### Multi-Video Collection Output
```
output/collections/collection_TIMESTAMP_N/
├── collection_intelligence.json   # Unified multi-video analysis
├── unified_knowledge_graph.gexf   # Cross-video entity graph
├── information_flow_map.json      # Concept evolution flows
├── information_flow_summary.md    # Readable flow report
├── concept_flows/                 # Individual flow files
└── individual_videos/             # Per-video detailed outputs
```

## Quality vs Cost Options (NEW in v2.20.4)

### Standard Quality (Default)
- **Model**: Gemini 2.5 Flash
- **Cost**: approx $0.003/video (~$0.0035/minute)
- **Quality**: Good entity and relationship extraction
- **Use Case**: High-volume processing, basic intelligence

### High Quality (--use-pro)
- **Model**: Gemini 2.5 Pro  
- **Cost**: approx $0.017/video (~$0.02/minute)
- **Quality**: Superior entity and relationship extraction
- **Use Case**: Critical analysis, professional intelligence work

```bash
# Choose your quality level
clipscribe transcribe URL               # Standard (Flash)
clipscribe transcribe URL --use-pro     # High quality (Pro)
```

## Recent Fixes (v2.20.4)

### Fixes
- **Fixed**: Entities/relationships not saved to output files
- **Fixed**: Missing GEXF knowledge graph generation
- **Fixed**: Advanced extraction pipeline not running
- **Validated**: End-to-end processing with quality output

## Use Cases

### Research & Analysis
- **Competitive Intelligence**: Extract information from competitor content
- **Market Research**: Extract insights from industry presentations 
- **Academic Research**: Process lecture series with unified concept tracking
- **News Analysis**: Track entity relationships across multi-source coverage

### Professional Intelligence
- **Military/Defense**: Automate video content analysis with high-quality entity extraction
- **Policy Research**: Analyze hours of government content in minutes.
- **Financial Intelligence**: Extract insights from earnings calls and analysis
- **Technology Research**: Track product evolution with relationship mapping

### Content Management
- **Video Libraries**: Index and search collections with structured entities
- **Knowledge Management**: Extract actionable intelligence from video assets
- **Training Materials**: Process educational content with concept flow mapping
- **Documentation**: Convert video content into searchable knowledge bases

## Configuration

### Environment Variables
```env
# Required
GOOGLE_API_KEY="your_gemini_api_key_here"

# Optional - Processing Controls
CONFIDENCE_THRESHOLD=0.4
COST_WARNING_THRESHOLD=1.0
DAILY_BUDGET_LIMIT=5.0

# Optional - Output Settings
OUTPUT_DIR=output
LOG_LEVEL=INFO

# Optional - Vertex AI Enterprise
VERTEX_AI_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

### Processing Modes
```bash
# Quality options (NEW)
poetry run clipscribe transcribe URL                   # Standard quality
poetry run clipscribe transcribe URL --use-pro         # High quality

# Media processing modes
poetry run clipscribe transcribe URL --mode audio      # Audio-only (faster)
poetry run clipscribe transcribe URL --mode video      # Full video processing

# Enterprise scale
poetry run clipscribe transcribe URL --use-vertex-ai   # Vertex AI processing
```

## Performance Benchmarks (v2.20.4 Validated)

### Processing Speed
- **Single 5-min Video**: 1-2 minutes (Flash), 1.5-2.5 minutes (Pro)
- **3-Video Series**: 4-6 minutes (Flash), 5-8 minutes (Pro)
- **CLI Startup**: 0.4s
- **Test Coverage**: 80%+ for core paths

### Cost Efficiency
- **Flash (--default)**: $0.0122 for 3.5-min video
- **Pro (--use-pro)**: $0.0167 for 5-min video
- **Per Minute**: $0.0035 (Flash) vs $0.02 (Pro)

## Documentation

### User Guides
- [Getting Started](docs/GETTING_STARTED.md) - Setup and first analysis
- [CLI Reference](docs/CLI_REFERENCE.md) - Complete command documentation
- [Output Formats](docs/OUTPUT_FORMATS.md) - All export format details
- [Platform Support](docs/PLATFORMS.md) - Supported video platforms

### Technical Documentation
- [Output Standards](docs/OUTPUT_FILE_STANDARDS.md) - Quality benchmarks and validation
- [Roadmap](docs/ROADMAP.md) - Architecture decisions and future development
- [Development](docs/DEVELOPMENT.md) - Contributing and development setup
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Requirements

- **Python**: 3.12 recommended
- **API Access**: Google API key with Gemini access enabled
- **System**: FFmpeg installed for video/audio processing
- **Storage**: ~50-200KB per video for complete output files
- **Memory**: 4GB+ recommended for multi-video collections

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**ClipScribe v2.20.4 - Professional Video Intelligence with Quality Control**

*Choose your balance: Standard quality at $0.003/video or Pro quality at $0.017/video*

## Contributing & Extending

ClipScribe is designed for extension:

### Custom Extractors
```python
from clipscribe.extractors.hybrid_extractor import HybridExtractor

class CustomExtractor(HybridExtractor):
    def extract_entities(self, text: str) -> List[Dict]:
        # Add your ML logic here
        return super().extract_entities(text) + [{'type': 'CUSTOM', 'text': 'My Entity'}]

# Use in pipeline
retriever = VideoIntelligenceRetriever(extractor=CustomExtractor())
```

### Running Tests
```bash
poetry run pytest --cov=clipscribe  # 80%+ coverage
```

### Development Setup
- See docs/DEVELOPMENT.md for full guidelines
- Use poetry for dependency management
- Follow rules in .cursor/rules/ for patterns

See GitHub issues for open tasks or submit PRs!
