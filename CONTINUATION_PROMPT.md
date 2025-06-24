# ClipScribe Project Continuation Prompt

*Last Updated: January 2025*

## Current Project State

ClipScribe is a mature video intelligence tool that extracts structured knowledge from video content. The project is feature-complete with comprehensive extraction capabilities, multiple output formats, and cost-optimized processing.

## Recent Major Changes

### Rules System Implementation (January 2025)
- Created comprehensive `.cursor/rules/` directory with 19 specialized rule files
- Aligned with Chimera Researcher project patterns
- Added master rule (README.mdc) that governs all other rules
- Implemented always-apply rules for critical patterns:
  - Core identity and mission
  - File organization discipline  
  - Cost optimization requirements
  - Documentation update triggers

### Documentation Structure
- Organized all user docs in `docs/` directory
- Created clear separation between user docs, developer docs, and rules
- Implemented documentation update rules to ensure consistency
- Added visualization guidelines for knowledge graphs

## Architecture Overview

```
ClipScribe
├── Video Retrieval (YouTube, Twitter/X, etc.)
├── Transcription (Gemini API or YouTube captions)
├── Entity Extraction (SpaCy + GLiNER + REBEL)
├── Knowledge Graph Generation
└── Multiple Export Formats
```

## Key Features Working Well

1. **Cost-Optimized Pipeline** - 92% cost reduction through intelligent routing
2. **Multi-Platform Support** - YouTube, Twitter/X, TikTok, generic URLs
3. **Hybrid Extraction** - Combines local models with LLM validation
4. **Rich Output Formats** - TXT, SRT, VTT, JSON, knowledge graphs
5. **Async Processing** - Efficient handling of multiple videos
6. **Chimera Integration** - Ready for use as video intelligence component

## Known Issues

1. **Large Video Memory** - Videos >2 hours may require chunking
2. **Platform Auth** - Some platforms (Twitter/X) may need authentication
3. **Model Downloads** - First run downloads several GB of models

## Next Planned Features

1. **Web Interface** - FastAPI-based UI for non-technical users
2. **Batch Processing** - Process entire playlists/channels
3. **Real-time Streaming** - Live transcription support
4. **Advanced Analytics** - Topic modeling, sentiment analysis
5. **API Endpoints** - RESTful API for integration

## Development Guidelines

### Before Starting Work
1. Review `.cursor/rules/` directory for project conventions
2. Check `cost-optimization.mdc` - cost awareness is critical
3. Follow `file-organization.mdc` - maintain clean structure
4. Read `core-identity.mdc` - understand project mission

### Making Changes
1. Always update tests for new features
2. Follow async patterns for I/O operations
3. Use type hints everywhere
4. End code comments with :-) 
5. Track API costs in all operations

### After Completing Tasks
1. Run the comprehensive task checklist in `documentation-updates.mdc`
2. Update this CONTINUATION_PROMPT.md
3. Commit with conventional format: `type(scope): description`

## Technical Debt

1. **Test Coverage** - Some integration tests need improvement
2. **Error Messages** - Could be more user-friendly in some cases
3. **Caching** - Local caching system could be more robust
4. **Platform Support** - Instagram/Facebook support incomplete

## Environment Setup

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone and setup
git clone https://github.com/bubroz/clipscribe
cd clipscribe
poetry install

# Configure
cp .env.example .env
# Add your GOOGLE_API_KEY to .env

# Run
poetry run clipscribe process "https://youtube.com/watch?v=..."
```

## Important Context

- ClipScribe is designed as a component of the larger Chimera Researcher system
- Cost optimization is paramount - always check API costs
- The hybrid extraction approach is key to quality + affordability
- All output is structured for easy integration with knowledge management systems
- The project follows a "video intelligence" philosophy, not just transcription

## Contact & Resources

- GitHub: https://github.com/bubroz/clipscribe
- Parent Project: Chimera Researcher
- Documentation: See `docs/` directory
- Rules & Conventions: See `.cursor/rules/`

---

*Remember: This is a living document. Update it whenever you make significant changes!*
