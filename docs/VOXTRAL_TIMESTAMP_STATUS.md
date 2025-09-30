# Voxtral Timestamp Capabilities & Word-Level Readiness

*Last Updated: September 6, 2025*
*Status: Segment timestamps ✅ | Word timestamps ⏳*

## Current Status

### What's Working
- **Segment-level timestamps**: Fully operational with ~10 second precision
- **PHP-style array notation**: `timestamp_granularities[]` required for segments
- **Multiple segments per video**: 100+ segments for detailed navigation
- **Timestamp accuracy**: Start/end times precise to 0.1 seconds

### API Limitation
As of September 2025, the Voxtral API **only accepts** `'segment'` as a valid value for `timestamp_granularities`. Attempting to use `'word'` results in:

```json
{
  "error": {
    "detail": [{
      "type": "enum",
      "loc": ["timestamp_granularities", 0],
      "msg": "Input should be 'segment'",
      "input": "word"
    }]
  }
}
```

## Our Implementation Readiness

### ✅ Infrastructure Complete
We've built full support for word-level timestamps that will activate automatically when the API enables it:

1. **Configuration** (`src/clipscribe/config/settings.py`)
   - `voxtral_word_timestamps`: Toggle for word timestamps
   - `word_timestamps_storage`: Storage strategy (inline/separate/both)
   - `word_confidence_threshold`: Filtering by confidence

2. **API Integration** (`src/clipscribe/retrievers/voxtral_transcriber.py`)
   - Conditional word timestamp requests
   - Response parsing for word arrays
   - Automatic fallback to segments

3. **Data Models** (`src/clipscribe/core_data.py`)
   - `WordTimestamp` model with confidence scores
   - Segment-level word storage
   - Properties for word access

4. **CLI Support** (`src/clipscribe/commands/cli.py`)
   - `--word-timestamps` flag ready
   - Automatic detection and storage

5. **Storage** (`src/clipscribe/retrievers/video_retriever_v2.py`)
   - Word distribution to segments
   - Separate word timestamp files
   - JSON export format

## Intelligent Workaround: Pseudo-Word Timestamps

Until the API supports word-level timestamps, we provide an approximation algorithm:

### Algorithm Overview
1. **Segment Analysis**: Parse each segment's text
2. **Word Counting**: Count words and characters
3. **Time Distribution**: Distribute segment duration across words
4. **Confidence Scoring**: Higher confidence for shorter segments

### Implementation
```python
def approximate_word_timestamps(segment: Dict) -> List[Dict]:
    """
    Generate approximate word timestamps from segment.
    
    Args:
        segment: Segment with text, start, and end times
        
    Returns:
        List of word dictionaries with approximate timestamps
    """
    text = segment['text']
    start_time = segment['start']
    end_time = segment['end']
    duration = end_time - start_time
    
    # Split into words
    words = text.split()
    if not words:
        return []
    
    # Calculate time per word (simple linear distribution)
    time_per_word = duration / len(words)
    
    # Generate word timestamps
    word_timestamps = []
    current_time = start_time
    
    for word in words:
        word_end = current_time + time_per_word
        word_timestamps.append({
            'word': word,
            'start': round(current_time, 2),
            'end': round(word_end, 2),
            'confidence': 0.7,  # Lower confidence for approximation
            'approximated': True
        })
        current_time = word_end
    
    return word_timestamps
```

### Advanced Approximation (Weighted by Word Length)
```python
def weighted_word_timestamps(segment: Dict) -> List[Dict]:
    """
    Generate weighted word timestamps based on word length.
    More accurate than linear distribution.
    """
    text = segment['text']
    words = text.split()
    
    # Calculate total character count (excluding spaces)
    total_chars = sum(len(word) for word in words)
    
    # Distribute time based on word length
    duration = segment['end'] - segment['start']
    current_time = segment['start']
    word_timestamps = []
    
    for word in words:
        # Time proportional to word length
        word_duration = (len(word) / total_chars) * duration
        word_end = current_time + word_duration
        
        word_timestamps.append({
            'word': word,
            'start': round(current_time, 2),
            'end': round(word_end, 2),
            'confidence': 0.8 if len(words) < 20 else 0.6,
            'approximated': True
        })
        current_time = word_end
    
    return word_timestamps
```

## Use Cases Enabled Today

### With Segment Timestamps (Available Now)
1. **Chapter Navigation**: Jump to topic sections
2. **Quote Attribution**: "At 2:34, the speaker said..."
3. **Content Search**: Find which segment contains keywords
4. **Rough Editing**: Extract 10-second clips
5. **Summary Alignment**: Link summaries to segments

### With Approximated Words (Workaround)
1. **Reading Assistance**: Highlight words during playback
2. **Language Learning**: Follow along word-by-word
3. **Accessibility**: Basic word-level captions
4. **Search Preview**: Show words around search matches

### Future with Real Word Timestamps
1. **Precise Editing**: Cut at exact word boundaries
2. **Karaoke Mode**: Perfect word synchronization
3. **Legal Transcription**: Court-admissible precision
4. **Interactive Transcripts**: Click any word to play
5. **Linguistic Analysis**: Measure speaking rates

## Monitoring for Updates

### Check API Capabilities
```bash
# Test if word timestamps are available
curl -X POST https://api.mistral.ai/v1/audio/transcriptions \
  -H "x-api-key: $MISTRAL_API_KEY" \
  -F "model=voxtral-mini-2507" \
  -F "file_url=https://example.com/audio.mp3" \
  -F "response_format=verbose_json" \
  -F "timestamp_granularities[]=word"
```

### Version Detection
When Mistral enables word timestamps, we expect:
- API version bump (e.g., v1.1 or v2)
- Documentation update at docs.mistral.ai
- Changelog announcement

## Activation Plan

When word timestamps become available:

1. **Remove Validation Block**: Delete the API error handling for word rejection
2. **Enable by Default**: Set `voxtral_word_timestamps = True` in settings
3. **Update Documentation**: Remove workaround sections
4. **Performance Testing**: Verify processing time impact
5. **Cost Analysis**: Check if pricing changes

## Recommendations

### For Now
- Use segment timestamps (10-second precision)
- Enable approximation for basic word highlighting
- Set expectations about precision limitations

### Best Practices
1. **Always store segments**: Even with word timestamps
2. **Cache transcriptions**: Avoid re-processing
3. **Version your outputs**: Track approximated vs real
4. **Monitor API updates**: Check Mistral changelog monthly

## Technical Details

### Segment Timestamp Format
```json
{
  "text": "This is a segment of speech.",
  "start": 10.5,
  "end": 15.3,
  "speaker": null
}
```

### Future Word Timestamp Format
```json
{
  "word": "speech",
  "start": 14.8,
  "end": 15.3,
  "confidence": 0.95
}
```

### Approximated Word Format
```json
{
  "word": "speech",
  "start": 14.8,
  "end": 15.3,
  "confidence": 0.7,
  "approximated": true
}
```

## Contact & Updates

- **Mistral API Status**: https://status.mistral.ai
- **Documentation**: https://docs.mistral.ai
- **Our Implementation**: `src/clipscribe/retrievers/voxtral_transcriber.py`

---

*Note: This document will be updated when Mistral enables word-level timestamps.*
