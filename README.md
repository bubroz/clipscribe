# ClipScribe

**AI-Powered Video Intelligence for Professional Analysis**

*Transform video content into structured, searchable intelligence • $0.002-0.0035 per minute*

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Use Cases](#use-cases) • [Documentation](#documentation)

---

ClipScribe extracts structured intelligence from video content through professional-grade entity recognition, relationship mapping, and key insight identification. Built for researchers, analysts, and organizations requiring reliable video intelligence at scale.

## What's New in v2.20.0

**Multi-Video Intelligence**: Complete collection processing with unified entity resolution, cross-video relationships, and information flow mapping.

### Validated Performance
- **Individual Videos**: 39-46 entities, 80-94 relationships per video
- **Multi-Video Intelligence**: 21 unified entities, 24 cross-video relationships  
- **Knowledge Graphs**: 281-edge unified graphs with concept flow mapping
- **Processing Cost**: $0.0611 total for 3-video series (~$0.02/video)
- **Processing Speed**: 5-7 minutes for complete multi-video analysis
- **Output Quality**: Intelligence analyst standards

## Features

### Single Video Analysis
- **Entity Extraction**: People, organizations, locations, concepts with confidence scores
- **Relationship Mapping**: 80+ relationships with evidence chains and timestamps
- **Key Points**: Intelligence briefing-style summaries (25-35 points per video)
- **Multiple Formats**: JSON, CSV, GEXF, Markdown for any workflow
- **Cost Optimized**: $0.002-0.0035 per minute via intelligent API routing

### Multi-Video Collections (NEW!)
- **Unified Intelligence**: Cross-video entity resolution and alias detection
- **Information Flows**: Track concept evolution across video series
- **Collection Analysis**: Synthesis reports spanning multiple videos
- **Knowledge Graphs**: Unified graphs with 200+ edges for collections
- **Professional Reports**: Intelligence analyst-grade documentation

### Platform Support
- **Universal Access**: YouTube, TikTok, Twitter/X, Vimeo + 1800 platforms via yt-dlp
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
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -e .
```

### 3. Configure API Access
```bash
# Create environment file
echo "GOOGLE_API_KEY=your_actual_key_here" > .env

# Optional: Configure Vertex AI for enterprise scale
echo "VERTEX_AI_PROJECT=your-project-id" >> .env
echo "VERTEX_AI_LOCATION=us-central1" >> .env
```

### 4. Verify Installation
```bash
poetry run clipscribe --version
# Should output: ClipScribe v2.20.0
```

## Quick Start

### Single Video Analysis
```bash
# Process a YouTube video
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID"

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
    retriever = VideoIntelligenceRetriever()
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

### Single Video Output
```
output/YYYYMMDD_platform_videoID/
├── transcript.txt                 # Plain text transcript
├── transcript.json                # Complete analysis with metadata
├── entities.json                  # Entity details with sources
├── entities.csv                   # Spreadsheet format
├── relationships.json             # Relationships with evidence chains
├── relationships.csv              # Spreadsheet format
├── knowledge_graph.json           # Graph structure
├── knowledge_graph.gexf           # Gephi-compatible format
├── report.md                      # Human-readable intelligence report
├── facts.txt                      # Key points in plain text
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

## Use Cases

### Research & Analysis
- **Competitive Intelligence**: Analyze competitor content strategies across video series
- **Market Research**: Extract insights from industry presentations and earnings calls
- **Academic Research**: Process lecture series with unified concept tracking
- **News Analysis**: Track entity relationships across multi-source coverage

### Professional Intelligence
- **Military/Defense**: Process training series with unified doctrine extraction
- **Policy Research**: Analyze government hearings with cross-session entity tracking
- **Financial Intelligence**: Extract insights from quarterly calls and market analysis
- **Technology Research**: Track product evolution across presentation series

### Content Management
- **Video Libraries**: Index and search large collections with unified entities
- **Knowledge Management**: Extract structured information from video assets
- **Training Materials**: Process educational series with concept flow mapping
- **Documentation**: Convert video content into searchable knowledge bases

## Quality Standards

ClipScribe v2.20.0 meets professional intelligence analyst standards:

### Key Points Quality
- 25-35 points per video in intelligence briefing format
- Specific, actionable information (not generic summaries)
- Strategic and tactical details included
- Professional intelligence report style

### Entity Classification
- Military units correctly classified as ORGANIZATION (not PRODUCT)
- Person entities include roles, backgrounds, experience descriptors
- Specific names and titles extracted (not just "Speaker")
- 25-50 total entities depending on content density

### Relationship Quality
- 60-90 relationships with specific predicates (not generic "related_to")
- Evidence chains with direct quotes and timestamps
- Clear subject-predicate-object structure
- Supporting evidence for key relationships

### Multi-Video Intelligence
- Entity unification across videos with alias resolution
- Cross-video relationship detection and validation
- Information flow mapping with concept evolution tracking
- Unified knowledge graphs with 200+ edges for 3-video collections

## Configuration

### Environment Variables
```env
# Required
GOOGLE_API_KEY="your_gemini_api_key_here"

# Optional - Output Settings
OUTPUT_DIR=output
LOG_LEVEL=INFO

# Optional - Vertex AI Enterprise
VERTEX_AI_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Optional - Processing Controls
CONFIDENCE_THRESHOLD=0.4
COST_WARNING_THRESHOLD=1.0
DAILY_BUDGET_LIMIT=5.0
```

### Processing Modes
```bash
# Audio mode (default) - cost optimized
poetry run clipscribe transcribe URL --mode audio

# Video mode - enhanced visual intelligence
poetry run clipscribe transcribe URL --mode video

# Vertex AI - enterprise scale
poetry run clipscribe transcribe URL --use-vertex-ai
```

## Performance Benchmarks

### Processing Speed
- **Single Video**: 2-4 minutes for complete analysis
- **3-Video Series**: 5-7 minutes with unified intelligence
- **Large Collections**: Smart concurrency prevents rate limiting

### Cost Efficiency
- **Per Video**: $0.015-0.030 for complete analysis
- **Per Minute**: ~$0.0035/minute of video content  
- **Multi-Video**: $0.0611 for 3-video series (cost sharing via unification)
- **Enterprise**: Vertex AI options for volume pricing

### Quality Metrics (Validated)
- **Entities**: 25-46 per video with professional classification
- **Relationships**: 80-94 per video with evidence chains
- **Multi-Video**: 21 unified entities, 24 cross-video relationships
- **Output Files**: 12+ formats per video with complete metadata

## Documentation

### User Guides
- [Getting Started](docs/GETTING_STARTED.md) - Setup and first analysis
- [CLI Reference](docs/CLI_REFERENCE.md) - Complete command documentation
- [Output Formats](docs/OUTPUT_FORMATS.md) - All export format details
- [Platform Support](docs/PLATFORMS.md) - Supported video platforms

### Technical Documentation
- [Output Standards](docs/OUTPUT_FILE_STANDARDS.md) - Quality benchmarks and validation
- [Multi-Video Intelligence](docs/advanced/architecture/MULTI_VIDEO_INTELLIGENCE_ARCHITECTURE.md) - Collection processing architecture
- [Roadmap](docs/ROADMAP.md) - Future development plans
- [Development](docs/DEVELOPMENT.md) - Contributing and development setup

## Why ClipScribe?

**Intelligence Analysts**: Extract actionable intelligence faster than manual review  
**Researchers**: Process video collections with unified entity tracking  
**Organizations**: Scale video intelligence at enterprise level with cost control  
**Developers**: Python API with structured outputs for custom workflows

## Requirements

- **Python**: 3.11+ (3.12 recommended)
- **API Access**: Google API key with Gemini access enabled
- **System**: FFmpeg installed for video/audio processing
- **Storage**: ~50-200KB per video for complete output files
- **Memory**: 4GB+ recommended for multi-video collections

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**ClipScribe v2.20.0 - Professional Video Intelligence Complete**
