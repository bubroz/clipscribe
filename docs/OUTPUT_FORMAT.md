# Output Format Reference

**Version:** v3.0.0  
**Last Updated:** November 13, 2025

Complete schema reference for ClipScribe's comprehensive JSON output.

---

## Overview

ClipScribe produces a **single comprehensive JSON file** containing all extracted intelligence:

**File location:** `output/timestamp_filename/transcript.json`

**File size:** ~200KB to 2MB (depending on content length and richness)

**Format:** Standard JSON (import into any tool: Pandas, SQL, visualization, research databases)

---

## Complete Schema

### Root Structure

```json
{
  "transcript": { ... },      // Transcription data
  "intelligence": { ... },    // Extracted intelligence
  "file_metadata": { ... }    // Processing metadata
}
```

---

## Transcript Data

### Schema

```json
{
  "transcript": {
    "segments": [
      {
        "start": 0.0,                    // Start time (seconds)
        "end": 5.0,                      // End time (seconds)
        "text": "Transcript text",       // Segment text
        "speaker": "SPEAKER_01",         // Speaker label (if diarization enabled)
        "words": [                       // Word-level timing (if available)
          {
            "word": "text",
            "start": 0.0,
            "end": 0.5,
            "score": 0.98,
            "speaker": "SPEAKER_01"
          }
        ],
        "confidence": 0.95               // Transcription confidence
      }
    ],
    "language": "en",                    // Detected language code
    "duration": 2172.5,                  // Total duration (seconds)
    "speakers": 12,                      // Number of unique speakers
    "provider": "whisperx-local",        // Provider used
    "model": "whisperx-large-v3",        // Model used
    "cost": 0.0,                         // Transcription cost (USD)
    "metadata": {                        // Provider-specific metadata
      "device": "cpu",
      "confidence": 0.95
    }
  }
}
```

### Fields Explained

**segments** (Array of objects)
- Each segment is a continuous speech block
- Timestamps in seconds from start
- Speaker attribution (if diarization enabled)
- Word-level data available for WhisperX providers

**speakers** (Integer)
- Count of unique speakers detected
- 0 for Voxtral (no diarization)
- 1-12+ for WhisperX providers (validated)

**cost** (Float)
- Actual transcription cost in USD
- $0.00 for WhisperX Local (FREE!)
- Tracked from API responses, not estimated

---

## Intelligence Data

### Schema

```json
{
  "intelligence": {
    "entities": [
      {
        "name": "Alex Karp",                   // Entity name
        "type": "PERSON",                      // spaCy entity type
        "confidence": 1.0,                     // Extraction confidence (0-1)
        "evidence": "Alex Karp, thanks for..." // Exact quote from transcript
      }
    ],
    "relationships": [
      {
        "subject": "Trump",                    // Subject entity
        "predicate": "announced",              // Action/relationship verb
        "object": "Gaza ceasefire deal",       // Object entity
        "evidence": "President Trump scores...", // Supporting quote
        "confidence": 1.0                      // Relationship confidence (0-1)
      }
    ],
    "topics": [
      {
        "name": "Government Shutdown",         // Topic name
        "relevance": 1.0,                      // How central to video (0-1)
        "time_range": "00:00-15:00"            // When discussed (MM:SS-MM:SS)
      }
    ],
    "key_moments": [
      {
        "timestamp": "00:30",                  // Exact time (MM:SS)
        "description": "What happened",        // Moment description
        "significance": 0.9,                   // Importance (0-1)
        "quote": "Exact quote from moment"     // Supporting quote
      }
    ],
    "sentiment": {
      "overall": "mixed",                      // Overall video sentiment
      "confidence": 0.9,                       // Confidence in assessment
      "per_topic": {                           // Sentiment per topic
        "Government Shutdown": "negative",
        "Gaza Ceasefire": "positive"
      }
    },
    "provider": "grok",                        // Intelligence provider
    "model": "grok-4-fast-reasoning",          // Model used
    "cost": 0.0030,                            // Intelligence cost (USD)
    "cost_breakdown": {
      "input_cost": 0.001410,
      "cached_cost": 0.0,
      "output_cost": 0.000705,
      "cache_savings": 0.0,
      "total": 0.002115,
      "pricing_tier": "standard",
      "context_tokens": 7050
    },
    "cache_stats": {
      "cache_hits": 0,
      "cache_misses": 1,
      "cached_tokens": 0,
      "prompt_tokens": 7050,
      "total_input_tokens": 7050,
      "cache_savings": 0.0,
      "hit_rate_percent": 0.0
    }
  }
}
```

### Entity Types (18 spaCy Standard)

- **PERSON** - People, including fictional
- **ORG** - Companies, agencies, institutions
- **GPE** - Countries, cities, states (geopolitical entities)
- **LOC** - Non-GPE locations (mountains, bodies of water)
- **EVENT** - Named events (wars, sports events, etc.)
- **PRODUCT** - Physical objects, vehicles
- **MONEY** - Monetary values
- **DATE** - Dates or periods
- **TIME** - Times smaller than a day
- **FAC** - Buildings, airports, highways
- **NORP** - Nationalities, religious/political groups
- **LANGUAGE** - Named languages
- **LAW** - Named documents made into laws
- **WORK_OF_ART** - Titles of books, songs, etc.
- **CARDINAL** - Numerals not falling under other types
- **ORDINAL** - "first", "second", etc.
- **QUANTITY** - Measurements, weights, distances
- **PERCENT** - Percentage values

### Confidence Scores

**Entity/Relationship Confidence:**
- `1.0` - Explicitly named, clear evidence
- `0.8-0.9` - Strong evidence, minor ambiguity
- `0.7-0.8` - Good evidence, some uncertainty
- `<0.7` - Weaker evidence (rare, usually filtered)

**Topic Relevance:**
- `1.0` - Main focus of video
- `0.8-0.9` - Major topic, substantial discussion
- `0.6-0.7` - Notable topic, discussed briefly
- `<0.6` - Minor mention

**Key Moment Significance:**
- `1.0` - Critical moment (major announcement, key debate)
- `0.8-0.9` - Important moment (notable statement)
- `0.7-0.8` - Interesting moment (worth highlighting)
- `<0.7` - Minor moment (rarely used)

---

## File Metadata

### Schema

```json
{
  "file_metadata": {
    "filename": "interview.mp3",              // Original filename
    "processed_at": "20251113_020026",        // Processing timestamp
    "total_cost": 0.0030,                     // Total cost (USD)
    "transcription_cost": 0.0,                // Transcription cost
    "intelligence_cost": 0.0030               // Intelligence cost
  }
}
```

### Cost Tracking

**Costs are ACTUAL, not estimated:**
- Transcription cost from provider API response
- Intelligence cost from Grok API usage
- Total cost = sum of both
- All costs in USD

**Validated ranges:**
- Voxtral: $0.001/min transcription
- WhisperX Local: $0.00 (FREE!)
- WhisperX Modal: $0.0018/min processing
- Grok: $0.002-0.005 typical per video

---

## Example Complete Output

**From 36min multi-speaker panel:**

```json
{
  "transcript": {
    "segments": [
      {
        "start": 0.0,
        "end": 3.146,
        "text": "Domestic deal maker? President Trump scores an international win...",
        "speaker": "SPEAKER_07",
        "words": [...],
        "confidence": 0.95
      }
      // ... 500+ more segments
    ],
    "language": "en",
    "duration": 2172.5,
    "speakers": 12,
    "provider": "whisperx-local",
    "model": "whisperx-large-v3",
    "cost": 0.0
  },
  "intelligence": {
    "entities": [
      {
        "name": "President Trump",
        "type": "PERSON",
        "confidence": 1.0,
        "evidence": "Domestic deal maker? President Trump scores..."
      }
      // ... 44 more entities
    ],
    "relationships": [
      {
        "subject": "Trump",
        "predicate": "scores",
        "object": "Gaza ceasefire deal",
        "evidence": "President Trump scores an international win...",
        "confidence": 1.0
      }
      // ... 10 more relationships
    ],
    "topics": [
      {
        "name": "Government Shutdown and ACA Subsidies",
        "relevance": 1.0,
        "time_range": "00:00-15:00"
      }
      // ... 4 more topics
    ],
    "key_moments": [
      {
        "timestamp": "00:30",
        "description": "Trump's Gaza ceasefire achievement...",
        "significance": 0.9,
        "quote": "President Trump scores an international win..."
      }
      // ... 5 more moments
    ],
    "sentiment": {
      "overall": "mixed",
      "confidence": 0.9,
      "per_topic": {
        "Government Shutdown": "negative",
        "Gaza Ceasefire": "positive"
      }
    },
    "provider": "grok",
    "model": "grok-4-fast-reasoning",
    "cost": 0.0030,
    "cost_breakdown": {...},
    "cache_stats": {...}
  },
  "file_metadata": {
    "filename": "The View Full Broadcast.mp3",
    "processed_at": "20251113_020026",
    "total_cost": 0.0030
  }
}
```

**Total data points:** 67 (45 entities + 11 relationships + 5 topics + 6 key moments)

---

## Usage Examples

### Import into Pandas

```python
import json
import pandas as pd

# Load output
with open('output/timestamp_filename/transcript.json') as f:
    data = json.load(f)

# Entities DataFrame
entities_df = pd.DataFrame(data['intelligence']['entities'])
print(entities_df[['name', 'type', 'confidence']])

# Relationships DataFrame
rels_df = pd.DataFrame(data['intelligence']['relationships'])
print(rels_df[['subject', 'predicate', 'object']])
```

### Import into SQL

```python
import sqlite3
import json

conn = sqlite3.connect('intelligence.db')

# Load data
with open('transcript.json') as f:
    data = json.load(f)

# Insert entities
for entity in data['intelligence']['entities']:
    conn.execute(
        "INSERT INTO entities (name, type, confidence, evidence, video_id) VALUES (?, ?, ?, ?, ?)",
        (entity['name'], entity['type'], entity['confidence'], entity['evidence'], video_id)
    )

conn.commit()
```

### Export Subset

```python
# Extract just entities and relationships for network analysis
import json

with open('transcript.json') as f:
    data = json.load(f)

network_data = {
    'nodes': data['intelligence']['entities'],
    'edges': data['intelligence']['relationships']
}

with open('network.json', 'w') as f:
    json.dump(network_data, f, indent=2)
```

---

## Field Availability by Provider

| Field | Voxtral | WhisperX Local | WhisperX Modal |
|-------|---------|----------------|----------------|
| **Transcript segments** | ✅ | ✅ | ✅ |
| **Speaker attribution** | ❌ | ✅ | ✅ |
| **Word-level timing** | ❌ | ✅ | ✅ |
| **Entities** | ✅ | ✅ | ✅ |
| **Relationships** | ✅ | ✅ | ✅ |
| **Topics** | ✅ | ✅ | ✅ |
| **Key moments** | ✅ | ✅ | ✅ |
| **Sentiment** | ✅ | ✅ | ✅ |
| **Cost breakdown** | ✅ | ✅ | ✅ |
| **Cache stats** | ✅ | ✅ | ✅ |

**All providers deliver same intelligence data** - only transcription features differ (speakers, word-timing).

---

**For complete guide, see [README.md](../README.md)**  
**For provider details, see [PROVIDERS.md](PROVIDERS.md)**  
**For CLI usage, see [CLI.md](CLI.md)**

