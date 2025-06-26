# ClipScribe Development Guide

*Last Updated: December 26, 2024 - v2.12.0*

## Overview

ClipScribe is a powerful, AI-powered video intelligence tool that supports **1800+ video platforms** through yt-dlp integration. It uses Google's Gemini 1.5 Flash for native audio/video processing, achieving significant cost reduction and speed improvement over traditional speech-to-text APIs.

## Key Features

- **Universal Platform Support**: Works with YouTube, Twitter/X, TikTok, Instagram, Vimeo, and 1800+ other sites.
- **AI-Powered Transcription**: Uses Gemini 1.5 Flash for high-accuracy transcription from audio or video.
- **Video Intelligence**: Extracts not just transcripts but structured knowledge including entities, relationships, key points, and summaries.
- **Visual Analysis**: Processes video frames to capture on-screen text, slides, and other visual elements (`--mode video`).
- **Batch Processing**: The `research` command allows concurrent processing of multiple videos from a search query.
- **Cost-Effective**: ~$0.002/minute for audio, with clear cost tracking.
- **Multiple Output Formats**: Generates 10+ formats including JSON, TXT, CSV, Excel, GEXF (for Gephi), and interactive Markdown reports.
- **Knowledge Graphs**: Automatically builds and visualizes knowledge graphs from extracted relationships.
- **Advanced Visualizations**: Interactive Plotly charts for comprehensive analysis (v2.12.0).
- **Performance Dashboards**: Real-time system monitoring and analytics (v2.12.0).

## Architecture

```
src/clipscribe/
├── commands/           # CLI implementation (Click)
│   └── cli.py
├── config/             # Configuration (Pydantic)
│   └── settings.py
├── extractors/         # Knowledge extraction (SpaCy, GLiNER, REBEL)
│   ├── model_manager.py        # NEW: Singleton model caching
│   ├── hybrid_extractor.py
│   └── advanced_hybrid_extractor.py
├── models.py           # Core data structures (Pydantic)
├── retrievers/         # Media retrieval and processing
│   ├── universal_video_client.py
│   ├── transcriber.py
│   └── video_retriever.py
└── utils/              # Shared utilities
    ├── filename.py
    ├── logging.py
    ├── performance.py          # NEW: Performance monitoring
    └── performance_dashboard.py # NEW: Streamlit dashboard components
```

## Technology Stack

- **Python 3.12+**: Modern Python features (3.13 supported).
- **Poetry**: Exclusive dependency management.
- **Click**: For building the command-line interface.
- **Rich**: For beautiful and informative CLI output (used for progress bars).
- **yt-dlp**: Video downloading from 1800+ sites.
- **Gemini 1.5 Flash**: The core AI model for transcription and analysis.
- **Pydantic v2**: For data validation and settings management.
- **Async/Await**: For high-performance, concurrent I/O operations.
- **spaCy, GLiNER, REBEL**: For the hybrid entity and relationship extraction engine.
- **NetworkX**: For building knowledge graphs.
- **Model Caching**: Singleton pattern for ML model management (v2.10.1+).
- **Plotly**: Interactive visualizations for analysis reports (v2.12.0).
- **openpyxl**: Excel export capabilities with multi-sheet workbooks (v2.12.0).
- **Streamlit**: Enhanced web interface with performance dashboards (v2.12.0).

## Cost Analysis

| Component | Traditional (Speech-to-Text v2) | ClipScribe (Gemini 1.5 Flash - Audio Mode) |
|-----------|--------------------------------|--------------------------------------------|
| API Cost | $1.44/hour | ~$0.12/hour |
| Processing Time | 20-30 min/hour | 2-5 min/hour |
| Accuracy (WER) | 16-20% | <5% |
| Platform Support | Limited | 1800+ sites |

*Video mode costs are higher due to processing of individual frames, but provide much richer data.*

## Development Setup

### Prerequisites
- Python 3.12+ (3.13 supported)
- Poetry for dependency management
- `ffmpeg` for audio/video processing
- A Google API key for Gemini

### Installation
```bash
# Clone the repository
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# Install dependencies with Poetry
poetry install

# Set up your environment
cp env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Poetry Tips
```bash
# Install without development dependencies
poetry install --sync --without dev

# Add a new dependency
poetry add beautifulsoup4

# Add a new development dependency
poetry add --group dev pytest-mock
```

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src/clipscribe

# Run a specific test file
poetry run pytest tests/unit/test_cli.py
```

### Code Quality
```bash
# Format code with Black
poetry run black src/ tests/

# Lint with Ruff (preferred over flake8)
poetry run ruff check .

# Type checking with MyPy
poetry run mypy src/
```

## Key Components

### `UniversalVideoClient`
Handles video downloading and metadata extraction from 1800+ platforms using `yt-dlp`. It can download audio-only or the full video file.

### `GeminiFlashTranscriber`
Processes audio or video files using Gemini 1.5 Flash's native multimodal capabilities. It performs the core transcription and initial analysis (summary, key points).

### `VideoIntelligenceRetriever`
The main orchestrator. It ties together the video client, transcriber, and extractors to perform the end-to-end intelligence gathering process. It manages caching, cost tracking, and output generation.

### Model Manager (`model_manager.py`) - **NEW in v2.10.1**
A singleton class that manages ML model instances to prevent repeated loading during batch processing. Provides 3-5x performance improvement by caching SpaCy, GLiNER, and REBEL models.

### Extractors (`spacy_extractor`, `gliner_extractor`, `rebel_extractor`)
These form the hybrid extraction pipeline. They work together to pull entities and relationships from the transcript, combining free, local models with more advanced ones for a cost-effective and comprehensive result. All extractors now use the ModelManager for efficient model reuse.

## Platform Support

ClipScribe supports 1800+ video platforms through yt-dlp.

**To check if a specific URL is supported:**
```python
from clipscribe.retrievers.universal_video_client import UniversalVideoClient

client = UniversalVideoClient()
is_supported = client.is_supported_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
```

## Contributing

### Adding New Features
1. Create a feature branch: `git checkout -b feature/your-amazing-feature`
2. Add tests for the new functionality.
3. Update relevant documentation (`docs/`, `README.md`).
4. Ensure all tests and code quality checks pass.
5. Submit a pull request with a clear description of the changes.

### Code Style
- Use **Black** for formatting.
- Add type hints for all function signatures.
- Write Google-style docstrings for all public modules, classes, and functions.

### Testing Guidelines
- Write unit tests for new functions and logic.
- Add integration tests for new features that involve multiple components.
- Mock external API calls to keep tests fast and reliable.
- Aim to maintain or increase code coverage.

## Troubleshooting

### Common Issues

**`ModuleNotFoundError` for `youtube_search_python`:**
- The correct import is `youtubesearchpython` (no underscores). This is a known quirk of the library.

**Pydantic v2 Compatibility:**
- For settings management, import `BaseSettings` from `pydantic_settings`.
- Use `field_validator` from `pydantic` instead of the old `validator`.

**`yt-dlp` Errors:**
- `yt-dlp` is updated frequently to keep up with changes on video platforms. If you encounter download errors, the first step is often to update it: `poetry update yt-dlp`.

## Recent Enhancements (v2.12.0)

### Advanced Visualizations
- **Interactive Charts**: Plotly-powered pie charts, bar charts, and gauge visualizations
- **Entity Source Analysis**: Visual breakdowns of extraction method effectiveness
- **Professional Quality**: Publication-ready charts with hover effects and customization
- **Graceful Fallback**: Simple charts when Plotly unavailable for maximum compatibility

### Excel Export Capabilities
- **Multi-Sheet Workbooks**: Organized data across Summary, Source Distribution, Entity Types, and Per-Video Analysis sheets
- **Professional Formatting**: Clean, readable layouts with proper headers and data types
- **One-Click Generation**: Available through Streamlit interface and CLI tools
- **Comprehensive Data**: All analysis metrics, breakdowns, and insights included

### Performance Dashboard Integration
- **Dedicated Streamlit Tab**: Comprehensive performance monitoring interface
- **Real-time System Health**: CPU, memory, and disk usage monitoring with gauge visualizations
- **Model Cache Analytics**: Hit rates, load times, and efficiency metrics with historical reports
- **Interactive Interface**: User-friendly dashboard for system monitoring and optimization

## Future Enhancements (v2.13.0+)

1. **Real-time Analytics**: Live performance monitoring during batch processing with WebSocket updates.
2. **Advanced Filtering**: Interactive filters for entity source analysis results in Streamlit.
3. **Export Automation**: Scheduled exports and automated report generation.
4. **Custom Visualization Templates**: User-defined chart templates for specialized analysis.
5. **Advanced Search**: Implement search for platforms beyond YouTube (e.g., Vimeo, Dailymotion).
6. **Plugin System**: Create a more formal plugin system for custom extractors and output formats.
7. **Deeper Chimera Integration**: Align more closely with the Chimera Researcher data models and workflows.

## Security Considerations

- **API Keys**: Never commit API keys to version control. Use `.env` files.
- **Temporary Files**: Downloaded media files are automatically cleaned up after processing.
- **Content Filtering**: Respects `MAX_VIDEO_DURATION` limits to prevent accidental processing of extremely long videos.
- **Error Handling**: Gracefully degrades if external services are unavailable.
- **Input Validation**: All URLs are validated before processing.

## Advanced Entity & Relationship Extraction (v2.2+)

ClipScribe implements a three-tier entity extraction system for a hybrid approach that balances cost and quality.

### 1. SpaCy (Tier 1 - Free)
- **Role**: Basic Named Entity Recognition (NER).
- **Finds**: Standard types like PERSON, ORGANIZATION, LOCATION.
- **Benefit**: Zero cost, very fast, and provides a good baseline.

### 2. GLiNER (Tier 2 - Local Model)
- **Role**: Specialized, fine-grained entity detection.
- **Finds**: Custom, domain-specific entities (e.g., TECHNOLOGY, WEAPON, FINANCIAL_METRIC) that standard NER models would miss.
- **Benefit**: High-quality, targeted extraction without API cost. Runs locally.

### 3. REBEL (Tier 3 - Local Model)
- **Role**: Relationship Extraction.
- **Finds**: Knowledge graph triples (subject, predicate, object) that connect the entities.
- **Example**: "Apple announced the iPhone" → (`Apple`, `announced`, `iPhone`).
- **Benefit**: Builds the connections that form the knowledge graph. Runs locally.

### 4. Gemini (Tier 4 - LLM Validation & Augmentation)
- **Role**: Selective validation of low-confidence extractions and augmentation where local models fail.
- **Benefit**: Ensures high quality and fills in gaps, but is used sparingly to control costs.

### Architecture Flow
```
Transcript ───────────────────────────► 4. Gemini (for direct relationship extraction)
     │
     │
     ▼
1. SpaCy (basic entities) ─► Merge ◄─ 2. GLiNER (custom entities)
                                │
                                ▼
                             Combined Entities
                                │
                                ▼
                         3. REBEL (relationships between entities) ─► Final Knowledge Graph
```

### Benefits
- **Comprehensive Intelligence**: Captures not just what is mentioned, but how things are related.
- **Knowledge Graph Ready**: The output is designed for immediate use in graph databases and visualization tools like Gephi.
- **Cost-Optimized**: This hybrid model can reduce extraction costs by over 98% compared to a pure-LLM approach by handling the majority of the work with free, local models.
- **Rich, Actionable Insights**: Provides a much deeper understanding of the video content than a simple transcript.

## Performance Considerations

### Model Caching (v2.10.1+)
ClipScribe now implements intelligent model caching to dramatically improve batch processing performance:

- **Singleton Pattern**: The `ModelManager` class ensures models are loaded only once per session
- **Memory Efficiency**: Models are shared across all processing operations
- **Performance Gains**: 3-5x faster batch processing compared to previous versions
- **Automatic Management**: No configuration required - caching happens automatically

### Error Recovery
- **Retry Logic**: Automatic retry for ffmpeg errors with exponential backoff
- **Graceful Degradation**: Processing continues even if individual videos fail
- **Warning Suppression**: Cleaned up console output by removing harmless warnings

### Memory Management
```python
# Clear model cache if needed (rarely required)
from clipscribe.extractors import model_manager
model_manager.clear_cache()
```

### Testing
- Comprehensive test suite for video processing
- Mock objects for API testing
- Performance benchmarks 