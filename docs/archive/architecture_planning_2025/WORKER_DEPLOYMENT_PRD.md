# ClipScribe Worker Service Deployment PRD

*Last Updated: 2025-08-31*
*Version: 1.1*
*Status: In Development*

## Executive Summary

This Product Requirements Document (PRD) outlines the phased deployment strategy for ClipScribe's worker service, addressing the critical need to process queued video jobs. The strategy accommodates both short-form content (<60 minutes) and long-form content (3+ hours) while optimizing for cost, complexity, and time-to-market as a solo developer project.

**Critical Update**: Based on legal and operational analysis, we're implementing a private alpha → closed beta → public launch strategy to ensure system stability and legal compliance before public availability.

## Problem Statement

Currently, ClipScribe's API successfully queues video processing jobs in Redis, but no worker service exists to process these jobs. This results in:
- Jobs accumulating in the queue without processing
- Users unable to receive their video intelligence results
- Complete failure of the core product functionality

## Solution Overview

A three-phase deployment approach:
1. **Phase 1 (MVP)**: Cloud Run worker for videos <60 minutes
2. **Phase 2**: Hybrid architecture adding Compute Engine for long videos
3. **Phase 3**: Migration to GKE for production scale

## Detailed Requirements

### Phase 1: Hybrid Cloud Run + Compute Engine (MVP)

Given our analysis showing ~40-50% of high-value videos exceed 60 minutes (government hearings, analyst briefings, podcasts), we're implementing a hybrid architecture from day one.

#### 1.1 Technical Specifications

**Cloud Run Service (Short Videos <45 min):**
```yaml
Service Name: clipscribe-worker
Platform: Google Cloud Run
Container: gcr.io/PROJECT_ID/clipscribe-worker:latest
Timeout: 3600 seconds (60 minutes)
Memory: 4Gi
CPU: 2
Concurrency: 1 (one job per instance)
Min Instances: 0 (scale to zero)
Max Instances: 10
VPC Connector: clipscribe-connector (existing)
```

**Compute Engine VM (Long Videos 45+ min):**
```yaml
Name: clipscribe-worker-vm
Machine Type: e2-standard-4 (4 vCPU, 16GB RAM)
Boot Disk: 100GB SSD
OS: Container-Optimized OS
Network: default
Zone: us-central1-a
Preemptible: Yes (70% cost savings)
Labels:
  purpose: long-video-processing
  environment: production
```

**Environment Variables:**
```
REDIS_URL: (from Secret Manager)
GCS_BUCKET: (from Secret Manager)
GOOGLE_API_KEY: (from Secret Manager)
WORKER_MODE: cloud-run
MAX_VIDEO_DURATION: 2700 (45 minutes safety margin)
```

#### 1.2 Worker Implementation

**Entry Point (`src/clipscribe/commands/worker.py`):**
```python
import click
import asyncio
from ..api.worker import run

@click.command()
@click.option('--mode', default='cloud-run', help='Worker mode')
def worker(mode):
    """Run the ClipScribe worker service."""
    if mode == 'cloud-run':
        # Cloud Run uses HTTP health checks
        from ..api.worker_server import run_http_worker
        run_http_worker()
    else:
        # Traditional RQ worker
        run()

if __name__ == '__main__':
    worker()
```

**HTTP Wrapper for Cloud Run (`src/clipscribe/api/worker_server.py`):**
```python
from fastapi import FastAPI, BackgroundTasks
import asyncio
from .worker import process_job, _redis_available

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "redis": _redis_available()}

@app.post("/process")
async def trigger_processing(background_tasks: BackgroundTasks):
    """Trigger worker to check queue and process jobs."""
    background_tasks.add_task(process_available_jobs)
    return {"status": "processing triggered"}

async def process_available_jobs():
    """Process all available jobs in queue."""
    # Implementation to fetch and process jobs
    pass
```

#### 1.3 Deployment Configuration

**Dockerfile Updates:**
```dockerfile
# Worker stage
FROM base as worker

USER root
RUN pip install --no-cache-dir rq google-cloud-storage

# Create required directories
RUN mkdir -p /app/temp /app/logs && \
    chown -R clipscribe:clipscribe /app

COPY --chown=clipscribe:clipscribe src ./src
USER clipscribe

WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8080/health || exit 1

CMD ["uvicorn", "src.clipscribe.api.worker_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Cloud Build Configuration:**
```yaml
# Add to existing cloudbuild.yaml
- name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
  id: "deploy-worker"
  waitFor: ["push-api-latest"]
  args:
    - "gcloud"
    - "run"
    - "deploy"
    - "clipscribe-worker"
    - "--image=gcr.io/$PROJECT_ID/clipscribe-worker:${_VERSION}"
    - "--platform=managed"
    - "--region=${_REGION}"
    - "--no-allow-unauthenticated"
    - "--set-env-vars=WORKER_MODE=cloud-run,MAX_VIDEO_DURATION=2700"
    - "--set-secrets=REDIS_URL=REDIS_URL:latest,GCS_BUCKET=GCS_BUCKET:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest"
    - "--vpc-connector=clipscribe-connector"
    - "--vpc-egress=all-traffic"
    - "--timeout=3600"
    - "--cpu=2"
    - "--memory=4Gi"
    - "--min-instances=0"
    - "--max-instances=10"
    - "--concurrency=1"
```

#### 1.4 Intelligent Job Routing

**API Enhancement (`src/clipscribe/api/app.py`):**
```python
@app.post("/v1/jobs")
async def create_job(req: Request, body: Dict[str, Any], ...):
    # Existing code...
    
    # Intelligent routing based on duration and load
    if "url" in body:
        try:
            # Quick metadata fetch without downloading
            from clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
            client = EnhancedUniversalVideoClient()
            metadata = await client.get_video_metadata(body["url"])
            
            # Route based on video characteristics
            job_metadata = {
                "duration": metadata.duration,
                "title": metadata.title,
                "channel": metadata.channel
            }
            
            # Determine processing target
            if metadata.duration < 2700:  # <45 minutes
                target = "cloud-run"
                queue_name = "cs:queue:short"
            else:  # 45+ minutes
                target = "compute-engine"
                queue_name = "cs:queue:long"
                
                # Enqueue to Cloud Tasks for VM processing
                await enqueue_long_video_task(job_id, body["url"], metadata.duration)
            
            # Store routing decision
            redis_conn.hset(f"cs:job:{job_id}", "processing_target", target)
            
        except Exception as e:
            # Default to short queue if metadata fetch fails
            logger.warning(f"Metadata fetch failed: {e}, defaulting to short queue")
            queue_name = "cs:queue:short"
    
    # Continue with job creation...
```

**Target Audience Optimization:**
```python
# Detect high-value content types
HIGH_VALUE_KEYWORDS = [
    "hearing", "testimony", "briefing", "conference",
    "podcast", "interview", "presentation", "webinar",
    "earnings call", "board meeting", "senate", "congress"
]

def is_high_value_content(metadata) -> bool:
    """Identify content likely used by analysts/researchers."""
    title_lower = metadata.title.lower()
    return any(keyword in title_lower for keyword in HIGH_VALUE_KEYWORDS)
```

#### 1.5 Monitoring and Alerting

**Cloud Monitoring Metrics:**
- Job processing duration
- Job success/failure rate
- Queue depth
- Worker instance count
- Memory/CPU utilization

**Alerting Policies:**
- Queue depth > 100 jobs
- Job failure rate > 10%
- Worker instances at max capacity
- Processing duration > 50 minutes (approaching timeout)

### Phase 2: Hybrid Architecture for Long Videos

#### 2.1 Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Web UI    │────▶│  API Service │────▶│  Redis Queue    │
└─────────────┘     └─────────────┘     └────────┬────────┘
                                                  │
                           ┌──────────────────────┴──────────────────────┐
                           │                                             │
                    (<45 min)                                     (>45 min)
                           │                                             │
                    ┌──────▼────────┐                          ┌────────▼────────┐
                    │ Cloud Run     │                          │ Cloud Tasks     │
                    │ Worker        │                          │                 │
                    └───────────────┘                          └────────┬────────┘
                                                                        │
                                                               ┌────────▼────────┐
                                                               │ Compute Engine  │
                                                               │ Worker VM       │
                                                               └─────────────────┘
```

#### 2.2 Compute Engine Worker Specifications

**VM Configuration:**
```yaml
Name: clipscribe-worker-vm
Machine Type: e2-standard-4 (4 vCPU, 16GB RAM)
Boot Disk: 100GB SSD
OS: Container-Optimized OS
Network: default
Zone: us-central1-a
Preemptible: Yes (for cost savings)
```

**Startup Script:**
```bash
#!/bin/bash
# Pull and run worker container
docker pull gcr.io/PROJECT_ID/clipscribe-worker:latest
docker run \
  --name clipscribe-worker \
  --restart unless-stopped \
  -e WORKER_MODE=compute-engine \
  -e REDIS_URL="${REDIS_URL}" \
  -e GCS_BUCKET="${GCS_BUCKET}" \
  -e GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
  gcr.io/PROJECT_ID/clipscribe-worker:latest
```

#### 2.3 Cloud Tasks Integration

**Task Queue Configuration:**
```python
from google.cloud import tasks_v2

def enqueue_long_video_task(job_id: str, video_url: str, duration: int):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, LOCATION, 'long-video-queue')
    
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': f'http://{WORKER_VM_IP}:8080/process-job',
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'job_id': job_id,
                'video_url': video_url,
                'duration': duration
            }).encode()
        }
    }
    
    response = client.create_task(parent=parent, task=task)
    return response
```

### Phase 3: Production GKE Migration

#### 3.1 GKE Cluster Specifications

**Cluster Configuration:**
```yaml
Name: clipscribe-cluster
Location: us-central1
Node Pools:
  - name: worker-pool
    machine_type: n2-standard-4
    disk_size: 100GB
    autoscaling:
      min_nodes: 1
      max_nodes: 10
    node_labels:
      workload: worker
```

#### 3.2 Kubernetes Deployment

**Worker Deployment (`k8s/worker-deployment.yaml`):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clipscribe-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: clipscribe-worker
  template:
    metadata:
      labels:
        app: clipscribe-worker
    spec:
      containers:
      - name: worker
        image: gcr.io/PROJECT_ID/clipscribe-worker:latest
        env:
        - name: WORKER_MODE
          value: "kubernetes"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: clipscribe-secrets
              key: redis-url
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
```

**Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: clipscribe-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: clipscribe-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: redis_queue_depth
        selector:
          matchLabels:
            queue: clipscribe
      target:
        type: AverageValue
        averageValue: "10"
```

## Implementation Timeline

### Pre-Launch Phase (Month 1) - Infrastructure & Safety
- Week 1-2: Implement and deploy hybrid worker architecture
  - Day 1-2: Implement worker HTTP wrapper
  - Day 3-4: Update Dockerfile and deployment configs
  - Day 5-6: Set up Compute Engine VM with container
  - Day 7-8: Implement intelligent job routing
  - Day 9-10: Add Cloud Tasks integration
- Week 3: Safety and monitoring
  - Implement comprehensive monitoring and alerting
  - Add emergency stop mechanisms
  - Deploy cost control systems
- Week 4: Testing and validation
  - Process test videos across all duration ranges
  - Validate error handling and retry logic
  - Stress test with concurrent jobs

### Private Alpha Phase (Month 2) - Controlled Testing
- Week 1: Token system implementation
  - Implement token-based authentication
  - Add usage tracking and limits
  - Create admin dashboard for monitoring
- Week 2-3: Alpha user onboarding
  - Generate 5-10 alpha tokens
  - Onboard trusted users (personal contacts)
  - Gather initial feedback
- Week 4: Iterate based on feedback
  - Fix critical bugs
  - Adjust rate limits and quotas
  - Improve error messages

### Closed Beta Phase (Month 3-4) - Expanded Testing
- Month 3: Beta infrastructure
  - Implement beta tier with special limits
  - Add feedback collection system
  - Create basic documentation site
  - Expand to 20-50 beta users
- Month 4: Refinement
  - Implement requested features
  - Optimize performance
  - Prepare payment integration
  - Draft legal documents (ToS, Privacy Policy)

### Public Launch Preparation (Month 5-6)
- Month 5: Business and legal setup
  - Form business entity (LLC)
  - Set up business banking
  - Configure Stripe for subscriptions
  - Finalize legal documents
- Month 6: Launch readiness
  - Build marketing website
  - Implement full user authentication
  - Set up customer support system
  - Prepare launch communications

### Post-Launch Phase 3 (When Revenue > $10K/month)
- Migrate to GKE for scale
- Implement enterprise features
- Add compliance certifications

## Success Metrics

### Phase 1
- 95% job success rate for videos <45 minutes
- <30 second queue to processing start time
- <$50/month infrastructure cost

### Phase 2
- Support for videos up to 6 hours
- 90% job success rate for all videos
- <$150/month infrastructure cost

### Phase 3
- 99.9% job success rate
- <10 second queue to processing time
- Linear cost scaling with usage

## Beta Token System

### Token Architecture

**Token Format:**
```python
# Format: {tier_prefix}_{random_string}
# Example: beta_a7b9c2d4e6f8g0h2

TOKEN_PREFIXES = {
    "alpha": "alp",      # Private alpha testers
    "beta": "bet",       # Closed beta users
    "student": "stu",    # Student tier
    "researcher": "res", # Researcher tier
    "analyst": "ana",    # Analyst tier
    "enterprise": "ent"  # Enterprise tier
}
```

**Token Management:**
```python
# Store in Redis with metadata
def create_beta_token(email: str, tier: str = "beta") -> str:
    token = f"{TOKEN_PREFIXES[tier]}_{secrets.token_urlsafe(16)}"
    
    redis_conn.hset(f"cs:token:{token}", mapping={
        "email": email,
        "tier": tier,
        "created": datetime.utcnow().isoformat(),
        "monthly_limit": TIER_LIMITS[tier]["videos"],
        "max_duration": TIER_LIMITS[tier]["duration"],
        "videos_used": 0,
        "status": "active"
    })
    
    return token
```

**Usage Tracking:**
```python
def track_token_usage(token: str, video_duration: int, cost: float):
    key = f"cs:token:{token}"
    
    # Increment counters
    redis_conn.hincrby(key, "videos_used", 1)
    redis_conn.hincrbyfloat(key, "total_cost", cost)
    redis_conn.hincrby(key, "total_duration", video_duration)
    
    # Monthly reset check
    month_key = f"{key}:month:{datetime.utcnow().strftime('%Y%m')}"
    redis_conn.hincrby(month_key, "videos", 1)
    redis_conn.expire(month_key, 2592000)  # 30 days
```

### Beta Distribution Strategy

**Phase 1 - Alpha (5-10 users):**
- Personal contacts only
- Manual email distribution
- Direct feedback channel
- No payment required

**Phase 2 - Beta (20-50 users):**
- Application form on simple landing page
- Selective approval process
- Beta agreement required
- Optional donations accepted

**Phase 3 - Early Access (100-500 users):**
- Waitlist system
- Gradual rollout
- Discounted pricing for early adopters
- Stripe integration live

## Risk Mitigation

### Technical Risks
1. **Cloud Run Timeout**: Mitigated by 45-minute safety margin
2. **Cold Starts**: Accepted for MVP, monitor user impact
3. **Long Video Failures**: Phase 2 addresses with Compute Engine

### Operational Risks
1. **Cost Overrun**: Strict limits on max instances
2. **Complexity**: Phased approach limits complexity per phase
3. **Monitoring Gaps**: Comprehensive metrics from day 1

## Appendices

### A. Cost Analysis

**Phase 1 (Cloud Run)**
- Compute: ~$0.00002/vCPU-second = ~$0.144/hour active
- Memory: ~$0.0000025/GiB-second = ~$0.036/hour active
- Expected: 10 videos/day × 20 min avg = ~$2/month

**Phase 2 (+ Compute Engine)**
- Preemptible e2-standard-4: ~$29/month
- Cloud Tasks: ~$0.40/million operations
- Total: ~$30-50/month

**Phase 3 (GKE)**
- Cluster management: $73/month
- Node pool: ~$150/month (2 nodes minimum)
- Total: ~$200-300/month base

### B. Alternative Approaches Considered

1. **All-in on Compute Engine**: Rejected due to higher operational overhead
2. **Vertex AI Pipelines**: Rejected due to complexity and cost
3. **Cloud Functions**: Rejected due to 9-minute timeout
4. **App Engine Flex**: Rejected due to limited control over scaling
