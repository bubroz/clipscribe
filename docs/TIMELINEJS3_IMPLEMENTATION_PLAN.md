# TimelineJS3 Export Implementation Plan

*Created: July 1, 2025 08:00 PDT*

## Overview
Add TimelineJS3 export format to ClipScribe for beautiful, interactive timeline visualizations.

## TimelineJS3 JSON Structure
```json
{
  "title": {
    "text": {
      "headline": "Video Title",
      "text": "Description"
    }
  },
  "events": [
    {
      "start_date": {
        "year": "2025",
        "month": "7",
        "day": "1"
      },
      "text": {
        "headline": "Event Title",
        "text": "Event description with context"
      },
      "media": {
        "url": "thumbnail_url",
        "caption": "Media caption"
      }
    }
  ]
}
```

## Implementation Steps

### 1. Create TimelineJS Formatter (Day 1)
**File**: `src/clipscribe/utils/timeline_js_formatter.py`
```python
class TimelineJSFormatter:
    """Convert Timeline v2.0 data to TimelineJS3 format."""
    
    def format_timeline(self, timeline_data: ConsolidatedTimeline) -> dict:
        """Convert consolidated timeline to TimelineJS3 JSON."""
        pass
```

### 2. Add Output Format (Day 1)
**File**: Update `src/clipscribe/models.py`
- Add `timelinejs` to OutputFormat enum
- Update `OUTPUT_FORMAT_INFO` with TimelineJS details

### 3. Integrate with VideoRetriever (Day 1)
**File**: Update `src/clipscribe/retrievers/video_retriever.py`
- Add TimelineJS export in `_save_transcript_files`
- Handle video thumbnails and media references

### 4. Add CLI Support (Day 2)
**File**: Update `src/clipscribe/commands/cli.py`
- Add `--format timelinejs` option
- Update help text and documentation

### 5. Test with Real Data (Day 2)
- Use PBS NewsHour timeline data
- Test date formatting edge cases
- Validate JSON structure

## Technical Considerations

### Date Handling
- Map ExtractedDate precision to TimelineJS format
- Handle partial dates (year only, month+year)
- Fallback for missing dates

### Media Integration
- Extract video thumbnails using yt-dlp
- Link to video timestamps
- Handle missing media gracefully

### Content Formatting
- Convert markdown to HTML for text fields
- Truncate long descriptions
- Preserve entity links

## Testing Plan
1. Unit tests for formatter
2. Integration test with real timeline data
3. Visual validation in TimelineJS viewer
4. Edge cases (no dates, long text, many events)

## Success Criteria
- [ ] Valid TimelineJS3 JSON output
- [ ] All temporal events included
- [ ] Proper date formatting
- [ ] Media thumbnails working
- [ ] Interactive timeline renders correctly

## Resources
- TimelineJS3 Documentation: https://timeline.knightlab.com/docs/
- JSON Schema: https://timeline.knightlab.com/docs/json-format.html
- Example timelines: https://timeline.knightlab.com/#examples 