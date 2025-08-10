# ClipScribe API v1 – Service Readiness Spec

*Last Updated: 2025-08-10 18:38 UTC*

## 1) Goals / Non‑Goals
- **Goals**: Enable browser UIs (e.g., Replit-hosted) to submit videos, observe progress, and download artifacts without privileged secrets; deliver a stable, versioned API with cost-aware guardrails.
- **Non‑Goals**: No frontend scaffolding; no client-held Gemini/cloud credentials; no admin console in v1.

## 2) API Contract (Normative)
Canonical OpenAPI: `docs/architecture/openapi.yaml`

### Endpoints
- `POST /v1/jobs` – Submit a job by `url` or `gcs_uri` with options.
- `GET /v1/jobs/{job_id}` – Status, progress, cost-to-date, manifest link, `schema_version`.
- `GET /v1/jobs/{job_id}/events` – Server-Sent Events (SSE) stream with progress.
- `GET /v1/jobs/{job_id}/artifacts` – List downloadable artifacts (signed URLs / redirects).
- `POST /v1/uploads/presign` – Return pre-signed GCS URL and `gcs_uri` for browser PUT.
- `GET /v1/estimate` – Preflight cost/time estimate and admission decision.
- `GET /openapi.json` – OpenAPI (staging only; prod configurable).

### Curl Examples

Submit a job by URL:
```bash
curl -X POST "$API_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
  }'
```

Watch progress (SSE):
```bash
curl -N -H "Authorization: Bearer $TOKEN" \
  "$API_BASE_URL/v1/jobs/$JOB_ID/events"
```

Presign upload + submit with gcs_uri:
```bash
# 1) Presign
curl -X POST "$API_BASE_URL/v1/uploads/presign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "filename": "video.mp4", "content_type": "video/mp4" }'

# 2) PUT to the returned upload_url, then
curl -X POST "$API_BASE_URL/v1/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "{ \"gcs_uri\": \"$GCS_URI\" }"
```

List artifacts:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$API_BASE_URL/v1/jobs/$JOB_ID/artifacts"
```

Preflight estimate:
```bash
curl "$API_BASE_URL/v1/estimate?url=https://www.youtube.com/watch?v=VIDEO_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Error Taxonomy
- `budget_exceeded`, `invalid_input`, `rate_limited`, `forbidden_origin`, `unsupported_media`, `upstream_error`.

### Versioning
- Accept `X-API-Version: v1` (default). Responses include artifact `schema_version`.

## 3) Auth, Tokens, and CORS
- **Public API Tokens**: Per-tenant tokens with scopes (`submit`, `status`, `artifacts`). Optional short‑lived “job token” for one-shot submit + status.
- **Rate Limits**: Per token + IP + Origin; leaky bucket; `429` with `Retry-After`.
- **CORS**: Allow-list per env.
  - Dev: `https://*.repl.co`, staging domains
  - Prod: production web domains only
  - Expose headers: `X-Request-ID`, `Retry-After`.

## 4) Job State Machine
`QUEUED → DOWNLOADING → TRANSCRIBING|UPLOADING → ANALYZING → WRITING_ARTIFACTS → COMPLETED|FAILED|CANCELED`
- Transient errors retry with backoff; DLQ for terminal worker errors.
- Idempotent replays safe (see §8).

## 5) Media Intake
- Preferred: URL submission (`url`).
- Upload flow: `POST /v1/uploads/presign` → browser `PUT` to GCS → `POST /v1/jobs { gcs_uri }`.
- GCS CORS: allow dev/staging origins; allow `Content-Type`.

## 6) Cost & Quotas (Admission Control)
- `GET /v1/estimate` returns expected cost/time, proposed model (Pro/Flash), and plan decision (implemented).
- Enforce per-token caps: daily spend (reservation-based), daily requests, RPM; concurrency aligned to Gemini tier.
- Budget reservations: reserve on submit using estimate; reconcile on completion with actual cost (refund/adjust). 429 includes `retry_after_seconds`, `estimated_cost_usd`, and `available_budget_usd`.
- Auto-route to Flash near caps; `budget_exceeded` with suggestions when over.

## 7) SSE Progress + Polling Parity
- SSE events: `status`, `progress` (chunk index/total), `cost` (to-date), `done`, `error`.
- Polling (`GET /v1/jobs/{id}`) returns same fields; fallback cadence 2–5s.

## 8) Idempotency, Deduplication, Caching
- `Idempotency-Key` on `POST /v1/jobs`.
- Content fingerprint: canonical URL signature (resolved URL + HEAD ETag/length) or upload hash.
- Checkpoints: persist chunk progress to resume without re-sending.
- Cache: return prior artifacts when fingerprint+config unchanged; artifacts are content-addressed and CDN-served; manifest includes `schema_version`.

## 9) Observability & SLOs
- Metrics: p50/p95 job duration, retries, throttle counts, cache hit-rate, duplicate suppression, cost/video, SSE disconnects, error taxonomy.
- Logs: structured with correlation IDs; include (hashed) token_id and origin.
- SLOs: success ≥ 99%; p95 for 10‑min video ≤ 3 min (Flash path). Alerts on SLO breach and upstream error spikes.

## 10) Mock Mode & Staging Ergonomics
- `MOCK_API=true` returns deterministic fixtures with artificial latency/jitter; no upstream calls.
- Swagger UI only in staging; prod can serve raw OpenAPI JSON.

## 11) Environments & Config
- `API_BASE_URL`, `CORS_ALLOW_ORIGINS`, `ADMISSION_*` caps, `PUBLIC_TOKEN_ISSUER_*`, `GCS_BUCKET`, `GCS_CORS_CONFIG`, `MOCK_API`, `ENABLE_SSE`.
- Deny-all CORS by default; distinct dev/staging/prod lists.

### Token Limits & Budgets (Milestone B)
- `TOKEN_MAX_RPM` (default 60): Per-token requests per minute limit
- `TOKEN_MAX_DAILY_REQUESTS` (default 2000): Per-token daily request cap
- `TOKEN_DAILY_BUDGET_USD` (default 5.0): Per-token daily USD budget cap
- `DEFAULT_EST_COST_USD` (default 0.035): Provisional per-job cost used for budget checks until real estimate is wired

## 12) Acceptance Criteria & Test Plan
- From a Replit app: submit URL job, receive SSE updates, fetch artifacts; presign PUT to GCS, submit `gcs_uri`, complete.
- CORS works for dev/staging; prod locked down.
- Duplicate clicks do not re-spend; retries resume from checkpoints.
- Preflight prevents budget overruns; `429` and `budget_exceeded` handled; docs provide guidance.
- Dashboards show KPIs; SLO alerts configured.

## 15) Implementation Milestones (Execution Plan)

- Milestone A: API skeleton and mock mode (0.5–1 day)
  - FastAPI/Starlette app with global error handler returning `Error` schema, `X-Request-ID` on all responses
  - Endpoints: `/v1/jobs` (accept + enqueue mock), `/v1/jobs/{id}` (mock states), `/v1/jobs/{id}/events` (mock SSE), `/v1/uploads/presign` (real GCS), `/v1/estimate` (mock)
  - CORS allow-list per env; staging token validator (issuer can be mock)
  - Deploy staging and validate Quickstart flows
  - Status: COMPLETED on 2025-08-09 (local dev): real GCS signed PUT (200), submit, status, SSE; `manifest_url` now points to real bucket

- Milestone B: Real queue, artifacts, idempotency (1–2 days)
  - Queue/workers, idempotency keys, content fingerprinting, checkpoints
  - Artifact writer + manifest (`schema_version`), signed URLs, CDN headers
  - Polling/SSE from real state; admission control + `429` with `Retry-After`
  - Status: VALIDATED (2025-08-10 18:38 UTC)
    - Implemented: Redis+RQ queue; worker writes `transcript.json` and `report.md` for URL jobs; API writes `manifest.json`; artifacts listing with signed URLs
    - Implemented: Redis persistence for idempotency, fingerprint dedup, active job set; admission control; per-token RPM/daily request/daily budget counters
    - Validated: URL path from table video produced `transcript.json` and `report.md` (job_id example: `2b9b06de78e946958f22bd8ff739df12`)
    - Validated: Presign V4 (200), PUT upload, and artifact listing in real bucket `clipscribe-api-uploads-20250809`
    - Observed: GCS/Vertex path may return markdown-fenced JSON; parser now strips code fences before JSON parse; tiny synthetic clips still produce minimal outputs by design
    - Pending: tighten Vertex response normalization for rare non-JSON-wrapped outputs; expand tests & docs

- Milestone C: Gemini path + throttling + observability (1–2 days)
  - Integrate retriever/transcriber with throttled concurrency and resilient retries
  - Implement `/v1/estimate` logic (cost/time, model proposal, admission)
  - Metrics dashboards, DLQ flow, alerts for SLO/error spikes

## 16) Readiness Checklist (Go/No-Go)

- Auth/Tokens: public token issue/validate; scopes enforced
- CORS: per-env allow-list; expose `X-Request-ID`, `Retry-After`
- Job System: queue running; idempotency; fingerprinting; checkpoints
- Presign Upload: working from browser; bucket CORS configured
- SSE: stable with keepalives; polling parity validated
- Artifacts: manifest with `schema_version`; signed URLs; content-addressed paths
- Admission Control: `/v1/estimate` accurate; caps enforced; 429 behavior verified
- Observability: structured logs; baseline metrics; error taxonomy present
- Docs: OpenAPI complete; Quickstart verified from fresh environment

## 13) Rollout & Backward Compatibility
- OpenAPI changes tracked; additive first; deprecations with warnings; support N‑1 for 90 days.
- Rollback: feature flags for endpoints; DLQ draining; cache invalidation controls.

## 14) Risks & Mitigations
- Upstream quotas: adaptive concurrency/backoff; DLQ + resume.
- Cost spikes: preflight budgets; Flash auto-routing; alarms.
- SSE blocked: polling fallback.
- Abuse: per-origin rate limits; short token TTL; anomaly detection.

---

Link to OpenAPI: `docs/architecture/openapi.yaml`
