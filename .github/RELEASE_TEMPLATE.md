# Release vX.Y.Z

## Highlights
- API artifacts endpoint returns signed URLs for private GCS (`requires_auth` exposed)
- Vertex path respected via Settings.use_vertex_ai; validated E2E
- Sliding-window RPM and minimal /metrics counters
- Docs: Quickstart SSE/upload examples, OpenAPI updates

## Changes
- See CHANGELOG.md for full details

## Upgrade Notes
- Server must run with ADC (`GOOGLE_APPLICATION_CREDENTIALS`) for artifact signing
- CORS and bucket CORS must be configured for browser uploads

## Credits
- Maintainer: Zac Forristall (@bubroz)
