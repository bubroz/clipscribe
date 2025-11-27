#!/bin/bash
# Deploy Station10.media GPU Worker to Cloud Run
# Run this from project root: ./deploy/deploy_gpu.sh

set -e  # Exit on error

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="us-central1"
GCS_BUCKET="${GCS_BUCKET:-your-bucket-name}"

echo "========================================"
echo "Station10.media GPU Worker Deployment"
echo "========================================"
echo ""
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "GCS Bucket: $GCS_BUCKET"
echo ""

# Step 1: Verify gcloud setup
echo "Step 1: Verifying gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Not authenticated. Running gcloud auth login..."
    gcloud auth login
fi

gcloud config set project $PROJECT_ID
echo "✓ Authenticated and project set"
echo ""

# Step 2: Store HuggingFace token in Secret Manager
echo "Step 2: Checking HuggingFace token in Secret Manager..."
if gcloud secrets describe HUGGINGFACE_TOKEN --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "✓ HUGGINGFACE_TOKEN secret exists"
else
    echo "Creating HUGGINGFACE_TOKEN secret..."
    if [ -f .env ] && grep -q HUGGINGFACE_TOKEN .env; then
        source .env
        echo -n "$HUGGINGFACE_TOKEN" | gcloud secrets create HUGGINGFACE_TOKEN \
            --project=$PROJECT_ID \
            --replication-policy="automatic" \
            --data-file=-
        echo "✓ Created HUGGINGFACE_TOKEN secret"
    else
        echo "ERROR: HUGGINGFACE_TOKEN not found in .env"
        echo "Add it to .env and re-run this script"
        exit 1
    fi
fi
echo ""

# Step 3: Build and deploy
echo "Step 3: Building and deploying GPU worker..."
echo "This will take 15-20 minutes..."
echo ""

gcloud builds submit \
    --config=deploy/cloudbuild-gpu.yaml \
    --substitutions=_VERSION=v1.0.0-gpu,_REGION=$REGION,_GCS_BUCKET=$GCS_BUCKET

echo ""
echo "✓ Deployment complete!"
echo ""

# Step 4: Verify deployment
echo "Step 4: Verifying deployment..."
gcloud run jobs describe station10-gpu-worker --region=$REGION

echo ""
echo "========================================"
echo "DEPLOYMENT SUCCESSFUL"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Upload test video: gsutil cp test_videos/wlONOh_iUXY_*.mp3 gs://$GCS_BUCKET/test/mtg_interview.mp3"
echo "2. Run worker: ./deploy/test_gpu.sh"
echo ""

