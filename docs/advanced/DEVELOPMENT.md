# ClipScribe Development Guide

*Last Updated: July 31, 2025 - v2.22.2 Stable*

## Overview

ClipScribe is a powerful, AI-powered video intelligence tool that supports **1800+ video platforms** through yt-dlp integration. It uses Google's Gemini 2.5 Pro as its default model to ensure the highest quality intelligence extraction. A faster, lower-cost option using Gemini 2.5 Flash is available via a command-line flag.

## 🚀 Enhanced Metadata Architecture (v2.19.0 Complete)

**Major Achievement**: Complete enhanced metadata implementation with:
- **Phase 1 - Entity Confidence**: Confidence scores, source attribution, temporal distribution
- **Phase 2 - Relationship Evidence**: Direct quotes, visual correlation, contradiction detection  
- **Phase 3 - Temporal Resolution**: Intelligent parsing of relative dates ("yesterday", "last week")
- **95%+ Test Coverage**: Comprehensive testing across all three phases
- **Zero Performance Impact**: Enhanced intelligence without speed degradation

### Enhanced Extraction Package Structure
```
src/clipscribe/extractors/
├── enhanced_entity_extractor.py    # Phase 1: Entity confidence & metadata
├── relationship_evidence_extractor.py # Phase 2: Evidence chains
├── temporal_reference_resolver.py  # Phase 3: Temporal resolution
├── advanced_hybrid_extractor.py    # Orchestrates all phases
├── entity_normalizer.py           # Cross-video entity resolution
├── entity_quality_filter.py       # Quality validation
└── __init__.py                    # Package exports
```

## Key Features

- **Universal Platform Support**: Works with YouTube, Twitter/X, TikTok, Instagram, Vimeo, and 1800+ other sites.
- **Pro-First Quality**: Uses Gemini 2.5 Pro by default for the highest quality entity and relationship extraction.
- **Cost Flexibility**: Provides an optional `--use-flash` flag for faster, lower-cost processing.
- **Multi-Video Analysis**: Sophisticated tools for analyzing entire series or collections of videos.
- **Multiple Output Formats**: Generates over 10 formats, including JSON, CSV, and GEXF for knowledge graphs.

## Architecture

```
src/clipscribe/
├── commands/           # CLI implementation (Click)
│   └── cli.py
├── config/             # Configuration (Pydantic)
│   └── settings.py
├── extractors/         # Knowledge extraction (Gemini-first)
│   ├── advanced_hybrid_extractor.py
│   └── multi_video_processor.py
├── models.py           # Core data structures (Pydantic)
├── retrievers/         # Media retrieval and processing
│   ├── universal_video_client.py
│   ├── transcriber.py
│   └── video_retriever.py
└── utils/              # Shared utilities
    ├── filename.py
    ├── logging.py
    └── performance.py
```

## Technology Stack

- **Python 3.11+**: Modern Python features (3.12+ recommended)
- **Poetry**: Exclusive dependency management
- **Click**: For building the command-line interface
- **Rich**: For beautiful and informative CLI output
- **Gemini 2.5 Pro**: The default AI model for the highest quality intelligence extraction.
- **Gemini 2.5 Flash**: An optional, faster model for use cases where speed is prioritized over quality.
- **Pydantic v2**: For data validation and settings management.
- **Async/Await**: For high-performance, concurrent I/O operations.
- **NetworkX**: For building knowledge graphs.
- **Streamlit**: For the Mission Control web interface.

## Contributing

### Adding a Feature
1. Create a feature branch: `git checkout -b feature/my-new-feature`
2. Add components in the appropriate `src/clipscribe/` subdirectory.
3. Add corresponding tests in the `tests/` directory.
4. Update relevant documentation in `docs/`.
5. Ensure all tests pass.
6. Submit a pull request with a clear description of the feature.

### Code Style
- Use **Black** for formatting
- Add type hints for all function signatures
- Write Google-style docstrings for all public modules and functions

### Testing Guidelines
- Write unit tests for individual components.
- Add integration tests for end-to-end workflows.
- Mock external dependencies like API calls.
- Aim for 80%+ test coverage on new code.

## Security Considerations

- **API Keys**: Never commit API keys to version control. Use `.env` files.
- **Dependencies**: Regularly update dependencies to patch security vulnerabilities.
- **Input Sanitization**: Ensure any user-provided input is properly sanitized.

## Scalability
- Design for thousands of concurrent users.
- Use asynchronous processing for all I/O-bound tasks.
- Implement intelligent caching to avoid redundant processing.
