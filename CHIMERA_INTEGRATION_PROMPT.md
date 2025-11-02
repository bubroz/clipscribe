# Station10 ↔ Chimera Integration - Context for Chimera Agent

**From:** Station10.media (ClipScribe) development team  
**To:** Chimera intelligence analysis platform  
**Purpose:** Design API-to-API integration for video intelligence → SAT analysis

---

## STATION10 CURRENT STATUS (October 30, 2025)

### What We Have (Production-Ready):

**Core Intelligence Extraction:**
- **Grok-4 Fast Reasoning** for entity/topic/sentiment extraction
- **WhisperX + pyannote.audio** for transcription + speaker diarization
- **Modal GPU infrastructure** (A10G, 11.6x realtime, $0.34/video cost)

**Validated Intelligence Output (Per Video):**
- **Entities:** 287 average (18 spaCy types: PERSON, ORG, GPE, EVENT, etc.)
  - 100% evidence quote coverage (every entity has supporting transcript quote)
  - Confidence scores (all 1.0 with Grok-4)
  - Cross-video tracking capability
  
- **Topics:** 3-5 per video
  - Relevance scores (0.80-1.0)
  - Time ranges (MM:SS-MM:SS in video)
  - Schema.org Event taxonomy
  
- **Key Moments:** 4-5 per video
  - Precise timestamps (MM:SS)
  - Significance scores (0.85-1.0)
  - Description + exact quote
  
- **Relationships:** 21 average
  - Subject → Predicate → Object structure
  - Evidence quotes for each relationship
  - Confidence scores
  
- **Sentiment:**
  - Overall sentiment (positive/negative/neutral)
  - Per-topic sentiment breakdown
  - Confidence scores

**APIs Available NOW:**
- `POST /api/topics/search` - Search topics across videos (13 topics indexed)
- `POST /api/entities/search` - Search entities with evidence (287 entities indexed)
- Database: SQLite with topics and entities tables

---

## INTEGRATION QUESTIONS FOR CHIMERA

### 1. **Current Chimera Status**

**Questions:**
- Is Phase 2A (Vertex AI RAG) stable and functional now?
- What API endpoints does Chimera currently expose?
- Can Chimera ingest documents via API, or is it file-upload only?
- Authentication method? (API keys, OAuth, other?)

### 2. **Data Format Requirements**

**Questions:**
- What format does Chimera expect for ingested documents?
  - Raw JSON?
  - Formatted text/markdown?
  - Structured document with metadata?
  
- Can Chimera handle our nested JSON structure?
  ```json
  {
    "video_id": "...",
    "title": "...",
    "entities": [{name, type, evidence, timestamp}],
    "topics": [{name, relevance, time_range}],
    "key_moments": [{timestamp, description, significance, quote}],
    "relationships": [{subject, predicate, object, evidence}],
    "sentiment": {overall, per_topic}
  }
  ```

- Or do you need flattened/simplified structure?

### 3. **Integration Architecture**

**Possible Approaches:**

**Option A: Station10 POSTs to Chimera**
```
Video processed → Station10 API
  ↓
POST to Chimera /api/clipscribe/ingest
  ↓
Chimera ingests into Vertex AI RAG
```

**Option B: Chimera Pulls from Station10**
```
Video processed → Station10 stores in GCS
  ↓
Chimera polls for new videos
  ↓
GET from Station10 /api/videos/{id}
  ↓
Chimera ingests into RAG
```

**Option C: Shared Database**
```
Video processed → Station10 writes to shared PostgreSQL
  ↓
Chimera reads from same database
  ↓
Ingests into Vertex AI RAG
```

**Questions:**
- Which approach fits Chimera's architecture best?
- Do you have an ingestion endpoint ready?
- Should we use webhooks/callbacks?

### 4. **What Station10 Can Provide**

**Data We Can Send:**

**Per Video:**
- Video metadata (title, channel, duration, URL, upload date)
- Complete transcript (segments with speaker attribution)
- Word-level timestamps (0.01s precision from WhisperX)
- Entities (287 avg, 18 types, 100% evidence quotes)
- Topics (3-5, with relevance and time ranges)
- Key moments (4-5, with timestamps and significance)
- Relationships (21 avg, with evidence)
- Sentiment (overall + per-topic)

**Across Videos (if needed):**
- Cross-video entity tracking (find "Trump" across 100 videos)
- Topic evolution over time
- Entity relationship graphs
- Sentiment trends

**Formats We Can Provide:**
- JSON (structured intelligence)
- CSV/TSV (for database import)
- Markdown (human-readable)
- Custom (whatever Chimera needs)

### 5. **Citation Integration**

**For CSL JSON Citations:**

We can provide:
```json
{
  "id": "station10_P-2_moment_0345",
  "type": "video-recording",
  "title": "All-In Podcast - Episode XYZ",
  "timestamp": "00:03:45",
  "note": "Israel-Hamas ceasefire announcement",
  "quote": "Thanks to President Trump, who announced it just yesterday.",
  "source": "Station10.media",
  "entity": "Donald Trump",
  "entity_type": "PERSON",
  "evidence": "...",
  "significance": 0.95,
  "url": "gs://bucket/video.mp4#t=225"  // Deep link to timestamp
}
```

**Questions:**
- Does this CSL JSON structure work for Chimera?
- How should we link video timestamps in citations?
- Do you need different metadata fields?

### 6. **Timeline & Implementation**

**Questions:**
- When will Chimera Phase 2A be stable enough for integration?
- How long does integration typically take on your side?
- Can we do integration testing in a dev/staging environment first?
- Any blocking issues we should know about?

### 7. **Business Model Alignment**

**Our Vision:**
- Station10 processes videos → complete intelligence
- Chimera ingests Station10 data → applies 54 SATs → generates reports
- **Combined value:** "Video to verified intelligence pipeline"

**Questions:**
- Pricing model for integration? (we pay you, you pay us, revenue share?)
- White-label options? (can we embed Chimera SAT analysis in Station10?)
- Co-marketing? (joint product positioning?)

---

## WHAT WE NEED FROM CHIMERA

**Technical:**
1. API endpoint for video intelligence ingestion (if available)
2. Authentication credentials (API key, service account)
3. Data format specification (JSON schema, required fields)
4. Rate limits and quotas
5. Error handling requirements

**Documentation:**
6. API reference for ingestion endpoints
7. Example requests/responses
8. Webhook/callback specifications (if async processing)

**Timeline:**
9. When Phase 2A will be stable
10. When we can start integration testing

---

## CONTACT INFORMATION

**Station10 Development:**
- Platform: Cursor (AI-assisted development)
- Primary Contact: Zac Forristall (zforristall@gmail.com)
- Repository: https://github.com/bubroz/clipscribe (private)
- Current Agent: Claude (Cursor-based)

**Integration Coordination:**
- Preferred: Async collaboration (agent-to-agent via written specs)
- Timeline: Week 3-4 (November 2025)
- Goal: Live integration by December 2025

---

## STATION10 AGENT READY TO:

1. Design ingestion API endpoint on our side (if you pull from us)
2. Implement POST client to your endpoint (if we push to you)
3. Transform our data to your required format
4. Add authentication (API keys, OAuth, whatever you need)
5. Test integration with sample videos

**We're ready when Chimera is ready. Please provide:**
- Current Phase 2A status
- Integration requirements (format, endpoints, auth)
- Timeline for when we can start

**Station10 is production-ready. APIs are validated. Standing by for Chimera integration specs. 🚀**

---

**PROMPT FOR CHIMERA AGENT:**

Copy/paste this entire document to your Chimera agent and ask:

"Station10 (video intelligence platform) is ready to integrate with Chimera for SAT analysis of video corpus. They have complete intelligence extraction working (entities, topics, key moments, sentiment with evidence quotes). Please review their current status and answer the integration questions so we can design the API-to-API data flow. Specifically: Is Phase 2A stable? What ingestion endpoints exist? What data format do you need? When can we start integration testing?"

