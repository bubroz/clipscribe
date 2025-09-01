# ClipScribe

**Video Intelligence Collection, Analysis, and Reporting**

![CI](https://img.shields.io/github/actions/workflow/status/bubroz/clipscribe/ci.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)
![Version](https://img.shields.io/badge/version-v2.44.0-informational)
![Status](https://img.shields.io/badge/status-private%20alpha-yellow)

*Transform video content into structured, searchable, and reportable intelligence*

[Features](#features) | [Installation](#installation) | [Quick Start](#quick-start) | [Documentation](#documentation) | [Beta Access](#beta-access)

---

ClipScribe extracts and analyzes structured data from video content through entity recognition, relationship mapping, and key insight identification. Built for researchers, analysts, and organizations requiring reliable video intelligence.

## ⚠️ Current Status: Private Alpha

ClipScribe is currently in private alpha testing. The service is not yet available for public use.

- **Worker Service**: Under development
- **Beta Timeline**: Private alpha (Month 1-2) → Closed beta (Month 3-4) → Public launch (Month 6)
- **Early Access**: Contact zforristall@gmail.com for beta access consideration

## v2.44.0 - Infrastructure Ready for Beta

**🚧 PRIVATE ALPHA DEPLOYMENT**: Successfully deployed API and web services to Google Cloud Run, worker service in development.

**🎯 KEY ACHIEVEMENTS**:
- **Infrastructure Deployed**: API and web services are deployed but access-restricted
- **Worker Development**: Hybrid Cloud Run + Compute Engine architecture in progress
- **Monitoring & Retry**: Comprehensive error handling and monitoring systems implemented
- **Cost Controls**: Emergency stop mechanisms and budget limits in place

**🔧 PRODUCTION CAPABILITIES**:
- Complete video intelligence extraction and analysis
- Multi-platform video processing (1800+ platforms via yt-dlp)
- Entity extraction, relationship mapping, and knowledge graph generation
- Enterprise-grade reliability with comprehensive error handling
- Advanced entity normalization and deduplication
- Cost-optimized transcription with Gemini 2.5 Pro/Flash

**📊 CURRENT TEST STATUS**: Exceptional coverage expansion with 13/15 core modules at 80%+ coverage. Systematic approach achieving 83-99% coverage on critical infrastructure.

**🧪 TEST EXCELLENCE**: High unit test pass rate with comprehensive edge case coverage and **enterprise-grade test isolation** for all core functionality. 99% coverage on 4 critical modules, 90%+ on ML infrastructure.

**💰 COST-OPTIMIZED**: $0.002/minute actual processing cost with intelligent model selection and sophisticated cost optimization algorithms.

**🏗️ ROBUST ARCHITECTURE**: Modular design with professional CLI, comprehensive error handling, and complete API isolation for reliable testing and deployment.

## Features

### Single Video Analysis
- **Large Video Support**: Process videos of any length through automatic chunking and smart transcribe-global analyze architecture.
- **Resilient Processing**: Enterprise-grade error handling with comprehensive retry logic and rate limiting.
- **Entity Extraction**: Advanced entity recognition with 16+ entity types and confidence scoring.
- **Relationship Mapping**: Evidence-based relationships with direct quotes and timestamps.
- **Knowledge Graphs**: Automated knowledge graph generation with Gephi compatibility.
- **Key Points**: AI-generated executive summaries and insights.
- **Multiple Formats**: JSON, CSV, GEXF, Markdown, Chimera formats for any workflow.
- **Cost Optimization**: $0.002/minute actual processing cost with intelligent model selection.

### Multi-Video Collections
- **Series Detection**: Automatic detection and processing of video series from same creator
- **Cross-Video Analysis**: Unified intelligence with entity resolution across multiple videos
- **Temporal Tracking**: Track concept evolution and information flows across video sequences
- **Collection Synthesis**: Automated synthesis reports spanning multiple videos
- **Unified Knowledge Graphs**: Combined knowledge graphs with relationship preservation
- **Professional Reports**: Analyst-grade documentation with comprehensive metadata

### Platform Support
- **Universal Access**: YouTube, TikTok, X, Vimeo + 1800 platforms via yt-dlp
- **Audio/Video Modes**: Optimized processing for different content types
- **Enterprise Scale**: Vertex AI integration for high-volume processing
- **Cost Control**: Budget limits and usage tracking

### Quality Assurance & Testing
- **Complete API Isolation**: All core functionality tested without external dependencies
- **Enterprise Test Coverage**: 13/15 core modules at 80%+ coverage, 4 modules at 90-99%
- **High Integration Test Pass Rate**: Comprehensive integration tests with complete isolation
- **Production-Ready Reliability**: Comprehensive error handling and edge case coverage
- **CI/CD Ready**: No external API dependencies for continuous integration
- **Advanced Entity Processing**: 99% coverage with sophisticated normalization and deduplication

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
```

### 2. Install Dependencies
```bash
# Poetry (required) - Install only what you need
poetry install --with dev  # Core + dev tools (~500MB)

# Optional: Add ML features (spaCy, transformers, torch)
poetry install -E ml --with dev

# Optional: Add enterprise features (GCP services)
poetry install -E enterprise --with dev

# Optional: Add API server (FastAPI, Redis)
poetry install -E api --with dev

# Install everything
poetry install --extras all --with dev
```

### Optional Dependencies Overview

ClipScribe uses an intelligent optional dependency system to minimize installation size and memory usage:

| Feature Set | Dependencies | Size | Use Case |
|-------------|--------------|------|----------|
| **Core** | Basic processing | ~500MB | CLI usage |
| **+ ML** | `spacy`, `transformers`, `torch` | +2GB | Entity extraction |
| **+ Enterprise** | `google-cloud-*` | +200MB | Cloud services |
| **+ API** | `fastapi`, `redis`, `rq` | +300MB | Server mode |
| **+ Web** | `streamlit` | +500MB | Web interface |
| **All** | Everything | ~4GB | Full features |

**Benefits:**
- Install only what you need
- Faster startup times
- Reduced memory footprint
- Smaller Docker images
- Graceful fallbacks if features aren't available

### Docker Deployment (NEW)

ClipScribe includes an optimized multi-stage `Dockerfile` for production deployments:

```bash
# Build the API server image
docker build --target api -t clipscribe-api .

# Build the web interface image
docker build --target web -t clipscribe-web .

# For local development, you can use docker-compose
docker-compose up --build
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
# Expected: ClipScribe v2.44.0

# Test imports for extension
poetry run python -c "from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever; print('Imports working')"
```

## Quick Start

### Single Video Analysis
```bash
# High quality processing (Gemini 2.5 Pro, DEFAULT)
poetry run clipscribe process video "https://www.youtube.com/watch?v=VIDEO_ID"

# Optional: Faster, standard quality processing (Gemini 2.5 Flash)
poetry run clipscribe process video "https://www.youtube.com/watch?v=VIDEO_ID" --use-flash

# Results saved to: output/YYYYMMDD_youtube_VIDEO_ID/
```

### Multi-Video Collection
```bash
# Process a 3-video series with unified intelligence
poetry run clipscribe collection series "URL1" "URL2" "URL3"

# Results saved to: output/collections/
```

### Python API
```python
import asyncio
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever

async def analyze_video():
    # High quality (Pro model, DEFAULT)
    retriever = VideoIntelligenceRetriever()
    
    # Or standard quality (Flash model)
    retriever = VideoIntelligenceRetriever(use_pro=False)
    
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

## Quality vs Cost Options (NEW in v2.21.0)

### High Quality (Default)
- **Model**: Gemini 2.5 Pro
- **Cost**: approx $0.017/video (~$0.02/minute)
- **Quality**: Superior entity and relationship extraction for professional intelligence work.
- **Use Case**: Critical analysis, academic research, professional intelligence.

### Standard Quality (--use-flash)
- **Model**: Gemini 2.5 Flash  
- **Cost**: approx $0.003/video (~$0.0035/minute)
- **Quality**: Good entity and relationship extraction, approximately 15-30% faster.
- **Use Case**: High-volume processing, budget-conscious applications, or when speed is the priority.

```bash
# Choose your quality level
clipscribe process video URL               # High quality (Pro, Default)
clipscribe process video URL --use-flash     # Standard quality (Flash)
```

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
poetry run clipscribe process video URL                   # High quality (Pro, Default)
poetry run clipscribe process video URL --use-flash         # Standard quality (Flash)

# Media processing modes
poetry run clipscribe process video URL --mode audio      # Audio-only (faster)
poetry run clipscribe process video URL --mode video      # Full video processing

# Enterprise scale
# Vertex AI is supported when configured (Settings.use_vertex_ai or environment variables).
```

## Performance Benchmarks (v2.44.0 Current Status)

### Processing Speed
- **Single 5-min Video**: 1-2 minutes (Flash), 1.5-2.5 minutes (Pro)
- **CLI Startup**: 0.4s (optimized with lazy loading)
- **Working Commands**: Core CLI commands stable with enterprise-grade validation
- **Test Coverage**: 83-99% coverage on critical infrastructure modules, 13/15 core modules at 80%+

### Test Excellence
- **Unit Tests**: 400+ tests passing with comprehensive edge case coverage
- **Integration Tests**: High pass rate with complete API isolation
- **Enterprise Isolation**: All external dependencies mocked for reliable CI/CD

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

## Beta Access

ClipScribe is following a phased release strategy:

### Private Alpha (Current Phase)
- Limited to 5-10 trusted testers
- Direct invitation only
- Focus on core functionality validation

### Closed Beta (Coming Soon)
- 20-50 selected users
- Application-based access
- Token-based authentication
- Free usage with feedback requirements

### Planned Pricing (Post-Launch)
- Student/Educator: $39/month (40 videos, <90 min each)
- Researcher: $79/month (100 videos, <2 hours each)
- Analyst: $199/month (200 videos, <3 hours each)
- Enterprise: $999/month (1000 videos, unlimited length)
- Pay-per-video: $0.99-$14.99 based on length

To request beta access, email zforristall@gmail.com with:
- Your use case and research interests
- Expected video processing volume
- Preferred video platforms

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**ClipScribe v2.44.0 - Private Alpha**

*Gemini 2.5 Pro is the default for the best results, with an optional `--use-flash` flag for speed.*

**Current Status**: Infrastructure deployed, worker service under development. Not yet available for public use.

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
poetry run pytest --cov=clipscribe
```

### Development Setup
- See docs/DEVELOPMENT.md for full guidelines
- Use poetry for dependency management
- Follow rules in .cursor/rules/ for patterns

See GitHub issues for open tasks or submit PRs!
