# Station10 Cloud Architecture - Research Summary

**Date**: October 13, 2025, 9:50 AM PDT  
**Goal**: Deploy multi-user Telegram bot to Google Cloud Run with video upload support

---

## Research Findings

### 1. Telegram Bot on Cloud Run - Core Requirements

**Webhook vs Polling**:
- ✅ **Webhooks**: Required for Cloud Run (HTTP request-response model)
- ❌ **Polling**: Doesn't work on Cloud Run (requires long-running process)

**What We Need**:
1. HTTP server (Flask/FastAPI/aiohttp) listening on PORT env var
2. `/webhook` endpoint to receive Telegram updates
3. `/health` endpoint for Cloud Run health checks
4. `setWebhook` call to register Cloud Run URL with Telegram

**Current Issue**: Our bot uses `app.run_webhook()` which doesn't work properly on Cloud Run - needs manual aiohttp server.

---

### 2. Telegram Video Upload Support

**File Size Limits** (Telegram Bot API):
- **Videos**: Up to 50MB via sendVideo
- **Documents**: Up to 2GB (for bot API premium)
- **File downloads**: Bots can download up to 20MB per file
- **Workaround**: For larger files, get `file_id` and process via URL

**Video Upload Workflow**:
```
User sends video → Bot receives file_id → Bot downloads via getFile
→ Save to GCS → Process with ClipScribe → Send results
```

**Handler needed**:
- Detect video message type
- Download file from Telegram servers
- Upload to GCS for persistence
- Queue for ClipScribe processing
- Notify user when complete

---

### 3. Cloud Run Specific Considerations

**Request Timeout**:
- Default: 5 minutes
- Max: 60 minutes (configurable)
- **Problem**: Video processing takes 3-10 minutes
- **Solution**: Queue video for background processing, respond immediately

**Cold Start**:
- Cloud Run scales to zero when idle
- First request after idle = slow (container startup)
- **Solution**: Set `--min-instances=1` for always-on bot

**Port Binding**:
- Must listen on `PORT` environment variable (default 8080)
- Must respond within timeout or Cloud Run kills container
- **Solution**: Respond to webhook immediately, process async

**Cost**:
- Charged per request + CPU time
- Always-on (min-instances=1): ~$10-20/month
- On-demand (min-instances=0): $0.40 per million requests

---

### 4. Architecture Decision: Async Processing Required

**The Fundamental Problem**:
- Telegram webhook requires response within 60 seconds
- Video processing takes 3-10 minutes (transcription + extraction)
- Cloud Run has 60-minute max timeout

**Solution**: Job Queue Pattern
```
Webhook receives /process or video upload
→ Responds immediately: "Queued for processing"
→ Adds job to Cloud Tasks or Pub/Sub
→ Worker processes video asynchronously
→ Sends Telegram notification when complete
```

**Why This is Better Than Current Code**:
- Current: Bot tries to process synchronously in webhook (times out)
- Fixed: Bot queues job, responds fast, processes in background

---

### 5. Video Upload Feature - Technical Design

**User sends video file to bot**:

1. **Receive**: Handler detects `message.video` or `message.document`
2. **Validate**: Check file size (≤20MB for bot download)
3. **Download**: Use `bot.get_file(file_id).download()`
4. **Upload to GCS**: Store in `clipscribe-videos/user_{telegram_id}/{filename}`
5. **Queue**: Add to processing queue with GCS path
6. **Respond**: "Video received! Processing... I'll notify you when done."
7. **Process**: Background worker runs ClipScribe
8. **Notify**: Telegram message with GCS draft page link

**For files >20MB**:
- User uploads to Google Drive / Dropbox
- Sends link to bot
- Bot downloads from link (using yt-dlp or requests)
- Same workflow continues

---

### 6. Recommended Architecture

**Service 1: Telegram Bot (Cloud Run)**
- Handles webhooks
- Receives commands and uploads
- Queues jobs
- Sends notifications
- Always-on (min-instances=1)

**Service 2: Video Processor (Cloud Run Jobs or Tasks)**
- Long-running video processing
- Triggered by Pub/Sub or Cloud Tasks
- Runs ClipScribe pipeline
- Saves to GCS
- Triggers notification

**Storage**:
- **Cloud Storage**: Videos, processed outputs, thumbnails
- **Cloud SQL (PostgreSQL)** or **Firestore**: User data, video metadata, costs
- (SQLite won't work - Cloud Run is stateless)

**Message Queue**:
- **Cloud Tasks** (simpler) or **Pub/Sub** (more scalable)
- Decouples webhook from processing
- Handles retry and failure

---

### 7. What Needs to Change in Current Code

**Station10 Bot (`src/clipscribe/bot/station10_bot.py`)**:
- ❌ Remove `run_polling()` fallback
- ✅ Add proper aiohttp HTTP server
- ✅ Add `/webhook` POST handler
- ✅ Add `/health` GET handler  
- ✅ Add video upload handler (`message.video`)
- ✅ Add document upload handler (`message.document`)
- ✅ Integrate Cloud Tasks for job queue
- ✅ Respond fast (< 60 seconds)

**Database (`src/clipscribe/database/`)**:
- ❌ Remove SQLite (doesn't persist on Cloud Run)
- ✅ Add Cloud SQL (PostgreSQL) or Firestore
- ✅ Connection pooling for performance

**Processing Worker** (new):
- ✅ Cloud Run Job triggered by Cloud Tasks
- ✅ Runs `VideoIntelligenceRetrieverV2.process_url()`
- ✅ Saves outputs to GCS
- ✅ Updates database
- ✅ Sends Telegram notification

**Deployment**:
- `cloudbuild-station10-bot.yaml` - Webhook service
- `cloudbuild-station10-worker.yaml` - Processing worker (new)

---

### 8. Estimated Build Complexity

**Phase 1**: Fix webhook HTTP server (1-2 hours)
- Rewrite bot.run() with proper aiohttp server
- Test locally with ngrok
- Deploy and verify

**Phase 2**: Add video upload support (2-3 hours)
- Add video/document message handlers
- Download from Telegram
- Upload to GCS
- Test with real uploads

**Phase 3**: Add job queue (2-3 hours)
- Integrate Cloud Tasks
- Build worker service
- Test end-to-end async processing

**Phase 4**: Migrate database (1-2 hours)
- Switch SQLite → Cloud SQL or Firestore
- Update all queries
- Test multi-user scenarios

**Total**: 6-10 hours of focused work

---

### 9. Cost Projection (3-User Station10)

**Monthly costs** (rough estimate):
- Cloud Run bot (always-on): $10-15
- Cloud Run workers (on-demand): $5-10 (based on video volume)
- Cloud Storage (72-hour retention): $2-5
- Cloud SQL (small instance) OR Firestore: $7-15
- Secret Manager: $0.06 per secret
- Cloud Tasks: $0.40 per million tasks (negligible)

**Total**: ~$25-50/month for 3 users processing 50-100 videos/month

**Well under your $150/month budget for 1000 videos.**

---

### 10. Alternative: Simpler Hybrid Approach

**Run bot on laptop, process on Cloud**:
- Bot runs locally (polling mode, simple)
- Video processing → Cloud Run worker
- Storage → GCS (already working)
- Database → Local SQLite (simple)

**Pros**: Much simpler, faster to build
**Cons**: Requires laptop always on, not truly multi-user

**For Station10 with 3 co-founders**: Full cloud deployment is better (always available, professional).

---

## Recommendation

Build properly in phases:

1. **Tonight**: Fix webhook HTTP server, deploy bot to Cloud Run
2. **Next session**: Add video upload support
3. **Next session**: Add job queue + worker
4. **Next session**: Migrate to Cloud SQL/Firestore

Don't rush the job queue - get webhook working first, then iterate.

