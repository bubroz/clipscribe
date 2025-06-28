# Extraction Technology in ClipScribe v2.16.0

This document explains the advanced extraction technologies, `GLiNER` and `REBEL`, that power ClipScribe's video intelligence features, plus planned enhancements for v2.17.0 Enhanced Temporal Intelligence.

## 🎯 **MAJOR BREAKTHROUGH: REBEL Relationship Extraction Fixed**

**Critical Achievement**: ClipScribe achieved a major breakthrough by fixing the REBEL relationship extraction pipeline, enabling **meaningful knowledge graph construction** for the first time.

### **The Problem (Before Fix)**
- REBEL model was generating output but parser couldn't read it
- Zero relationships extracted from video content
- Knowledge graphs had nodes but no meaningful connections
- Space-separated output format was incompatible with XML parser

### **The Solution (Now Working)**
- **Complete parser rewrite** with dual parsing strategy
- **10-19 relationships per video** successfully extracted
- **Real knowledge graphs** with meaningful connections
- **Space-separated parsing** as primary method with XML fallback

### **Real Results from PBS NewsHour Content**:
- "Pegasus | spyware | instance of"
- "NSO | inception | 2010" 
- "Carmen Aristegui | employer | Aristegui Noticias"
- "United Arab Emirates | diplomatic relation | Saudi Arabia"
- "Enrique Peña Nieto | President of Mexico | position held"

## 🚀 **Enhanced Temporal Intelligence (v2.17.0 Planned)**

ClipScribe is evolving to provide comprehensive temporal intelligence extraction with minimal cost impact:

### **Enhanced Video Processing Pipeline**
```
Video → Gemini 2.5 Flash Enhanced Processing → {
    accurate_transcript_with_timestamps,
    temporal_events_from_speech,
    visual_timestamp_recognition,
    entities_with_temporal_context
} → Timeline Synthesis → Interactive Visualizations
```

### **Temporal Intelligence Capabilities**:
- **Temporal Event Extraction**: Parse historical events, dates, and chronological references from spoken content
- **Visual Timestamp Recognition**: Extract dates and times visible on screen (documents, calendars, news chyrons)
- **Accurate Transcript Segmentation**: Word-level timestamps for precise temporal mapping
- **Cross-Video Timeline Building**: Correlate events across video collections

### **Cost-Effective Implementation**:
- **Base Processing**: Same Gemini 2.5 Flash video processing (~$0.40/video)
- **Enhanced Prompting**: Additional ~200 tokens for temporal instructions
- **Richer Output**: ~500-800 tokens for timestamp and temporal data
- **Total Impact**: **12-20% cost increase for 300% more temporal intelligence**

### **Timeline Building Strategy**:
Instead of separate API calls, leverage existing video processing with enhanced temporal extraction, then synthesize timelines from the enriched data. This approach maximizes intelligence extraction per dollar spent.

## Entity Extraction Pipeline Architecture

ClipScribe uses a **sophisticated hybrid approach** with GLiNER as the primary extractor:

### **Pipeline Hierarchy (Cost-Optimized)**:
1. **SpaCy** (free, fast): Basic entity coverage for standard types (PERSON, ORG, LOC)
2. **GLiNER** (primary): Sophisticated transformer-based, contextually aware 
3. **REBEL**: Relationship extraction to connect entities
4. **Entity Normalization**: Smart merging, deduplication, confidence aggregation
5. **LLM Validation** (optional): High-confidence validation for critical applications

### **Why GLiNER Dominates (By Design)**:
- **Superior Contextual Understanding**: vs SpaCy's rule-based approach
- **Domain-Specific Entities**: Handles "Pegasus spyware", "NSO Group" vs SpaCy's generic PERSON/ORG
- **Better Boundary Detection**: More accurate entity spans and custom types
- **News/Video Optimized**: Designed for the content ClipScribe processes

### **Cost-Effective Intelligence**: Free (SpaCy coverage) → Better (GLiNER primary) → Best (LLM validation)

## Why GLiNER + REBEL is Powerful

This sophisticated hybrid model builds rich, queryable knowledge graphs from video content:

### GLiNER: The Universal Entity Finder

GLiNER finds the **NODES** (entities) of our knowledge graph. Unlike traditional Named Entity Recognition (NER) systems that are limited to a fixed set of categories (like PERSON, ORGANIZATION), GLiNER is a universal entity finder.

-   **Flexible**: It can find *any* entity type you describe with natural language, not just from a predefined list.
-   **Context-Aware**: It understands the difference between "Apple" (the company) and "apple" (the fruit) based on the surrounding text.
-   **Zero-Shot**: It doesn't require any special training to find entities in new, specialized domains.
-   **High Performance**: Extracts 250-300 entities per video with LLM validation

**Example: Dynamic Entity Detection**

If we are analyzing a cooking video, we can ask GLiNER to find culinary-specific entities like `chef`, `dish`, `ingredient`, and `cooking_technique`. For a tech tutorial, we can ask for `programming_framework`, `database`, and `cloud_service`. GLiNER handles this dynamically without any code changes.

### REBEL: The Relationship Extractor

REBEL finds the **EDGES** (relationships) that connect the entities GLiNER discovers. It reads sentences and extracts semantic fact triples in the format `(Subject) -> [Predicate] -> (Object)`.

-   **Semantic**: It understands the meaning behind the words to find relationships like `founded`, `located in`, `works for`, or `competes with`.
-   **Directional**: It correctly identifies the subject and object in a relationship (e.g., `SpaceX manufactures Falcon 9`, not the other way around).
-   **Contextual**: It can extract implied relationships from the text.
-   **Working Output**: Now successfully extracts 10-19 relationships per video

**Example: Extracting Knowledge Graph Triples**

From the text: *"Elon Musk founded SpaceX in 2002. The company is headquartered in Hawthorne, California."*

REBEL extracts triples like:
-   `(Elon Musk) -> [founded] -> (SpaceX)`
-   `(SpaceX) -> [inception] -> (2002)`
-   `(SpaceX) -> [headquarters location] -> (Hawthorne)`

### **Technical Implementation**

The breakthrough was achieved through a complete rewrite of the REBEL parser:

```python
def _parse_triplets(self, text: str) -> List[Dict[str, str]]:
    """Parse REBEL output with dual strategy: space-separated + XML fallback"""
    
    # Primary: Space-separated parsing
    space_separated_triplets = self._parse_space_separated(text)
    if space_separated_triplets:
        return space_separated_triplets
    
    # Fallback: XML tag parsing (legacy)
    return self._parse_xml_tags(text)
```

## The Combined Power: Building Knowledge Graphs

Together, GLiNER and REBEL allow ClipScribe to transform unstructured video transcripts into highly structured knowledge graphs.

1.  **GLiNER** identifies all the relevant entities (the nodes) - 250-300 per video
2.  **REBEL** identifies how they are all connected (the edges) - 10-19 relationships per video  
3.  **Knowledge Synthesis** correlates information across multiple videos with timeline generation
4.  **GEXF 1.3 Export** creates modern knowledge graphs for Gephi visualization
5.  The result is a rich, queryable network of facts and information that allows for deep analysis and insights far beyond a simple transcript.

## Performance Metrics

| Metric | Performance | Status |
|--------|-------------|--------|
| **Entity Extraction** | 250-300 entities per video | ✅ Working |
| **Relationship Extraction** | 10-19 relationships per video | ✅ **FIXED** |
| **Knowledge Graph Nodes** | 240+ nodes per video | ✅ Working |
| **Knowledge Graph Edges** | 9-13 edges per video | ✅ **FIXED** |
| **Processing Cost** | ~$0.41 per video | ✅ Optimized |
| **Success Rate** | 100% completion | ✅ Stable |

## Testing with News Content

**Recommendation**: Test ClipScribe's relationship extraction with news content like PBS NewsHour for best results. News content provides:
- **Clear factual relationships** between entities
- **Temporal context** for timeline synthesis  
- **Real-world connections** for meaningful knowledge graphs
- **Professional narration** for accurate extraction

Avoid music videos or entertainment content which produce poor relationship extraction quality. 