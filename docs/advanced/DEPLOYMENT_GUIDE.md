# ClipScribe Deployment Guide

*Last Updated: July 20, 2025*  
*Version: v2.19.3*

## Overview

ClipScribe can be deployed to multiple platforms. This guide covers the two recommended options:

1. **Streamlit Cloud** - Quick & free for testing
2. **Google Cloud Run** - Professional & scalable for production

## Deployment Options Comparison

| Feature | Streamlit Cloud | Google Cloud Run |
|---------|----------------|------------------|
| **Setup Time** | 5 minutes | 30 minutes |
| **Cost** | Free (1 app) | ~$15/month warm instance |
| **Custom Domain** | ❌ | ✅ |
| **Cold Start** | 30-60s | 0s (with warm instance) |
| **Professional URL** | yourapp.streamlit.app | clipscribe.com |
| **Resource Limits** | Limited | 32GB RAM, 60min timeout |
| **API Support** | UI only | UI + API endpoints |
| **Best For** | Testing, demos to friends | Production, professional demos |

## Option 1: Streamlit Cloud (Quick Start)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free)
- Repository pushed to GitHub

### Deployment Steps

1. **Connect Repository**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select your ClipScribe repository

2. **Configure App**
   - Main file: `streamlit_app/ClipScribe_Mission_Control.py`
   - Python version: 3.12
   - Add secrets in Streamlit Cloud dashboard:
     ```toml
     GOOGLE_API_KEY = "your-api-key-here"
     ```

3. **Deploy**
   - Click "Deploy"
   - Wait 2-5 minutes for initial build
   - Your app will be live at: `https://[your-app-name].streamlit.app`

### Limitations
- Cold starts after 7 days of inactivity
- Limited compute resources
- No custom domain support
- Hobby-tier appearance

## Option 2: Google Cloud Run (Professional)

### Prerequisites
- Google Cloud Project with billing enabled
- gcloud CLI installed
- Docker installed (for local testing)
- Domain name (optional but recommended)

### Initial Setup

1. **Enable Required APIs**
   ```bash
   gcloud services enable \
     cloudbuild.googleapis.com \
     run.googleapis.com \
     containerregistry.googleapis.com
   ```

2. **Set Default Project**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

### Manual Deployment

1. **Build and Test Locally**
   ```bash
   # Build Docker image
   docker build -t clipscribe .
   
   # Test locally
   docker run -p 8080:8080 \
     -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
     clipscribe
   ```

2. **Deploy to Cloud Run**
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

1. **Set Up Cloud Build Trigger**
   ```bash
   # Create trigger for main branch
   gcloud builds triggers create github \
     --repo-name=clipscribe \
     --repo-owner=YOUR_GITHUB_USERNAME \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

2. **Push to Deploy**
   - Any push to main branch triggers automatic deployment
   - Cloud Build handles Docker build and Cloud Run deployment

### Custom Domain Setup

1. **Verify Domain Ownership**
   ```bash
   gcloud domains verify YOUR_DOMAIN.COM
   ```

2. **Map Domain to Cloud Run**
   ```bash
   gcloud run domain-mappings create \
     --service clipscribe \
     --domain clipscribe.yourdomain.com \
     --region us-central1
   ```

3. **Update DNS Records**
   - Add the provided DNS records to your domain registrar
   - Wait 15-30 minutes for propagation

### Environment Variables

For Cloud Run, set these via the console or CLI:

```bash
gcloud run services update clipscribe \
  --update-env-vars \
    GOOGLE_API_KEY=$GOOGLE_API_KEY,\
    VERTEX_AI_PROJECT=$PROJECT_ID,\
    VERTEX_AI_LOCATION=us-central1
```

## Cost Optimization

### Streamlit Cloud
- **Free tier**: 1 app, unlimited usage
- **No costs**: Perfect for personal use

### Cloud Run
- **Free tier**: 2M requests, 360k GB-seconds/month
- **Warm instance**: ~$15/month (keeps app responsive)
- **Per-request after free tier**: ~$0.001 per video processed

**Recommendation**: Keep min-instances=0 for development, =1 for production demos

## Security Best Practices

1. **Never commit secrets**
   - Use environment variables
   - Store API keys in platform secret managers

2. **Cloud Run Security**
   ```bash
   # Restrict to authenticated users only
   gcloud run services update clipscribe \
     --no-allow-unauthenticated
   
   # Add specific users
   gcloud run services add-iam-policy-binding clipscribe \
     --member="user:email@example.com" \
     --role="roles/run.invoker"
   ```

3. **API Key Management**
   - Use Google Secret Manager for production
   - Rotate keys regularly
   - Monitor usage in Google Cloud Console

## Monitoring & Logs

### Streamlit Cloud
- Basic logs in Streamlit dashboard
- Limited metrics

### Cloud Run
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=clipscribe" \
  --limit 50

# Stream logs
gcloud alpha run services logs tail clipscribe

# View metrics in Cloud Console
# https://console.cloud.google.com/run
```

## Troubleshooting

### Common Issues

1. **Cold Start (Streamlit Cloud)**
   - Expected behavior after inactivity
   - Solution: Use Cloud Run with min-instances=1

2. **Memory Errors**
   - Increase Cloud Run memory to 8Gi for large videos
   - Consider implementing video chunking

3. **Timeout Errors**
   - Cloud Run max timeout is 60 minutes
   - Break long videos into segments

4. **Authentication Issues**
   - Verify GOOGLE_API_KEY is set correctly
   - Check Cloud Run service account permissions

## Deployment Checklist

- [ ] API keys configured as environment variables
- [ ] Docker image builds successfully
- [ ] Local testing passes
- [ ] Cloud Build trigger configured (if using CI/CD)
- [ ] Custom domain verified (if using)
- [ ] Monitoring alerts set up
- [ ] Backup deployment documented
- [ ] Team members have access

## Recommended Progression

1. **Week 1**: Deploy to Streamlit Cloud for testing
2. **Week 2**: Set up Cloud Run for demos
3. **Week 3**: Configure custom domain
4. **Week 4**: Enable CI/CD with Cloud Build

Remember: Start simple, then scale as needed :-) 