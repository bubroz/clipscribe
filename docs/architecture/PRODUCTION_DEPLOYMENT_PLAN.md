# ClipScribe – Production Deployment Plan (API + Replit UI)

Last Updated: 2025-08-11
Status: Authoritative checklist for prod readiness

## 1) Goals
- Public API on custom domain with signed artifact URLs
- Replit-hosted frontend (browser-only) calling API with a public token
- Zero long‑lived keys in CI (WIF) and safe, repeatable deploys

## 2) Environments
- dev (local) – localhost:8081
- staging – Cloud Run, protected; CORS allows Replit staging
- prod – Cloud Run + custom domain; strict CORS and tokens

## 3) Authentication (Workload Identity Federation)
- Create Workload Identity Pool/Provider trusting GitHub OIDC (repo/branch bound)
- Service Account (SA): `clipscribe-ci@PROJECT.iam.gserviceaccount.com`
- IAM:
  - SA grants to GitHub principal: `roles/iam.workloadIdentityUser`, `roles/iam.serviceAccountTokenCreator`
  - SA runtime roles: `roles/aiplatform.user`, `roles/storage.objectAdmin` (or finer bucket‑level roles)
- GitHub Actions: `google-github-actions/auth@v2` to mint short‑lived ADC (no JSON key)

## 4) Cloud resources
- GCS buckets: uploads (tmp) and artifacts (private); lifecycle rules for tmp
- Cloud Run service: `clipscribe-api` (min 1 instance if low-latency desired)
- Redis: managed (e.g., Memorystore) or self-managed (staging/local only)

## 5) CORS
- API CORS allowlist per env: dev (`https://*.repl.co`), staging, prod (final domain(s))
- GCS bucket CORS: allow `PUT` and `Content-Type` header for presigned uploads

## 6) Tokens & admission control
- Public API token (scopes: submit, status, artifacts); rotateable via env/secret
- Per‑token RPM, daily request, and daily budget enforcement (already implemented)

## 7) CI/CD workflows (GitHub Actions)
- ci.yml: lint (black/ruff), type (mypy), tests (unit/integration), security (bandit/pip‑audit), coverage
- e2e_manual.yml: workflow_dispatch → WIF → Vertex E2E + upload artifacts
- deploy.yml (to add): on tag push → build container → deploy to Cloud Run via WIF

## 8) Build & deploy (Cloud Run)
- Container build (Dockerfile) → Artifact Registry → Cloud Run deploy
- Env vars:
  - `GCS_BUCKET`, `CORS_ALLOW_ORIGINS`
  - `USE_VERTEX_AI=true`, `VERTEX_AI_PROJECT`, `VERTEX_AI_LOCATION`
  - Policy caps: `TOKEN_MAX_RPM`, `TOKEN_MAX_DAILY_REQUESTS`, `TOKEN_DAILY_BUDGET_USD`
  - Logging level, output dir etc.
- Health check: `/metrics` basic exposure; add readiness if desired

## 9) Domain & TLS
- Reserve domain (e.g., api.yourdomain.com)
- Map domain to Cloud Run; verify DNS & TLS auto‑managed by Cloud Run
- Update CORS allowlists to final domain(s)

## 10) Replit UI integration
- Secrets in Replit: `API_BASE_URL`, `PUBLIC_TOKEN`
- Flows:
  - URL Job: POST /v1/jobs → open SSE → list `/artifacts` → download signed URLs
  - Upload Job: `/uploads/presign` → browser PUT (Content‑Type required) → `/v1/jobs { gcs_uri }`
- Client policies: honor Retry‑After on 429; jittered backoff; SSE reconnect

## 11) Observability
- Logs: structured with request IDs
- Metrics: minimal counters (rpm, daily rejects, budget reserves/rejects)
- Future: uptime checks, error rate alerts, p95 duration dashboards

## 12) Security hardening
- Private buckets; signed URLs only; short expiry
- No long-lived keys (WIF in CI/CD)
- PROD tokens limited scope; rotateable
- Branch protections; secret scanning

## 13) Acceptance criteria
- Replit UI can:
  - Submit URL jobs; see SSE progress; list and download artifacts
  - Upload local file via presign flow; see end‑to‑end completion
- API enforces caps; 429 honor Retry‑After
- Artifacts endpoint returns valid signed URLs; public GET to bucket is denied
- Deploy on tag publishes new API to Cloud Run within 10 minutes

## 14) Rollback strategy
- Keep N-1 tagged image in Artifact Registry
- `gcloud run services update --image <prev>` to revert
- Tokens & budgets stay in Redis; no schema migration required

## 15) Task checklist
- [ ] Create WIF pool/provider in GCP (GitHub OIDC)
- [ ] Create `clipscribe-ci` SA; grant WIF and token creator; assign Vertex/Storage roles
- [ ] Convert e2e_manual.yml to WIF auth (remove JSON secret usage)
- [ ] Add deploy.yml (WIF) to build & deploy to Cloud Run on tag
- [ ] Configure Cloud Run env vars; connect Redis
- [ ] Set API CORS and bucket CORS
- [ ] Map domain; verify TLS
- [ ] Add Replit secrets; run UI smoke test
- [ ] Draft v2.29.7 release; tag and deploy
- [ ] Post‑deploy validation: SSE stream, artifacts listing, rate limits, budget caps

## 16) Appendices
- Example gcloud commands for WIF (see discussion notes)
- Example curl/JS snippets (see API Quickstart)
