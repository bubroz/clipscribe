#!/bin/bash
# Deploy and Test Vertex AI GPU Worker
# Simpler than Cloud Run - just build image and submit jobs

set -e

PROJECT_ID="prismatic-iris-429006-g6"
REGION="us-central1"
GCS_BUCKET="prismatic-iris-429006-g6-clipscribe"

echo "========================================"
echo "Vertex AI GPU Worker Deployment & Test"
echo "========================================"
echo ""

# Step 1: Build Docker image
echo "Step 1: Building Docker image with GPU support..."
echo "This will take 15-20 minutes (first time only)..."
echo ""

# Use docker builder directly with -f flag
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/station10-gpu-worker:latest \
    --machine-type=E2_HIGHCPU_8 \
    --timeout=30m \
    . \
    --gcs-log-dir=gs://$PROJECT_ID\_cloudbuild/logs \
    2>&1 | tee /tmp/build.log &

# Wait for docker builder step (uses default cloudbuild.yaml which we'll create)
# Actually, simpler: just use docker in Cloud Build
cat > /tmp/cloudbuild_gpu.yaml << 'EOF'
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-f'
      - 'Dockerfile.gpu'
      - '-t'
      - 'gcr.io/$PROJECT_ID/station10-gpu-worker:latest'
      - '.'
    timeout: 1200s
images:
  - 'gcr.io/$PROJECT_ID/station10-gpu-worker:latest'
EOF

gcloud builds submit --config=/tmp/cloudbuild_gpu.yaml

echo "✓ Image built and pushed"
echo ""

# Step 2: Upload test video
echo "Step 2: Uploading test video to GCS..."
if gsutil ls gs://$GCS_BUCKET/test/mtg_interview.mp3 >/dev/null 2>&1; then
    echo "✓ Test video already uploaded"
else
    gsutil cp test_videos/wlONOh_iUXY_*.mp3 gs://$GCS_BUCKET/test/mtg_interview.mp3
    echo "✓ Uploaded test video"
fi
echo ""

# Step 3: Submit Vertex AI job
echo "Step 3: Submitting job to Vertex AI with L4 GPU..."
echo "This should take ~7-10 minutes to process 71-minute video"
echo ""

python3 deploy/submit_vertex_ai_job.py \
    --video gs://$GCS_BUCKET/test/mtg_interview.mp3 \
    --output gs://$GCS_BUCKET/test/vertex_results/ \
    --project $PROJECT_ID \
    --region $REGION \
    --gpu NVIDIA_L4

echo ""
echo "========================================"
echo "DOWNLOADING AND ANALYZING RESULTS"
echo "========================================"
echo ""

# Download results
rm -rf test_results_vertex
mkdir -p test_results_vertex
gsutil -m cp -r gs://$GCS_BUCKET/test/vertex_results/* test_results_vertex/ 2>/dev/null || echo "Results not yet available"

if [ -f test_results_vertex/results.json ]; then
    echo "✓ Results downloaded"
    echo ""
    
    # Display metrics
    cat test_results_vertex/results.json | jq '{
        duration_minutes: .duration_minutes,
        processing_minutes: .processing_minutes,
        realtime_factor: .realtime_factor,
        speakers_found: .speakers_found,
        confidence: .confidence,
        gpu_cost: .gpu_cost
    }'
    
    echo ""
    echo "Speakers:"
    cat test_results_vertex/results.json | jq -r '.speakers[] | "  \(.speaker): \(.total_time)s"'
    
    # Validate
    echo ""
    echo "========================================"
    echo "VALIDATION"
    echo "========================================"
    echo ""
    
    PROC_MIN=$(cat test_results_vertex/results.json | jq -r '.processing_minutes')
    GPU_COST=$(cat test_results_vertex/results.json | jq -r '.gpu_cost')
    SPEAKERS=$(cat test_results_vertex/results.json | jq -r '.speakers_found')
    
    printf "Processing time: %.1f minutes\n" $PROC_MIN
    printf "GPU cost: \$%.4f\n" $GPU_COST
    echo "Speakers found: $SPEAKERS"
    echo ""
    
    # Check pass/fail
    if (( $(echo "$PROC_MIN < 15" | bc -l) )) && (( $(echo "$GPU_COST < 0.15" | bc -l) )) && (( SPEAKERS >= 2 )); then
        echo "✓✓✓ VALIDATION PASSED ✓✓✓"
        echo ""
        echo "Vertex AI GPU infrastructure works!"
        echo "Continue with Week 1-16 development."
    else
        echo "✗✗✗ VALIDATION FAILED ✗✗✗"
        echo ""
        echo "GPU approach doesn't meet requirements."
        echo "Consider Voxtral-only strategy."
    fi
else
    echo "✗ Results not found. Check Vertex AI console for errors."
fi

