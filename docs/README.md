# ClipScribe Documentation v2.29.7

*Last Updated: August 23, 2025*

## Overarching Goals and Stages

**Stage 1**: Quick series analysis (3 videos in <5 minutes) for competitive intelligence
**Stage 2**: Enterprise scale (thousands of users, 1000+ videos) with Kubernetes deployment
**Focus**: Intelligence extraction excellence with safe concurrency limits

## Quick Start for Real Use

For immediate 3-video analysis:
```bash
poetry run python examples/pbs_fast_batch.py --limit 3
# Select option 4 (Test mode) for maximum speed
``` 

## API Documentation

- API Readiness Spec: `docs/architecture/API_V1_SERVICE_READINESS.md`
- OpenAPI (machine-readable): `docs/architecture/openapi.yaml`
- API Quickstart: `docs/API_QUICKSTART.md`
- Replit Project Guide: `docs/REPLIT_PROJECT_GUIDE.md`
 - Cost Analysis: `docs/COST_ANALYSIS.md`
- Testing Policy: E2E tests are opt-in (Vertex ADC by default; AI Studio allowed with explicit flag).
- Architecture: `docs/architecture/ARCHITECTURE_DIAGRAM.md`