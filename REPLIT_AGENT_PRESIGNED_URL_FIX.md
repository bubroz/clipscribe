# Presigned URL 403 Error - Investigation & Fix

**Date:** November 26, 2025  
**Status:** 🔴 Root Cause Identified, Fix In Progress

---

## Problem Summary

The presigned URL endpoint is returning mock URLs (`signature=mock`) instead of real signed URLs, causing 403 errors when browsers try to upload files.

---

## Root Cause

The `generate_signed_url()` call in the presign endpoint is failing silently and falling through to the mock fallback. The service account needs specific IAM permissions to generate signed URLs.

---

## Fixes Applied

### 1. Service Account Permissions ✅
Granted the following permissions to `16459511304-compute@developer.gserviceaccount.com`:

- ✅ `roles/storage.objectCreator` - Create objects in bucket
- ✅ `roles/storage.legacyBucketWriter` - Write access to bucket  
- ✅ `roles/iam.serviceAccountTokenCreator` - Sign blobs (required for presigned URLs)

**Bucket IAM Policy:**
```bash
gcloud storage buckets get-iam-policy gs://clipscribe-artifacts-16459511304
```

**Project IAM Policy:**
```bash
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:16459511304-compute@developer.gserviceaccount.com"
```

### 2. Code Improvements ✅
- Added error logging to surface actual exceptions when signing fails
- Committed and pushed to GitHub (will be in next deployment)

### 3. GCS CORS Configuration ✅
- CORS configured on bucket to allow browser uploads
- Verified with `gsutil cors get gs://clipscribe-artifacts-16459511304`

---

## Current Status

**Issue:** Code is still returning mock URLs  
**Deployed Version:** `v3.1.3` (includes error logging, but signing still failing)  
**Permissions:** ✅ All required permissions granted

**Possible Causes:**
1. **Permission Propagation Delay:** IAM changes can take 1-2 minutes to propagate
2. **Code Needs Redeployment:** The improved error logging needs to be deployed to see actual errors
3. **Service Account Self-Signing:** May need explicit service account email in signing call

---

## Next Steps

### Option 1: Wait for Permission Propagation (Recommended)
IAM permission changes can take 1-2 minutes to propagate. Wait 2-3 minutes, then test again:

```bash
curl -X POST https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/uploads/presign \
  -H "Authorization: Bearer bet_7ePK4urh71QTBB5fNfDsUw" \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.mp3","content_type":"audio/mpeg"}'
```

Check if URL contains `signature=mock` or a real signature.

### Option 2: Check Cloud Run Logs
Once the improved error logging is deployed, check logs for actual error:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=clipscribe-api" \
  --limit=20 \
  --format="table(timestamp,textPayload,jsonPayload.message)"
```

### Option 3: Manual Test with Real Signed URL
Test if signing works locally (requires Google Cloud SDK):

```python
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('clipscribe-artifacts-16459511304')
blob = bucket.blob('uploads/test/test.mp3')
url = blob.generate_signed_url(
    version='v4',
    expiration=900,
    method='PUT',
    content_type='audio/mpeg'
)
print(url)
```

---

## Verification Commands

### Test Presign Endpoint
```bash
TOKEN="bet_7ePK4urh71QTBB5fNfDsUw"
curl -X POST https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/uploads/presign \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.mp3","content_type":"audio/mpeg"}' | jq -r '.upload_url'
```

**Expected:** URL should NOT contain `signature=mock`  
**Actual:** Currently returns `signature=mock`

### Test Upload to Presigned URL
```bash
UPLOAD_URL="<url_from_presign_endpoint>"
echo "test content" | curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: audio/mpeg" \
  --data-binary @- \
  -w "\nHTTP Status: %{http_code}\n"
```

**Expected:** HTTP 200 or 204  
**Actual:** HTTP 403 (because URL is mock)

---

## Alternative Solution (If Permissions Don't Work)

If the service account signing still fails, we can:

1. **Use a dedicated service account** with explicit signing permissions
2. **Generate signed URLs server-side** using a service account key (less secure)
3. **Use resumable uploads** instead of presigned URLs (more complex but more reliable)

---

## Summary

- ✅ **Permissions:** All required IAM roles granted
- ✅ **CORS:** Configured on bucket
- ✅ **Code:** Error logging improved (needs deployment)
- ⏳ **Status:** Waiting for permission propagation or code redeployment

**Recommendation:** Wait 2-3 minutes for IAM propagation, then test again. If still failing, check Cloud Run logs for the actual error message once the improved logging is deployed.

