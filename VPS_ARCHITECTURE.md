# VPS Batch Worker Architecture

**Purpose**: 24/7 background video processing without keeping laptop on  
**Status**: Planned for Phase 1.3  
**Timeline**: November 2025

---

## The Problem

**Current workflow limitations**:
```
Process 50 videos:
├─ Laptop must stay on (8-10 hours)
├─ Can't close lid or sleep
├─ Network must be stable
└─ Blocks other work
```

**What journalists actually need**:
```
Evening: Submit 50 videos to process
Night: Go to sleep
Morning: Results ready
```

---

## The Solution

### VPS as Batch Processing Worker

**Architecture**:
```
┌─────────────────┐
│  Local Machine  │  (Your laptop, residential IP)
│  (macOS/Linux)  │
└────────┬────────┘
         │
         │ 1. Download videos (yt-dlp works here)
         │ 2. Upload to R2 storage
         ↓
┌─────────────────┐
│  Cloudflare R2  │  (Video storage)
│   (Cloud CDN)   │
└────────┬────────┘
         │
         │ 3. VPS fetches videos from R2
         ↓
┌─────────────────┐
│   VPS Worker    │  (Datacenter IP, but doesn't download from YouTube)
│  (24/7 online)  │
└────────┬────────┘
         │
         │ 4. Process with Voxtral + Grok-4
         │ 5. Store results in R2
         ↓
┌─────────────────┐
│  Cloudflare R2  │  (Results storage)
│  (Cloud CDN)    │
└────────┬────────┘
         │
         │ 6. Fetch results
         ↓
┌─────────────────┐
│  Local Machine  │  (View results)
└─────────────────┘
```

---

## Why This Works

### ✅ Solves YouTube IP Blocking
- **Local machine** (residential IP) downloads videos
- **VPS** never touches YouTube directly
- VPS only processes files from R2

### ✅ 24/7 Processing
- Submit jobs anytime
- VPS runs continuously
- Fetch results when ready

### ✅ No Laptop Dependency
- Close laptop after submitting
- Sleep, travel, work on other things
- Results ready when you check back

### ✅ Cost Effective
- VPS: ~$10/month (always on)
- R2 storage: ~$0.015/GB ($0.75 for 50 videos)
- Processing: $0.03/video × 50 = $1.50
- **Total**: ~$12.25 for 50-video batch vs keeping laptop on

---

## Implementation (Phase 1.3)

### Local CLI Extensions

```bash
# Submit batch job to VPS
clipscribe batch submit urls.txt \
  --vps \
  --notify email@example.com

# Check status
clipscribe batch status --job-id abc123

# Fetch results when ready
clipscribe batch fetch abc123 --output-dir results/

# List all jobs
clipscribe batch list --recent 10
```

### VPS Worker Service

```python
# /home/station10/worker/main.py

class BatchWorker:
    async def poll_jobs(self):
        """Poll R2 for new job requests"""
        while True:
            jobs = await self.r2.list_pending_jobs()
            for job in jobs:
                await self.process_job(job)
            await asyncio.sleep(60)  # Check every minute
    
    async def process_job(self, job):
        """Process single video from R2"""
        # 1. Download video from R2
        video_path = await self.r2.download(job.video_key)
        
        # 2. Process with hybrid processor
        result = await self.processor.process_video(video_path)
        
        # 3. Upload results to R2
        await self.r2.upload_results(job.id, result)
        
        # 4. Send notification (email/webhook)
        await self.notify(job.user_email, job.id)
        
        # 5. Cleanup
        os.remove(video_path)
```

### Systemd Service

```ini
# /etc/systemd/system/clipscribe-worker.service
[Unit]
Description=ClipScribe Batch Worker
After=network.target

[Service]
Type=simple
User=station10
WorkingDirectory=/home/station10/clipscribe
ExecStart=/home/station10/.local/bin/poetry run python worker/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Storage Architecture

### R2 Bucket Structure

```
clipscribe-processing/
├── jobs/
│   ├── abc123/
│   │   ├── metadata.json      (job details)
│   │   ├── video.mp4          (uploaded video)
│   │   └── status.json        (processing status)
│   └── def456/
│       └── ...
├── results/
│   ├── abc123/
│   │   ├── core.json
│   │   ├── knowledge_graph.json
│   │   ├── transcript.txt
│   │   └── report.md
│   └── def456/
│       └── ...
└── archive/
    └── completed/             (cleaned up after 30 days)
```

### Cost Analysis

**R2 Storage Costs**:
- Storage: $0.015/GB/month
- Class A operations (uploads): $4.50 per million
- Class B operations (downloads): $0.36 per million
- Egress: FREE (Cloudflare R2 has no egress fees)

**Example: 50-video batch**:
```
Videos: 50 × 500MB = 25GB
Storage: 25GB × $0.015 = $0.38/month
Uploads: 50 × 2 files × $4.50/1M = $0.00045
Downloads: 50 × 2 files × $0.36/1M = $0.000036
Processing: 50 × $0.03 = $1.50
VPS: $10/month (fixed)

Total: ~$11.88 for 50 videos
Per video: $0.24
```

Compare to keeping laptop on:
- Electricity: ~$0.15/hour × 10 hours = $1.50
- Opportunity cost: Can't use laptop
- Risk: Sleep/crash = lost progress

**VPS is actually CHEAPER and more reliable.**

---

## Job Queue System

### Simple Implementation (Phase 1)

```python
# Job stored as JSON in R2
{
  "job_id": "abc123",
  "user_email": "user@example.com",
  "submitted_at": "2025-10-15T20:00:00Z",
  "video_url": "original YouTube URL",
  "video_key": "jobs/abc123/video.mp4",  # R2 path
  "status": "pending",  # pending, processing, complete, failed
  "progress": 0,  # 0-100
  "cost": 0.0,
  "results_key": null,  # Set when complete
  "error": null
}
```

### Advanced Implementation (Phase 3)

- PostgreSQL for job queue
- WebSocket for real-time updates
- Priority queue (urgent vs batch)
- Resource allocation (multiple workers)

---

## Notification System

### Phase 1: Email

```python
# When job completes
send_email(
    to=job.user_email,
    subject=f"ClipScribe: Job {job.job_id} Complete",
    body=f"""
    Your batch processing job is complete!
    
    Videos processed: {job.video_count}
    Total cost: ${job.cost:.2f}
    
    Fetch results:
    clipscribe batch fetch {job.job_id}
    
    View online:
    https://r2.clipscribe.com/results/{job.job_id}/
    """
)
```

### Phase 3: Webhook

```python
# POST to user-specified webhook
webhook_payload = {
    "event": "job.complete",
    "job_id": job.job_id,
    "results_url": f"https://r2.clipscribe.com/results/{job.job_id}/",
    "cost": job.cost,
    "video_count": job.video_count
}
```

---

## Security Considerations

### API Authentication

```python
# User gets API key from local CLI
api_key = generate_api_key(user_email)

# All job submissions include API key
headers = {"Authorization": f"Bearer {api_key}"}
```

### R2 Access Control

- Each user has isolated prefix: `jobs/{user_id}/`
- Pre-signed URLs for uploads (time-limited)
- Results only accessible by job owner

### VPS Security

- Minimal services (worker only, no public web)
- Firewall: Only outbound to R2 and APIs
- No SSH password auth (keys only)
- Automatic security updates

---

## Monitoring & Logging

### What to Track

```python
metrics = {
    "jobs_processed": 127,
    "jobs_pending": 3,
    "jobs_failed": 2,
    "total_cost": 4.56,
    "processing_time_avg": 182,  # seconds
    "uptime": "99.8%",
    "last_processed": "2025-10-15T20:45:00Z"
}
```

### Alerts

- Worker crashes (auto-restart)
- Job failures (notify user + admin)
- High error rate (>5% failures)
- Cost anomalies (unexpected spike)

---

## Migration Path

### Current State (v2.54.1)
```
Local CLI → Process locally → Results in local files
```

### Phase 1.3 (Nov 2025)
```
Local CLI → Upload to R2 → VPS processes → Results in R2 → Fetch to local
```

### Phase 3 (Feb 2026)
```
Web UI → Upload to R2 → VPS processes → View in web dashboard
```

---

## Cost Comparison

### Process 50 videos locally
```
Time: 8-10 hours (must keep laptop on)
Electricity: ~$1.50
Opportunity cost: Can't use laptop
Risk: High (sleep, crash, network issues)
Cost: $1.50 + processing ($1.50) = $3.00
```

### Process 50 videos on VPS
```
Time: 8-10 hours (but laptop closed)
Setup: 5 minutes (upload to R2)
Fetch: 2 minutes (download results)
Cost: VPS ($10/mo = $0.33/day) + storage ($0.38) + processing ($1.50) = $2.21
```

**VPS is cheaper AND better.**

---

## Next Steps

1. **Week 1**: Implement R2 integration in CLI
2. **Week 2**: Build VPS worker service
3. **Week 3**: Test with 10-video batch
4. **Week 4**: Deploy production worker
5. **Month 2**: Test with 50-video batch

---

*This is the proper use of the VPS we set up during the Telegram exploration.*

