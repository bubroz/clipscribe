#!/bin/bash
# Test Station10.media GPU Worker
# Run this after deployment: ./deploy/test_gpu.sh

set -e

PROJECT_ID="prismatic-iris-429006-g6"
REGION="us-central1"
GCS_BUCKET="prismatic-iris-429006-g6-clipscribe"

echo "========================================"
echo "Testing GPU Worker"
echo "========================================"
echo ""

# Upload test video if not already uploaded
echo "Uploading test video to GCS..."
if gsutil ls gs://$GCS_BUCKET/test/mtg_interview.mp3 >/dev/null 2>&1; then
    echo "✓ Test video already uploaded"
else
    gsutil cp test_videos/wlONOh_iUXY_*.mp3 gs://$GCS_BUCKET/test/mtg_interview.mp3
    echo "✓ Uploaded test video"
fi
echo ""

# Run Cloud Run Job
echo "Executing GPU worker..."
echo "This should take ~10 minutes for 71-minute video"
echo ""

START_TIME=$(date +%s)

gcloud run jobs execute station10-gpu-worker \
    --region=$REGION \
    --set-env-vars=INPUT_VIDEO_GCS_PATH=gs://$GCS_BUCKET/test/mtg_interview.mp3,OUTPUT_GCS_PATH=gs://$GCS_BUCKET/test/results/ \
    --wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "✓ Processing complete in ${ELAPSED} seconds"
echo ""

# Download and display results
echo "Downloading results..."
rm -rf test_results
mkdir -p test_results
gsutil -m cp -r gs://$GCS_BUCKET/test/results/* test_results/ 2>/dev/null || true

echo ""
echo "========================================"
echo "RESULTS"
echo "========================================"
echo ""

if [ -f test_results/results.json ]; then
    cat test_results/results.json | jq '{
        duration_minutes: (.duration / 60),
        processing_minutes: (.processing_time / 60),
        realtime_factor: .realtime_factor,
        speakers_found: .speakers_found,
        confidence: .confidence,
        gpu_cost: .gpu_cost
    }'
    
    echo ""
    echo "Speakers found:"
    cat test_results/results.json | jq -r '.speakers[] | "  \(.speaker): \(.total_time)s (\(.segments) segments)"'
    
    echo ""
    echo "✓ Full transcript: test_results/transcript.txt"
    echo "✓ Full results: test_results/results.json"
else
    echo "ERROR: Results not found. Check logs:"
    echo "  gcloud logging read 'resource.labels.job_name=station10-gpu-worker' --limit=50"
fi

echo ""
echo "========================================"
echo "VALIDATION"
echo "========================================"
echo ""

# Parse metrics for validation
if [ -f test_results/results.json ]; then
    PROC_TIME=$(cat test_results/results.json | jq -r '.processing_time')
    GPU_COST=$(cat test_results/results.json | jq -r '.gpu_cost // 0')
    SPEAKERS=$(cat test_results/results.json | jq -r '.speakers_found // 0')
    REALTIME=$(cat test_results/results.json | jq -r '.realtime_factor // 0')
    
    # Convert to minutes for comparison
    PROC_MIN=$(echo "$PROC_TIME / 60" | bc -l)
    
    echo "Results:"
    printf "  Processing time: %.1f minutes\n" $PROC_MIN
    printf "  GPU cost: \$%.4f\n" $GPU_COST
    echo "  Speakers found: $SPEAKERS"
    printf "  Realtime factor: %.1fx\n" $REALTIME
    echo ""
    
    # Validate
    PASS=true
    
    if (( $(echo "$PROC_MIN > 15" | bc -l) )); then
        echo "✗ FAIL: Processing too slow (>15 min)"
        PASS=false
    else
        echo "✓ PASS: Processing time acceptable"
    fi
    
    if (( $(echo "$GPU_COST > 0.15" | bc -l) )); then
        echo "✗ FAIL: Cost too high (>\$0.15)"
        PASS=false
    else
        echo "✓ PASS: Cost acceptable"
    fi
    
    if (( SPEAKERS < 2 )); then
        echo "✗ FAIL: Speaker diarization failed (found $SPEAKERS, expected 2)"
        PASS=false
    else
        echo "✓ PASS: Speaker diarization works"
    fi
    
    echo ""
    if [ "$PASS" = true ]; then
        echo "========================================"
        echo "✓✓✓ VALIDATION PASSED ✓✓✓"
        echo "========================================"
        echo ""
        echo "Cloud Run GPU infrastructure validated!"
        echo "Continue with Week 1-16 development plan."
    else
        echo "========================================"
        echo "✗✗✗ VALIDATION FAILED ✗✗✗"
        echo "========================================"
        echo ""
        echo "Cloud Run GPU does not meet requirements."
        echo "PIVOT REQUIRED - do not continue building on this infrastructure."
    fi
fi

