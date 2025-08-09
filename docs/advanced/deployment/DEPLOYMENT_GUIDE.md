# ClipScribe Deployment Guide

*Last Updated: August 8, 2025*  
*Version: v2.29.3*

## Overview

ClipScribe can be deployed to multiple platforms. This guide covers the two recommended options:

1. **Streamlit Cloud** - Quick & free for testing and demos.
2. **Google Cloud Run** - Professional & scalable for production.

## Deployment Options Comparison

| Feature | Streamlit Cloud | Google Cloud Run |
|---|---|---|
| **Setup Time** | 5 minutes | 30 minutes |
| **Cost** | Free (1 app) | ~$15/month warm instance |
| **Custom Domain** |  |  |
| **Cold Start** | 30-60s | 0s (with warm instance) |
| **Resource Limits** | Limited | 32GB RAM, 60min timeout |
| **API Support** | UI only | UI + API endpoints |
| **Best For** | Testing, demos | Production, professional use |

## Option 1: Streamlit Cloud (Quick Start)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free)
- Repository pushed to GitHub

### Deployment Steps

1. **Connect Repository**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account and select your ClipScribe repository.

2. **Configure App**
   - Main file: `streamlit_app/ClipScribe_Mission_Control.py`
   - Python version: 3.12
   - Add secrets in the Streamlit Cloud dashboard:
     ```toml
     GOOGLE_API_KEY = "your-api-key-here"
     ```

3. **Deploy**
   - Click "Deploy" and wait 2-5 minutes.
   - Your app will be live at: `https://[your-app-name].streamlit.app`

## Option 2: Google Cloud Run (Professional)

### Prerequisites
- Google Cloud Project with billing enabled
- gcloud CLI and Docker installed

### Initial Setup

1. **Enable Required APIs**
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
   ```

2. **Set Default Project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

### Deployment

```bash
# Deploy from source
gcloud run deploy clipscribe \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --min-instances 1 \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY
```

### Automated Deployment (CI/CD)
Use the `cloudbuild.yaml` file in the repository to set up a Cloud Build trigger for automatic deployments on pushes to the main branch.

### Custom Domain Setup
1. **Verify Domain Ownership**: `gcloud domains verify YOUR_DOMAIN.COM`
2. **Map Domain to Cloud Run**: `gcloud run domain-mappings create --service clipscribe --domain clipscribe.yourdomain.com`
3. **Update DNS Records** in your domain registrar.

## Security Best Practices

- **Never commit secrets**: Use environment variables or platform secret managers.
- **Restrict access**: For Cloud Run, use `--no-allow-unauthenticated` and add specific users via IAM roles.
- **Rotate keys**: Regularly rotate your API keys.

## Monitoring & Logs

- **Streamlit Cloud**: Basic logs are available in the dashboard.
- **Cloud Run**: Use `gcloud logging read` or `gcloud alpha run services logs tail clipscribe` to view logs. Metrics are available in the Google Cloud Console.
