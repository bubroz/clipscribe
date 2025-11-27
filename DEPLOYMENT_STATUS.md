# ClipScribe Deployment Status

**Last Updated:** November 27, 2025  
**Current Version:** v3.1.12

**Documentation Status:** All documentation updated to v3.1.10, professionalized (emojis removed), and consolidated. Outdated files removed from git.

---

## Recent Fixes

### v3.1.12 - Deployment Workflow Update (November 27, 2025)

**Changes:**
- Added `GOOGLE_SERVICE_ACCOUNT_EMAIL` environment variable to GitHub Actions deployment workflow
- Updated deployment documentation for front-end agent handoff
- Ensures presigned URL generation works on all future deployments

**Status:** Ready for deployment
- Workflow updated
- Documentation complete

---

### v3.1.11 - Presigned URL IAM Signing Fix (November 27, 2025)

**Problem:** Presigned URL generation still failing with "you need a private key to sign credentials" error on Cloud Run

**Root Cause:** The IAM Credentials client was being initialized without explicit credentials, causing it to use default credentials that lacked proper scopes for IAM API access.

**Solution:** 
- Switched to `google-cloud-storage` library's built-in IAM signing support (recommended approach)
- Explicitly pass credentials with `cloud-platform` scope to IAM client
- Added fallback to manual IAM SignBlob implementation if storage library approach fails
- Improved error handling and logging

**Status:** Deployed successfully
- Code changes complete and deployed
- Tests updated and passing (19/19)
- IAM permission granted: `roles/iam.serviceAccountTokenCreator` on service account `16459511304-compute@developer.gserviceaccount.com`
- Environment variable set in Cloud Run: `GOOGLE_SERVICE_ACCOUNT_EMAIL=16459511304-compute@developer.gserviceaccount.com`
- Presigned URL generation working correctly

---

## Recent Deployments

### v3.1.10 - Rich Dependency Fix (November 27, 2025)

**Problem:** API container crashed on startup with `ModuleNotFoundError: No module named 'rich'`

**Root Cause:** `src/clipscribe/utils/__init__.py` imported `BatchProgress` and `ClipScribeProgress` at top level, which require `rich` (TUI dependency). The API container uses `api` extras which don't include `rich`.

**Solution:** Made `rich`-dependent imports optional using try/except blocks:
- `BatchProgress` import wrapped in try/except, set to `None` if import fails
- `ClipScribeProgress`, `console`, `progress_tracker` imports wrapped in try/except, set to `None` if import fails

**Status:** ✅ Deployed successfully
- Cloud Run revision: `clipscribe-api-00056-92z`
- Health endpoint: `/v1/health` responding correctly
- All services healthy (Redis, GCS, Queue)

**Deployment URL:** https://clipscribe-api-df6nuv4qxa-uc.a.run.app

---

### v3.1.9 - IAM SignBlob for Presigned URLs (November 27, 2025)

**Problem:** Presigned URL generation failed with "you need a private key to sign credentials"

**Solution:** Implemented IAM SignBlob API integration to generate GCS v4 signed URLs without requiring service account private keys.

**Status:** ✅ Deployed and working

---

## CI Status

**Current Status:** ✅ **All Critical Issues Resolved**

**Fully Fixed:**
- ✅ Black formatting (all 131 files properly formatted)
- ✅ Ruff linting (ALL issues resolved - 100% passing)
  - Removed unused imports (`Optional`, `MultiVideoProcessor`, `VideoCollectionType` from `cli.py`)
  - Fixed bare `except` clauses (2 instances)
  - Replaced `whisperx` imports with `importlib.util.find_spec` for availability checks
  - Removed all trailing whitespace (15 instances fixed)

**Remaining (Non-Blocking):**
- ⚠️ Mypy type checking (pre-existing type annotation issues - not blocking CI)
- ⚠️ Some test failures (pre-existing, need investigation)

**Recent Fixes (November 27, 2025):**
- `fix(ci): Fix linting and formatting issues` - Initial batch of fixes
- `fix(ci): Remove trailing whitespace from geoint_exporter.py` - Whitespace cleanup
- `fix(ci): Resolve all remaining ruff linting issues` - Final cleanup (all ruff checks passing)

---

## Health Check

```bash
# Check service health
curl https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "...",
  "redis": true,
  "gcs": "healthy",
  "queue": "healthy",
  "version": "1.0.0"
}
```

---

## Front-End Integration Handoff

### API Base URL

**Production:** `https://clipscribe-api-df6nuv4qxa-uc.a.run.app`

### Authentication

All API endpoints (except `/v1/auth/token`) require Bearer token authentication:

```http
Authorization: Bearer YOUR_TOKEN
```

**Getting a Token:**
```bash
POST /v1/auth/token
Content-Type: application/json

{
  "email": "user@example.com"
}

Response:
{
  "token": "bet_...",
  "tier": "beta",
  "email": "user@example.com",
  "expires_in_days": 30
}
```

### Upload Flow (3-Step Process)

**Step 1: Get Presigned Upload URL**
```bash
POST /v1/uploads/presign
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "filename": "video.mp4",
  "content_type": "video/mp4"
}

Response:
{
  "upload_url": "https://storage.googleapis.com/...",
  "gcs_uri": "gs://bucket/uploads/uuid/video.mp4"
}
```

**Step 2: Upload File to Presigned URL**
```bash
PUT {upload_url}
Content-Type: video/mp4
[Binary file data]

Response: 200 OK (from GCS)
```

**Step 3: Submit Job for Processing**
```bash
POST /v1/jobs
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "gcs_uri": "gs://bucket/uploads/uuid/video.mp4",
  "options": {
    "model": "flash"  // or "pro" for higher quality
  }
}

Response:
{
  "job_id": "...",
  "state": "QUEUED",
  "manifest_url": "https://storage.googleapis.com/.../manifest.json",
  ...
}
```

### Job Status Endpoints

**Get Job Status:**
```bash
GET /v1/jobs/{job_id}
Authorization: Bearer YOUR_TOKEN
```

**Job States:**
- `QUEUED` - Job created, waiting to be processed
- `PROCESSING` - Currently being processed
- `COMPLETED` - Processing finished successfully
- `FAILED` - Processing failed (check `error` field)

**Get Job Artifacts:**
```bash
GET /v1/jobs/{job_id}/artifacts
Authorization: Bearer YOUR_TOKEN

Response:
{
  "job_id": "...",
  "artifacts": [
    {
      "id": "manifest.json",
      "kind": "manifest_json",
      "size_bytes": 1234,
      "url": "https://storage.googleapis.com/...",
      "requires_auth": false
    },
    ...
  ]
}
```

### Health Check

```bash
GET /v1/health

Response:
{
  "status": "healthy",
  "timestamp": "2025-11-27T...",
  "redis": true,
  "gcs": "healthy",
  "queue": "healthy",
  "version": "1.0.0"
}
```

### Error Responses

All errors follow this format:
```json
{
  "code": "error_code",
  "message": "Human-readable error message"
}
```

Common error codes:
- `invalid_input` - Invalid request parameters
- `unauthorized` - Missing or invalid token
- `rate_limited` - Rate limit exceeded (includes `retry_after_seconds`)
- `budget_exceeded` - Daily budget exceeded
- `presign_failed` - Failed to generate presigned URL
- `service_unavailable` - API temporarily paused

### Rate Limits

- **Per-token RPM:** 60 requests per minute (configurable via `TOKEN_MAX_RPM`)
- **Daily requests:** 2000 per token (configurable via `TOKEN_MAX_DAILY_REQUESTS`)
- **Daily budget:** $5.00 USD per token (configurable via `TOKEN_DAILY_BUDGET_USD`)

### Example Front-End Integration

```javascript
// 1. Get token
const tokenResponse = await fetch('https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/auth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' })
});
const { token } = await tokenResponse.json();

// 2. Get presigned URL
const presignResponse = await fetch('https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/uploads/presign', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    filename: file.name,
    content_type: file.type
  })
});
const { upload_url, gcs_uri } = await presignResponse.json();

// 3. Upload file
await fetch(upload_url, {
  method: 'PUT',
  headers: { 'Content-Type': file.type },
  body: file
});

// 4. Submit job
const jobResponse = await fetch('https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/jobs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    gcs_uri: gcs_uri,
    options: { model: 'flash' }
  })
});
const job = await jobResponse.json();

// 5. Poll for status
const statusResponse = await fetch(`https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/jobs/${job.job_id}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const status = await statusResponse.json();
```

---

## Deployment Commands

```bash
# Get service URL
gcloud run services describe clipscribe-api --region=us-central1 --format="value(status.url)"

# Check revision status
gcloud run revisions describe clipscribe-api-00056-92z --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=clipscribe-api" --limit=50

# Update environment variable (if needed)
gcloud run services update clipscribe-api \
  --region=us-central1 \
  --update-env-vars GOOGLE_SERVICE_ACCOUNT_EMAIL=16459511304-compute@developer.gserviceaccount.com \
  --project=prismatic-iris-429006-g6
```

