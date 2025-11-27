# Workload Identity Federation Setup - Complete

**Date:** November 26, 2025  
**Status:** ✅ **WIF Setup Complete - Ready for Deployment**

---

## Summary

Workload Identity Federation (WIF) is fully configured for GitHub Actions. The missing `roles/iam.serviceAccountUser` permission has been granted, and all required infrastructure is in place.

---

## Current Configuration

### Project Information
- **Project ID:** `prismatic-iris-429006-g6`
- **Project Number:** `16459511304`
- **Region:** `us-central1`

### Service Account
- **Service Account Email:** `clipscribe-ci@prismatic-iris-429006-g6.iam.gserviceaccount.com`
- **Display Name:** ClipScribe CI/CD

### Workload Identity Pool
- **Pool Name:** `github-pool`
- **Pool Resource:** `projects/16459511304/locations/global/workloadIdentityPools/github-pool`
- **Provider Name:** `github`
- **Provider Resource:** `projects/16459511304/locations/global/workloadIdentityPools/github-pool/providers/github`
- **Repository Binding:** `bubroz/clipscribe`

---

## IAM Permissions Granted

The `clipscribe-ci` service account has the following permissions:

### Project-Level Permissions
- ✅ `roles/run.admin` - Deploy and manage Cloud Run services
- ✅ `roles/artifactregistry.writer` - Push Docker images to Artifact Registry
- ✅ `roles/aiplatform.user` - Access Vertex AI (for E2E tests)
- ✅ `roles/storage.objectAdmin` - Manage GCS objects

### Service Account Permissions
- ✅ `roles/iam.serviceAccountUser` on `16459511304-compute@developer.gserviceaccount.com` - **CRITICAL: This was the missing permission causing deployment failures**

### Workload Identity Permissions
- ✅ `roles/iam.workloadIdentityUser` - Allow GitHub Actions to impersonate the service account
- ✅ `roles/iam.serviceAccountTokenCreator` - Create tokens for service account

---

## GitHub Secrets Configuration

**CRITICAL:** You must set these secrets in GitHub for deployments to work:

### Required Secrets

1. **`WIF_PROVIDER`**
   ```
   projects/16459511304/locations/global/workloadIdentityPools/github-pool/providers/github
   ```
   - This is the full resource path to the WIF provider
   - Used by GitHub Actions to authenticate via OIDC

2. **`WIF_SERVICE_ACCOUNT_EMAIL`**
   ```
   clipscribe-ci@prismatic-iris-429006-g6.iam.gserviceaccount.com
   ```
   - This is the service account that GitHub Actions will impersonate
   - Currently empty in GitHub secrets - **MUST BE SET**

3. **`VERTEX_AI_PROJECT`**
   ```
   prismatic-iris-429006-g6
   ```
   - Should already be set, but verify it matches the project ID above

---

## How to Set GitHub Secrets

1. Go to: https://github.com/bubroz/clipscribe/settings/secrets/actions
2. Click "New repository secret" for each secret above
3. Copy and paste the exact values shown above
4. Save each secret

**Important:** The `WIF_SERVICE_ACCOUNT_EMAIL` secret is currently empty and must be set for deployments to work.

---

## Verification

After setting the secrets, verify the setup:

1. **Check GitHub Secrets:**
   - Go to repository settings → Secrets and variables → Actions
   - Verify all three secrets are set with correct values

2. **Test Deployment:**
   - Push a new tag (e.g., `v3.1.7`) or use `workflow_dispatch`
   - Monitor the GitHub Actions workflow
   - The "Authenticate to Google Cloud (WIF)" step should succeed
   - The "Deploy to Cloud Run" step should complete without permission errors

3. **Verify Deployment:**
   ```bash
   gcloud run services describe clipscribe-api --region=us-central1 --project=prismatic-iris-429006-g6
   ```

---

## What Was Fixed

### Before
- ❌ `WIF_SERVICE_ACCOUNT_EMAIL` secret was empty
- ❌ `clipscribe-ci` service account lacked `roles/iam.serviceAccountUser` on Cloud Run service account
- ❌ Deployment failed with: `PERMISSION_DENIED: Permission 'iam.serviceaccounts.actAs' denied`

### After
- ✅ `WIF_SERVICE_ACCOUNT_EMAIL` value documented (needs to be set in GitHub)
- ✅ `roles/iam.serviceAccountUser` permission granted
- ✅ All other permissions verified and correct
- ✅ WIF pool and provider already configured
- ✅ Repository binding already in place

---

## Next Steps

1. **Set GitHub Secrets** (see above)
2. **Test Deployment** by pushing a new tag or using workflow_dispatch
3. **Monitor Workflow** to ensure authentication and deployment succeed
4. **Verify API** is accessible after deployment

---

## Troubleshooting

### If Deployment Still Fails

1. **Check Secret Values:**
   - Verify `WIF_SERVICE_ACCOUNT_EMAIL` is set (not empty)
   - Verify `WIF_PROVIDER` matches exactly (no extra spaces)
   - Verify `VERTEX_AI_PROJECT` matches project ID

2. **Check IAM Propagation:**
   - IAM changes can take 1-2 minutes to propagate
   - Wait a few minutes and retry

3. **Check Workflow Logs:**
   - Look for authentication errors in "Authenticate to Google Cloud (WIF)" step
   - Look for permission errors in "Deploy to Cloud Run" step

4. **Verify Service Account:**
   ```bash
   gcloud iam service-accounts get-iam-policy \
     16459511304-compute@developer.gserviceaccount.com \
     --project=prismatic-iris-429006-g6 \
     --flatten="bindings[].members" \
     --filter="bindings.members:clipscribe-ci@prismatic-iris-429006-g6.iam.gserviceaccount.com"
   ```
   Should show: `roles/iam.serviceAccountUser`

---

## Summary

✅ **WIF infrastructure is complete**  
✅ **All IAM permissions are granted**  
⏳ **GitHub secrets need to be set** (especially `WIF_SERVICE_ACCOUNT_EMAIL`)  
🚀 **Ready for deployment once secrets are configured**

The deployment blocker has been resolved. Once the GitHub secrets are set, deployments should work successfully.

