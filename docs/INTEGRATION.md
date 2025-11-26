# ClipScribe Integration Contract

**Last Updated:** November 26, 2025  
**Version:** 1.0.0

## Agent Coordination

**Cursor Agent (Backend):** Manages ClipScribe Python API  
**Replit Agent (Frontend):** Manages Dashboard web application

---

## API Endpoints

### Base URL

**Production:** `https://clipscribe-api-df6nuv4qxa-uc.a.run.app`

### Authentication

All requests require Bearer token in Authorization header:
```
Authorization: Bearer tok_abc123...
```

### Endpoints Used by Dashboard

#### 1. Get Auth Token
```http
POST /v1/auth/token
Content-Type: application/json

{
  "email": "info@clipscribe.ai"
}
```

**Response:**
```json
{
  "token": "bet_abc123...",
  "tier": "beta",
  "email": "info@clipscribe.ai",
  "expires_in_days": 30
}
```

**Note:** Token expires in 30 days. Store securely.

#### 2. Request Presigned Upload URL
```http
POST /v1/uploads/presign
Authorization: Bearer bet_abc123...
Content-Type: application/json

{
  "filename": "interview.mp3",
  "content_type": "audio/mpeg"
}
```

**Response:**
```json
{
  "upload_url": "https://storage.googleapis.com/bucket/...",
  "gcs_uri": "gs://bucket/uploads/xyz.../interview.mp3"
}
```

#### 3. Submit Processing Job
```http
POST /v1/jobs
Authorization: Bearer bet_abc123...
Content-Type: application/json

{
  "gcs_uri": "gs://bucket/uploads/xyz.../interview.mp3",
  "options": {
    "transcription_provider": "whisperx-local",
    "intelligence_provider": "grok"
  }
}
```

**Response:**
```json
{
  "job_id": "abc123...",
  "state": "QUEUED",
  "progress": {
    "current_chunk": 0,
    "total_chunks": 0
  },
  "cost_to_date_usd": 0.0,
  "manifest_url": "https://storage.googleapis.com/bucket/jobs/abc123.../manifest.json",
  "created_at": "2025-11-26T12:00:00Z"
}
```

#### 4. Get Job Status
```http
GET /v1/jobs/{job_id}
Authorization: Bearer bet_abc123...
```

**Response:**
```json
{
  "job_id": "abc123...",
  "state": "PROCESSING",
  "progress": {
    "current_chunk": 2,
    "total_chunks": 5
  },
  "cost_to_date_usd": 0.0015,
  "updated_at": "2025-11-26T12:05:00Z"
}
```

**Status Values:**
- `QUEUED` - Job submitted, waiting to start
- `PROCESSING` - Currently processing
- `COMPLETED` - Processing finished successfully
- `FAILED` - Processing failed (check `error` field)

#### 5. Get Job Results (Artifacts)
```http
GET /v1/jobs/{job_id}/artifacts
Authorization: Bearer bet_abc123...
```

**Response:**
```json
{
  "manifest_url": "https://storage.googleapis.com/bucket/jobs/abc123.../manifest.json",
  "json_url": "https://storage.googleapis.com/bucket/jobs/abc123.../transcript.json",
  "docx_url": "https://storage.googleapis.com/bucket/jobs/abc123.../transcript.docx",
  "csv_urls": {
    "entities": "https://storage.googleapis.com/bucket/jobs/abc123.../entities.csv",
    "relationships": "https://storage.googleapis.com/bucket/jobs/abc123.../relationships.csv",
    "topics": "https://storage.googleapis.com/bucket/jobs/abc123.../topics.csv"
  }
}
```

#### 6. SSE Status Stream (Optional)
```http
GET /v1/jobs/{job_id}/events
Authorization: Bearer bet_abc123...
Accept: text/event-stream
```

**Response:** Server-Sent Events stream with real-time updates

---

## JSON Schema Contract

### Complete Output Structure

**File:** `examples/sample_outputs/multispeaker_panel_36min.json`  
**Documentation:** `docs/OUTPUT_FORMAT.md`

### Root Structure
```json
{
  "transcript": { ... },
  "intelligence": { ... },
  "file_metadata": { ... }
}
```

### Transcript Schema
```json
{
  "transcript": {
    "segments": [
      {
        "start": 0.0,
        "end": 5.2,
        "text": "Transcript text",
        "speaker": "SPEAKER_01",
        "words": [...],  // Optional: word-level timing
        "confidence": 0.95
      }
    ],
    "language": "en",
    "duration": 2172.5,
    "speakers": 12,
    "provider": "whisperx-local",
    "model": "whisperx-large-v3",
    "cost": 0.0
  }
}
```

### Intelligence Schema
```json
{
  "intelligence": {
    "entities": [
      {
        "name": "Alex Karp",
        "type": "PERSON",
        "confidence": 1.0,
        "evidence": "Exact quote from transcript"
      }
    ],
    "relationships": [
      {
        "subject": "Trump",
        "predicate": "announced",
        "object": "Gaza ceasefire deal",
        "evidence": "Supporting quote",
        "confidence": 1.0
      }
    ],
    "topics": [
      {
        "name": "Government Shutdown",
        "relevance": 1.0,
        "time_range": "00:00-15:00"
      }
    ],
    "key_moments": [
      {
        "timestamp": "00:30",
        "description": "What happened",
        "significance": 0.9,
        "quote": "Exact quote"
      }
    ],
    "sentiment": {
      "overall": "mixed",
      "confidence": 0.9,
      "per_topic": { ... }
    },
    "provider": "grok",
    "model": "grok-4-fast-reasoning",
    "cost": 0.0030
  }
}
```

### Database Mapping

**ClipScribe JSON → Dashboard PostgreSQL:**

```typescript
{
  filename: clipscribeOutput.file_metadata.filename,
  duration: clipscribeOutput.transcript.duration,
  speakers: clipscribeOutput.transcript.speakers,
  cost: clipscribeOutput.file_metadata.total_cost,
  status: "completed",
  transcriptData: clipscribeOutput.transcript,  // Full transcript object
  intelligenceData: {
    entities: clipscribeOutput.intelligence.entities,
    relationships: clipscribeOutput.intelligence.relationships,
    topics: clipscribeOutput.intelligence.topics,
    key_moments: clipscribeOutput.intelligence.key_moments,
    sentiment: clipscribeOutput.intelligence.sentiment
  },
  geointData: clipscribeOutput.intelligence.geoint || null  // Optional GEOINT
}
```

---

## CORS Configuration

### API CORS (FastAPI Middleware)

**Current Status:** CORS configured for `https://clipscribe.ai`  
**Required:** Add `https://clipscribe-front-smashcrashman.replit.app`

**Note:** FastAPI CORS middleware does not support wildcard patterns like `*.repl.co`. Specific domains must be added individually.

**Manual Fix Required:**
1. Go to: https://console.cloud.google.com/run/detail/us-central1/clipscribe-api
2. Click "Edit & Deploy New Revision"
3. Expand "Variables & Secrets"
4. Edit `CORS_ALLOW_ORIGINS` environment variable
5. Set value: `https://clipscribe.ai,https://clipscribe-front-smashcrashman.replit.app`
6. Click "Deploy"

**Or via gcloud (if URL parsing issues resolved):**
```bash
gcloud run services update clipscribe-api \
  --region=us-central1 \
  --update-env-vars CORS_ALLOW_ORIGINS="https://clipscribe.ai,https://clipscribe-front-smashcrashman.replit.app"
```

### GCS Bucket CORS (Browser Uploads)

**Status:** ✅ **CONFIGURED**

The GCS bucket `clipscribe-artifacts-16459511304` has CORS configured to allow browser-based file uploads.

**Configuration:**
- **Origins:** `*` (allows uploads from any domain - appropriate for presigned URLs)
- **Methods:** `PUT`, `POST`, `GET`, `HEAD`, `OPTIONS`
- **Headers:** `Content-Type`, `x-goog-meta-*`, `x-goog-resumable`
- **Max Age:** 3600 seconds (1 hour preflight cache)

**Verification:**
```bash
gsutil cors get gs://clipscribe-artifacts-16459511304
```

**Note:** This CORS configuration enables browser uploads to presigned URLs. The bucket accepts cross-origin PUT requests from any origin, which is necessary for the Replit dashboard upload flow.

---

## Change Protocol

### When Cursor Changes API:

1. Update this file with new endpoint/schema
2. Update `docs/API.md` with full documentation
3. Notify founder
4. Founder informs Replit Agent
5. Replit Agent updates integration code

### When Replit Needs New Feature:

1. Create GitHub issue with label `integration`
2. Founder assigns to Cursor Agent
3. Cursor Agent implements and updates this doc
4. Replit Agent tests and confirms

### Breaking Changes:

- Must provide 30-day deprecation notice
- Old endpoints remain functional during transition
- Version API endpoints (`/v1/`, `/v2/`) for major changes

---

## Error Handling

### Standard Error Response
```json
{
  "code": "error_code",
  "message": "Human-readable error message",
  "retry_after_seconds": 60  // Optional, for rate limits
}
```

### Common Error Codes:
- `invalid_input` - Bad request (400)
- `unauthorized` - Missing/invalid token (401)
- `not_found` - Job/resource not found (404)
- `rate_limited` - Too many requests (429)
- `budget_exceeded` - Daily budget exceeded (429)
- `service_unavailable` - API paused/maintenance (503)

---

## Rate Limits

**Per Token:**
- RPM: 60 requests/minute (configurable)
- Daily Requests: 2000/day (configurable)
- Daily Budget: $5.00 USD (configurable)

**Headers:**
- `Retry-After` - Seconds to wait before retry
- `X-Request-ID` - Unique request identifier

---

## Testing

**Sample Files:**
- `examples/sample_outputs/multispeaker_panel_36min.json` - 12 speakers, 36 min
- `examples/sample_outputs/business_interview_30min.json` - Business interview
- `examples/sample_outputs/technical_single_speaker_16min.json` - Single speaker

**Test Workflow:**
1. Get auth token: `POST /v1/auth/token`
2. Request presigned upload URL: `POST /v1/uploads/presign`
3. Upload test file to GCS
4. Submit job with GCS URI: `POST /v1/jobs`
5. Poll status: `GET /v1/jobs/{job_id}`
6. Fetch artifacts when COMPLETED: `GET /v1/jobs/{job_id}/artifacts`
7. Verify JSON structure matches schema

---

## Support

**Issues:** Create GitHub issue with label `integration`  
**Documentation:** `docs/API.md` for complete API reference  
**Schema Reference:** `docs/OUTPUT_FORMAT.md` for JSON structure

