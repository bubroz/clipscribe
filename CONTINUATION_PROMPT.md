# ClipScribe Continuation Prompt

## Current State (January 24, 2025 - v2.4.3)

ClipScribe is a powerful video intelligence extraction tool that transcribes videos and extracts structured knowledge using Gemini 2.5 Flash. It's designed to work with Chimera Researcher for comprehensive knowledge management.

### Major Recent Changes

#### v2.4.3 - Robust Error Handling & Better Extraction
Major improvements to handle real-world usage:
- **Fixed JSON parsing**: Now handles malformed Gemini responses gracefully
- **Fixed VideoTranscript error**: Proper handling of transcript objects
- **Fixed GLiNER truncation**: Smart chunking for long transcripts
- **Less aggressive graph cleaning**: Keeps 80%+ of data (was ~20%)
- **Fixed visualization path**: --visualize flag now works correctly

#### v2.4.2 - Complete Removal of Subtitle Formats
- **Removed all SRT/VTT generation**: Focusing purely on intelligence extraction, not video captioning
- **Bug fixes**: Fixed missing `use_advanced_extraction` attribute and sys import shadowing
- **Cleaned up**: All documentation and examples now use JSON for structured output

#### Earlier Versions
- v2.4.1: Fixed GEXF edge generation for Gephi
- v2.4.0: Added GEXF format, removed subtitle formats
- v2.3.0: Added timeout support, enhanced extraction quality

### Project Structure
```
src/clipscribe/
├── commands/       # CLI interface
├── config/         # Configuration management
├── extractors/     # Knowledge extraction modules
│   ├── spacy_extractor.py
│   ├── gliner_extractor.py
│   ├── rebel_extractor.py
│   ├── hybrid_extractor.py
│   ├── advanced_hybrid_extractor.py
│   └── graph_cleaner.py     # AI-powered graph cleaning
├── models.py       # Data models
├── retrievers/     # Video/audio processing
│   ├── transcriber.py
│   ├── universal_video_client.py
│   ├── video_mode_detector.py
│   └── video_retriever.py
└── utils/          # Utilities
```

### Key Features
- **1800+ Platform Support**: YouTube, Twitter/X, TikTok, Vimeo, etc. via yt-dlp
- **Cost-Effective**: Audio mode at $0.002/min (92% cheaper than alternatives)
- **Advanced Extraction**: SpaCy + GLiNER + REBEL + LLM validation
- **Knowledge Graphs**: GEXF export for Gephi, interactive HTML visualizations
- **Timeout Support**: Handle videos up to 4 hours with configurable timeouts
- **AI Graph Cleaning**: Remove noise while preserving meaningful connections
- **Robust Error Handling**: Gracefully handles API errors and malformed responses

### Core Dependencies
- Python 3.12 (not 3.13 due to compatibility)
- Poetry for dependency management
- Gemini 2.5 Flash/Pro via google-generativeai
- SpaCy, GLiNER, REBEL for entity extraction
- yt-dlp for video retrieval
- Pyvis and Plotly for visualizations

### Recent Test Results
- PBS News Hour (57 min): $0.114, good entity extraction
- Pentagon briefing (28 min): Used for GEXF/visualization testing
- Discord tutorial (57 min): $0.116, successful with all fixes applied

### Known Issues & TODOs
1. **JSON Parsing Warnings**: Gemini occasionally returns malformed JSON (now handled)
2. **Large Graphs**: Performance with 150+ node graphs could be better
3. **Cost Optimization**: Consider caching entity extraction results

### Next Features to Consider
1. **Streaming Processing**: Handle live videos/streams
2. **Incremental Processing**: Resume interrupted long videos
3. **Batch Graph Analysis**: Compare knowledge graphs across videos
4. **Export to Neo4j**: Direct graph database integration
5. **Multi-language Support**: Expand beyond English transcription

### Environment Setup
```bash
# Required
GOOGLE_API_KEY=your_key_here
GEMINI_REQUEST_TIMEOUT=14400  # 4 hours for long videos

# Optional
GLINER_MODEL=urchade/gliner_mediumv2.1
REBEL_MODEL=Babelscape/rebel-large
```

### Quick Commands
```bash
# Standard transcription with graph cleaning and visualization
poetry run clipscribe transcribe "URL" --clean-graph --visualize

# Audio-only mode (fast & cheap)
poetry run clipscribe transcribe "URL" --mode audio

# Generate visualization from existing output
python scripts/visualize_knowledge_graph.py output/*/knowledge_graph.json

# Convert old outputs to Chimera format
python scripts/convert_to_chimera.py output/YYYYMMDD_platform_videoId
```

### Critical Notes
- User strongly prefers news content over music videos for testing
- GEXF edges must connect entities, not predicates
- All comments should end with :-) to maintain project style
- Focus on intelligence extraction, not video captioning
- Graph cleaning should preserve meaningful data, not aggressively prune

### What's Working Well
- Robust JSON parsing handles Gemini's occasional formatting issues
- GLiNER processes long transcripts without truncation
- Graph cleaning preserves 80%+ of meaningful data
- Visualization works seamlessly with --visualize flag
- Error handling prevents crashes from API issues

Remember: ClipScribe is about extracting knowledge from videos, not creating subtitles :-)