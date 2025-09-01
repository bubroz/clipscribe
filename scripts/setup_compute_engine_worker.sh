#!/bin/bash
# Setup script for ClipScribe Compute Engine worker
# This creates a VM that runs traditional RQ workers for long videos

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"prismatic-iris-429006-g6"}
ZONE=${COMPUTE_ZONE:-"us-central1-a"}
INSTANCE_NAME=${INSTANCE_NAME:-"clipscribe-worker-vm"}
MACHINE_TYPE=${MACHINE_TYPE:-"e2-standard-4"}
BOOT_DISK_SIZE=${BOOT_DISK_SIZE:-"100"}

echo "Setting up Compute Engine worker VM..."

# Create the VM instance
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network=default,network-tier=PREMIUM \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account="16459511304-compute@developer.gserviceaccount.com" \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --create-disk=auto-delete=yes,boot=yes,device-name=$INSTANCE_NAME,image=projects/cos-cloud/global/images/cos-stable-117-18613-75-37,mode=rw,size=$BOOT_DISK_SIZE,type=pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=purpose=clipscribe-worker,environment=production \
    --metadata=startup-script='#!/bin/bash
# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

# Get secrets from Secret Manager
export REDIS_URL=$(gcloud secrets versions access latest --secret="REDIS_URL")
export GCS_BUCKET=$(gcloud secrets versions access latest --secret="GCS_BUCKET")
export GOOGLE_API_KEY=$(gcloud secrets versions access latest --secret="GOOGLE_API_KEY")

# Create worker script
cat > /home/chronos/run_worker.sh << EOF
#!/bin/bash
docker run -d \
  --name clipscribe-worker \
  --restart unless-stopped \
  -e REDIS_URL="\$REDIS_URL" \
  -e GCS_BUCKET="\$GCS_BUCKET" \
  -e GOOGLE_API_KEY="\$GOOGLE_API_KEY" \
  -e WORKER_MODE=compute-engine \
  -e CLIPSCRIBE_LOG_LEVEL=INFO \
  gcr.io/$PROJECT_ID/clipscribe-worker:latest \
  python -m rq worker clipscribe-long --url "\$REDIS_URL"
EOF

chmod +x /home/chronos/run_worker.sh

# Pull and run the worker container
docker pull gcr.io/$PROJECT_ID/clipscribe-worker:latest
/home/chronos/run_worker.sh

# Set up log rotation
echo "0 0 * * * docker logs clipscribe-worker > /home/chronos/worker-\$(date +\%Y\%m\%d).log && docker logs --clear clipscribe-worker" | crontab -
'

echo "VM created. Waiting for startup script to complete..."
sleep 30

# Get the external IP
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "Worker VM created successfully!"
echo "Instance: $INSTANCE_NAME"
echo "External IP: $EXTERNAL_IP"
echo "Zone: $ZONE"
echo ""
echo "To SSH into the VM:"
echo "gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "To view worker logs:"
echo "gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='docker logs clipscribe-worker'"
