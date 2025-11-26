# Presigned URL Deployment Status - Critical Update

**Date:** November 26, 2025 21:45 UTC  
**Status:** 🔴 **Deployment Blocked - Missing Dockerfile**

---

## Critical Issue Discovered

The v3.1.4 deployment is **failing** because:

1. **GitHub Actions Workflow** references `Dockerfile.api` which **does not exist**
2. **No Docker builds** are running for v3.1.1, v3.1.2, v3.1.3, or v3.1.4
3. **Current running service** is using an **old gcr.io image** from November 13
4. **Code changes** (error handling improvements) are **committed but not deployed**

---

## Current Deployment Status

### Cloud Run Service
- **Running Revision:** `clipscribe-api-00048-rhr` (old gcr.io image)
- **Latest Failed Revision:** `clipscribe-api-00050-pn9` (tried to use non-existent v3.1.3 image)
- **Image:** `gcr.io/prismatic-iris-429006-g6/clipscribe-api@sha256:319ebe9a...` (from Nov 13)
- **Code Version:** Old code (still returns mock URLs)

### GitHub Actions
- **Workflow:** `.github/workflows/deploy.yml`
- **Trigger:** Tag push (`v3.1.4` pushed)
- **Status:** ❌ **Failing** - Cannot find `Dockerfile.api`
- **Builds:** No builds found for v3.1.x tags

### Artifact Registry
- **Images Available:** Only old versions (v2.54.2, v2.53.0, etc.)
- **Missing:** All v3.1.x images (v3.1.1, v3.1.2, v3.1.3, v3.1.4)

---

## Root Cause

The deployment workflow (`.github/workflows/deploy.yml`) expects:
```yaml
file: Dockerfile.api
```

But this file **does not exist** in the repository. The workflow fails at the Docker build step.

---

## Fix Required

### Option 1: Create Dockerfile.api (Recommended)
Create a Dockerfile specifically for the API service, or update the workflow to use an existing Dockerfile.

### Option 2: Update Workflow
Modify `.github/workflows/deploy.yml` to use the correct Dockerfile path (likely `Dockerfile` with a target).

### Option 3: Manual Deployment
Build and deploy manually using the existing gcr.io images or create the Dockerfile.api.

---

## Code Changes Status

### Committed (Not Deployed)
- ✅ Error handling improved (returns error instead of mock)
- ✅ Better logging for presigned URL failures
- ✅ GCS bucket name sanitization

### IAM Permissions
- ✅ `roles/storage.objectCreator` - Granted
- ✅ `roles/storage.legacyBucketWriter` - Granted  
- ✅ `roles/iam.serviceAccountTokenCreator` - Granted (project level)
- ✅ `roles/iam.serviceAccountTokenCreator` - Granted (service account level)

**All permissions are correctly configured.**

---

## Immediate Action Required

**The code changes cannot be deployed until the Dockerfile issue is resolved.**

1. **Create `Dockerfile.api`** OR
2. **Update `.github/workflows/deploy.yml`** to use correct Dockerfile
3. **Trigger new deployment** (push new tag or manual workflow dispatch)

---

## Testing Current State

The current running service (old code) still returns mock URLs:
```bash
curl -X POST https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/uploads/presign \
  -H "Authorization: Bearer bet_7ePK4urh71QTBB5fNfDsUw" \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.mp3","content_type":"audio/mpeg"}'

# Returns: {"upload_url":"...?signature=mock",...}
```

**Once the new code is deployed, it will return an error message showing the actual signing failure, which will help us fix it.**

---

## Next Steps

1. **Fix Dockerfile issue** (create Dockerfile.api or update workflow)
2. **Deploy new code** (will show actual error instead of mock)
3. **Fix signing issue** based on error message
4. **Verify presigned URLs work**

**ETA:** Once Dockerfile is fixed, deployment takes ~5-10 minutes.

