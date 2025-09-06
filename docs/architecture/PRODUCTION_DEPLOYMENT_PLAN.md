# ClipScribe Production Architecture

*Last Updated: 2025-08-26*
*Version: v2.51.0*

## Overview

This document provides a high-level overview of the ClipScribe production architecture as deployed on Google Cloud Run. The system is designed as a scalable, multi-service application to provide robust video intelligence processing.

## Core Services

The production environment consists of two main services:

1.  **`clipscribe-api`**: A FastAPI application that serves as the core of the platform. It handles all video processing, AI-powered analysis, job queuing, and data storage.
2.  **`clipscribe-web`**: A lightweight, static web server that provides the user interface for interacting with the API.

These services are deployed as separate, containerized applications on Google Cloud Run, which allows them to be scaled and managed independently.

## Technology Stack

-   **Cloud Platform**: Google Cloud Run
-   **Backend**: Python 3.12 with FastAPI and Uvicorn
-   **Job Queuing**: Redis and RQ for asynchronous job processing
-   **AI Models**: Google's Gemini 2.5 Pro and Flash models
-   **Build & Deploy**: Docker with multi-stage builds and Google Cloud Build for CI/CD

## Deployment & CI/CD

The entire build and deployment process is automated via the `cloudbuild.yaml` file in the root of the repository. This pipeline handles:

1.  **Building** the Docker images for both the `api` and `web` services.
2.  **Pushing** the images to Google Container Registry.
3.  **Deploying** the new versions to Google Cloud Run.

This allows for consistent, repeatable, and reliable deployments.

## Custom Domain & DNS

The services are configured to be accessible via a custom domain, with DNS managed by Cloudflare.

-   **API**: `api.yourdomain.com`
-   **Web**: `yourdomain.com`

Google Cloud Run automatically handles SSL certificate provisioning and renewal for these custom domains.

## Security

-   **Secrets Management**: The `GOOGLE_API_KEY` is passed to the Cloud Run service as an environment variable. For a more secure setup, it is recommended to use a secret manager like Google Secret Manager.
-   **Service Permissions**: The services are configured to be publicly accessible, but this can be restricted using IAM roles in a more secure environment.
