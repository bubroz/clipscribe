# ClipScribe Deployment Guide

*Last Updated: 2025-09-30*
*Version: v2.51.1*
*Status: Beta Deployment Strategy*

## Overview

ClipScribe is designed for a scalable, multi-service deployment on **Google Cloud Run**. This guide provides instructions for deploying ClipScribe in beta/production environments.

**⚠️ IMPORTANT**: ClipScribe is currently in private alpha. This deployment guide is for beta testers and the development team only.

**✨ NEW in v2.51.1**: curl-cffi browser impersonation for bot detection bypass is now included. Ensure your deployment environment supports curl-cffi dependencies (see requirements below).

## Beta Deployment Timeline

### Phase 1: Infrastructure (Month 1)
- Deploy API and Web services ✅
- Deploy Worker service (Cloud Run + Compute Engine) ⏳
- Implement monitoring and alerting
- Add cost controls and emergency stops

### Phase 2: Alpha Testing (Month 2)
- Deploy token authentication system
- Onboard 5-10 alpha testers
- Manual monitoring and support
- Gather feedback and iterate

### Phase 3: Beta Testing (Month 3-4)
- Scale to 20-50 beta users
- Implement usage tracking
- Add automated monitoring
- Prepare for payments

### Phase 4: Production (Month 5-6)
- Enable Stripe integration
- Launch marketing website
- Open public access
- Scale infrastructure

## Architecture

The production environment consists of three core services:

1.  **`clipscribe-api`**: A FastAPI application that handles job queueing and API endpoints
2.  **`clipscribe-web`**: A lightweight static web server that provides the user interface
3.  **`clipscribe-worker`**: A hybrid worker service (Cloud Run + Compute Engine) that processes videos

These services are deployed as separate containers but work together through Redis and Cloud Tasks.

## Automated Deployment with Cloud Build

The recommended and most reliable way to deploy ClipScribe is by using the `cloudbuild.yaml` file included in the repository. This file automates the entire build and deployment process.

### Prerequisites

- A Google Cloud Project with billing enabled.
- The `gcloud` CLI installed and authenticated.
- The following APIs enabled in your Google Cloud project:
  - Cloud Build API (`cloudbuild.googleapis.com`)
  - Cloud Run API (`run.googleapis.com`)
  - Artifact Registry API (`artifactregistry.googleapis.com`) or Container Registry API (`containerregistry.googleapis.com`)
- **curl-cffi dependencies** (v2.51.1+):
  - `curl-cffi` 0.13.0+ installed via Poetry
  - `yt-dlp` 2025.09.26+ with ImpersonateTarget support
  - System dependencies: `libcurl` with HTTP/3 support (included in most modern Docker base images)

### Deployment Steps

1.  **Configure your Project ID**:
    Open the `cloudbuild.yaml` file and replace `$PROJECT_ID` with your actual Google Cloud project ID if you are not using command line substitution.

2.  **Submit the Build**:
    From the root of the project directory, run the following command:

    ```bash
    gcloud builds submit --config cloudbuild.yaml
    ```

    This command will:
    - Build the `api` and `web` container images using the multi-stage `Dockerfile`.
    - Push the images to your project's Container Registry.
    - Deploy both services to Google Cloud Run.

3.  **Verify the Deployment**:
    After the build completes, you can verify that the services are running with the following command:

    ```bash
    gcloud run services list --region=us-central1
    ```

    You will see the URLs for your live `clipscribe-api` and `clipscribe-web` services.

## Custom Domain with Cloudflare

Once your services are deployed, you can map them to a custom domain using Cloudflare.

### 1. Add Custom Domain to Cloud Run

For each service (`clipscribe-api` and `clipscribe-web`), you need to map a custom domain:

```bash
# For the API service
gcloud run domain-mappings create --service clipscribe-api --domain api.yourdomain.com --region us-central1

# For the web service
gcloud run domain-mappings create --service clipscribe-web --domain yourdomain.com --region us-central1
```

### 2. Update DNS in Cloudflare

After running the commands above, Google Cloud will provide you with DNS records (usually a CNAME record). You will need to add these records to your domain's DNS settings in your Cloudflare dashboard.

- Log in to your Cloudflare account.
- Select your domain.
- Go to the "DNS" section.
- Add the `CNAME` records provided by Google Cloud.

### 3. SSL and Propagation

- **SSL Certificate**: Google Cloud will automatically provision a free SSL certificate for your custom domain. This process can take up to 15 minutes.
- **DNS Propagation**: It may take some time for the DNS changes to propagate.

Once the process is complete, your services will be available at your custom domain.

## Security Best Practices

- **Never commit secrets**: Use environment variables or a secret manager for your `GOOGLE_API_KEY`. The `cloudbuild.yaml` is currently configured with a placeholder; for a production setup, you should use Google Secret Manager.
- **Restrict Access**: For internal services, use `--no-allow-unauthenticated` and configure IAM for access control.

## Monitoring & Logs

- Use the Google Cloud Console to monitor the performance of your Cloud Run services.
- View logs with the following `gcloud` command:

  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=clipscribe-api" --limit=50
  ```
