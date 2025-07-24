# ClipScribe v2.20.0

## AI-Powered Video Intelligence for Professional Analysis

<p align="center">
  <strong>🎯 Professional intelligence extraction from 1800+ video platforms</strong>
</p>

<p align="center">
  <em>All 6 core components complete • Intelligence analyst standards • $0.015-0.030 per video</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#validation">Validation</a> •
  <a href="#documentation">Documentation</a>
</p>

---

ClipScribe transforms video content into structured, searchable intelligence through professional-grade extraction of entities, relationships, and key insights. Built for researchers, analysts, and organizations that need reliable video intelligence at scale.

## 🏆 **v2.20.0 - ALL CORE COMPONENTS COMPLETE!**

**Major Milestone**: Professional intelligence-grade extraction achieved with comprehensive validation on military training content.

### ✅ **Proven Performance (Validated on 3-Video Military Series)**
- **Key Points**: 31-34 intelligence briefing-style points per video  
- **Entities**: 25-44 entities with specific military roles and classifications
- **Relationships**: 64-89 relationships with evidence chains and direct quotes
- **Processing Cost**: $0.0167-0.0263 per video (~$0.0035/minute)
- **Processing Speed**: 2-4 minutes per video for complete intelligence extraction
- **Quality Standard**: Professional intelligence analyst benchmarks achieved

### 🎯 **Core Capabilities**
- **Professional Key Points Extraction**: Intelligence briefing-style summaries with strategic and tactical details
- **Enhanced Entity Classification**: Military units, person roles, organizations properly identified
- **Evidence-Based Relationships**: Direct quotes, timestamps, and supporting evidence for all connections
- **Multi-Platform Support**: YouTube, TikTok, Twitter/X, and 1800+ platforms via yt-dlp
- **Cost Leadership**: $0.002-0.006 per minute processing cost
- **Multiple Export Formats**: JSON, CSV, GEXF, Markdown reports, knowledge graphs

## ✨ **Key Features**

### 🧠 **Intelligence Extraction**
- **Key Points**: 25-35 actionable insights per video in intelligence briefing format
- **Entity Recognition**: Military roles, organizations, locations, events with proper classification
- **Relationship Mapping**: Evidence-backed relationships with direct quotes and context
- **Cross-Video Analysis**: Track entities and concepts across video series
- **Quality Standards**: Comprehensive output validation with professional benchmarks

### ⚡ **Performance & Reliability**
- **Fast Processing**: 2-4 minutes per video for complete analysis
- **Cost Efficient**: Industry-leading $0.015-0.030 per video processing cost
- **Reliable Extraction**: Confidence-free architecture focusing on quality over metrics
- **Scalable Processing**: Smart concurrency handling for single videos to large collections
- **Enterprise Ready**: Vertex AI support for large-scale processing

### 📊 **Export & Integration**
- **12 File Formats**: Complete analysis exported in multiple formats per video
- **Knowledge Graphs**: GEXF format compatible with Gephi and network analysis tools
- **Structured Data**: JSON and CSV formats for programmatic access
- **Human Reports**: Markdown intelligence reports for direct consumption
- **API Integration**: Python API for custom workflows and integrations

## 📋 **Requirements**

- **Python**: 3.11+ (3.12 recommended)
- **API Access**: Google API key with Gemini access enabled
- **System**: FFmpeg installed for video/audio processing
- **Storage**: ~50-200KB per video for complete output files

## 🚀 **Installation**

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

## ⚡ **Quick Start**

### Single Video Analysis
```bash
# Process a YouTube video
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID"

# Results saved to: output/YYYYMMDD_youtube_VIDEO_ID/
```

### Batch Processing
```bash
# Process multiple videos
poetry run clipscribe transcribe "URL1" "URL2" "URL3"

# Process from file
echo "URL1\nURL2\nURL3" > urls.txt
poetry run python examples/pbs_fast_batch.py --urls urls.txt
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

## 📁 **Output Structure**

Each processed video generates a complete intelligence package:

```
output/YYYYMMDD_platform_videoID/
├── transcript.txt                 # Plain text transcript
├── transcript.json               # Complete analysis with metadata
├── entities.json                 # Entity details with sources
├── entities.csv                  # Spreadsheet format
├── relationships.json            # Relationships with evidence chains
├── relationships.csv            # Spreadsheet format
├── knowledge_graph.json         # Graph structure
├── knowledge_graph.gexf         # Gephi-compatible format
├── report.md                    # Human-readable intelligence report
├── facts.txt                    # Key points in plain text
├── chimera_format.json          # Integration format
└── manifest.json                # File inventory and metadata
```

## 🎯 **Use Cases**

### **Research & Analysis**
- **Competitive Intelligence**: Analyze competitor content and strategies
- **Market Research**: Extract insights from industry videos and presentations
- **Academic Research**: Process lecture series and educational content
- **News Analysis**: Track entities and relationships across news coverage

### **Professional Intelligence**
- **Military Analysis**: Process training content and operational briefings
- **Policy Research**: Analyze government hearings and policy discussions
- **Financial Intelligence**: Extract insights from earnings calls and market analysis
- **Technology Research**: Process technical presentations and product demos

### **Content Management**
- **Video Libraries**: Index and search large video collections
- **Knowledge Management**: Extract and organize information from video assets
- **Documentation**: Convert video content into structured documentation
- **Training Materials**: Process educational content for knowledge extraction

## 📊 **Quality Standards**

ClipScribe v2.20.0 meets professional intelligence analyst standards:

### **Key Points Quality**
- ✅ 25-35 points per video in intelligence briefing format
- ✅ Specific, actionable information (not generic summaries)
- ✅ Strategic and tactical details included
- ✅ Professional intelligence report style

### **Entity Classification**
- ✅ Military units correctly classified as ORGANIZATION (not PRODUCT)
- ✅ Person entities include roles, backgrounds, experience descriptors
- ✅ Specific names and titles extracted (not just "Speaker")
- ✅ 25-50 total entities depending on content density

### **Relationship Quality**
- ✅ 60-90 relationships with specific predicates (not generic "related_to")
- ✅ Evidence chains with direct quotes and timestamps
- ✅ Clear subject-predicate-object structure
- ✅ Supporting evidence for key relationships

See [docs/OUTPUT_FILE_STANDARDS.md](docs/OUTPUT_FILE_STANDARDS.md) for complete quality benchmarks.

## 🔧 **Configuration**

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

## 📈 **Performance Benchmarks**

### **Processing Speed**
- **Single Video**: 2-4 minutes for complete analysis
- **3-Video Series**: 5-7 minutes with parallel processing
- **Large Collections**: Smart concurrency prevents rate limiting

### **Cost Efficiency**
- **Base Processing**: $0.015-0.030 per video
- **Cost Per Minute**: ~$0.0035/minute of video content
- **Validated Costs**: $0.0611 for complete 3-video series (18 minutes total)

### **Quality Metrics**
- **Key Points**: 92 total across 3 military training videos
- **Entities**: 113 total entities with professional classification
- **Relationships**: 236 evidence-backed relationships
- **Output Files**: 12 formats per video with complete metadata

## 🧪 **Testing & Validation**

ClipScribe includes comprehensive testing for reliability:

```bash
# Run full test suite
poetry run pytest

# Run specific test categories
poetry run pytest tests/unit/
poetry run pytest tests/integration/

# Validate against test video collection
poetry run python examples/test_validation.py
```

### **Test Categories**
- **Unit Tests**: Core component functionality
- **Integration Tests**: End-to-end processing workflows  
- **Edge Cases**: Error handling and unusual content
- **Performance Tests**: Speed and cost validation

## 📚 **Documentation**

### **User Guides**
- [Getting Started](docs/GETTING_STARTED.md) - Setup and first analysis
- [CLI Reference](docs/CLI_REFERENCE.md) - Complete command documentation
- [Output Formats](docs/OUTPUT_FORMATS.md) - All export format details
- [Platform Support](docs/PLATFORMS.md) - Supported video platforms

### **Technical Documentation**
- [Output Standards](docs/OUTPUT_FILE_STANDARDS.md) - Quality benchmarks and validation
- [Roadmap](docs/ROADMAP.md) - Future development plans
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Development](docs/DEVELOPMENT.md) - Contributing and development setup

## 🚀 **Roadmap**

### **Completed v2.20.0**
- ✅ Professional key points extraction
- ✅ Enhanced entity classification  
- ✅ Evidence-based relationships
- ✅ Confidence-free architecture
- ✅ Comprehensive output standards

### **Next: Temporal Intelligence (Q4 2025)**
- 🕐 Precise timestamp extraction with OpenAI Whisper
- 📊 TimelineJS integration for interactive visualizations
- 🎯 Entity temporal context and timeline mapping

See [docs/ROADMAP.md](docs/ROADMAP.md) for complete development plan.

## 🤝 **Contributing**

We welcome contributions! Please see:
- [Contributing Guidelines](CONTRIBUTING.md)
- [Development Setup](docs/DEVELOPMENT.md)
- [Code Standards](docs/DEVELOPMENT.md#code-standards)

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for universal video platform support
- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI intelligence extraction  
- [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/) for CLI excellence

---

<p align="center">
  <strong>ClipScribe v2.20.0 - Professional Video Intelligence Complete</strong>
</p>
