# ClipScribe Cold Start Optimization & Monitoring PRD

*Last Updated: 2025-08-31*
*Version: 1.1*
*Status: In Development*

## Executive Summary

This PRD addresses cold start performance for ClipScribe's scale-to-zero worker architecture on Google Cloud Run. It defines strategies to minimize cold start impact, monitor performance, and provide optimal user experience while maintaining cost efficiency.

**Beta Considerations**: During alpha/beta, we'll gather real-world cold start metrics to refine our optimization strategies before public launch. Beta users will receive clear communication about initialization times.

## Problem Statement

Scale-to-zero architecture introduces cold starts when:
- First request after idle period requires container initialization
- Python runtime and dependencies must load (5-15 seconds typical)
- Redis connections must be established
- Google Cloud clients must authenticate

This impacts:
- User perception of service responsiveness
- Job processing latency
- Overall system reliability metrics

## Cold Start Analysis

### Baseline Measurements

**Container Initialization Timeline:**
```
Step                          Time      Cumulative
--------------------------------------------------
Container allocation          1-2s      2s
Python runtime startup        1-2s      4s
Import dependencies           3-5s      9s
Redis connection             0.5-1s    10s
GCS client initialization    1-2s      12s
First request processing     0.5-1s    13s
--------------------------------------------------
Total cold start:            10-15s
```

**Dependency Import Analysis:**
```python
# Heavy imports contributing to cold start
import google.cloud.storage      # ~1.5s
import clipscribe.retrievers     # ~2.0s
import clipscribe.extractors     # ~1.8s
from yt_dlp import YoutubeDL     # ~0.8s
import redis                     # ~0.2s
import fastapi                   # ~0.3s
```

## Optimization Strategies

### 1. Container Optimization

#### 1.1 Minimal Base Image

```dockerfile
# Optimized Dockerfile
FROM python:3.12-slim as builder

# Build stage - compile dependencies
WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction

# Runtime stage - minimal image
FROM python:3.12-slim

# Copy only compiled dependencies
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Install only runtime requirements
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY src ./src

# Pre-compile Python files
RUN python -m compileall -b src/

# Optimize Python startup
ENV PYTHONOPTIMIZE=2
ENV PYTHONDONTWRITEBYTECODE=1
```

#### 1.2 Dependency Optimization

```python
# src/clipscribe/api/worker_optimized.py
import asyncio
import os

# Lazy imports to reduce initial load time
_redis_conn = None
_gcs_client = None

def get_redis_connection():
    global _redis_conn
    if _redis_conn is None:
        import redis
        _redis_conn = redis.from_url(os.getenv("REDIS_URL"))
    return _redis_conn

def get_gcs_client():
    global _gcs_client
    if _gcs_client is None:
        from google.cloud import storage
        _gcs_client = storage.Client()
    return _gcs_client

# FastAPI with minimal middleware
from fastapi import FastAPI
app = FastAPI(
    openapi_url=None,  # Disable OpenAPI generation
    docs_url=None,     # Disable docs
    redoc_url=None     # Disable redoc
)
```

### 2. Warm-up Strategies

#### 2.1 Proactive Warming

```python
# Cloud Scheduler job configuration
resource "google_cloud_scheduler_job" "worker_warmer" {
  name             = "clipscribe-worker-warmer"
  description      = "Keep worker warm during business hours"
  schedule         = "*/15 8-18 * * MON-FRI"  # Every 15 min, 8am-6pm weekdays
  time_zone        = "America/Los_Angeles"
  
  http_target {
    uri         = "https://clipscribe-worker.run.app/health"
    http_method = "GET"
    
    oidc_token {
      service_account_email = google_service_account.worker_warmer.email
    }
  }
}
```

#### 2.2 Predictive Warming

```python
class PredictiveWarmer:
    """Warm containers based on usage patterns."""
    
    def __init__(self, redis_conn):
        self.redis = redis_conn
        self.pattern_key = "cs:usage:pattern"
    
    async def record_usage(self):
        """Record job submission time."""
        hour = datetime.utcnow().hour
        day = datetime.utcnow().weekday()
        
        # Increment hourly counter
        key = f"{self.pattern_key}:{day}:{hour}"
        self.redis.incr(key)
        self.redis.expire(key, 604800)  # 7 days
    
    async def should_warm(self) -> bool:
        """Determine if we should warm based on patterns."""
        current_hour = datetime.utcnow().hour
        current_day = datetime.utcnow().weekday()
        
        # Check usage in surrounding hours
        total_usage = 0
        for hour_offset in range(-1, 2):  # Previous, current, next hour
            hour = (current_hour + hour_offset) % 24
            key = f"{self.pattern_key}:{current_day}:{hour}"
            usage = int(self.redis.get(key) or 0)
            total_usage += usage
        
        # Warm if average usage > 5 jobs per hour
        return total_usage > 15
```

### 3. Connection Pooling

#### 3.1 Redis Connection Pool

```python
# Singleton connection pool
class ConnectionManager:
    _instance = None
    _redis_pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_redis(self):
        if self._redis_pool is None:
            import redis
            self._redis_pool = redis.ConnectionPool.from_url(
                os.getenv("REDIS_URL"),
                max_connections=10,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,   # TCP_KEEPIDLE
                    2: 1,   # TCP_KEEPINTVL
                    3: 3,   # TCP_KEEPCNT
                }
            )
        return redis.Redis(connection_pool=self._redis_pool)
```

#### 3.2 GCS Client Reuse

```python
# Thread-safe GCS client singleton
import threading

class GCSManager:
    _instance = None
    _lock = threading.Lock()
    _client = None
    
    @classmethod
    def get_client(cls):
        if cls._client is None:
            with cls._lock:
                if cls._client is None:
                    from google.cloud import storage
                    cls._client = storage.Client()
        return cls._client
```

### 4. Monitoring Implementation

#### 4.1 Cold Start Metrics

```python
import time
from datetime import datetime

class ColdStartMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.is_cold_start = os.getenv("K_REVISION", "") != self._get_cached_revision()
        self.metrics = {}
    
    def record_milestone(self, name: str):
        """Record timing milestone during startup."""
        elapsed = time.time() - self.start_time
        self.metrics[name] = elapsed
        
        if self.is_cold_start:
            # Log to Cloud Monitoring
            logger.info(f"cold_start_milestone", extra={
                "milestone": name,
                "elapsed_seconds": elapsed,
                "revision": os.getenv("K_REVISION")
            })
    
    def complete_startup(self):
        """Mark startup complete and report metrics."""
        total_time = time.time() - self.start_time
        
        if self.is_cold_start:
            # Report to monitoring
            monitoring_client.create_time_series(
                name="custom.googleapis.com/clipscribe/cold_start_duration",
                value=total_time,
                labels={
                    "service": "worker",
                    "region": os.getenv("K_SERVICE_REGION", "unknown")
                }
            )
            
            # Cache revision to detect future cold starts
            self._cache_revision(os.getenv("K_REVISION"))
    
    def _get_cached_revision(self) -> str:
        try:
            with open("/tmp/cached_revision", "r") as f:
                return f.read().strip()
        except:
            return ""
    
    def _cache_revision(self, revision: str):
        with open("/tmp/cached_revision", "w") as f:
            f.write(revision)

# Usage in startup
monitor = ColdStartMonitor()
monitor.record_milestone("python_started")

from fastapi import FastAPI
monitor.record_milestone("fastapi_imported")

app = FastAPI()
monitor.record_milestone("app_created")

# ... more initialization ...

monitor.complete_startup()
```

#### 4.2 Performance Dashboard

```python
# Monitoring queries for dashboard
MONITORING_QUERIES = {
    "cold_start_frequency": """
        fetch cloud_run_revision::run.googleapis.com/container/startup_latencies
        | filter resource.service_name == 'clipscribe-worker'
        | group_by 1h, [value_count]
        | every 1h
    """,
    
    "cold_start_duration_p95": """
        fetch custom.googleapis.com/clipscribe/cold_start_duration
        | filter metric.service == 'worker'
        | group_by 1h, [value_percentile_95]
        | every 1h
    """,
    
    "warm_vs_cold_requests": """
        fetch cloud_run_revision::run.googleapis.com/request_count
        | filter resource.service_name == 'clipscribe-worker'
        | group_by [metric.response_code_class], 1h
        | ratio
    """
}
```

### 5. User Experience Optimization

#### 5.1 Expectation Management

```python
# API response during cold start
@app.post("/v1/jobs")
async def create_job(body: Dict[str, Any]):
    # Check if this is likely a cold start
    if await is_likely_cold_start():
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "state": "INITIALIZING",
                "message": "Starting video processor. Your job will begin processing in 10-15 seconds.",
                "estimated_start_time": (datetime.utcnow() + timedelta(seconds=15)).isoformat()
            }
        )
    
    # Normal response for warm starts
    return create_normal_response(job_id)

async def is_likely_cold_start() -> bool:
    """Detect if workers are likely cold."""
    last_job_key = "cs:last_job_time"
    last_job_time = redis_conn.get(last_job_key)
    
    if not last_job_time:
        return True
    
    # If no jobs in last 15 minutes, likely cold
    time_since_last = time.time() - float(last_job_time)
    return time_since_last > 900
```

#### 5.2 Progressive Enhancement with Useful Activities

```python
# API-side useful activities during cold start
async def perform_cold_start_activities(video_url: str) -> dict:
    """
    Perform useful activities during the 15-second cold start.
    Returns immediately valuable information to the user.
    """
    results = {}
    
    # 1. Fetch and validate video metadata (2-3 seconds)
    try:
        metadata = await fetch_video_metadata(video_url)
        results["metadata"] = {
            "title": metadata.title,
            "duration": metadata.duration,
            "channel": metadata.channel,
            "upload_date": metadata.upload_date,
            "view_count": metadata.view_count
        }
        
        # 2. Check for existing/duplicate processing (1 second)
        duplicate = await check_duplicate_processing(video_url)
        if duplicate:
            results["duplicate_warning"] = {
                "job_id": duplicate.job_id,
                "processed_date": duplicate.date,
                "status": duplicate.status
            }
        
        # 3. Generate cost and time estimates (1 second)
        estimate = calculate_processing_estimate(metadata.duration)
        results["estimate"] = {
            "processing_time": f"{estimate.time_minutes} minutes",
            "cost": f"${estimate.cost:.2f}",
            "quality_recommendation": "Pro" if metadata.duration < 300 else "Flash"
        }
        
        # 4. Identify content type and optimization (1 second)
        content_type = identify_content_type(metadata)
        results["content_analysis"] = {
            "type": content_type,
            "recommended_extractors": get_optimal_extractors(content_type),
            "priority_entities": get_priority_entities(content_type)
        }
        
        # 5. Pre-fetch thumbnail and preview (2-3 seconds)
        if not duplicate:
            preview = await generate_preview(video_url, metadata)
            results["preview"] = {
                "thumbnail_url": preview.thumbnail,
                "duration_formatted": preview.duration_str,
                "key_frames": preview.key_frames
            }
        
        # 6. Check API quotas and availability (1 second)
        quota_status = await check_api_quotas()
        results["system_status"] = {
            "api_available": quota_status.available,
            "daily_quota_remaining": quota_status.remaining,
            "estimated_wait_time": quota_status.wait_time
        }
        
    except Exception as e:
        logger.warning(f"Cold start activity failed: {e}")
        # Return partial results
    
    return results

def identify_content_type(metadata) -> str:
    """Identify high-value content types for analysts."""
    title_lower = metadata.title.lower()
    channel_lower = metadata.channel.lower()
    
    # Government/Intelligence content
    if any(term in title_lower for term in ["hearing", "testimony", "briefing", "senate", "congress"]):
        return "government_proceedings"
    
    # Financial/Business content
    elif any(term in title_lower for term in ["earnings call", "investor", "quarterly", "financial"]):
        return "financial_analysis"
    
    # Research/Academic content
    elif any(term in title_lower for term in ["conference", "presentation", "lecture", "seminar"]):
        return "academic_research"
    
    # Long-form interviews/podcasts
    elif metadata.duration > 3600 and "podcast" in channel_lower:
        return "podcast_interview"
    
    else:
        return "general_content"
```

```javascript
// Enhanced frontend handling with useful feedback
async function submitJob(videoUrl) {
    const response = await fetch('/api/v1/jobs', {
        method: 'POST',
        body: JSON.stringify({ url: videoUrl })
    });
    
    const data = await response.json();
    
    if (data.state === 'INITIALIZING') {
        // Show useful information during cold start
        showColdStartInfo({
            metadata: data.cold_start_info.metadata,
            estimate: data.cold_start_info.estimate,
            preview: data.cold_start_info.preview,
            duplicate: data.cold_start_info.duplicate_warning
        });
        
        // Start countdown timer
        startWarmupCountdown(15, data.job_id);
        
    } else {
        // Normal flow for warm start
        startJobPolling(data.job_id);
    }
}

function showColdStartInfo(info) {
    // Display rich information panel
    const panel = createInfoPanel({
        title: info.metadata.title,
        duration: info.metadata.duration,
        cost: info.estimate.cost,
        time: info.estimate.processing_time,
        thumbnail: info.preview?.thumbnail_url
    });
    
    // Show duplicate warning if exists
    if (info.duplicate) {
        showDuplicateWarning(info.duplicate);
    }
    
    // Display countdown with progress
    showNotification({
        type: 'info',
        title: 'Initializing Video Processor',
        message: 'Analyzing video and preparing extraction engines...',
        progress: true,
        duration: 15000
    });
}
```

## Implementation Checklist

### Phase 1: Measurement (Week 1)
- [ ] Deploy cold start monitoring
- [ ] Establish baseline metrics
- [ ] Create performance dashboard

### Phase 2: Quick Wins (Week 2)
- [ ] Optimize Dockerfile
- [ ] Implement lazy imports
- [ ] Add connection pooling

### Phase 3: Warming Strategy (Week 3)
- [ ] Deploy scheduled warmer
- [ ] Implement usage pattern tracking
- [ ] Add predictive warming

### Phase 4: UX Enhancement (Week 4)
- [ ] Update API responses
- [ ] Enhance frontend handling
- [ ] A/B test messaging

## Success Metrics

### Technical Metrics
- **P50 Cold Start**: < 8 seconds
- **P95 Cold Start**: < 15 seconds
- **Warm Start Ratio**: > 70% during peak hours
- **Container Efficiency**: < 500MB image size

### User Experience Metrics
- **Perceived Performance**: > 4.0/5 user rating
- **Job Abandonment**: < 5% due to cold starts
- **Support Tickets**: < 2% mentioning slow starts

## Cost Analysis

### Warming Costs
```
Scheduled warming (business hours):
- 15-minute intervals × 10 hours × 5 days = 200 warm-ups/week
- Cost: 200 × 0.005 (avg request cost) = $1/week = $4/month

Predictive warming (based on patterns):
- Estimated 50 additional warm-ups/week
- Cost: 50 × 0.005 = $0.25/week = $1/month

Total warming cost: ~$5/month
```

### ROI Calculation
- Improved user experience → Higher retention
- Reduced support burden → Lower operational cost
- Better performance metrics → Improved product positioning

## Beta Phase Approach

### Alpha Phase (Month 1-2)
- Accept 10-15 second cold starts
- Clear messaging to alpha testers
- Collect detailed performance metrics
- Manual warming during testing sessions

### Beta Phase (Month 3-4)
- Implement scheduled warming (business hours)
- Add cold start activity features
- Target <10 second cold starts
- A/B test different messaging approaches

### Production Phase (Month 6+)
- Full predictive warming
- <8 second P50 cold starts
- Seamless user experience
- Cost-optimized warming strategy

## Future Enhancements

1. **Container Pre-warming**: Use Cloud Run's upcoming pre-warming features
2. **Edge Caching**: Deploy lightweight edge functions for instant response
3. **WebAssembly**: Explore WASM for faster cold starts
4. **Microservice Split**: Separate heavy dependencies into dedicated services
