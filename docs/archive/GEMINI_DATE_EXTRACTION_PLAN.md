# Comprehensive Gemini Date Extraction Implementation Plan

*Last Updated: July 2, 2025 02:26 PDT*
*Author: Zac Forristall (zforristall@gmail.com)*

## Executive Summary

We've discovered that ClipScribe is already using Gemini's multimodal capabilities (video mode) for enhanced temporal intelligence but NOT extracting dates from the visual or transcript content. This is a massive missed opportunity - we're paying the 10x video processing cost but not getting the date extraction benefit.

**Current State**: 0.7% date extraction success (1 out of 135 events)
**Target State**: 70-85% for news content, 40-50% average across all content
**Cost Impact**: $0 additional (already in video mode)
**Implementation Time**: 4-6 hours

## Key Discoveries

1. **We're Already Multimodal**: Enhanced temporal intelligence uses video mode by default
2. **Visual Dates Everywhere**: News content shows dates in chyrons, overlays, documents
3. **Zero Additional Cost**: We're already paying for video processing
4. **Simple Implementation**: Add dates to existing extraction schemas

## Detailed Implementation Plan

### Phase 1: Enhance Transcription Schema (2 hours)

#### 1.1 Update Combined Extraction Schema
**File**: `src/clipscribe/retrievers/transcriber.py`
**Line**: ~280 (response_schema)

```python
# Add to existing response_schema
"dates": {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "original_text": {"type": "STRING"},       # "October 2018"
            "normalized_date": {"type": "STRING"},     # "2018-10-01"
            "precision": {"type": "STRING", "enum": ["exact", "day", "month", "year", "approximate"]},
            "confidence": {"type": "NUMBER"},
            "context": {"type": "STRING"},             # Surrounding context
            "source": {"type": "STRING", "enum": ["transcript", "visual", "both"]},
            "visual_description": {"type": "STRING"},  # If from visual
            "timestamp": {"type": "NUMBER"}            # When it appeared
        },
        "required": ["original_text", "normalized_date", "precision", "confidence", "source"]
    }
}
```

#### 1.2 Update Visual Temporal Cues Schema
**File**: `src/clipscribe/retrievers/transcriber.py`
**Line**: ~600 (temporal_schema)

Add explicit date extraction to visual_temporal_cues:
```python
"visual_dates": {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "timestamp": {"type": "NUMBER"},
            "date_text": {"type": "STRING"},
            "screen_location": {"type": "STRING"},  # "lower_third", "overlay", "document"
            "confidence": {"type": "NUMBER"}
        }
    }
}
```

### Phase 2: Process Extracted Dates (1 hour)

#### 2.1 Create Gemini Date Processor
**New File**: `src/clipscribe/timeline/gemini_date_processor.py`

```python
class GeminiDateProcessor:
    """Process dates extracted by Gemini from transcript and visual cues."""
    
    def merge_multimodal_dates(
        self, 
        transcript_dates: List[Dict],
        visual_dates: List[Dict],
        video_metadata: Dict
    ) -> List[ExtractedDate]:
        """
        Merge dates from transcript and visual sources.
        
        Strategy:
        1. Deduplicate dates that appear in both
        2. Boost confidence when dates appear in multiple sources
        3. Resolve conflicts (visual usually more accurate)
        4. Convert relative dates using video publish date
        """
        
    def associate_dates_with_events(
        self,
        temporal_events: List[TemporalEvent],
        extracted_dates: List[ExtractedDate]
    ) -> List[TemporalEvent]:
        """
        Smart association of dates with temporal events.
        
        Strategy:
        1. Match by temporal proximity (±30 seconds)
        2. Match by entity mentions
        3. Match by contextual similarity
        4. Fall back to nearest date
        """
```

### Phase 3: Integration Points (1 hour)

#### 3.1 Update Video Retriever
**File**: `src/clipscribe/retrievers/video_retriever.py`
**Line**: ~450

Replace ContentDateExtractor with Gemini dates:
```python
# OLD: 
extracted_date = self.content_date_extractor.extract_date_from_content(...)

# NEW:
extracted_date = self._extract_date_from_gemini_results(
    gemini_dates=transcript_result.get('dates', []),
    visual_dates=transcript_result.get('visual_temporal_cues', {}).get('visual_dates', []),
    event=temporal_event
)
```

#### 3.2 Update Temporal Extractor
**File**: `src/clipscribe/timeline/temporal_extractor_v2.py`
**Line**: ~650

Prefer Gemini dates over regex:
```python
# Check Gemini dates first
if self.gemini_dates:
    date = self._find_best_gemini_date(event_description, timestamp)
    if date:
        return date
        
# Fall back to regex only if no Gemini date
return self.date_extractor.extract_date_from_content(...)
```

### Phase 4: Testing & Validation (2 hours)

#### 4.1 Test Suite
Create comprehensive tests:
- News content (PBS NewsHour) - expect 70-85%
- Documentary (Pegasus) - expect 60-75%
- Educational content - expect 40-50%
- Music videos - expect 5-10%

#### 4.2 Quality Metrics
Track and report:
- Date extraction success rate by content type
- Visual vs transcript date accuracy
- Confidence score distribution
- TimelineJS timeline quality improvement

## Expected Results

### Success Metrics
| Metric | Current | Expected | Improvement |
|--------|---------|----------|-------------|
| Date Extraction Rate | 0.7% | 70-85% (news) | 10,000%+ |
| Timeline Quality | Poor | Excellent | Dramatic |
| Additional Cost | $0 | $0 | Free! |
| Implementation Time | - | 4-6 hours | One session |

### Content Type Performance
| Content Type | Current | Expected | Why |
|--------------|---------|----------|-----|
| PBS NewsHour | 1% | 80-85% | Dates in chyrons, overlays |
| Documentaries | 1% | 70-75% | Timeline graphics, documents |
| Educational | 0.5% | 40-50% | Mixed visual/spoken dates |
| Interviews | 0.5% | 50-60% | Depends on visuals |
| Music Videos | 0% | 5-10% | Rare temporal content |

## Risk Mitigation

1. **Backward Compatibility**: Keep regex fallback for non-visual mode
2. **Graceful Degradation**: Handle missing visual data gracefully
3. **Cost Control**: No additional API calls (piggyback existing)
4. **Quality Assurance**: Validate dates are reasonable (not future, not ancient)

## Timeline

**Total Time**: 4-6 hours

1. **Hour 1-2**: Implement schema changes
2. **Hour 3**: Create date processor
3. **Hour 4**: Integration and initial testing
4. **Hour 5-6**: Full testing and refinement

## Success Criteria

- [ ] 70%+ date extraction on PBS NewsHour test video
- [ ] TimelineJS shows actual historical dates
- [ ] Zero additional API costs
- [ ] All tests passing
- [ ] Documentation updated

## Next Steps After Implementation

1. **Fine-tune prompts** for specific content types
2. **Add date validation** using external sources
3. **Implement cross-video date correlation**
4. **Create date confidence boosting** algorithms

## Key Code Snippets

### Enhanced Prompt Addition
```python
# Add to combined_prompt in transcriber.py
Extract ALL dates and temporal expressions including:
- Dates mentioned in speech ("in October 2018", "last June")  
- Dates shown visually (overlays, documents, graphics)
- Relative dates ("three years ago" - calculate from video date)
- Date ranges ("from 2018 to 2021")
- Partial dates ("early 2019", "summer of 2020")

For each date, identify:
- Original text/visual appearance
- Normalized ISO date
- Precision level
- Confidence score
- Whether from transcript, visual, or both
- Related context/event
```

### Visual Date Extraction
```python
# Add to visual temporal cues prompt
Pay special attention to:
- News chyrons and lower thirds with dates
- Document headers showing dates
- Timeline graphics and charts
- Calendar displays
- Date overlays and watermarks
- Historical footage timestamps

These visual dates are often more accurate than spoken dates.
```

## Conclusion

This implementation leverages our existing multimodal infrastructure to achieve dramatic improvements in date extraction at zero additional cost. The key insight is that we're already processing video content but not extracting the rich temporal information available visually.

With 70-85% date extraction for news content, TimelineJS exports will transform from sequential processing dates to rich historical timelines that accurately represent the temporal narrative of the content. 