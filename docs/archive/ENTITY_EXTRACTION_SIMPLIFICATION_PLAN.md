# Entity Extraction Simplification Plan

*Created: 2025-07-21 01:05 PDT*
*Author: AI Assistant with Zac Forristall*

## Executive Summary

ClipScribe's current entity extraction pipeline is over-engineered, running 4+ models when Gemini already provides comprehensive entity and relationship extraction. This plan outlines a simplification strategy to improve quality, reduce complexity, and maintain the same cost.

## Current Architecture Problems

### 1. Redundant Processing
- **Gemini** extracts 20-50+ entities with relationships ($0.0035/video)
- **SpaCy** re-extracts basic entities (PERSON, ORG, GPE)
- **GLiNER** re-extracts custom entities
- **REBEL** re-extracts relationships
- **EntityQualityFilter** aggressively filters out entities

### 2. Quality Issues
- Entity count drops from Gemini's 20-50 → 1-6 final entities
- Aggressive language filtering removes valid English entities
- Multiple models create conflicting results requiring complex merging

### 3. Performance Impact
- 4x processing time for marginal benefit
- Complex deduplication and merging logic
- Harder to debug and maintain

## Proposed Solution: Trust Gemini

### Phase 1: Immediate Simplification (Option 1)

#### 1.1 Remove Redundant Extractors
- Remove SpaCy, GLiNER, REBEL from pipeline
- Keep only Gemini's comprehensive extraction
- Simplify AdvancedHybridExtractor to pass-through

#### 1.2 Refactor Quality Filter
- Convert from filtering to tagging
- Add language detection as metadata, not filter
- Let users decide what languages to include

#### 1.3 Benefits
- **Quality**: 20-50+ entities instead of 1-6
- **Speed**: 4x faster processing
- **Simplicity**: Single source of truth
- **Cost**: Same ($0.0035/video)

### Phase 2: Future Enhancement (Option 3 - Roadmap)

#### 2.1 Ontology Integration
- Map entities to Wikidata/DBpedia
- Add semantic types and relationships
- Enable advanced queries and reasoning

#### 2.2 Optional Local Models
- SpaCy/GLiNER as fallback for offline mode
- Configurable pipeline for specific use cases
- Clear documentation on trade-offs

## Implementation Tasks

### 1. Code Changes
```python
# Simplified AdvancedHybridExtractor
class AdvancedHybridExtractor:
    def extract_entities_and_relationships(self, text, transcript=None):
        # If we have Gemini results, use them directly
        if transcript and transcript.entities:
            return self._format_gemini_results(transcript)
        
        # Fallback to local models only if needed
        return self._local_extraction_fallback(text)
```

### 2. Quality Filter Refactor
```python
# From filtering to tagging
class EntityLanguageTagger:
    def tag_entities(self, entities):
        for entity in entities:
            entity.detected_language = self._detect_language(entity.entity)
            entity.language_confidence = self._calculate_confidence(entity.entity)
        return entities  # Return ALL entities, tagged
```

### 3. Testing Plan
- Test with PBS NewsHour segments (rich entities)
- Compare entity counts before/after
- Validate relationship quality
- Measure processing time improvements

### 4. Documentation Updates
- Update architecture diagrams
- Revise entity extraction documentation
- Add migration guide for existing users
- Document language tagging feature

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Entities per video | 1-6 | 20-50+ |
| Processing time | ~4s | ~1s |
| Code complexity | High | Low |
| Maintenance burden | High | Low |
| Entity quality | Variable | Consistent |

## Risk Mitigation

1. **Backward Compatibility**
   - Keep flag for legacy mode if needed
   - Clear migration documentation
   - Version bump to indicate breaking change

2. **Edge Cases**
   - Offline mode support with local models
   - Non-English content handling
   - Very long videos (chunking strategy)

3. **Quality Assurance**
   - Comprehensive test suite
   - Before/after comparisons
   - User feedback collection

## Timeline

### Week 1: Core Implementation
- Day 1-2: Remove redundant extractors
- Day 3-4: Refactor quality filter
- Day 5: Testing and validation

### Week 2: Documentation & Polish
- Day 1-2: Update all documentation
- Day 3-4: Create migration guide
- Day 5: Release v2.20.0

## Future Roadmap (Option 3)

### Q3 2025: Ontology Research
- Evaluate Wikidata, DBpedia, YAGO
- Design integration architecture
- Prototype entity mapping

### Q4 2025: Ontology Integration
- Implement entity type mapping
- Add semantic relationships
- Enable SPARQL-like queries

### 2026: Advanced Features
- Multi-language ontologies
- Custom domain ontologies
- Knowledge graph reasoning

## Conclusion

This simplification will make ClipScribe more effective, easier to maintain, and provide better results. By trusting Gemini's sophisticated extraction and removing redundant processing, we can deliver on our performance promises while reducing complexity. 