# Release v2.29.7

## Highlights
- API artifacts endpoint now returns signed URLs for private GCS objects and exposes `requires_auth=false` so clients can download directly.
- Vertex path honored via `Settings.use_vertex_ai`; both URL and GCS URI paths validated E2E.
- Sliding-window RPM limiter and minimal `/metrics` counters.
- Docs polished: API Quickstart SSE + presigned upload examples; OpenAPI examples and error schemas.

## Changes
- See CHANGELOG.md for full details

## Upgrade Notes
- API server must run with ADC (`GOOGLE_APPLICATION_CREDENTIALS`) to sign private GCS objects for `/v1/jobs/{id}/artifacts`.
- Configure API CORS and GCS bucket CORS for browser uploads (PUT, Content-Type).

## Credits
- Maintainer: Zac Forristall (@bubroz)
