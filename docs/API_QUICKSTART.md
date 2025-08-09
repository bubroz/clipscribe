# ClipScribe API Quickstart

*Last Updated: 2025-08-09*

This guide shows how to use the API v1 to submit a job, watch progress, and download artifacts from a browser-hosted frontend (e.g., Replit).

## Base URLs
- Staging: `https://api.staging.clipscribe.com`
- Production: `https://api.clipscribe.com`

OpenAPI (staging): `GET /openapi.json`

## Auth
Use a browser-safe public API token (scope: `submit`, `status`, `artifacts`). Do not embed privileged secrets in the frontend.

Header:
```
Authorization: Bearer YOUR_PUBLIC_TOKEN
```

## Submit a job (URL)
```bash
curl -X POST "$API_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
  }'
```
Response includes `job_id`, `state`, `schema_version`, and `manifest_url`.

## Watch progress (SSE)
Use Server-Sent Events for live updates.

```bash
curl -N -H "Authorization: Bearer $TOKEN" \
  "$API_BASE_URL/v1/jobs/$JOB_ID/events"
```

Events include `status`, `progress`, `cost`, `done`, `error`.

Fallback: poll `GET /v1/jobs/{job_id}` every 2–5s.

## Pre-sign an upload (optional)
For local files, first request a pre-signed URL, PUT the file to GCS, then submit the `gcs_uri`.

```bash
# 1) Request a pre-signed URL
curl -X POST "$API_BASE_URL/v1/uploads/presign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "content_type": "video/mp4"
  }'

# 2) Upload the file (example with curl)
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: video/mp4" \
  --data-binary @video.mp4

# 3) Submit a job using the returned gcs_uri
curl -X POST "$API_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "{ \"gcs_uri\": \"$GCS_URI\" }"
```

Tip: If `upload_url` contains `signature=mock`, the server is running without `GCS_BUCKET`/ADC or service account creds. Export `GCS_BUCKET` and (for signing) `GOOGLE_APPLICATION_CREDENTIALS` in the server terminal and restart.

## List artifacts
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$API_BASE_URL/v1/jobs/$JOB_ID/artifacts"
```
Returns artifact metadata and signed URLs (or redirecting endpoints) for `transcript.json`, `entities.json`, `relationships.json`, `knowledge_graph.gexf`, `report.md`, and `manifest.json`.

## Estimate cost (preflight)
```bash
curl "$API_BASE_URL/v1/estimate?url=https://www.youtube.com/watch?v=VIDEO_ID" \
  -H "Authorization: Bearer $TOKEN"
```
Returns `estimated_cost_usd`, `estimated_duration_seconds`, `proposed_model`, and `admission` decision.

## CORS & Errors
- CORS allow-lists differ per environment; dev includes `https://*.repl.co`.
- Common errors: `rate_limited (429)`, `budget_exceeded`, `invalid_input`, `forbidden_origin`.

For full details see `docs/architecture/API_V1_SERVICE_READINESS.md` and the OpenAPI at `/openapi.json`.

### Example: Handle 429 with Retry-After
```bash
resp=$(curl -s -D - -o /tmp/body.json \
  -H "Authorization: Bearer $TOKEN" \
  "$API_BASE_URL/v1/jobs/$JOB_ID")

status=$(echo "$resp" | head -n1 | awk '{print $2}')
retry_after=$(echo "$resp" | awk -F': ' 'BEGIN{IGNORECASE=1} /^Retry-After:/ {print $2}' | tr -d '\r')

if [ "$status" = "429" ] && [ -n "$retry_after" ]; then
  echo "Rate limited. Sleeping $retry_after seconds..."
  sleep "$retry_after"
  curl -H "Authorization: Bearer $TOKEN" "$API_BASE_URL/v1/jobs/$JOB_ID" | jq .
else
  cat /tmp/body.json | jq .
fi
```
