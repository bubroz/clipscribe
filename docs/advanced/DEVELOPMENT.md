# ClipScribe Development Guide

*Last Updated: 2025-09-30 - v2.51.1*

## Overview

ClipScribe is a powerful, AI-powered video intelligence tool that supports **1800+ video platforms** with automatic bot detection bypass and is now deployed as a scalable, multi-service application on Google Cloud Run. It uses Voxtral for transcription and Grok-4 for uncensored intelligence extraction, with curl-cffi browser impersonation for reliable video downloads.

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
- **Voxtral (Mistral)**: For uncensored transcription.
- **Grok-4 (xAI)**: For uncensored intelligence extraction.
- **curl-cffi**: For browser impersonation and bot detection bypass.
- **yt-dlp**: For video downloading from 1800+ platforms.
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

## Bot Detection Architecture (v2.51.1)

### curl-cffi Browser Impersonation

ClipScribe uses `curl-cffi` to bypass bot detection on video platforms:

**How it works:**
1. **ImpersonateTarget**: Uses yt-dlp's `ImpersonateTarget` class to configure browser fingerprints
2. **TLS Fingerprinting**: Mimics real browser TLS handshakes (cipher suites, extensions, order)
3. **JA3 Signature**: Matches Chrome 131's JA3 fingerprint
4. **HTTP/2 Fingerprinting**: Replicates genuine browser HTTP/2 frame patterns

**Implementation:**
```python
# In UniversalVideoClient.__init__()
from yt_dlp.networking.impersonate import ImpersonateTarget

target = ImpersonateTarget(
    client="chrome",      # Lowercase required by curl-cffi
    version="131",
    os="macos",          # Lowercase required
    os_version="14"
)
self.ydl_opts["impersonate"] = target
```

**Key Details:**
- Default target: `Chrome-131:Macos-14` (configurable)
- Auto-enabled for all downloads
- Case normalization happens automatically
- Zero runtime overhead
- Works with all 1800+ yt-dlp extractors

**Testing:**
- Run `poetry run clipscribe --debug process video URL` to see impersonation logs
- Check `yt-dlp --list-impersonate-targets` for available targets
- Test with: `poetry run python -c "from yt_dlp.networking.impersonate import ImpersonateTarget; print(ImpersonateTarget('chrome', '131', 'macos', '14'))"`

## Security Considerations

- **API Keys**: Never commit API keys to version control. Use `.env` files.
- **Dependencies**: Regularly update dependencies to patch security vulnerabilities.
- **Input Sanitization**: Ensure any user-provided input is properly sanitized.
- **Bot Detection**: curl-cffi impersonation respects platform ToS - it only appears as a normal browser.

## Scalability
- Design for thousands of concurrent users.
- Use asynchronous processing for all I/O-bound tasks.
- Implement intelligent caching to avoid redundant processing.
- curl-cffi scales horizontally - no shared state required.
