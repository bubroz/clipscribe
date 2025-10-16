# Station10.media Cloud Run Production Architecture

**Last Updated:** October 15, 2025  
**Status:** Week 1 - Architecture design  
**Target:** Production SaaS on Google Cloud

---

## Architecture Overview

```
Customer (station10.media web UI)
    ↓
Upload video or paste URL
    ↓
Next.js Frontend (Cloud Run)
    ↓
FastAPI Backend (Cloud Run)
    ↓
Upload to GCS (gs://station10-videos/)
    ↓
Trigger Cloud Run Job (GPU or CPU based on tier)
    ↓
Processing:
  Standard Tier: Voxtral API + pyannote CPU
  Premium Tier: WhisperX on Cloud Run GPU (T4)
    ↓
Store results in GCS (gs://station10-results/)
    ↓
Pub/Sub notification → Cloud Function
    ↓
Google Chat + Gmail notification
    ↓
Customer views results in web UI
```

---

## Processing Tiers (Economic Optimization)

### Standard Tier (90% of customers)

**Target customers:** News, podcasts, general interviews  
**Price:** $0.10/minute  
**Processing:**

```python
# Cloud Run CPU instance (no GPU needed)
# Cost: $0.000024/vCPU-second

Pipeline:
1. Voxtral API transcription
   - Cost: $0.001/minute
   - Speed: 1-2x realtime
   - Accuracy: 95%

2. pyannote speaker diarization (CPU)
   - Cost: ~$0.002/minute (Cloud Run CPU time)
   - Speed: Adds 30-50% to total time
   - Accuracy: 95%+ speaker separation

3. Grok-4 intelligence extraction
   - Cost: ~$0.002/minute
   - Entities + relationships + clips

Total cost: ~$0.005/minute
Total time: 1.5-2x realtime (30-min video in 45-60 min)
Margin: $0.095/minute (95%)
```

### Premium Tier (10% of customers)

**Target customers:** Medical, legal, technical, intelligence  
**Price:** $0.20/minute  
**Processing:**

```python
# Cloud Run with NVIDIA T4 GPU
# GPU cost: $0.35/hour = $0.00583/minute

Pipeline:
1. WhisperX on GPU
   - Cost: ~$0.06/video (GPU time)
   - Speed: 8-10x realtime (30-min video in 3-4 min)
   - Accuracy: 97-99%
   - Built-in speaker diarization

2. Grok-4 intelligence extraction
   - Cost: ~$0.002/minute
   - Same as standard

Total cost: ~$0.065/minute
Total time: 10x realtime (30-min video in 3 min!)
Margin: $0.135/minute (68%)
```

---

## Infrastructure Costs

### Fixed Costs (Monthly)

```
PostgreSQL (Cloud SQL, db-f1-micro): $9.37
Redis (Memorystore, M1): $30
Cloud Run (frontend/API, scales to zero): $0
Domain (station10.media): $1/month
SendGrid (email, free tier): $0
─────────────────────────────────────
Total fixed: ~$40/month
```

### Variable Costs (Per Video)

**Standard tier example (30-minute video):**
```
Voxtral: 30 × $0.001 = $0.03
pyannote CPU: 30 × $0.002 = $0.06
Grok: 30 × $0.002 = $0.06
GCS storage: $0.001
Cloud Run CPU: $0.01
─────────────────────────
Total: $0.16 per 30-min video
Price: $3.00
Margin: $2.84 (95%)
```

**Premium tier example (30-minute video):**
```
WhisperX GPU: ~$0.02 (3 min GPU time)
Grok: $0.06
GCS storage: $0.001
Cloud Run: $0.01
─────────────────────────
Total: $0.09 per 30-min video  
Price: $6.00
Margin: $5.91 (99%)
```

---

## Scale Economics

### Month 1 (Launch, 50 videos/day avg)

```
Mix: 45 standard, 5 premium

Standard: 45 × 30 min avg × $0.005/min = $6.75/day
Premium: 5 × 30 min avg × $0.003/min = $0.45/day
Infrastructure: $40/month = $1.33/day
─────────────────────────────────────
Total costs: ~$260/month

Revenue: 
Standard: 45 × $3 = $135/day
Premium: 5 × $6 = $30/day
Total: $165/day = $4,950/month

Profit: $4,690/month (95% margin)
```

### Month 6 (Growth, 200 videos/day)

```
Mix: 180 standard, 20 premium

Costs: ~$1,100/month (infrastructure + processing)
Revenue: ~$20,000/month
Profit: ~$18,900/month (95% margin)
```

### Month 12 (Scale, 500 videos/day)

```
Mix: 450 standard, 50 premium

Costs: ~$2,800/month
Revenue: ~$50,000/month
Profit: ~$47,200/month (94% margin)
Annual run rate: $566K/year profit
```

---

## Cloud Run Configuration

### Frontend (Next.js)

```yaml
service: station10-frontend
region: us-central1
min-instances: 0 (scale to zero)
max-instances: 10
memory: 512Mi
cpu: 1
timeout: 60s
```

### API (FastAPI)

```yaml
service: station10-api
region: us-central1
min-instances: 0
max-instances: 20
memory: 1Gi
cpu: 2
timeout: 300s (for job submission)
```

### Worker - Standard Tier (CPU)

```yaml
job: station10-worker-standard
region: us-central1
memory: 4Gi
cpu: 4
timeout: 3600s (1 hour max per video)
parallelism: 10 (10 concurrent videos)
```

### Worker - Premium Tier (GPU)

**UPDATE (Oct 16):** Cloud Run Jobs don't support GPU. Using Vertex AI instead.

```yaml
# Vertex AI Custom Job (replaces Cloud Run GPU Job)
job: station10-worker-premium
region: us-central1
machine: n1-standard-4
accelerator: nvidia-l4 (1 GPU)
timeout: 1800s (30 min max)
container: gcr.io/PROJECT/whisperx-gpu-worker
```

---

## Deployment Strategy

### Week 1-8: Development (Local Only)
```
Development: M3 Max CPU (free, validates features)
No cloud deployment yet
Build and test all features locally
```

### Week 9-12: Cloud Setup (Staging)
```
Deploy to Cloud Run (staging environment)
Test GPU workers with real videos
Validate costs match projections
No customers yet
```

### Week 13-14: Production Prep
```
Production Cloud Run deployment
Stripe integration
DNS setup (station10.media → Cloud Run)
Load testing
```

### Week 15-16: Beta & Launch
```
Beta users on production Cloud Run
Monitor costs and performance
Public launch
```

---

## Cost Monitoring & Alerts

### Budget Alerts

```
Set up Cloud Billing alerts:
- Warning at $100/month
- Alert at $200/month
- Hard limit at $500/month (before revenue covers it)

Track per-tier costs:
- Standard tier should stay <$0.006/min
- Premium tier should stay <$0.08/min
- If costs spike, investigate immediately
```

### Performance Monitoring

```
Cloud Monitoring dashboards:
- Processing time per tier
- GPU utilization (should be >80%)
- Error rates
- Customer satisfaction (processing time)
```

---

## Why Cloud Run (vs Alternatives)

### vs AWS Lambda
```
Lambda:
- 15-minute timeout (too short for long videos)
- More expensive GPU instances
- Complex cold starts with GPU

Cloud Run:
- 60-minute timeout (good for most videos)
- Better GPU pricing
- Faster cold starts
✅ Winner: Cloud Run
```

### vs Dedicated GPU Server
```
Dedicated:
- $150-300/month fixed
- Break-even at ~100 premium videos/day
- Server management required
- Single point of failure

Cloud Run:
- $0 fixed, pay per use
- Infinite scale
- Google manages it
- Auto-redundancy
✅ Winner: Cloud Run (until 100+ premium/day)
```

### vs Your M3 Max
```
M3 Max:
- FREE!
- But: 4+ hours for 88-min video
- Capacity: ~5 videos/day max
- Can't serve customers at scale

Cloud Run GPU:
- $0.058/video
- 10 minutes for 88-min video  
- Capacity: Unlimited
- Can serve 1000s of customers
✅ Winner: Cloud Run for SaaS
```

---

## Decision: Build for Cloud Run GPU

**Architecture:**
- Frontend: Cloud Run (Next.js, serverless)
- API: Cloud Run (FastAPI, serverless)
- Standard workers: Cloud Run CPU Jobs
- Premium workers: Cloud Run GPU Jobs (T4)
- Storage: GCS
- Database: Cloud SQL PostgreSQL
- Queue: Cloud Tasks + Pub/Sub
- Notifications: Cloud Functions → Google Chat/Gmail

**Why this works:**
- Scales from 0 to infinity
- Pay only for what you use
- 95%+ profit margins at all scales
- Google manages everything
- No servers to maintain

**Start building for this in Week 9 (web interface phase).**

---

**Your test is still running - let it finish to validate multi-speaker works. But we're building for Cloud Run GPU either way.** 🚀
