# Vertex AI GPU Worker Deployment

Complete deployment guide for Station10 GPU-accelerated transcription on Vertex AI.

---

## 📋 **Quick Start**

### Prerequisites
1. GCP project with Vertex AI API enabled
2. GPU quota approved (T4, L4, or A100)
3. `gcloud` CLI authenticated
4. Poetry installed (for local testing)

### One-Command Deploy
```bash
# Deploy everything and run test
./deploy/deploy_vertex_ai.sh
```

This will:
1. Build Docker image with WhisperX + GPU support (~20 min)
2. Upload test video to GCS
3. Submit GPU job to Vertex AI
4. Wait for completion and download results

---

## 🛠️ **Individual Components**

### 1. Docker Container (`Dockerfile.gpu`)

**Purpose:** WhisperX container with CUDA support for GPU acceleration.

**Build manually:**
```bash
gcloud builds submit --config=deploy/cloudbuild-gpu-simple.yaml
```

**Contains:**
- Python 3.11
- WhisperX with faster-whisper
- pyannote.audio for speaker diarization
- CUDA 12.1 + cuDNN 8
- GCS client for I/O

**Build time:** ~20 minutes  
**Cost:** ~$0.10-0.25 per build  
**Output:** `gcr.io/PROJECT_ID/station10-gpu-worker:latest`

---

### 2. Job Submission (`submit_vertex_ai_job.py`)

**Purpose:** Submit transcription jobs to Vertex AI with GPU.

**Basic usage:**
```bash
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/video.mp3 \
    --output gs://BUCKET/results/ \
    --gpu NVIDIA_TESLA_T4
```

**All options:**
```bash
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/video.mp3 \            # Input video/audio (required)
    --output gs://BUCKET/results/ \             # Output directory (required)
    --project YOUR_PROJECT_ID \                 # GCP project (default: prismatic-iris-429006-g6)
    --region us-central1 \                      # Region (default: us-central1)
    --gpu NVIDIA_L4 \                          # GPU type (default: NVIDIA_TESLA_T4)
    --timeout 30 \                              # Max runtime in minutes (default: 30)
    --no-wait                                   # Don't wait for completion (async mode)
```

**Supported GPUs:**
- `NVIDIA_TESLA_T4` - $0.35/hr, good for <60min videos
- `NVIDIA_L4` - $0.70/hr, 2x faster, best for 60-120min videos
- `NVIDIA_TESLA_A100` - $3.67/hr, overkill for audio

**Cost protection:**
- Automatic timeout after 30 minutes (configurable)
- Job terminates even if code hangs
- Prevents runaway costs from bugs

**Output files (written to GCS):**
- `transcript.vtt` - WebVTT with timestamps
- `transcript.json` - Full structured output
- `metadata.json` - Processing details

---

### 3. Cost Monitoring (`setup_cost_alerts.py`)

**Purpose:** Set up budget alerts and Cloud Monitoring for cost control.

**Deploy alerts:**
```bash
# Without budget alerts (no billing account needed)
poetry run python deploy/setup_cost_alerts.py \
    --project YOUR_PROJECT_ID

# With budget alerts (requires billing account)
poetry run python deploy/setup_cost_alerts.py \
    --project YOUR_PROJECT_ID \
    --billing-account billingAccounts/XXXXXX-XXXXXX-XXXXXX
```

**What it creates:**
1. **Budget Alerts:** Email when spend hits $25, $45, $50 (for $50 budget)
2. **Monitoring Alert:** Alert if spend exceeds $10/hour
3. **Verification:** Lists all active alerts

**Find your billing account ID:**
```bash
gcloud billing accounts list
```

**After deployment:**
1. Go to Cloud Console → Monitoring → Alerting
2. Add email/SMS notification channels
3. Test with a small GPU job

---

### 4. Full Deployment Script (`deploy_vertex_ai.sh`)

**Purpose:** End-to-end deployment and testing.

**What it does:**
```bash
./deploy/deploy_vertex_ai.sh
```

1. **Check Docker image** (skip rebuild if exists)
2. **Upload test video** to GCS
3. **Submit Vertex AI job** with T4 GPU
4. **Wait for completion** (~10-15 min)
5. **Download results** from GCS
6. **Analyze output** (show transcript, speakers, cost)

**Customize:**
Edit the script to:
- Change GPU type (line 47): `--gpu NVIDIA_L4`
- Use different test video (line 23): `INPUT_FILE=your_video.mp3`
- Adjust timeout (line 47): Add `--timeout 60`

---

## 💰 **Cost Management**

### Per-Job Cost Estimates

| GPU Type | $/Hour | 30min Video | 60min Video | 90min Video |
|----------|--------|-------------|-------------|-------------|
| T4 | $0.35 | $0.06 | $0.12 | $0.17 |
| L4 | $0.70 | $0.12 | $0.23 | $0.35 |
| A100 | $3.67 | $0.61 | $1.22 | $1.83 |

**Processing time:**
- T4: ~0.5x realtime (60min video takes ~30min)
- L4: ~2x realtime (60min video takes ~7-10min)
- A100: ~5x realtime (60min video takes ~3-5min)

**Best value:**
- **Short videos (<30min):** T4 (cost matters more than speed)
- **Medium videos (30-90min):** L4 (best balance)
- **Long videos (>90min):** L4 (speed justifies cost)

### Budget Recommendations

**Development (Weeks 1-4):**
- Set budget: $50/month
- Alert thresholds: $25, $45, $50
- Expected spend: $15-30

**Production (Month 4+):**
- Set budget: $1,000/month
- Alert thresholds: $500, $800, $1,000
- Expected spend: $500-800 (100 jobs/day)

### Cost Alerts Setup
```bash
# Deploy all alerts
poetry run python deploy/setup_cost_alerts.py \
    --project PROJECT_ID \
    --billing-account billingAccounts/XXXXXX-XXXXXX-XXXXXX

# Verify alerts
gcloud alpha billing budgets list --billing-account=billingAccounts/XXXXXX-XXXXXX-XXXXXX
```

---

## 🚨 **Troubleshooting**

### Issue: "ResourceExhausted: GPU quota exceeded"

**Cause:** No quota for requested GPU type.

**Fix:**
1. Check current quota:
   ```bash
   gcloud compute regions describe us-central1 --format="table(quotas.metric,quotas.limit)"
   ```
2. Request quota increase:
   - Go to IAM & Admin → Quotas
   - Filter: "Vertex AI API" + "custom_model_training"
   - Select GPU type + region
   - Click "EDIT QUOTAS" and request increase

**Workaround:** Use T4 instead of L4 (T4 usually has quota)

---

### Issue: "Invalid machine type for GPU"

**Cause:** L4 GPUs only work with G2 machine types.

**Fix:** The script handles this automatically. If you're calling the API directly:
- L4 → Use `g2-standard-4` or `g2-standard-8`
- T4/A100 → Use `n1-standard-4` or `n1-standard-8`

---

### Issue: Docker image not found

**Cause:** Image hasn't been built yet.

**Fix:**
```bash
gcloud builds submit --config=deploy/cloudbuild-gpu-simple.yaml
```

**Verify:**
```bash
gcloud container images list --repository=gcr.io/PROJECT_ID
gcloud container images describe gcr.io/PROJECT_ID/station10-gpu-worker:latest
```

---

### Issue: Job times out after 30 minutes

**Cause:** Video is too long for default timeout.

**Fix:**
```bash
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/long_video.mp3 \
    --output gs://BUCKET/results/ \
    --timeout 60  # Increase to 60 minutes
```

**Note:** Longer timeouts increase max cost. A 60min timeout on L4 costs max $0.70.

---

### Issue: "Permission denied" on GCS

**Cause:** Service account doesn't have GCS access.

**Fix:**
```bash
# Give Vertex AI service account GCS access
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

---

## 📊 **Testing & Validation**

### Test Suite

**1. Small video (5-10 min):**
```bash
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/test_5min.mp3 \
    --output gs://BUCKET/results/test1/ \
    --gpu NVIDIA_TESLA_T4
```
**Expected:** <3 min processing, <$0.02 cost

**2. Medium video (30-60 min):**
```bash
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/test_60min.mp3 \
    --output gs://BUCKET/results/test2/ \
    --gpu NVIDIA_L4
```
**Expected:** <10 min processing, <$0.25 cost

**3. Long video (90+ min):**
```bash
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/test_90min.mp3 \
    --output gs://BUCKET/results/test3/ \
    --gpu NVIDIA_L4 \
    --timeout 45
```
**Expected:** <15 min processing, <$0.35 cost

### Validation Checklist

After each test, verify:
- [ ] Job completed successfully (not timeout/error)
- [ ] `transcript.vtt` exists and has timestamps
- [ ] `transcript.json` has full transcript
- [ ] Speaker labels present (if multi-speaker)
- [ ] Processing time < 2x realtime for L4
- [ ] Cost matches estimates

---

## 🔄 **Deployment Workflow**

### Initial Setup (One-Time)
```bash
# 1. Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 2. Create GCS bucket
gsutil mb -l us-central1 gs://PROJECT_ID-clipscribe

# 3. Build Docker image
gcloud builds submit --config=deploy/cloudbuild-gpu-simple.yaml

# 4. Request GPU quota (if needed)
# Go to IAM & Admin → Quotas → Request increase

# 5. Deploy cost alerts
poetry run python deploy/setup_cost_alerts.py --project PROJECT_ID
```

### Regular Development
```bash
# Test with single video
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/test.mp3 \
    --output gs://BUCKET/results/

# Rebuild Docker (only when code changes)
gcloud builds submit --config=deploy/cloudbuild-gpu-simple.yaml
```

### Production Deployment
```bash
# 1. Tag Docker image
gcloud container images add-tag \
    gcr.io/PROJECT_ID/station10-gpu-worker:latest \
    gcr.io/PROJECT_ID/station10-gpu-worker:v1.0.0

# 2. Update job submission to use tagged version
# Edit submit_vertex_ai_job.py line 62:
# "image_uri": f"gcr.io/{project_id}/station10-gpu-worker:v1.0.0",

# 3. Deploy with production GPU
poetry run python deploy/submit_vertex_ai_job.py \
    --video gs://BUCKET/video.mp3 \
    --output gs://BUCKET/results/ \
    --gpu NVIDIA_L4
```

---

## 📚 **Related Documentation**

- `../VERTEX_AI_GPU_STATUS.md` - Current status and validation results
- `../TECHNICAL_DEBT.md` - Known issues and gaps
- `../docs/CLI_REFERENCE.md` - ClipScribe CLI documentation
- [Vertex AI Custom Training](https://cloud.google.com/vertex-ai/docs/training/custom-training)
- [WhisperX Documentation](https://github.com/m-bain/whisperX)

---

## 🎯 **Next Steps**

After successful deployment:

1. **Run test suite** (5min, 60min, 90min videos)
2. **Document performance metrics** (speed, cost, quality)
3. **Deploy cost alerts** to prevent surprises
4. **Set up monitoring dashboard** (Cloud Monitoring)
5. **Integrate with Station10** (API endpoints)

**Questions?** Check `TECHNICAL_DEBT.md` for known issues and `VERTEX_AI_GPU_STATUS.md` for current status.

