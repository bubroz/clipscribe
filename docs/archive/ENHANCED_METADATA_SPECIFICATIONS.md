# Enhanced Entity & Relationship Metadata Specifications

*Last Updated: July 6, 2025 13:33 PDT*
*Version: v2.19.0 Phase 3 Architecture Ready*
*Related: [Extraction Technology](EXTRACTION_TECHNOLOGY.md) | [Chimera Integration](CHIMERA_INTEGRATION.md)*

## Overview

This document defines the enhanced metadata structures for ClipScribe v2.19.0, focusing on providing rich, structured data that enables sophisticated analysis by tools like Chimera Researcher.

## Design Principles

1. **Backward Compatibility**: All enhancements are additive - existing integrations continue to work
2. **Source Attribution**: Every piece of data traces back to its extraction method
3. **Confidence Scoring**: All extractions include reliability metrics
4. **Evidence-Based**: Claims are supported by context and evidence
5. **Chimera-Ready**: Structured for easy consumption by analysis tools

## Entity Metadata Structure

### Enhanced Entity Model (v2.19.0)

```python
class EnhancedEntity(BaseModel):
    """Enhanced entity with confidence and attribution."""
    
    # Core fields (backward compatible)
    entity: str                    # The entity text (e.g., "Joe Biden")
    type: str                      # Entity type (PERSON, ORG, LOC, etc.)
    
    # Enhanced metadata (new in v2.19.0)
    confidence: float              # Overall confidence score (0.0-1.0)
    extraction_sources: List[str]  # Which methods found this entity
    mention_count: int             # Total occurrences in video
    
    # Context windows
    context_windows: List[EntityContext]  # Surrounding context for each mention
    
    # Alias management
    aliases: List[str]             # Alternative names/references
    canonical_form: str            # Normalized primary form
    
    # Source-specific confidence
    source_confidence: Dict[str, float]  # Per-source confidence scores
    
    # Temporal distribution
    temporal_distribution: List[TemporalMention]  # When entity appears

class EntityContext(BaseModel):
    """Context window for an entity mention."""
    
    text: str                      # Surrounding text (±50 chars)
    timestamp: str                 # When mentioned (HH:MM:SS)
    confidence: float              # Context-specific confidence
    speaker: Optional[str]         # Who mentioned it (if known)
    visual_present: bool           # Entity visible on screen
    
class TemporalMention(BaseModel):
    """When and how an entity is mentioned."""
    
    timestamp: str                 # HH:MM:SS format
    duration: float                # How long discussed (seconds)
    context_type: str              # "spoken", "visual", "both"
```

### Confidence Score Calculation

```python
def calculate_entity_confidence(
    entity: str,
    sources: List[ExtractionSource]
) -> float:
    """Calculate overall confidence score for an entity."""
    
    # Base confidence from source agreement
    source_count = len(sources)
    base_confidence = min(0.5 + (source_count * 0.15), 0.95)
    
    # Modifiers
    modifiers = []
    
    # Length modifier (longer entities more reliable)
    word_count = len(entity.split())
    if word_count >= 3:
        modifiers.append(0.05)
    elif word_count == 1 and len(entity) < 4:
        modifiers.append(-0.10)
    
    # Type modifier (some types more reliable)
    type_confidence = {
        "PERSON": 0.05,
        "ORG": 0.03,
        "GPE": 0.04,
        "DATE": 0.08,
        "MISC": -0.05
    }
    modifiers.append(type_confidence.get(entity_type, 0))
    
    # Source quality modifier
    high_quality_sources = ["gemini", "gliner", "spacy"]
    if any(s in sources for s in high_quality_sources):
        modifiers.append(0.05)
    
    # Calculate final confidence
    final_confidence = base_confidence + sum(modifiers)
    return max(0.1, min(0.99, final_confidence))
```

### Alias Detection & Normalization

```python
class AliasNormalizer:
    """Detect and normalize entity aliases."""
    
    def normalize_entities(
        self,
        entities: List[Entity]
    ) -> List[EnhancedEntity]:
        """Group entities by their canonical form."""
        
        # Common patterns
        patterns = [
            # Titles: "President Biden" → "Joe Biden"
            (r"^(President|Dr\.|Mr\.|Mrs\.|Ms\.)\s+", ""),
            # Last names: "Biden" → check against full names
            # Acronyms: "FBI" → "Federal Bureau of Investigation"
            # Common variations: "US" → "United States"
        ]
        
        # Group by similarity
        groups = self._group_similar_entities(entities)
        
        # Select canonical form (most complete/frequent)
        enhanced = []
        for group in groups:
            canonical = self._select_canonical(group)
            aliases = [e.entity for e in group if e.entity != canonical]
            
            enhanced.append(EnhancedEntity(
                entity=canonical,
                aliases=aliases,
                mention_count=sum(e.count for e in group),
                # ... other fields
            ))
        
        return enhanced
```

## Relationship Metadata Structure

### Enhanced Relationship Model (v2.19.0)

```python
class EnhancedRelationship(BaseModel):
    """Relationship with evidence and context."""
    
    # Core fields (backward compatible)
    subject: str                   # Subject entity
    predicate: str                 # Relationship type
    object: str                    # Object entity
    
    # Enhanced metadata (new in v2.19.0)
    confidence: float              # Overall confidence (0.0-1.0)
    evidence: RelationshipEvidence # Supporting evidence
    
    # Validation
    supporting_mentions: int       # How many times mentioned
    contradictions: List[Contradiction]  # Conflicting claims
    
    # Temporal context
    first_mention: str            # When first stated
    temporal_validity: Optional[TemporalValidity]  # When true
    
    # Source attribution
    extraction_method: str         # Which method found this
    extraction_confidence: Dict[str, float]  # Per-method confidence

class RelationshipEvidence(BaseModel):
    """Evidence supporting a relationship."""
    
    direct_quote: Optional[str]    # Exact quote if available
    timestamp: str                 # When claimed (HH:MM:SS)
    speaker: Optional[str]         # Who made the claim
    visual_context: Optional[str]  # What was on screen
    confidence_factors: List[str]  # Why we're confident
    
class Contradiction(BaseModel):
    """A contradicting claim."""
    
    claim: str                     # The contradicting statement
    timestamp: str                 # When stated
    speaker: Optional[str]         # Who contradicted
    severity: str                  # "minor", "major", "direct"
    
class TemporalValidity(BaseModel):
    """When a relationship is/was valid."""
    
    start_date: Optional[str]      # When relationship began
    end_date: Optional[str]        # When it ended (if applicable)
    certainty: str                 # "stated", "inferred", "uncertain"
```

### Evidence Chain Building

```python
class EvidenceChainBuilder:
    """Build evidence chains for relationships."""
    
    def build_evidence(
        self,
        relationship: Relationship,
        transcript: Transcript,
        visual_context: Dict[str, Any]
    ) -> RelationshipEvidence:
        """Construct evidence for a relationship."""
        
        evidence = RelationshipEvidence()
        
        # Find direct quotes
        quote_window = 100  # characters around relationship
        for segment in transcript.segments:
            if self._contains_relationship(segment, relationship):
                evidence.direct_quote = self._extract_quote(
                    segment, 
                    relationship,
                    window=quote_window
                )
                evidence.timestamp = segment.timestamp
                evidence.speaker = segment.speaker
                break
        
        # Add visual context
        if visual_context:
            timestamp_sec = self._timestamp_to_seconds(evidence.timestamp)
            evidence.visual_context = visual_context.get(
                timestamp_sec,
                "No specific visual context"
            )
        
        # Determine confidence factors
        evidence.confidence_factors = []
        if evidence.direct_quote:
            evidence.confidence_factors.append("direct_quote_found")
        if evidence.speaker:
            evidence.confidence_factors.append("speaker_identified")
        if relationship.subject in evidence.direct_quote:
            evidence.confidence_factors.append("subject_in_quote")
            
        return evidence
```

## Temporal Enhancement Structure

### Temporal Reference Resolution

```python
class TemporalReference(BaseModel):
    """A temporal reference in the video."""
    
    reference_text: str            # Original text (e.g., "last Tuesday")
    reference_type: str            # "relative", "absolute", "contextual"
    resolved_date: Optional[str]   # Resolved date (YYYY-MM-DD)
    confidence: float              # Resolution confidence
    resolution_method: str         # How we resolved it
    context: str                   # Surrounding context

class TemporalResolver:
    """Resolve relative temporal references."""
    
    def resolve_reference(
        self,
        reference: str,
        video_date: datetime,
        context: str
    ) -> TemporalReference:
        """Resolve a temporal reference to absolute date."""
        
        # Relative date patterns
        relative_patterns = {
            r"last (\w+day)": self._resolve_last_weekday,
            r"(\d+) days? ago": self._resolve_days_ago,
            r"last (week|month|year)": self._resolve_last_period,
            r"yesterday": lambda: video_date - timedelta(days=1),
            r"today": lambda: video_date,
            r"tomorrow": lambda: video_date + timedelta(days=1)
        }
        
        # Try each pattern
        for pattern, resolver in relative_patterns.items():
            match = re.search(pattern, reference, re.IGNORECASE)
            if match:
                resolved = resolver(match, video_date)
                return TemporalReference(
                    reference_text=reference,
                    reference_type="relative",
                    resolved_date=resolved.strftime("%Y-%m-%d"),
                    confidence=0.85,
                    resolution_method=f"pattern:{pattern}",
                    context=context
                )
        
        # Check if already absolute
        absolute_date = self._parse_absolute_date(reference)
        if absolute_date:
            return TemporalReference(
                reference_text=reference,
                reference_type="absolute",
                resolved_date=absolute_date.strftime("%Y-%m-%d"),
                confidence=0.95,
                resolution_method="direct_parse",
                context=context
            )
        
        # Contextual resolution (requires more context)
        contextual = self._resolve_from_context(reference, context)
        if contextual:
            return contextual
            
        # Unresolved
        return TemporalReference(
            reference_text=reference,
            reference_type="unknown",
            resolved_date=None,
            confidence=0.0,
            resolution_method="unresolved",
            context=context
        )
```

## Integration Format

### Chimera-Compatible Output

```json
{
  "video_id": "6ZVj1_SE4Mo",
  "extraction_version": "2.19.0",
  "extraction_timestamp": "2025-07-05T10:36:00Z",
  
  "entities": [
    {
      "entity": "Joe Biden",
      "type": "PERSON",
      "confidence": 0.95,
      "extraction_sources": ["spacy", "gliner", "gemini"],
      "mention_count": 12,
      "context_windows": [
        {
          "text": "...President Joe Biden announced today...",
          "timestamp": "00:02:15",
          "confidence": 0.98,
          "speaker": "News Anchor",
          "visual_present": true
        }
      ],
      "aliases": ["President Biden", "Biden", "The President"],
      "canonical_form": "Joe Biden",
      "source_confidence": {
        "spacy": 0.92,
        "gliner": 0.94,
        "gemini": 0.98
      },
      "temporal_distribution": [
        {
          "timestamp": "00:02:15",
          "duration": 45.5,
          "context_type": "both"
        }
      ]
    }
  ],
  
  "relationships": [
    {
      "subject": "Joe Biden",
      "predicate": "announced",
      "object": "infrastructure bill",
      "confidence": 0.92,
      "evidence": {
        "direct_quote": "Today, I'm proud to announce our new infrastructure bill",
        "timestamp": "00:02:45",
        "speaker": "Joe Biden",
        "visual_context": "Podium with presidential seal",
        "confidence_factors": [
          "direct_quote_found",
          "speaker_identified",
          "subject_in_quote",
          "visual_confirmation"
        ]
      },
      "supporting_mentions": 3,
      "contradictions": [],
      "first_mention": "00:02:45",
      "temporal_validity": {
        "start_date": "2025-07-05",
        "end_date": null,
        "certainty": "stated"
      },
      "extraction_method": "rebel",
      "extraction_confidence": {
        "rebel": 0.88,
        "gemini": 0.95
      }
    }
  ],
  
  "temporal_references": [
    {
      "reference_text": "last Tuesday",
      "reference_type": "relative",
      "resolved_date": "2025-06-30",
      "confidence": 0.85,
      "resolution_method": "pattern:last (\\w+day)",
      "context": "The meeting last Tuesday resulted in..."
    }
  ],
  
  "metadata": {
    "processing_time": 125.3,
    "total_cost": 0.0255,
    "quality_metrics": {
      "entity_confidence_avg": 0.89,
      "relationship_confidence_avg": 0.86,
      "temporal_resolution_rate": 0.78
    }
  }
}
```

## Implementation Status

### ✅ Phase 1: Entity Confidence & Attribution (COMPLETE)
1. ✅ Extended Entity model with EnhancedEntity structure
2. ✅ Updated extractors to calculate confidence scores
3. ✅ Implemented alias detection and normalization
4. ✅ Added comprehensive source attribution tracking
5. ✅ 90% test coverage with 4/4 tests passing

### ✅ Phase 2: Relationship Evidence (COMPLETE)
1. ✅ Extended Relationship model with evidence chain support
2. ✅ Implemented RelationshipEvidenceExtractor with quote extraction
3. ✅ Added contradiction detection across transcript segments
4. ✅ Included visual correlation and supporting mention tracking
5. ✅ 95% test coverage with 17/17 tests passing

### 🚧 Phase 3: Temporal Enhancement (ARCHITECTURE READY)
1. ✅ Created TemporalReferenceResolver with intelligent content date detection
2. ✅ Implemented multi-source date detection (explicit dates, Gemini extraction, context clues, metadata)
3. ✅ Built content vs publication date differential handling for archive footage
4. 🚧 Pipeline integration into AdvancedHybridExtractor (NEXT)
5. 🚧 Comprehensive testing suite creation following Phase 1 & 2 patterns (NEXT)

## Testing Strategy

### Unit Tests
- Confidence calculation accuracy
- Alias detection correctness
- Evidence chain building
- Temporal resolution accuracy

### Integration Tests
- Full pipeline with enhanced metadata
- Backward compatibility verification
- Chimera format validation
- Performance benchmarks

### Quality Metrics
- Average confidence scores
- Resolution success rates
- Evidence completeness
- Processing time impact

## Migration Path

### For Existing Users
1. All existing fields remain unchanged
2. New fields are optional/have defaults
3. Gradual adoption possible
4. No breaking changes

### For Chimera Integration
1. Enhanced format immediately available
2. Richer data for analysis
3. Better confidence metrics
4. More evidence for validation

Remember: The goal is richer extraction, not analysis. We provide the data, Chimera provides the insights :-) 