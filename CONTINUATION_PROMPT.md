# ClipScribe AI Assistant Continuation Prompt

## Current State (2025-01-24)

### Just Completed - v2.4.3 Released ✅
- Fixed JSON parsing with enhanced parser that auto-corrects missing commas/quotes
- Fixed VideoTranscript subscript error (changed to `.full_text` access)
- Improved GLiNER chunking to 800 chars with proper sentence boundaries
- Made graph cleaning MUCH less aggressive (now only removes ~1% vs 82%)
- Fixed macOS visualization file opening
- Removed all subtitle generation code (SRT/VTT) in v2.4.2

### Test Results
- No more JSON parsing warnings
- GLiNER processing 38 chunks successfully (420 entities extracted)
- Graph preservation: 193/195 nodes kept (99%), 176/179 edges kept (98%)
- All 203 relationships preserved through cleaning
- Cost remains at ~$0.12 per hour-long video

### Next Implementation: GeminiPool 🚀
We're implementing a multi-instance Gemini approach to avoid token limits:
- `src/clipscribe/retrievers/gemini_pool.py` - Already created
- Uses separate Gemini instances for different tasks
- Prevents token accumulation and context pollution
- Should eliminate timeout issues

### Also Created (Not Yet Integrated)
- `src/clipscribe/extractors/batch_extractor.py` - Single API call extraction
- `src/clipscribe/extractors/streaming_extractor.py` - Chunked parallel processing

## Integration Plan for GeminiPool

1. **Modify Transcriber**:
   - Replace single client with GeminiPool
   - Use different instances for transcription, extraction, validation
   
2. **Update VideoRetriever**:
   - Pass GeminiPool to transcriber and extractors
   - Ensure proper instance management

3. **Test Thoroughly**:
   - Verify token limits are avoided
   - Check cost tracking across instances
   - Ensure quality remains high

## Testing Notes
- User (Zac) prefers news content over music videos for testing
- PBS News Hour works well for entity/relationship extraction
- Use `--no-cache` flag to test fresh extractions

## Known Issues
- Auto-cleaning still triggers for graphs >100 nodes + >150 relationships
- Need to respect `--skip-cleaning` flag better
- Consider making auto-clean thresholds configurable

## Recent Commands
```bash
# Test with all fixes (use --no-cache to avoid cached results)
poetry run clipscribe transcribe "https://www.youtube.com/watch?v=UjDpW_SOrlw" \
  --mode audio --skip-cleaning --visualize --no-cache -o output/test_nocache
```

## Architecture Decisions
- Hybrid extraction approach works well (SpaCy + GLiNER + REBEL + LLM)
- Graph cleaning should be conservative by default
- Cost optimization remains critical (~$0.12/hour target)
- Multiple Gemini instances may be key to reliability

Remember: Always test with news content, not Rick Astley! 🎵❌📰✅