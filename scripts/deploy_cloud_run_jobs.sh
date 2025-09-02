#!/bin/bash
# Deploy Cloud Run Jobs for ClipScribe Worker
# This script deploys the Cloud Run Jobs infrastructure to fix timeout issues

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"prismatic-iris-429006-g6"}
REGION=${REGION:-"us-central1"}
VERSION=${VERSION:-"v2.46.0"}

echo "🚀 Deploying ClipScribe Cloud Run Jobs"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Version: $VERSION"

# Check if gcloud is configured
if ! gcloud config get-value project > /dev/null 2>&1; then
    echo "❌ Please configure gcloud first: gcloud config set project $PROJECT_ID"
    exit 1
fi

# Build and deploy using Cloud Build
echo "📦 Building and deploying Cloud Run Jobs..."
gcloud builds submit \
    --config=cloudbuild-jobs.yaml \
    --substitutions=_VERSION=$VERSION,_REGION=$REGION \
    --project=$PROJECT_ID

echo "✅ Cloud Run Jobs deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Verify Flash job: gcloud run jobs describe clipscribe-worker-flash --region=$REGION"
echo "2. Verify Pro job: gcloud run jobs describe clipscribe-worker-pro --region=$REGION"
echo "3. Run a test job manually:"
echo "   gcloud run jobs execute clipscribe-worker-flash --region=$REGION"
echo ""
echo "🧪 To run baseline tests locally:"
echo "   python scripts/run_baseline_tests.py --category news --model both --limit 2"
echo ""
echo "📊 Monitor job executions:"
echo "   https://console.cloud.google.com/run/jobs?project=$PROJECT_ID"
