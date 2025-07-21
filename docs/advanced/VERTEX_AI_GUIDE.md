# Vertex AI Integration Guide

*Last Updated: July 20, 2025*
*Related: [Getting Started](../GETTING_STARTED.md) | [Pre-Upload Videos](../PRE_UPLOAD_VIDEOS.md)*

## Overview

ClipScribe supports Google Cloud Vertex AI for enterprise-scale video processing. While the standard Gemini API is perfect for most users, Vertex AI offers advantages for large-scale deployments.

## When to Use Vertex AI vs Gemini API

### Use Gemini API (Default) When:
- Processing < 100 videos per day
- Want simplest setup (just an API key)
- Cost is ~$0.0035 per video
- Don't need enterprise features

### Use Vertex AI When:
- Processing 100+ videos per day
- Need enterprise security/compliance
- Want to pre-upload videos to GCS
- Need higher quotas and reliability
- Have existing GCP infrastructure

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Vertex AI API** enabled in your project
3. **Service Account** with proper permissions
4. **Google Cloud SDK** installed locally

## Setup Instructions

### 1. Enable Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com
```

### 2. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create clipscribe-vertex \
    --display-name="ClipScribe Vertex AI"

# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:clipscribe-vertex@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create vertex-ai-key.json \
    --iam-account=clipscribe-vertex@PROJECT_ID.iam.gserviceaccount.com
```

### 3. Configure Environment

```bash
# Set authentication
export GOOGLE_APPLICATION_CREDENTIALS="path/to/vertex-ai-key.json"

# Set project details
export VERTEX_AI_PROJECT="your-project-id"
export VERTEX_AI_LOCATION="us-central1"  # or your preferred region
```

## Pre-Uploading Videos to GCS

Vertex AI requires videos to be in Google Cloud Storage. ClipScribe provides tools to help:

### Method 1: Pre-Upload Script

```bash
# Pre-upload videos from URLs
python scripts/pre_upload_videos.py \
    --urls "https://youtube.com/watch?v=video1" \
           "https://youtube.com/watch?v=video2" \
    --bucket "your-gcs-bucket"
```

### Method 2: Batch Upload

```python
from clipscribe.utils.gcs_uploader import GCSVideoUploader

uploader = GCSVideoUploader(
    project_id="your-project-id",
    bucket_name="your-bucket"
)

# Upload multiple videos
videos = [
    "https://youtube.com/watch?v=video1",
    "https://youtube.com/watch?v=video2"
]

gcs_uris = await uploader.batch_upload(videos)
```

## Processing Videos with Vertex AI

### Using GCS URIs Directly

```bash
# Process pre-uploaded video
clipscribe transcribe "gs://your-bucket/videos/video.mp4" \
    --mode video
```

### Programmatic Usage

```python
from clipscribe.retrievers.vertex_ai_transcriber import VertexAITranscriber

transcriber = VertexAITranscriber(
    project_id="your-project-id",
    location="us-central1"
)

# Process video from GCS
result = await transcriber.transcribe_video(
    "gs://your-bucket/videos/video.mp4"
)
```

## Cost Comparison

### Gemini API Costs
- **Processing**: $0.0035 per video (10 min)
- **Setup**: None
- **Storage**: None (direct URLs)

### Vertex AI Costs
- **Processing**: ~$0.003 per video (slightly lower)
- **Storage**: ~$0.02/GB/month (GCS)
- **Network**: Egress charges if downloading
- **Setup**: GCP infrastructure costs

## Performance & Limits

### Gemini API
- **Rate Limit**: 15 requests/minute
- **Daily Limit**: 1500 requests
- **Max Video Size**: 1GB
- **Timeout**: 5 minutes

### Vertex AI
- **Rate Limit**: Higher (project-based)
- **Daily Limit**: No hard limit
- **Max Video Size**: 2GB
- **Timeout**: Configurable

## Best Practices

### 1. Batch Processing
```python
# Process multiple videos efficiently
videos = load_video_list()
for batch in chunks(videos, size=10):
    await process_batch(batch)
```

### 2. Cost Optimization
- Pre-upload during off-peak hours
- Use lifecycle policies to auto-delete old videos
- Process in regions close to your users

### 3. Error Handling
```python
try:
    result = await transcriber.transcribe_video(gcs_uri)
except VertexAIError as e:
    if e.code == 'RESOURCE_EXHAUSTED':
        # Implement exponential backoff
        await asyncio.sleep(60)
        retry()
```

## Migration from Gemini API

Switching from Gemini API to Vertex AI:

1. **Keep your existing code** - ClipScribe handles routing
2. **Pre-upload videos** to GCS
3. **Update environment** variables
4. **Process using GCS URIs** instead of URLs

## Troubleshooting

### "Permission Denied"
```bash
# Check service account permissions
gcloud projects get-iam-policy PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:clipscribe-vertex@*"
```

### "Video Not Found"
```bash
# Verify GCS upload
gsutil ls gs://your-bucket/videos/
```

### "Quota Exceeded"
- Check Vertex AI quotas in Cloud Console
- Request quota increase if needed
- Implement rate limiting in your code

## Example: Enterprise Pipeline

```python
# Enterprise video processing pipeline
class EnterpriseVideoPipeline:
    def __init__(self):
        self.uploader = GCSVideoUploader()
        self.transcriber = VertexAITranscriber()
        
    async def process_video_batch(self, urls: List[str]):
        # 1. Upload to GCS
        gcs_uris = await self.uploader.batch_upload(urls)
        
        # 2. Process with Vertex AI
        results = []
        for uri in gcs_uris:
            result = await self.transcriber.transcribe_video(uri)
            results.append(result)
            
        # 3. Clean up GCS (optional)
        if self.auto_cleanup:
            await self.uploader.cleanup(gcs_uris)
            
        return results
```

## Security Considerations

1. **Service Account Keys**: Store securely, rotate regularly
2. **GCS Buckets**: Use private buckets with proper IAM
3. **Network**: Use VPC Service Controls if required
4. **Audit Logs**: Enable Cloud Audit Logs for compliance

## Getting Help

- **GCP Support**: For Vertex AI issues
- **ClipScribe Issues**: GitHub issues
- **Documentation**: This guide and GCP docs

Remember: Vertex AI is powerful but requires more setup. Start with Gemini API and migrate when you need scale! 🚀 