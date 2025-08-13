# ClipScribe Replit Project Guide

*Last Updated: 2025-08-13*

This guide helps you run the ClipScribe API from Replit and connect a browser UI.

## Environment

Set these secrets in Replit:
- `HOST=0.0.0.0`  (default in code is 127.0.0.1; Replit needs 0.0.0.0)
- `PORT=8080`
- `CORS_ALLOW_ORIGINS=https://*.repl.co`
- Optional GCS: `GCS_BUCKET`, `GOOGLE_APPLICATION_CREDENTIALS`

## Start the API

```bash
poetry install --with dev,test --no-interaction --no-root
poetry run python -c "from clipscribe.api.app import run; run()"
```

Replit will expose the service at a public URL on the configured port.

## Browser Flow (UI)

1) Submit job by URL
```http
POST /v1/jobs  (Authorization: Bearer <token>)
{ "url": "https://www.youtube.com/watch?v=..." }
```

2) Listen for progress (SSE)
```http
GET /v1/jobs/{job_id}/events  (Authorization: Bearer <token>)
```

3) List artifacts
```http
GET /v1/jobs/{job_id}/artifacts  (Authorization: Bearer <token>)
```

4) Optional upload flow
```http
POST /v1/uploads/presign  (Authorization: Bearer <token>)
PUT  <upload_url> with Content-Type
POST /v1/jobs { "gcs_uri": "gs://..." }
```

Notes:
- Objects are stored under `uploads/` prefix.
- Without GCS credentials, presign returns a mock URL (dev-friendly).

## Rate Limits & Budgets

Env caps (per token): `TOKEN_MAX_RPM`, `TOKEN_MAX_DAILY_REQUESTS`, `TOKEN_DAILY_BUDGET_USD`.
Handle 429 by using the `Retry-After` header.

## Useful Endpoints

- `GET /metrics` minimal counters
- `GET /openapi.json` (staging/dev) OpenAPI

## Code Map (UI Integrations)

- API server: `src/clipscribe/api/app.py`
- Job submit/queue: `/v1/jobs`
- Events (SSE): `/v1/jobs/{id}/events`
- Artifacts: `/v1/jobs/{id}/artifacts`
- Presign: `/v1/uploads/presign`

## Troubleshooting

- CORS: Confirm `CORS_ALLOW_ORIGINS` includes your Replit URL.
- Bind: Ensure `HOST=0.0.0.0` in Replit.
- Signed URLs: Set `GCS_BUCKET` and `GOOGLE_APPLICATION_CREDENTIALS` or expect mock presign.


