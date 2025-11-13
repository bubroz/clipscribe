# ClipScribe API Reference

**Version:** v3.0.0  
**Last Updated:** November 13, 2025

Complete API reference for ClipScribe with GCS-first processing and presigned upload flow.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Upload Flow](#upload-flow-step-by-step)
- [Job Processing](#job-processing)
- [Endpoint Reference](#endpoint-reference)
- [Search Endpoints](#search-endpoints)
- [Rate Limiting](#rate-limiting)
- [Example Clients](#example-clients)

---

## Overview

### GCS-First Architecture

ClipScribe API v3.0.0 uses **GCS (Google Cloud Storage) presigned uploads** for file processing:

**Why GCS?**
- ✅ Secure (presigned URLs, no API key in upload)
- ✅ Scalable (handles large files)
- ✅ Reliable (Google infrastructure)
- ✅ Fast (direct upload to cloud)

**User Flow:**
1. Request presigned upload URL
2. Upload file to GCS via presigned URL
3. Submit GCS URI for processing
4. Track job progress
5. Download results

---

## Authentication

### Get API Token

```bash
POST /v1/auth/token
Content-Type: application/json

{
  "email": "your@email.com"
}
```

**Response:**
```json
{
  "token": "tok_abc123...",
  "tier": "beta",
  "email": "your@email.com",
  "expires_in_days": 30
}
```

**Use token in all requests:**
```bash
Authorization: Bearer tok_abc123...
```

---

## Upload Flow (Step-by-Step)

### Step 1: Request Presigned Upload URL

```bash
POST /v1/uploads/presign
Authorization: Bearer tok_abc123...
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

**Save the `gcs_uri`** - you'll need it in Step 3!

### Step 2: Upload File to Presigned URL

```bash
curl -X PUT "https://storage.googleapis.com/bucket/..." \
  -H "Content-Type: audio/mpeg" \
  --data-binary @interview.mp3
```

**Response:**
```
200 OK
```

File is now in GCS, ready for processing.

### Step 3: Submit Processing Job

```bash
POST /v1/jobs
Authorization: Bearer tok_abc123...
Content-Type: application/json

{
  "gcs_uri": "gs://bucket/uploads/xyz.../interview.mp3",
  "options": {
    "model": "pro"  # Optional
  }
}
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "state": "QUEUED",
  "manifest_url": "https://storage.googleapis.com/.../manifest.json",
  "created_at": "2025-11-13T00:00:00Z"
}
```

### Step 4: Track Job Progress

```bash
GET /v1/jobs/abc123def456
Authorization: Bearer tok_abc123...
```

**Response (QUEUED):**
```json
{
  "job_id": "abc123def456",
  "state": "QUEUED",
  "created_at": "2025-11-13T00:00:00Z",
  "updated_at": "2025-11-13T00:00:00Z"
}
```

**Response (PROCESSING):**
```json
{
  "job_id": "abc123def456",
  "state": "PROCESSING",
  "progress": {
    "current_chunk": 3,
    "total_chunks": 10
  }
}
```

**Response (COMPLETED):**
```json
{
  "job_id": "abc123def456",
  "state": "COMPLETED",
  "manifest_url": "https://storage.googleapis.com/.../manifest.json",
  "cost_to_date_usd": 0.06
}
```

### Step 5: Stream Progress (Optional, SSE)

```bash
GET /v1/jobs/abc123def456/events
Authorization: Bearer tok_abc123...
Accept: text/event-stream
```

**Response (Server-Sent Events):**
```
data: {"state": "QUEUED"}

data: {"state": "PROCESSING", "progress": {"current_chunk": 1, "total_chunks": 10}}

data: {"state": "PROCESSING", "progress": {"current_chunk": 5, "total_chunks": 10}}

data: {"state": "COMPLETED", "cost_to_date_usd": 0.06}
```

---

## Endpoint Reference

### POST /v1/auth/token

Get API authentication token.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "token": "tok_...",
  "tier": "beta",
  "expires_in_days": 30
}
```

### POST /v1/uploads/presign

Get presigned GCS upload URL.

**Request:**
```json
{
  "filename": "video.mp3",
  "content_type": "audio/mpeg"
}
```

**Response:**
```json
{
  "upload_url": "https://storage.googleapis.com/...",
  "gcs_uri": "gs://bucket/uploads/.../video.mp3"
}
```

### POST /v1/jobs

Submit processing job (GCS URI only).

**Request:**
```json
{
  "gcs_uri": "gs://bucket/uploads/.../video.mp3",
  "options": {
    "model": "pro"  // Optional: "pro" or default
  }
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "state": "QUEUED",
  "manifest_url": "https://...",
  "created_at": "2025-11-13T00:00:00Z"
}
```

**Headers:**
- `Idempotency-Key` (optional): Prevent duplicate jobs
- `Authorization`: Bearer token (required)

### GET /v1/jobs/{job_id}

Get job status and results.

**Response:**
```json
{
  "job_id": "abc123",
  "state": "COMPLETED",
  "manifest_url": "https://...",
  "cost_to_date_usd": 0.06,
  "created_at": "2025-11-13T00:00:00Z",
  "updated_at": "2025-11-13T00:05:00Z"
}
```

**Job States:**
- `QUEUED`: Job accepted, waiting for processing
- `PROCESSING`: Currently being processed
- `COMPLETED`: Successfully completed
- `FAILED`: Processing failed (see `error` field)

### GET /v1/jobs/{job_id}/events

Stream job progress via Server-Sent Events (SSE).

**Response:** Stream of events in `text/event-stream` format

### GET /v1/jobs/{job_id}/artifacts

List result files.

**Response:**
```json
{
  "artifacts": [
    {
      "type": "analysis",
      "path": "gs://bucket/jobs/abc123/analysis.json",
      "content_type": "application/json"
    },
    {
      "type": "transcript",
      "path": "gs://bucket/jobs/abc123/transcript.json"
    }
  ]
}
```

---

## Search Endpoints

### Entity Search

Search for entities across all processed videos.

**Endpoint:** `GET /v1/search/entities?q=Tesla`

### Topic Search

Search for topics across all processed videos.

**Endpoint:** `GET /v1/search/topics?q=AI`

---

## Rate Limiting

### Limits

**Per-token limits:**
- **RPM (Requests Per Minute):** 60 (configurable)
- **Daily Requests:** 2,000 (configurable)
- **Daily Budget:** $5.00 USD (configurable)

### Error Responses

**429 Rate Limited:**
```json
{
  "code": "rate_limited",
  "message": "Per-token RPM exceeded",
  "retry_after_seconds": 10
}
```

**429 Budget Exceeded:**
```json
{
  "code": "budget_exceeded",
  "message": "Daily budget exceeded",
  "retry_after_seconds": 3600
}
```

---

## Example Clients

### Python Client

```python
import requests
import time

class ClipScribeClient:
    def __init__(self, api_token):
        self.base_url = "https://api.clipscribe.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def process_file(self, local_file_path):
        # Step 1: Get presigned upload URL
        response = requests.post(
            f"{self.base_url}/uploads/presign",
            headers=self.headers,
            json={
                "filename": "video.mp3",
                "content_type": "audio/mpeg"
            }
        )
        upload_data = response.json()
        
        # Step 2: Upload file
        with open(local_file_path, 'rb') as f:
            requests.put(
                upload_data["upload_url"],
                headers={"Content-Type": "audio/mpeg"},
                data=f
            )
        
        # Step 3: Submit job
        job_response = requests.post(
            f"{self.base_url}/jobs",
            headers=self.headers,
            json={"gcs_uri": upload_data["gcs_uri"]}
        )
        job = job_response.json()
        
        # Step 4: Wait for completion
        while True:
            status_response = requests.get(
                f"{self.base_url}/jobs/{job['job_id']}",
                headers=self.headers
            )
            status = status_response.json()
            
            if status["state"] == "COMPLETED":
                return status
            elif status["state"] == "FAILED":
                raise Exception(f"Job failed: {status.get('error')}")
            
            time.sleep(5)  # Poll every 5 seconds

# Usage
client = ClipScribeClient("tok_abc123...")
result = client.process_file("interview.mp3")
print(f"Cost: ${result['cost_to_date_usd']}")
```

### cURL Examples

**Complete workflow:**

```bash
# 1. Get presigned URL
curl -X POST https://api.clipscribe.com/v1/uploads/presign \
  -H "Authorization: Bearer tok_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"filename": "video.mp3", "content_type": "audio/mpeg"}' \
  > presign_response.json

# Extract upload_url and gcs_uri
UPLOAD_URL=$(jq -r '.upload_url' presign_response.json)
GCS_URI=$(jq -r '.gcs_uri' presign_response.json)

# 2. Upload file
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: audio/mpeg" \
  --data-binary @video.mp3

# 3. Submit job
curl -X POST https://api.clipscribe.com/v1/jobs \
  -H "Authorization: Bearer tok_abc123..." \
  -H "Content-Type: application/json" \
  -d "{\"gcs_uri\": \"$GCS_URI\"}" \
  > job_response.json

JOB_ID=$(jq -r '.job_id' job_response.json)

# 4. Check status
curl https://api.clipscribe.com/v1/jobs/$JOB_ID \
  -H "Authorization: Bearer tok_abc123..."
```

---

**For CLI usage, see [CLI.md](CLI.md)**  
**For provider details, see [PROVIDERS.md](PROVIDERS.md)**  
**For architecture, see [ARCHITECTURE.md](ARCHITECTURE.md)**

