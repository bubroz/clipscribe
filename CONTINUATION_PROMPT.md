# ClipScribe Development Continuation Prompt

## Last Updated: 2024-06-24 17:45 PST

### Current Version: v2.5.1

## Recent Changes (Today's Session)

### 1. Auto-Clean Threshold Fix
- Raised thresholds from 100/150 to 300/500 nodes/relationships
- Now properly respects --skip-cleaning flag
- Prevents over-aggressive cleaning of legitimate content

### 2. Optimized API Batching ✨
- **MAJOR IMPROVEMENT**: Reduced API calls from 6 to 2-3
- Combined extraction gets summary, key points, topics, entities, relationships in ONE call
- Uses Gemini's official response_schema for guaranteed JSON formatting
- Added optional second-pass extraction for comprehensive coverage
- 50-60% cost reduction while maintaining quality

### 3. New Export Formats
- Added CSV export for entities and relationships
- Added markdown report generation with:
  - Executive summary
  - Cost indicators (🟢🟡🔴)
  - Key statistics tables
  - Top entities by type
  - Key relationships
  - File index

### 4. Bug Fixes
- Fixed JSON parsing issues with enhanced parser
- Fixed VideoTranscript subscript error
- Fixed GLiNER chunking (now 800 chars)
- Fixed graph cleaner filtering bug
- Fixed macOS visualization

## Current State

### What's Working Well ✅
- GeminiPool architecture preventing token limit issues
- Transcription with Gemini 2.5 Flash
- SpaCy + GLiNER entity extraction
- Knowledge graph generation
- Cost tracking and optimization
- Multiple output formats (JSON, CSV, Markdown, GEXF)

### Known Issues 🔧
- GLiNER truncation warnings (from library, not our code)
- Graph cleaning still needs refinement
- Need to implement Mermaid diagrams in markdown reports

### Next Priority Tasks 🎯

1. **Rich Progress Indicators**
   - Use Rich library for beautiful progress bars
   - Show phase progress and time estimates
   - Real-time cost tracking

2. **Enhanced Markdown Reports**
   - Add Mermaid relationship diagrams
   - Collapsible sections for details
   - Better formatting for large datasets

3. **Platform Testing**
   - Test Twitter/X support
   - Test TikTok support
   - Ensure multi-platform batch processing works

4. **Performance Monitoring**
   - Add metrics collection
   - Track API response times
   - Monitor extraction quality

## Architecture Notes

### GeminiPool Design
- Separate Gemini instances per task type
- Prevents token accumulation
- Fresh context for each operation
- Task types: TRANSCRIPTION, SUMMARY, KEY_POINTS, ENTITIES, RELATIONSHIPS, GRAPH_CLEANING

### Cost Optimization Strategy
- Batch multiple extractions in single API call
- Use structured output for reliability
- Optional second-pass for quality
- Smart thresholds for auto-cleaning

## Testing Commands

```bash
# Test with news content (preferred)
clipscribe https://www.youtube.com/watch?v=UjDpW_SOrlw --no-cache

# Test with --skip-cleaning
clipscribe https://www.youtube.com/watch?v=UjDpW_SOrlw --skip-cleaning --no-cache

# Test CSV/Markdown output
clipscribe https://www.youtube.com/watch?v=UjDpW_SOrlw --output-dir test_reports
```

## Environment Variables
- GOOGLE_API_KEY (required)
- GLINER_MODEL=urchade/gliner_mediumv2.1
- REBEL_MODEL=Babelscape/rebel-large

## Dependencies
All managed through Poetry. Key packages:
- google-generativeai (Gemini API)
- spacy (NLP)
- gliner (Entity extraction)
- yt-dlp (Video downloading)
- click (CLI)
- rich (Progress bars - to be added)

---
Remember: Always test with news content, not music videos! User strongly prefers PBS News Hour examples.