# PRD: Word-Level Timestamps for Voxtral Transcription

**Version:** 1.0  
**Date:** September 6, 2025  
**Status:** Ready for Implementation

## Executive Summary

Enable word-level timestamp extraction from Voxtral API to provide precise temporal alignment for transcripts, enabling advanced features like searchable video moments, quote extraction with exact timing, and synchronized subtitles.

## Problem Statement

Current transcription provides only full text without temporal information, making it impossible to:
- Jump to specific moments in video when searching for quotes
- Create accurate subtitles or captions
- Extract clips based on spoken content
- Verify quotes with exact timestamps

## Solution Overview

Leverage Voxtral's `timestamp_granularities` parameter to receive word-level timing data, storing it alongside transcripts for temporal intelligence.

## Technical Specification

### API Changes
```python
# Add to transcription request
data.add_field("timestamp_granularities", json.dumps(["word", "segment"]))
data.add_field("response_format", "verbose_json")
```

### Response Structure
```json
{
  "text": "Full transcript text",
  "words": [
    {
      "word": "Hello",
      "start": 0.28,
      "end": 0.58,
      "confidence": 0.95
    }
  ],
  "segments": [
    {
      "id": 0,
      "text": "Hello world.",
      "start": 0.28,
      "end": 1.24,
      "words": [0, 1]  // Word indices
    }
  ]
}
```

### Storage Format
```python
class TimestampedWord:
    word: str
    start_time: float  # Seconds
    end_time: float
    confidence: float
    
class TimestampedSegment:
    text: str
    start_time: float
    end_time: float
    word_indices: List[int]
```

## Implementation Plan

### Phase 1: API Integration (Completed)
- ✅ Add timestamp parameters to API request
- ✅ Parse word-level data from response
- ✅ Update VoxtralTranscriptionResult dataclass

### Phase 2: Storage & Retrieval
- Store word timestamps in `transcript_words.json`
- Index words for fast search
- Link words to segments

### Phase 3: Feature Enablement
- Timestamp search: Find when specific phrases were spoken
- Quote extraction: Get exact timestamps for any text selection
- Subtitle generation: Export SRT/VTT with precise timing

## Success Metrics

- **Accuracy:** Word timestamps within ±0.1s of actual speech
- **Coverage:** 100% of words have timestamps
- **Performance:** No impact on transcription speed
- **Storage:** < 10% increase in output size

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API doesn't return word data | High | Fallback to segment-only timestamps |
| Increased response size | Low | Compress word data in storage |
| Timestamp drift in long videos | Medium | Validate against segment boundaries |

## Dependencies

- Voxtral API must support `timestamp_granularities` parameter
- Response must include `words` array when requested
- Storage format must be backward compatible

## Future Enhancements

1. **Interactive Transcript:** Click any word to jump to that moment
2. **Phrase Search:** Find exact moments when phrases were spoken
3. **Clip Generation:** Extract video clips based on transcript selection
4. **Speaker Diarization:** Combine with speaker detection for attribution

## Acceptance Criteria

- [ ] Word timestamps extracted from all transcriptions
- [ ] Timestamps accurate to within ±0.1 seconds
- [ ] Word data stored in structured format
- [ ] No performance degradation
- [ ] Backward compatibility maintained
