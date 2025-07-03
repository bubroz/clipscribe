# ⚠️ DISCONTINUED: TimelineJS3 Export Implementation Plan

**STATUS: PERMANENTLY DISCONTINUED - July 2, 2025**

This feature has been **permanently cancelled** as part of ClipScribe's strategic pivot away from timeline development. Timeline accuracy was only 24.66%, insufficient for production use.

**See**: [Strategic Pivot Document](STRATEGIC_PIVOT_2025_07_02.md) for details on the strategic decision and new direction.

**Replacement**: ClipScribe now focuses exclusively on core intelligence extraction enhancement: entity extraction, relationship mapping, and cross-video intelligence analysis.

---

# ARCHIVED CONTENT BELOW

*The content below has been archived for historical reference only.*

# TimelineJS3 Export Implementation Plan

*Last Updated: June 30, 2025*  
*Status: CANCELLED - Strategic pivot to core intelligence extraction*

Add TimelineJS3 export format to ClipScribe for beautiful, interactive timeline visualizations.

## TimelineJS3 JSON Structure

The TimelineJS3 format expects a specific JSON structure with a title slide and events array:

```json
{
  "title": {
    "media": {
      "url": "",
      "caption": "",
      "credit": ""
    },
    "text": {
      "headline": "Timeline Title",
      "text": "Timeline Description"
    }
  },
  "events": [
    {
      "media": {
        "url": "https://youtube.com/...",
        "caption": "Video description",
        "credit": "Video source"
      },
      "start_date": {
        "year": "2023",
        "month": "6",
        "day": "15"
      },
      "text": {
        "headline": "Event Title",
        "text": "Event description"
      }
    }
  ]
}
```

## Implementation Plan (CANCELLED)

### 1. Create TimelineJS Formatter (Day 1)
**File**: `src/clipscribe/utils/timeline_js_formatter.py`

```python
class TimelineJSFormatter:
    """Convert Timeline v2.0 data to TimelineJS3 format."""
    
    def format_timeline(self, timeline_data: ConsolidatedTimeline) -> dict:
        """Convert consolidated timeline to TimelineJS3 JSON."""
        # Implementation cancelled
```

### 2. Update Output Format System (Day 1)
- Add `timelinejs` to OutputFormat enum
- Update `OUTPUT_FORMAT_INFO` with TimelineJS details

### 3. Integration into VideoRetriever (Day 1)
- Modify `_save_transcript_files` method
- Add `_save_timelinejs_file` method
- Add TimelineJS export in `_save_transcript_files`

### 4. Update CLI Interface (Day 1)
- Add timeline_js as a supported format
- Add `--format timelinejs` option

### 5. Testing & Validation (Day 2)
- Use PBS NewsHour timeline data
- Test real-world TimelineJS3 export
- Visual validation in TimelineJS viewer

## Expected Output

### Sample TimelineJS3 Export
- Map ExtractedDate precision to TimelineJS format
- Handle events without dates (use video date)
- Include media URLs and captions for rich timeline

## Acceptance Criteria (CANCELLED)

Timeline development discontinued due to insufficient accuracy.

1. Production-ready TimelineJS formatter
2. Integration test with real timeline data
3. Visual validation in TimelineJS viewer

### Success Metrics
- [ ] Valid TimelineJS3 JSON output
- [ ] No timeline processing errors
- [ ] Beautiful visual timeline render
- [ ] Interactive timeline renders correctly

## Resources
- TimelineJS3 Documentation: https://timeline.knightlab.com/docs/
- JSON Schema: https://timeline.knightlab.com/docs/json-format.html
- Example timelines: https://timeline.knightlab.com/#examples 