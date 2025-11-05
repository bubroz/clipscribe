# ClipScribe Architecture

**Last Updated:** November 4, 2025  
**Version:** v2.61.0  
**Status:** Production - Modal GPU + Grok-4 Structured Outputs

---

## System Overview

ClipScribe is a video intelligence extraction system that processes videos to extract:
- **Transcription** with speaker diarization
- **Entities** (18 spaCy types: PERSON, ORG, GPE, EVENT, etc.)
- **Topics** with relevance scores and time ranges
- **Key moments** with timestamps and significance
- **Relationships** between entities with evidence
- **Sentiment** (overall and per-topic)

All extractions include evidence quotes from the transcript.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Video Input                            │
│                  (MP3/MP4/URL via GCS)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Modal GPU Service                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ WhisperX (large-v3)                                   │  │
│  │ - Transcription (word-level timestamps, 0.01s)       │  │
│  │ - Processing: 11.6x realtime on A10G                 │  │
│  └────────────────────┬──────────────────────────────────┘  │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ pyannote.audio                                        │  │
│  │ - Speaker diarization (who spoke when)               │  │
│  │ - Adaptive thresholds for multi-speaker              │  │
│  └────────────────────┬──────────────────────────────────┘  │
│                       ▼                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Grok-4 Fast Reasoning (Structured Outputs)           │  │
│  │ - Entity extraction (18 spaCy types)                 │  │
│  │ - Topic detection (relevance + time ranges)          │  │
│  │ - Key moments (timestamps + significance)            │  │
│  │ - Relationships (subject-predicate-object)           │  │
│  │ - Sentiment analysis (overall + per-topic)           │  │
│  │ - Evidence quotes (100% coverage)                    │  │
│  └────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Storage (GCS)                     │
│                 transcript.json                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ {                                                     │  │
│  │   "segments": [...],           # Transcript          │  │
│  │   "word_segments": [...],      # Word-level timing   │  │
│  │   "entities": [...],           # 18 spaCy types      │  │
│  │   "relationships": [...],      # With evidence       │  │
│  │   "topics": [...],             # Relevance + time    │  │
│  │   "key_moments": [...],        # Timestamps + sig    │  │
│  │   "sentiment": {...}           # Overall + per-topic │  │
│  │ }                                                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Local SQLite Database                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ topics table: video_id, name, relevance, time_range  │  │
│  │ entities table: video_id, name, type, evidence       │  │
│  └────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Search APIs                               │
│  - POST /api/topics/search (find topics across videos)     │
│  - POST /api/entities/search (find entities across videos) │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Modal GPU Service (Production)

**Platform:** Modal Labs serverless GPU  
**GPU:** A10G (NVIDIA)  
**Performance:** 11.6x realtime (16min video → 1.4min processing)

**WhisperX:**
- Model: large-v3
- Accuracy: 97-99%
- Output: Word-level timestamps (0.01s precision)
- Language: English (primary)

**pyannote.audio:**
- Purpose: Speaker diarization
- Adaptive thresholds (0.80 clustering)
- Multi-speaker handling (tested up to 5 speakers)

**Grok-4 Fast Reasoning:**
- Model: grok-4-fast-reasoning
- Method: Structured Outputs (JSON schema enforcement)
- Context: 2M tokens (~1M characters)
- Pricing: $0.20/M input, $0.50/M output
- Features:
  - Entity extraction (18 spaCy standard types)
  - Topic detection (relevance scoring)
  - Key moments (significance scoring)
  - Relationship mapping (evidence-based)
  - Sentiment analysis (overall + per-topic)

### 2. Google Cloud Storage

**Purpose:** Intermediate storage for results  
**Location:** gs://clipscribe-validation/  
**Format:** JSON (transcript.json per video)

**Output Structure:**
```json
{
  "segments": [{"start": 0.0, "end": 5.2, "speaker": "SPEAKER_00", "text": "..."}],
  "word_segments": [{"word": "hello", "start": 0.1, "end": 0.3, "score": 0.98}],
  "entities": [{"name": "Trump", "type": "PERSON", "confidence": 1.0, "evidence": "quote"}],
  "relationships": [{"subject": "Trump", "predicate": "announced", "object": "ceasefire", "evidence": "quote"}],
  "topics": [{"name": "Gaza Ceasefire", "relevance": 0.95, "time_range": "00:00-15:00"}],
  "key_moments": [{"timestamp": "03:45", "description": "Major announcement", "significance": 0.95, "quote": "exact quote"}],
  "sentiment": {"overall": "positive", "confidence": 0.9, "per_topic": {...}}
}
```

### 3. Local Database (SQLite)

**Purpose:** Enable search across multiple videos  
**Location:** data/clipscribe.db (local, .gitignored)

**Schema:**
```sql
-- Topics table
CREATE TABLE topics (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    name TEXT NOT NULL,
    relevance REAL NOT NULL,
    time_range TEXT,
    schema_type TEXT DEFAULT 'Event'
);

-- Entities table
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence TEXT
);
```

### 4. Search APIs (FastAPI)

**Purpose:** Query intelligence across videos

**Endpoints:**
- `POST /api/topics/search` - Find topics by name, relevance, type
- `POST /api/entities/search` - Find entities by name, type, confidence
- `GET /api/topics/video/{id}` - Get all topics for a video
- `GET /api/entities/video/{id}` - Get all entities for a video
- `GET /api/entities/types` - List all entity types in database

**Performance:** <100ms query times (validated)

---

## Technology Stack

**Production:**
- **Modal Labs:** Serverless GPU infrastructure
- **WhisperX:** OpenAI Whisper large-v3 + forced alignment
- **pyannote.audio:** Speaker diarization
- **Grok-4 Fast Reasoning:** xAI language model with Structured Outputs
- **Google Cloud Storage:** Artifact storage
- **SQLite:** Local database for search

**Development:**
- **Python 3.12:** Primary language
- **Poetry:** Dependency management
- **FastAPI:** API framework
- **Pydantic:** Schema validation
- **pytest:** Testing framework

**Cost Structure:**
- WhisperX: ~$0.33 per 88min video (Modal GPU time)
- Grok-4: ~$0.01 per video (intelligence extraction)
- **Total:** ~$0.34 per video

---

## Data Flow

**End-to-End Processing:**

1. **Input:** Video file (MP3/MP4) uploaded to GCS
2. **Transcription:** Modal WhisperX → transcript with word-level timestamps
3. **Diarization:** Modal pyannote → speaker labels added to segments
4. **Intelligence:** Modal Grok-4 → entities, topics, moments, relationships, sentiment
5. **Storage:** Results written to GCS as JSON
6. **Database:** JSON data loaded into SQLite (optional, for search)
7. **Query:** Search APIs query database for cross-video intelligence

**Processing Time:** ~6-10 minutes per video (varies by length)  
**Realtime Factor:** 11.6x (processes faster than playback)

---

## Key Design Decisions

**Why Modal (not local):**
- GPU access (WhisperX requires CUDA)
- Serverless scaling (no infrastructure management)
- Cost-effective ($0.33/video vs hosting GPU server)

**Why Grok-4 Fast Reasoning:**
- Structured Outputs (type-safe, guaranteed schema)
- Evidence quotes (100% coverage prevents hallucinations)
- Cost-effective ($0.20/$0.50 per M tokens)
- 2M token context (handles 87k+ character transcripts)

**Why SQLite (not PostgreSQL):**
- Simple for current scale (hundreds of videos)
- No server needed
- Fast queries (<100ms)
- Easy to migrate later if needed

**Why Structured Outputs:**
- Type safety (guaranteed JSON structure)
- Evidence enforcement (no hallucinations)
- Better extraction quality (validated: +25% relationships, +67% topics, +100% moments)

---

## Current Limitations

**What works:**
- ✅ Modal processing (video → intelligence)
- ✅ Search APIs (query across videos)
- ✅ Grok-4 Structured Outputs (validated)

**What doesn't work:**
- ❌ Local CLI (`clipscribe process`) - deprecated, old architecture
- ❌ Real-time processing - batch only
- ❌ Web interface - API-only currently

**Workaround:** Use Modal directly for processing, Search APIs for querying

---

**This is the actual architecture as of November 4, 2025. Validated and working.**

