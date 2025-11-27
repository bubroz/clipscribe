# IAM Permissions Verification for Presigned URLs

**Last Updated:** November 27, 2025  
**Purpose:** Verify and grant required IAM permissions for presigned URL generation on Cloud Run

---

## Required Permission

The Cloud Run service account needs `roles/iam.serviceAccountTokenCreator` on **itself** to use IAM SignBlob API for generating presigned URLs.

**Service Account:** `16459511304-compute@developer.gserviceaccount.com`  
**Project:** `prismatic-iris-429006-g6`

---

## Verification

### Check Current IAM Policy

```bash
gcloud iam service-accounts get-iam-policy \
  16459511304-compute@developer.gserviceaccount.com \
  --project=prismatic-iris-429006-g6 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:16459511304-compute@developer.gserviceaccount.com"
```

**Expected Output:** Should show `roles/iam.serviceAccountTokenCreator` binding

---

## Grant Permission (if missing)

### Using gcloud CLI

```bash
gcloud iam service-accounts add-iam-policy-binding \
  16459511304-compute@developer.gserviceaccount.com \
  --member="serviceAccount:16459511304-compute@developer.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=prismatic-iris-429006-g6
```

### Using Cloud Console

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=prismatic-iris-429006-g6
2. Find service account: `16459511304-compute@developer.gserviceaccount.com`
3. Click on the service account
4. Go to "Permissions" tab
5. Click "Grant Access"
6. Add principal: `16459511304-compute@developer.gserviceaccount.com`
7. Select role: `Service Account Token Creator`
8. Click "Save"

---

## Environment Variable (Optional but Recommended)

Set `GOOGLE_SERVICE_ACCOUNT_EMAIL` in Cloud Run to avoid metadata server queries:

```bash
gcloud run services update clipscribe-api \
  --region=us-central1 \
  --update-env-vars GOOGLE_SERVICE_ACCOUNT_EMAIL=16459511304-compute@developer.gserviceaccount.com \
  --project=prismatic-iris-429006-g6
```

---

## Testing

After granting permissions, test the presign endpoint:

```bash
curl -X POST https://clipscribe-api-df6nuv4qxa-uc.a.run.app/v1/uploads/presign \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.mp3", "content_type": "audio/mpeg"}'
```

**Expected Response:**
```json
{
  "upload_url": "https://storage.googleapis.com/...",
  "gcs_uri": "gs://..."
}
```

**Error Response (if permission missing):**
```json
{
  "code": "presign_failed",
  "message": "Failed to generate presigned URL: IAM SignBlob API call failed: ..."
}
```

---

## Troubleshooting

### Permission Denied Error

**Symptom:** `PERMISSION_DENIED` or `Permission 'iam.serviceaccounts.signBlob' denied`

**Solution:** Grant `roles/iam.serviceAccountTokenCreator` as shown above

### Token Expired Error

**Symptom:** `INVALID_ARGUMENT` or token-related errors

**Solution:** Ensure credentials are refreshed. The implementation automatically refreshes credentials.

### Service Account Email Not Found

**Symptom:** `Could not determine service account email`

**Solution:** Set `GOOGLE_SERVICE_ACCOUNT_EMAIL` environment variable in Cloud Run

---

## References

- [IAM SignBlob API Documentation](https://cloud.google.com/iam/docs/reference/credentials/rest/v1/projects.serviceAccounts/signBlob)
- [GCS Signed URLs with IAM](https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers#signing-iam)
- [Service Account Token Creator Role](https://cloud.google.com/iam/docs/service-accounts#the_service_account_token_creator_role)


