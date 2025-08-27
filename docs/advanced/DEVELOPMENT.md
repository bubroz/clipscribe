# ClipScribe Development Guide

*Last Updated: 2025-08-26 - v2.44.0*

## Overview

ClipScribe is a powerful, AI-powered video intelligence tool that supports **1800+ video platforms** and is now deployed as a scalable, multi-service application on Google Cloud Run. It uses Google's Gemini 2.5 Pro as its default model to ensure the highest quality intelligence extraction, with an optional, faster Gemini 2.5 Flash model available.

## Architecture

The project is structured as a service-oriented application with a clear separation of concerns. The core logic is contained within the `src/clipscribe` directory, with a professional CLI, a FastAPI-based API, and a static web front end.

```
src/clipscribe/
├── api/                # FastAPI application
│   └── app.py
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
```

## Technology Stack

- **Python 3.12+**: Modern Python features.
- **Poetry**: Exclusive dependency management.
- **Click**: For building the command-line interface.
- **FastAPI**: For the production API service.
- **Uvicorn**: For the ASGI server.
- **Redis & RQ**: For the job queuing system.
- **Gemini 2.5 Pro/Flash**: For AI-powered intelligence extraction.
- **Pydantic v2**: For data validation and settings management.
- **Async/Await**: For high-performance, concurrent I/O operations.
- **NetworkX**: For building knowledge graphs.

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
