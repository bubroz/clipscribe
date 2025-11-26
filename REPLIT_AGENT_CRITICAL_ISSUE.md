# CRITICAL: Missing Dockerfile Blocks Deployment

**Date:** November 26, 2025 22:05 UTC  
**Status:** 🔴 **BLOCKED - Dockerfile Does Not Exist**

---

## Critical Discovery

The deployment workflow (`.github/workflows/deploy.yml`) expects:
- `Dockerfile` with `target: api`

**But `Dockerfile` does not exist in the repository.**

This is why:
- No builds are running for v3.1.x tags
- The service is still using the old November 13 image
- New code changes cannot be deployed

---

## Current State

### Repository
- ✅ Code fixes committed (error handling improvements)
- ✅ Workflow fixed (uses correct Dockerfile path)
- ❌ **Dockerfile missing** - cannot build images

### Running Service
- **Image:** `gcr.io/prismatic-iris-429006-g6/clipscribe-api@sha256:319ebe9a...` (Nov 13)
- **Code:** Old code (returns mock URLs)
- **Status:** Working but outdated

---

## Required Action

**We need to create a `Dockerfile` with an `api` target** that:
1. Builds the ClipScribe API service
2. Installs dependencies (Poetry)
3. Runs the FastAPI application
4. Exposes port 8000

---

## Next Steps

1. **Create Dockerfile** with `api` target
2. **Test build locally** (if possible)
3. **Push new tag** to trigger deployment
4. **Monitor build** in GitHub Actions
5. **Verify deployment** once complete

---

## Impact

- **Presigned URLs:** Still returning mock (old code)
- **Dashboard Integration:** Blocked until deployment completes
- **Timeline:** Delayed until Dockerfile is created

---

**This is the root cause of why the deployment isn't happening.**

