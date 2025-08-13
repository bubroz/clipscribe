# ClipScribe Architecture (High-Level)

Last Updated: August 11, 2025

Mermaid Diagram (source of truth):

```mermaid
flowchart LR
  B["Browser UI (Replit)"] -- "PUT (signed)" --> T[("GCS uploads/")]
  B -- "POST /v1/jobs" --> A["API (FastAPI)"]
  A -- "SSE: /v1/jobs/{id}/events" --> B
  A -- "/v1/jobs/{id}/artifacts (signed URLs)" --> B

  A -- "enqueue" --> R[("Redis")]
  R --> W["RQ Worker"]

  W -- "download/transcribe/analyze" --> GMI["Gemini 2.5 (Pro/Flash)"]
  W -- "or via Vertex AI" --> V["Vertex AI (optional)"]

  W --> GA[("GCS artifacts (private)")]
  A -- "list + sign" --> GA

  A -. "estimate/admission: RPM, daily req, budget" .-> RC[("Redis counters+budget")]
```

- Browser uploads via presigned GCS URL
- API (FastAPI): job submission, SSE progress, artifacts (signed URLs)
- Redis + RQ: queue/worker for processing
- GCS: artifact storage; API signs URLs
- Gemini 2.5 Pro/Flash; Vertex AI optional path
