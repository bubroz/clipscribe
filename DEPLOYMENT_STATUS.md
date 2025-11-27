# ClipScribe Deployment Status

**Last Updated:** November 27, 2025  
**Current Version:** v3.1.10

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

### v3.1.9 - IAM SignBlob for Presigned URLs (January 27, 2025)

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

## Next Steps

1. **CI Improvements:**
   - Address remaining mypy type annotation issues
   - Investigate and fix test failures

2. **Monitoring:**
   - Monitor Cloud Run logs for any errors
   - Verify presigned URL generation continues working
   - Check API response times

---

## Deployment Commands

```bash
# Get service URL
gcloud run services describe clipscribe-api --region=us-central1 --format="value(status.url)"

# Check revision status
gcloud run revisions describe clipscribe-api-00056-92z --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=clipscribe-api" --limit=50
```

