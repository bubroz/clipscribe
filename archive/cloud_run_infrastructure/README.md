# Cloud Run Infrastructure Archive

**Archived:** October 28, 2025  
**Reason:** Migrated to Modal Labs for GPU transcription

## Contents

**Docker Files:**
- `Dockerfile` - Multi-stage build for Cloud Run
- `Dockerfile.api` - FastAPI service
- `Dockerfile.job` - Cloud Run Jobs worker

**Cloud Build:**
- `cloudbuild.yaml` - Main build config
- `cloudbuild-jobs.yaml` - Jobs build config  
- `cloudbuild-worker.yaml` - Worker build config

**Docker Configs:**
- `docker/nginx.conf` - Nginx configuration
- `docker/redis.conf` - Redis configuration
- `docker/supervisord.conf` - Supervisor configuration

## Why Archived

**Original Plan:** Deploy WhisperX on Cloud Run with GPU support

**Reality:** Cloud Run doesn't support GPUs in Jobs/Services (only Cloud Run Functions with limited GPU access)

**Pivot Decision (Oct 19, 2025):** Migrated to Modal Labs
- A10G GPU support
- 11.6x realtime processing
- 92% profit margin
- Simpler deployment (no Docker, no quotas)

**Status:** Modal deployment successful and validated. Cloud Run infrastructure no longer needed.

## Future Use

May be useful if:
- Deploying web frontend to Cloud Run (CPU only)
- Running API services on Cloud Run
- Need Docker containers for other services

Can retrieve from this archive if needed.

