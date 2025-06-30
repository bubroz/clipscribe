# Timeline Intelligence v2.0 Architecture

*Last Updated: June 29, 2025*
*Status: CRITICAL REDESIGN REQUIRED*

## 🚨 Current State: Fundamentally Broken

The current Timeline Building Pipeline (v1.0) has critical architectural flaws that make it unusable:

### Major Issues Discovered (June 29, 2025)
1. **Event Duplication**: Same event (`evt_6ZVj1_SE4Mo_0`) repeated 44 times
2. **Wrong Dates**: 90% of events show video publish date (2023) instead of actual event dates (2018-2021)
3. **Entity Explosion**: Creates duplicate events for each entity combination
4. **No Temporal Intelligence**: Extracts entity mentions, not temporal events
5. **No Quality Control**: No deduplication, filtering, or validation

### Example of Current Broken Output
```json
{
  "event_id": "evt_6ZVj1_SE4Mo_0",  // Same ID repeated 44 times!
  "timestamp": "2023-01-03T19:00:08",  // Wrong date (video publish date)
  "description": "Claudio Ganyeri's expertise...",  // Same description
  "involved_entities": ["Pegasus"],  // Different entity combinations
  "extracted_date": null,  // Failed to extract actual date
  "date_source": "video_published_date"  // Fallback to wrong source
}
```

## 🚀 BREAKTHROUGH: yt-dlp Temporal Intelligence Integration

**MAJOR DISCOVERY**: ClipScribe already uses yt-dlp but ignores its powerful temporal metadata extraction! This could solve most of our timeline issues.

### yt-dlp Temporal Features We're Missing:

#### 1. Chapter Information (`--embed-chapters`)
```bash
# Extract chapter timestamps and titles
yt-dlp --embed-chapters --extract-info URL
```
**Benefits for Timeline v2.0:**
- Precise chapter boundaries with timestamps
- Chapter titles could indicate topic changes
- Natural video segmentation for better temporal parsing

#### 2. Word-Level Captions (`--write-subs --embed-subs`)
```bash
# Get precise word-level timestamps
yt-dlp --write-auto-subs --write-subs --embed-subs --sub-langs en URL
```
**Benefits for Timeline v2.0:**
- Exact timestamp for every word spoken
- More precise event location than current transcript
- Could enable sub-second temporal event extraction

#### 3. Section Downloads (`--download-sections`)
```bash
# Extract specific time ranges
yt-dlp --download-sections "*21:30-45:15" URL
```
**Benefits for Timeline v2.0:**
- Could process only relevant sections
- Focus temporal extraction on important segments

#### 4. SponsorBlock Integration (`--sponsorblock-mark`)
```bash
# Identify content vs non-content sections
yt-dlp --sponsorblock-mark all URL
```
**Benefits for Timeline v2.0:**
- Skip intro/outro/sponsor segments
- Focus on actual content for temporal extraction
- Better signal-to-noise ratio

### Enhanced Universal Video Client for Timeline v2.0
```python
class TemporalUniversalVideoClient(UniversalVideoClient):
    """Enhanced video client with temporal intelligence extraction."""
    
    def __init__(self):
        super().__init__()
        # Add temporal extraction options
        self.temporal_opts = {
            **self.ydl_opts,
            'writesubtitles': True,           # Extract subtitles
            'writeautomaticsub': True,        # Auto-generated captions
            'subtitleslangs': ['en'],         # English subtitles
            'writeinfojson': True,            # Full metadata
            'extract_flat': False,            # Full extraction
            'sponsorblock_mark': 'all',       # SponsorBlock markers
            'embed_chapters': True,           # Chapter information
            'getcomments': True,              # User comments (may have timestamps)
        }
    
    async def extract_temporal_metadata(self, video_url: str) -> TemporalMetadata:
        """Extract comprehensive temporal metadata from video."""
        
        with yt_dlp.YoutubeDL(self.temporal_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return TemporalMetadata(
                chapters=self._extract_chapters(info),
                subtitles=self._extract_subtitles(info),
                sponsorblock_segments=self._extract_sponsorblock(info),
                comments_with_timestamps=self._extract_timestamped_comments(info),
                video_sections=self._identify_content_sections(info)
            )
    
    def _extract_chapters(self, info: dict) -> List[Chapter]:
        """Extract chapter information with precise timestamps."""
        chapters = []
        for chapter in info.get('chapters', []):
            chapters.append(Chapter(
                title=chapter.get('title', ''),
                start_time=chapter.get('start_time', 0),
                end_time=chapter.get('end_time', 0),
                url=chapter.get('url', '')
            ))
        return chapters
    
    def _extract_subtitles(self, info: dict) -> WordLevelSubtitles:
        """Extract word-level subtitle data with precise timestamps."""
        # Parse subtitle files for word-level timing
        # This enables sub-second temporal event extraction
        pass
    
    def _extract_sponsorblock(self, info: dict) -> List[VideoSegment]:
        """Extract SponsorBlock segments to identify content vs non-content."""
        segments = []
        for segment in info.get('sponsorblock_chapters', []):
            segments.append(VideoSegment(
                category=segment.get('category'),  # intro, sponsor, outro, etc.
                start_time=segment.get('start_time'),
                end_time=segment.get('end_time')
            ))
        return segments
```

### Timeline Pipeline v2.0 with yt-dlp Integration
```python
class TemporalEventExtractorV2:
    """Enhanced temporal event extractor using yt-dlp metadata."""
    
    async def extract_temporal_events(self, 
                                    video_url: str,
                                    transcript: str) -> List[TemporalEvent]:
        """Extract events using yt-dlp temporal metadata + transcript analysis."""
        
        # 1. Get comprehensive temporal metadata from yt-dlp
        temporal_metadata = await self.video_client.extract_temporal_metadata(video_url)
        
        # 2. Use chapter boundaries to segment transcript
        chapter_segments = self._segment_transcript_by_chapters(
            transcript, temporal_metadata.chapters
        )
        
        # 3. Use word-level subtitles for precise timing
        word_timestamps = temporal_metadata.subtitles.word_level_timing
        
        # 4. Extract events from each segment with precise timestamps
        events = []
        for segment in chapter_segments:
            segment_events = await self._extract_events_from_segment(
                segment, word_timestamps
            )
            events.extend(segment_events)
        
        # 5. Filter out non-content sections (intro/outro/sponsors)
        content_events = self._filter_content_events(
            events, temporal_metadata.sponsorblock_segments
        )
        
        return content_events
    
    def _get_precise_timestamp(self, text_phrase: str, word_timestamps: dict) -> float:
        """Get precise video timestamp for when specific text was spoken."""
        # Use word-level timing to find exact moment phrase was said
        # This enables sub-second precision for temporal events
        pass
```

### Benefits of yt-dlp Integration:

1. **Precise Timestamps**: Sub-second accuracy instead of rough estimates
2. **Chapter Segmentation**: Natural video structure for better parsing
3. **Content Filtering**: Skip intro/outro/sponsors automatically
4. **Word-Level Timing**: Know exactly when each word was spoken
5. **Rich Context**: Comments, descriptions with temporal references
6. **Multi-Language**: Support for multiple subtitle languages

### Implementation Impact:

**Before (Current Broken State):**
- Events all at `video_timestamp_seconds: 0`
- Wrong dates from video metadata
- 44 duplicates of same event

**After (yt-dlp Enhanced):**
- Precise timestamps: "At 15:23, when discussing NSO Group..."
- Chapter context: "In the 'Investigation Methods' chapter..."
- Content-only events: No timeline pollution from intros/sponsors
- Sub-second precision: "At 15:23.7 seconds, the speaker says..."

This integration could transform our broken timeline into a precision temporal intelligence system :-)

## 📐 Timeline Pipeline v2.0 Architecture

### Core Design Principles
1. **Events are Temporal Facts**: An event must have "what happened" and "when it happened"
2. **One Event, One Entry**: Never duplicate events with different entity combinations
3. **Dates from Content**: Always extract dates from transcript/content, never from metadata
4. **Quality Over Quantity**: Better to have 10 accurate events than 100 duplicates
5. **Cross-Video Synthesis**: Merge similar events from multiple videos

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Timeline Pipeline v2.0                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Video Input → Temporal Event Extraction → Event Processing │
│                           ↓                        ↓        │
│              Temporal NLP Parser          Event Deduplicator│
│                           ↓                        ↓        │
│              Date Normalization          Quality Filter     │
│                           ↓                        ↓        │
│              Event Synthesis ← ← ← ← ← Cross-Video Merger  │
│                           ↓                                 │
│                  High-Quality Timeline                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Component Specifications

### 1. Temporal Event Extractor
```python
class TemporalEventExtractor:
    """Extract actual temporal events from video transcripts."""
    
    def extract_temporal_events(self, transcript: str, video_metadata: dict) -> List[TemporalEvent]:
        """
        Extract events that have both temporal and factual components.
        
        Looks for patterns like:
        - "In 2018, NSO Group was founded"
        - "On July 15th, the investigation revealed"
        - "Three months later, Khashoggi was killed"
        - "The following year, Pegasus was discovered on phones"
        """
        events = []
        
        # Use spaCy's temporal NER
        doc = self.nlp(transcript)
        
        # Find temporal expressions and their context
        for sent in doc.sents:
            temporal_markers = self._extract_temporal_markers(sent)
            if temporal_markers:
                event = self._build_event_from_sentence(sent, temporal_markers)
                if event and self._is_valid_event(event):
                    events.append(event)
        
        return events
```

### 2. Temporal Expression Parser
```python
class TemporalExpressionParser:
    """Parse and normalize temporal expressions to absolute dates."""
    
    def parse_temporal_expression(self, 
                                expression: str, 
                                context_date: datetime,
                                video_metadata: dict) -> TemporalResult:
        """
        Convert temporal expressions to absolute dates.
        
        Examples:
        - "July 2021" → 2021-07-01
        - "last year" → context_date - 1 year
        - "three months ago" → context_date - 3 months
        - "in 2018" → 2018-01-01 (with year precision)
        
        NEVER returns video publish date as fallback!
        """
        # Use dateparser with strict settings
        parsed = dateparser.parse(
            expression,
            settings={
                'RELATIVE_BASE': context_date,
                'STRICT_PARSING': True,
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
        
        if not parsed:
            return None
            
        return TemporalResult(
            date=parsed,
            precision=self._determine_precision(expression),
            confidence=self._calculate_confidence(expression, parsed),
            original_text=expression
        )
```

### 3. Event Deduplicator
```python
class EventDeduplicator:
    """Merge duplicate events and consolidate entities."""
    
    def deduplicate_events(self, events: List[Event]) -> List[Event]:
        """
        Merge events with same ID or similar content.
        
        Strategy:
        1. Group by event_id
        2. For each group, merge all entities
        3. Keep best date extraction
        4. Consolidate descriptions
        5. Average confidence scores
        """
        # Group by event_id
        event_groups = defaultdict(list)
        for event in events:
            event_groups[event.event_id].append(event)
        
        # Merge each group
        deduplicated = []
        for event_id, group in event_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                merged = self._merge_event_group(group)
                deduplicated.append(merged)
        
        # Secondary pass: merge semantically similar events
        return self._merge_similar_events(deduplicated)
```

### 4. Timeline Quality Filter
```python
class TimelineQualityFilter:
    """Ensure only real temporal events make it to timeline."""
    
    def filter_events(self, events: List[Event]) -> List[Event]:
        """
        Apply quality criteria to filter events.
        
        Requirements:
        - Must have extracted date (not video date)
        - Must have meaningful description
        - Must have confidence > 0.7
        - Must not be generic statement
        - Must describe something that happened
        """
        filtered = []
        
        for event in events:
            # Check date quality
            if not event.extracted_date or event.date_source == "video_published_date":
                continue
                
            # Check description quality
            if self._is_generic_statement(event.description):
                continue
                
            # Check temporal quality
            if not self._describes_temporal_event(event.description):
                continue
                
            # Check confidence
            if event.confidence < 0.7:
                continue
                
            filtered.append(event)
            
        return filtered
```

### 5. Cross-Video Timeline Synthesizer
```python
class CrossVideoTimelineSynthesizer:
    """Build coherent timeline across multiple videos."""
    
    def synthesize_timeline(self, 
                          video_timelines: Dict[str, List[Event]]) -> Timeline:
        """
        Merge timelines from multiple videos into coherent narrative.
        
        Process:
        1. Collect all events from all videos
        2. Identify same/similar events across videos
        3. Merge duplicates keeping best information
        4. Resolve date conflicts
        5. Order chronologically
        6. Build narrative connections
        """
        # Collect all events
        all_events = []
        for video_id, events in video_timelines.items():
            for event in events:
                event.source_videos = [video_id]
                all_events.append(event)
        
        # Find and merge similar events
        merged_events = self._merge_similar_cross_video_events(all_events)
        
        # Resolve temporal conflicts
        resolved_events = self._resolve_temporal_conflicts(merged_events)
        
        # Build chronological timeline
        timeline = self._build_chronological_timeline(resolved_events)
        
        # Add narrative connections
        return self._add_narrative_connections(timeline)
```

## 📊 Event Data Model v2.0

```python
@dataclass
class TemporalEvent:
    """Represents a temporal event in the timeline."""
    
    # Identity
    event_id: str  # Unique based on content + time
    content_hash: str  # Hash of description + date for deduplication
    
    # Temporal Information
    date: datetime  # Actual date of event
    date_precision: DatePrecision  # YEAR, MONTH, DAY, EXACT
    date_confidence: float  # 0.0-1.0
    extracted_date_text: str  # Original text that led to date
    
    # Event Information
    description: str  # What happened
    event_type: EventType  # FACTUAL, CLAIMED, REPORTED, INFERRED
    involved_entities: List[Entity]  # All entities (consolidated)
    
    # Source Information
    source_videos: List[str]  # Can come from multiple videos
    video_timestamps: Dict[str, float]  # Timestamp per video
    extraction_method: str  # How this was extracted
    
    # Quality Metrics
    confidence: float  # Overall confidence
    validation_status: ValidationStatus  # VERIFIED, UNVERIFIED, DISPUTED
    validation_notes: Optional[str]
```

## 🎯 Quality Metrics

### Event Quality Score
```python
def calculate_event_quality_score(event: TemporalEvent) -> float:
    """Calculate quality score for timeline event."""
    
    score = 0.0
    
    # Date quality (40%)
    if event.date_precision == DatePrecision.EXACT:
        score += 0.4
    elif event.date_precision == DatePrecision.DAY:
        score += 0.3
    elif event.date_precision == DatePrecision.MONTH:
        score += 0.2
    elif event.date_precision == DatePrecision.YEAR:
        score += 0.1
    
    # Description quality (30%)
    if len(event.description) > 50 and event.event_type == EventType.FACTUAL:
        score += 0.3
    elif len(event.description) > 30:
        score += 0.2
    else:
        score += 0.1
    
    # Entity richness (20%)
    entity_score = min(len(event.involved_entities) / 5.0, 1.0) * 0.2
    score += entity_score
    
    # Confidence (10%)
    score += event.confidence * 0.1
    
    return score
```

## 🚀 Implementation Plan

### Phase 1: yt-dlp Temporal Integration (Week 1) **HIGH PRIORITY**
1. **Enhanced UniversalVideoClient** - Add temporal metadata extraction
2. **Chapter Information Extraction** - Parse video chapters with timestamps
3. **Word-Level Subtitle Integration** - Extract precise timing data
4. **SponsorBlock Integration** - Filter content vs non-content sections
5. **Test with Pegasus documentary** - Validate temporal metadata quality

### Phase 2: Core Temporal Extraction (Week 2)
1. Implement TemporalEventExtractorV2 with yt-dlp metadata
2. Build TemporalExpressionParser with dateparser + chapter context
3. Create comprehensive test suite with known timelines
4. Validate against Pegasus documentary timeline with precise timestamps

### Phase 3: Deduplication & Quality (Week 3)
1. Implement EventDeduplicator with content hashing + temporal proximity
2. Build TimelineQualityFilter with yt-dlp quality metrics
3. Test with multi-video collections
4. Measure quality improvements vs v1.0

### Phase 4: Cross-Video Synthesis (Week 4)
1. Implement CrossVideoTimelineSynthesizer with chapter alignment
2. Build narrative connection algorithms using precise timestamps
3. Test with documentary series
4. Validate temporal coherence across videos

### Phase 5: Integration & UI (Week 5)
1. Replace existing Timeline Building Pipeline
2. Update Mission Control UI with precision timestamp display
3. Add yt-dlp quality indicators to UI
4. Deploy and monitor

## 🧪 Testing Strategy

### Test Cases
1. **Known Timeline**: Pegasus investigation (2018-2021)
   - Expected: ~20-30 high-quality events with precise timestamps
   - Chapter-based segmentation
   - No duplicates, all with correct dates
   
2. **Multi-Video Series**: Documentary parts 1 & 2
   - Expected: Merged events from both videos with chapter correlation
   - Consistent chronology
   - Chapter-based event grouping
   
3. **yt-dlp Features**:
   - Videos with chapters (timestamps + titles)
   - Videos with word-level captions
   - Videos with SponsorBlock data
   - Multi-language subtitle support

### Success Metrics
- **Deduplication Rate**: >95% (no duplicate events)
- **Date Accuracy**: >90% correct dates
- **Timestamp Precision**: Sub-second accuracy where available
- **Event Quality**: Average score >0.7
- **Processing Time**: <30s per hour of video
- **Chapter Utilization**: >80% of videos with chapters use them effectively

## ⚠️ Migration Notes

The v2.0 pipeline is NOT backward compatible with v1.0 output. Migration requires:
1. Reprocessing all existing collections with yt-dlp temporal extraction
2. Updating all timeline visualizations to show precise timestamps
3. Migrating stored timeline data to new format with chapter context
4. Updating API contracts to include yt-dlp metadata

**Key Change**: Timeline events will have both video timestamps AND chapter context, enabling much richer temporal intelligence.

## 📝 Conclusion

Timeline Pipeline v2.0 represents a complete architectural redesign focused on extracting real temporal events with accurate dates. By implementing proper temporal NLP, event deduplication, and quality filtering, we can transform the currently broken timeline feature into a powerful tool for understanding chronological narratives across video content.

Remember: Quality over quantity - 20 accurate events are infinitely more valuable than 82 duplicates with wrong dates :-) 