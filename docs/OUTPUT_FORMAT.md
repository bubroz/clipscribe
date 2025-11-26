# Output Format Reference

**Version:** v3.1.0  
**Last Updated:** November 2025

Complete schema reference for ClipScribe's multi-format export system.

---

## Overview

ClipScribe produces **5 export formats** for every workflow:

1. **JSON** - Complete structured data (always generated)
2. **DOCX** - Professional reports (Google Docs/Word/Pages)
3. **CSV** - Data tables (5 files: entities, relationships, topics, key_moments, segments)
4. **PPTX** - Executive presentations (7-slide deck)
5. **Markdown** - Searchable documentation (GitHub/VS Code/Obsidian)

**Select formats with `--formats` flag:**
```bash
clipscribe process video.mp3 --formats all                 # All 5 formats
clipscribe process video.mp3 --formats json docx csv       # Specific formats
```

**Default formats** (if not specified): `json`, `docx`, `csv`

---

## Format 1: JSON (Complete Data)

**Always generated** - Contains all extracted intelligence in machine-readable format.

**File location:** `output/timestamp_filename/transcript.json`

**File size:** ~200KB to 2MB (depending on content length and richness)

**Best for:** Developers, APIs, databases, custom processing, Pandas/R analysis

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
        "confidence": 0.95,              // Transcription confidence
        "geoint": {                       // Geolocation data (Beta, video files only)
          "timestamp": 1634523400123000,  // Absolute timestamp (microseconds, KLV) or null
          "sensor": {                     // Drone/platform location
            "lat": 34.12345,              // Latitude (degrees)
            "lon": -118.67890,            // Longitude (degrees)
            "alt": 1500.5,                // Altitude (meters MSL)
            "heading": 45.2               // Heading angle (degrees, if available)
          },
          "target": {                     // Camera look target (if available)
            "lat": 34.12500,              // Frame center latitude
            "lon": -118.68000,            // Frame center longitude
            "elev": 0.0                   // Ground elevation (meters)
          },
          "likely_visual_observation": true  // Heuristic: narrow FOV or high depression angle
        }
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
- `geoint` block (optional, Beta) - Geolocation data for video files with telemetry

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

## Format 2: DOCX (Professional Reports)

**File location:** `output/timestamp_filename/intelligence_report.docx`  
**File size:** ~35-45KB  
**Best for:** Stakeholder reports, sharing with non-technical teams, editing findings

**Compatible with:**
- Google Docs (upload and auto-converts)
- Microsoft Word (Windows/Mac)
- Apple Pages
- LibreOffice Writer

**Structure:**
1. Title page with metadata (date, duration, provider, cost)
2. Executive summary (key metrics)
3. Entities table (top 20 with evidence quotes)
4. Relationships section (top 15 with full evidence)
5. Topics analysis with time ranges
6. Key moments timeline
7. Sentiment analysis breakdown
8. Footer with ClipScribe branding

**Features:**
- Standard Word formatting (no advanced features for compatibility)
- Tables use universal styles
- Page breaks for logical sections
- Evidence quotes for verifiability

**Generate:**
```bash
clipscribe process video.mp3 --formats docx
```

---

## Format 3: CSV (Data Tables)

**File location:** `output/timestamp_filename/` (root of output directory)  
**Number of files:** 5 CSV files  
**Total size:** ~20-100KB  
**Best for:** Excel analysis, database import, Pandas/R processing, pivot tables

**Compatible with:**
- Google Sheets
- Microsoft Excel
- Apple Numbers
- Any CSV-compatible tool
- Pandas: `pd.read_csv()`

**Files Generated:**

### entities.csv
```csv
name,type,confidence,evidence
Alex Karp,PERSON,1.0,"Alex Karp, thanks for having us into the Palantir lair..."
Palantir,ORG,1.0,"Palantir has been working with Ukraine since the beginning..."
```

**Columns:** name, type, confidence, evidence (truncated to 500 chars)

### relationships.csv
```csv
subject,predicate,object,evidence,confidence
Trump,announced,Gaza ceasefire deal,"President Trump scores an international win...",1.0
Palantir,works_with,Ukraine,"Palantir has been working with Ukraine...",1.0
```

**Columns:** subject, predicate, object, evidence, confidence

### topics.csv
```csv
name,relevance,time_range
Government Shutdown,1.0,00:00-15:00
Gaza Ceasefire,0.9,00:15-20:00
```

**Columns:** name, relevance, time_range

### key_moments.csv
```csv
timestamp,description,significance,quote
00:30,Trump's Gaza ceasefire achievement,0.9,"President Trump scores an international win..."
```

**Columns:** timestamp, description, significance, quote

### segments.csv
```csv
start,end,speaker,text,confidence
4.081,13.117,SPEAKER_07,"Domestic deal maker? President Trump...",0.95
```

**Columns:** start, end, speaker, text, confidence

**Features:**
- UTF-8 with BOM encoding (Excel displays unicode correctly)
- Proper quote escaping (handles commas in data)
- Evidence truncated to prevent cell overflow
- Header row included

**Generate:**
```bash
clipscribe process video.mp3 --formats csv
```

---

## Format 4: PPTX (Executive Presentations)

**File location:** `output/timestamp_filename/executive_summary.pptx`  
**File size:** ~30-40KB  
**Best for:** Executive briefings, investor presentations, stakeholder updates

**Compatible with:**
- Google Slides (upload and renders correctly)
- Microsoft PowerPoint (Windows/Mac)
- Apple Keynote
- LibreOffice Impress

**Slide Structure (7 slides):**

1. **Title Slide**
   - "Intelligence Extraction Report"
   - Processing date

2. **Executive Summary**
   - Key metrics (entities, relationships, speakers, topics, moments)
   - Processing cost

3. **Key Entities**
   - Top 10 entities with confidence scores
   - Bullet list format

4. **Relationships**
   - Top 8 relationships
   - Subject → predicate → object format

5. **Topics & Timeline**
   - Topics with relevance scores
   - Time ranges for each topic

6. **Key Moments**
   - Top 6 significant moments
   - Timestamps and significance scores

7. **Sentiment Analysis**
   - Overall sentiment
   - Per-topic sentiment breakdown

**Features:**
- Standard slide layouts (universal compatibility)
- System fonts (no custom fonts)
- No animations or transitions
- Text sizing prevents overflow

**Generate:**
```bash
clipscribe process video.mp3 --formats pptx
```

---

## Format 5: Markdown (Searchable Documentation)

**File location:** `output/timestamp_filename/report.md`  
**File size:** ~4-10KB  
**Best for:** GitHub repos, VS Code/Obsidian notes, version control, documentation

**Compatible with:**
- GitHub (renders automatically)
- VS Code (preview mode)
- Obsidian (opens as note)
- Any text editor

**Structure:**
- Clean heading hierarchy (# ## ###)
- Executive summary (bullet list)
- Entities table (top 20)
- Relationships with blockquote evidence (top 15)
- Topics table
- Key moments with timestamps
- Sentiment breakdown
- Footer with links

**Features:**
- GitHub-flavored markdown syntax
- Tables for structured data
- Blockquotes for evidence
- Proper escaping (pipe characters)
- Newline handling for readability

**Example:**
```markdown
## Relationships

### 1. Trump → announced → Gaza ceasefire deal
**Confidence:** 1.00
> President Trump scores an international win with the Gaza ceasefire deal
```

**Generate:**
```bash
clipscribe process video.mp3 --formats markdown
```

---

## GEOINT Output Files (Beta)

**Status:** Beta feature, automatically generated for video files with telemetry

When processing video files (MP4, MPG, TS, MKV) that contain geolocation telemetry, ClipScribe automatically generates additional visualization files:

### mission.kml

**File location:** `output/timestamp_filename/mission.kml`  
**File size:** ~10-50KB (depends on flight duration)  
**Best for:** Google Earth, GIS software, geographic analysis

**Contents:**
- Flight path (yellow line showing drone movement)
- Target track (red line showing where camera was looking)
- Look vectors (gray lines connecting sensor to target periodically)
- Event placemarks (pins at locations where audio events occurred)

**Usage:**
- Open directly in Google Earth
- Import into QGIS, ArcGIS for spatial analysis
- Share with stakeholders for geographic context

**Format:** KML 2.2 (Open Geospatial Consortium standard)

### mission_map.html

**File location:** `output/timestamp_filename/mission_map.html`  
**File size:** ~15-20KB  
**Best for:** Web sharing, offline viewing, quick visualization

**Contents:**
- Interactive Leaflet.js map
- Satellite imagery layer (Esri World Imagery)
- Street overlay (OpenStreetMap)
- Flight path visualization
- Event markers with popups

**Features:**
- Standalone HTML (no internet required after initial load)
- Zoom, pan, layer toggle
- Click markers to see transcript quotes
- Responsive design (works on mobile)

**Usage:**
- Open in any web browser
- Share via email or file sharing
- Embed in reports or presentations

### GEOINT Data in transcript.json

When GEOINT data is available, transcript segments are enriched with `geoint` blocks:

```json
{
  "transcript": {
    "segments": [
      {
        "text": "Target vehicle acquired at the intersection.",
        "start": 15.4,
        "end": 18.2,
        "geoint": {
          "timestamp": 1634523400123000,
          "sensor": {
            "lat": 34.12345,
            "lon": -118.67890,
            "alt": 1500.5,
            "heading": 45.2
          },
          "target": {
            "lat": 34.12500,
            "lon": -118.68000,
            "elev": 0.0
          },
          "likely_visual_observation": true
        }
      }
    ]
  },
  "geoint": {
    "kml_path": "output/timestamp_filename/mission.kml",
    "telemetry_count": 450,
    "geo_events_count": 23
  }
}
```

**Availability:**
- Only generated for video files with embedded telemetry
- Requires DJI/Autel subtitle files or KLV metadata
- Automatically detected, no flags needed
- Gracefully skipped if no telemetry found (no error)

**For detailed GEOINT documentation, see [GEOINT.md](advanced/GEOINT.md)**

---

**For complete guide, see [README.md](../README.md)**  
**For provider details, see [PROVIDERS.md](PROVIDERS.md)**  
**For CLI usage, see [CLI.md](CLI.md)**

