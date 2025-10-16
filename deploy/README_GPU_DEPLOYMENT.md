# Cloud Run GPU Deployment Guide

**Purpose:** Validate WhisperX on Cloud Run GPU for Station10.media premium tier

**Timeline:** 30-45 minutes total (build, deploy, test)

---

## Prerequisites

**You need:**
- [x] GCP Project: `prismatic-iris-429006-g6`
- [x] GCS Bucket: `prismatic-iris-429006-g6-clipscribe`
- [x] Service account with permissions
- [ ] HuggingFace token stored in Secret Manager
- [ ] gcloud CLI authenticated

---

## Step 1: Store HuggingFace Token in Secret Manager (5 min)

```bash
cd /Users/base/Projects/clipscribe

# Get your HuggingFace token from .env
source .env
echo $HUGGINGFACE_TOKEN

# Store in GCP Secret Manager
echo -n "$HUGGINGFACE_TOKEN" | gcloud secrets create HUGGINGFACE_TOKEN \
  --project=prismatic-iris-429006-g6 \
  --replication-policy="automatic" \
  --data-file=-

# Or update if already exists
echo -n "$HUGGINGFACE_TOKEN" | gcloud secrets versions add HUGGINGFACE_TOKEN \
  --project=prismatic-iris-429006-g6 \
  --data-file=-

# Verify
gcloud secrets describe HUGGINGFACE_TOKEN --project=prismatic-iris-429006-g6
```

---

## Step 2: Build & Deploy GPU Worker (15-20 min)

```bash
cd /Users/base/Projects/clipscribe

# Authenticate if needed
gcloud auth login
gcloud config set project prismatic-iris-429006-g6

# Submit build (will take 15-20 minutes)
gcloud builds submit \
  --config=deploy/cloudbuild-gpu.yaml \
  --substitutions=_VERSION=v1.0.0-gpu,_REGION=us-central1

# This will:
# 1. Build Docker image with WhisperX + GPU support (~15 min)
# 2. Push to Container Registry
# 3. Deploy as Cloud Run Job with T4 GPU
# 4. Configure secrets and environment
```

---

## Step 3: Upload Test Video to GCS (1 min)

```bash
# Upload MTG interview (71 minutes, 2 speakers)
gsutil cp test_videos/wlONOh_iUXY_*.mp3 \
  gs://prismatic-iris-429006-g6-clipscribe/test/mtg_interview.mp3

# Verify upload
gsutil ls gs://prismatic-iris-429006-g6-clipscribe/test/
```

---

## Step 4: Run GPU Worker (10 min processing)

```bash
# Execute Cloud Run Job with GPU
gcloud run jobs execute station10-gpu-worker \
  --region=us-central1 \
  --set-env-vars=INPUT_VIDEO_GCS_PATH=gs://prismatic-iris-429006-g6-clipscribe/test/mtg_interview.mp3,OUTPUT_GCS_PATH=gs://prismatic-iris-429006-g6-clipscribe/test/results/ \
  --wait

# This will:
# 1. Start Cloud Run Job with T4 GPU
# 2. Download video from GCS
# 3. Process with WhisperX on GPU
# 4. Upload results to GCS
# 5. Print metrics (time, cost, speakers)
```

---

## Step 5: Check Results (1 min)

```bash
# Download results
mkdir -p test_results
gsutil -m cp -r gs://prismatic-iris-429006-g6-clipscribe/test/results/* test_results/

# View transcript
cat test_results/transcript.txt

# View full results with metrics
cat test_results/results.json | jq '.'

# Check speaker diarization
cat test_results/results.json | jq '.speakers'
```

---

## Success Criteria

**Pass if:**
- ✓ Processing time: <10 minutes for 71-minute video (>7x realtime)
- ✓ GPU cost: <$0.10 per video
- ✓ Multi-speaker: Finds 2 speakers (Tim + MTG)
- ✓ Accuracy: >95% confidence
- ✓ Word-level timestamps: Present

**Fail if:**
- ✗ Processing time: >15 minutes (too slow)
- ✗ GPU cost: >$0.15 (too expensive)
- ✗ Speakers: Finds 0 or 1 (diarization broken)
- ✗ Deployment fails (GPU not available in region)

---

## Expected Results

**Predicted metrics:**
```json
{
  "duration_seconds": 4277,
  "processing_time": 600,  # 10 minutes
  "realtime_factor": 7.1,  # 7x faster than realtime
  "speakers_found": 2,
  "gpu_cost": 0.058,
  "total_cost": 0.058  # Just GPU, no Voxtral for premium
}
```

**If these match predictions → GPU validation PASSES → Continue building.**

**If significantly different → Investigate before proceeding.**

---

## Troubleshooting

### Build fails
```bash
# Check build logs
gcloud builds list --limit=1
gcloud builds log <BUILD_ID>
```

### Job fails
```bash
# Check job logs
gcloud run jobs executions list --job=station10-gpu-worker --region=us-central1
gcloud logging read "resource.labels.job_name=station10-gpu-worker" --limit=50
```

### No GPU available
```bash
# Try different region
# us-central1, us-west1, europe-west4 have T4 GPUs
```

---

## Next Steps (After Validation)

**If GPU validation succeeds:**
1. Document actual performance metrics
2. Update cost projections with real numbers
3. Continue Week 1-16 development plan
4. Build web interface knowing infrastructure works

**If GPU validation fails:**
1. Identify blocker (cost? speed? availability?)
2. Pivot strategy immediately
3. Consider alternatives (dedicated GPU, different cloud provider)
4. Do NOT build 16 weeks on broken infrastructure

---

*This is the critical validation. Everything depends on this working.*

