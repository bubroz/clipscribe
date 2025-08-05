# Pre-Upload Videos to Google Cloud Storage

*Last Updated: July 20, 2025*

This guide explains how to pre-upload videos to Google Cloud Storage (GCS) for faster Vertex AI processing and to avoid upload timeouts.

## Overview

When processing videos with Vertex AI, large files can timeout during upload. Pre-uploading videos to GCS solves this problem and enables:

- **Faster processing** - No upload time during analysis
- **Batch operations** - Process multiple videos efficiently  
- **Reliability** - Avoid network timeout issues
- **Cost optimization** - Upload once, process multiple times

## Quick Start

```bash
# Pre-upload all test videos
poetry run python scripts/pre_upload_test_videos.py

# Pre-upload specific videos
poetry run python scripts/pre_upload_test_videos.py --urls "https://youtube.com/watch?v=..." 
```

## Pre-Upload Script

The `scripts/pre_upload_test_videos.py` script handles:

1. **Video downloading** from YouTube/other platforms
2. **GCS upload** with progress tracking
3. **Tracking files** to avoid re-uploads
4. **Summary generation** with all GCS URIs

### Features

- **Smart tracking** - Avoids re-uploading already processed videos
- **Parallel processing** - Can handle multiple videos efficiently
- **Error handling** - Continues on failures, reports at end
- **Progress logging** - Real-time status updates

### Output Structure

```
output/
├── video_cache/           # Downloaded videos
│   └── *.mp4
├── pre_uploaded_videos/   # Upload tracking
│   ├── {video_id}_gcs_info.json  # Individual tracking
│   └── upload_summary.json        # Complete summary
```

## Using Pre-Uploaded Videos

### 1. Direct GCS URI Processing

```python
# Use pre-uploaded video directly
gcs_uri = "gs://bucket-name/videos/timestamp/video.mp4"

result = await transcriber.transcribe_audio(
    audio_file=None,
    gcs_uri=gcs_uri,
    mode="video"
)
```

### 2. Load from Summary

```python
import json

# Load pre-uploaded videos
with open("output/pre_uploaded_videos/upload_summary.json") as f:
    uploads = json.load(f)

for video in uploads["successful_uploads"]:
    print(f"URL: {video['url']}")
    print(f"GCS: {video['gcs_uri']}")
    print(f"Size: {video['file_size_mb']:.1f} MB")
```

### 3. Test Script Usage

```bash
# Test Vertex AI with pre-uploaded videos
poetry run python scripts/test_vertex_ai_gcs.py
```

## Upload Summary Format

```json
{
  "successful_uploads": [
    {
      "url": "https://www.youtube.com/watch?v=...",
      "gcs_uri": "gs://bucket/path/video.mp4",
      "local_path": "output/video_cache/video.mp4",
      "uploaded_at": "2025-07-20T22:14:02.862646",
      "file_size_mb": 81.93
    }
  ],
  "failed_uploads": [
    {
      "url": "https://...",
      "error": "Age-restricted content"
    }
  ],
  "skipped": [
    {
      "url": "https://...",
      "gcs_uri": "gs://..."  // Already uploaded
    }
  ]
}
```

## Common Issues

### 1. Age-Restricted Videos
Some YouTube videos require authentication. These will fail with:
```
ERROR: Sign in to confirm your age. This video may be inappropriate...
```

**Solution**: Skip these videos or use authenticated download methods.

### 2. Upload Timeouts
Large videos may timeout during upload. The script uses:
- 600 second timeout
- Retry logic with exponential backoff
- Resumable uploads for large files

### 3. Duplicate Detection
The script tracks uploads by video ID. For YouTube URLs:
- `youtu.be/VIDEO_ID` → extracts `VIDEO_ID`
- `youtube.com/watch?v=VIDEO_ID` → extracts `VIDEO_ID`

## Best Practices

1. **Batch uploads** - Pre-upload multiple videos at once
2. **Check tracking** - Review `upload_summary.json` for status
3. **Monitor costs** - GCS storage has ongoing costs
4. **Clean up** - Delete old videos from GCS when done
5. **Use caching** - Keep tracking files for efficiency

## GCS Management

### List Uploaded Videos
```bash
gsutil ls -l gs://prismatic-iris-429006-g6-clipscribe-staging/videos/
```

### Delete Old Videos
```bash
# Delete videos older than 7 days
gsutil -m rm -r "gs://bucket/videos/2025-07-13*"
```

### Check Storage Costs
```bash
gsutil du -sh gs://prismatic-iris-429006-g6-clipscribe-staging/
```

## Integration with ClipScribe

Pre-uploaded videos integrate seamlessly:

```python
# Regular processing (uploads first)
result = await retriever.process_url("https://youtube.com/...")

# Pre-uploaded processing (no upload)
result = await retriever.process_gcs_uri("gs://bucket/video.mp4")
```

## Roadmap

Future enhancements planned:

1. **Proactive caching** - Monitor channels, pre-download new videos
2. **Parallel uploads** - Upload multiple videos simultaneously  
3. **Compression** - Reduce file sizes before upload
4. **Expiration** - Auto-delete old videos from GCS
5. **CLI integration** - Add `clipscribe pre-upload` command

## Cost Considerations

- **Storage**: ~$0.02/GB/month for standard storage
- **Upload**: Free (ingress)
- **Processing**: Same Vertex AI costs, but faster
- **Download**: ~$0.12/GB if downloading from GCS

For 20 test videos (~2GB total): ~$0.04/month storage cost.

Remember: Pre-uploading is most valuable for frequently processed videos or when testing  

# Add enterprise note
## Enterprise Use
Pre-upload for batch processing thousands of videos 