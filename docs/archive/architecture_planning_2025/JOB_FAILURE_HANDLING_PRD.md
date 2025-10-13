# ClipScribe Job Failure Handling & Retry Strategy PRD

*Last Updated: 2025-08-31*
*Version: 1.1*
*Status: In Development*

## Executive Summary

This PRD defines a comprehensive failure handling and retry strategy for ClipScribe's video processing jobs. The strategy balances reliability, cost efficiency, and user experience while providing clear visibility into job failures for debugging and improvement.

**Beta Considerations**: During alpha/beta phases, we'll implement enhanced logging and user feedback collection for failures to improve the system before public launch.

## Problem Statement

Video processing jobs can fail for various reasons:
- Transient network errors (API timeouts, download failures)
- Resource limitations (memory, timeout constraints)
- Invalid inputs (private videos, deleted content)
- Service outages (Gemini API, Google Cloud Storage)
- Unexpected errors (malformed responses, encoding issues)

Without proper failure handling, users experience:
- Lost processing requests with no feedback
- Unnecessary costs from infinite retries
- Poor visibility into failure reasons
- Manual intervention requirements

## Solution Overview

A multi-layered failure handling approach:
1. **Automatic retry with exponential backoff** for transient failures
2. **Failure classification** to determine retry eligibility
3. **Dead letter queue** for permanent failures
4. **User notification** and error transparency
5. **Monitoring and alerting** for systematic issues

## Detailed Requirements

### 1. Failure Classification System

#### 1.1 Error Categories

**Retriable Errors:**
```python
RETRIABLE_ERRORS = {
    "NetworkTimeout": {
        "patterns": ["timeout", "timed out", "connection reset"],
        "max_retries": 3,
        "backoff_factor": 2
    },
    "RateLimitExceeded": {
        "patterns": ["rate limit", "quota exceeded", "429"],
        "max_retries": 5,
        "backoff_factor": 3,
        "initial_wait": 60
    },
    "TemporaryServiceError": {
        "patterns": ["503", "service unavailable", "temporarily unavailable"],
        "max_retries": 3,
        "backoff_factor": 2
    },
    "ResourceConstraint": {
        "patterns": ["memory", "resource exhausted"],
        "max_retries": 2,
        "backoff_factor": 1.5
    }
}
```

**Non-Retriable Errors:**
```python
NON_RETRIABLE_ERRORS = {
    "InvalidInput": {
        "patterns": ["private video", "deleted", "not found", "404", "invalid url"]
    },
    "AuthenticationFailure": {
        "patterns": ["401", "403", "forbidden", "unauthorized"]
    },
    "PaymentRequired": {
        "patterns": ["402", "payment required", "billing"]
    },
    "ContentViolation": {
        "patterns": ["terms of service", "copyright", "content policy"]
    },
    "VideoExceedsLimits": {
        "patterns": ["exceeds maximum duration", "video too large", "over 6 hours"]
    },
    "QuotaExceeded": {
        "patterns": ["daily limit reached", "monthly quota exceeded", "tier limit"]
    }
}
```

#### 1.2 Error Classification Logic

```python
from typing import Tuple, Optional
import re

class ErrorClassifier:
    def classify_error(self, error: Exception) -> Tuple[str, bool, Optional[dict]]:
        """
        Classify an error and determine if it's retriable.
        
        Returns:
            (error_type, is_retriable, retry_config)
        """
        error_message = str(error).lower()
        
        # Check non-retriable first (fail fast)
        for error_type, config in NON_RETRIABLE_ERRORS.items():
            if any(pattern in error_message for pattern in config["patterns"]):
                return error_type, False, None
        
        # Check retriable errors
        for error_type, config in RETRIABLE_ERRORS.items():
            if any(pattern in error_message for pattern in config["patterns"]):
                return error_type, True, config
        
        # Unknown errors are retriable with conservative settings
        return "UnknownError", True, {
            "max_retries": 2,
            "backoff_factor": 2,
            "initial_wait": 30
        }
```

### 2. Retry Implementation

#### 2.1 RQ Configuration

```python
# src/clipscribe/api/worker.py
from rq import Retry
from datetime import timedelta

def enqueue_job_with_retry(queue, job_id: str, payload: dict):
    """Enqueue job with retry configuration."""
    queue.enqueue(
        "clipscribe.api.worker.process_job",
        job_id,
        payload,
        job_timeout="2h",  # 2 hour timeout for long videos
        result_ttl=86400,   # Keep results for 24 hours
        failure_ttl=604800, # Keep failures for 7 days
        retry=Retry(
            max=3,
            interval=[60, 300, 900]  # 1min, 5min, 15min
        )
    )
```

#### 2.2 Custom Retry Logic

```python
import asyncio
from functools import wraps
from typing import Callable, Any

class RetryHandler:
    def __init__(self, classifier: ErrorClassifier):
        self.classifier = classifier
    
    def with_retry(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            last_error = None
            
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_type, is_retriable, config = self.classifier.classify_error(e)
                    
                    if not is_retriable:
                        # Log non-retriable error and raise
                        await self._log_permanent_failure(error_type, e, *args)
                        raise
                    
                    attempt += 1
                    if attempt > config["max_retries"]:
                        # Max retries exceeded
                        await self._move_to_dlq(error_type, e, attempt, *args)
                        raise
                    
                    # Calculate backoff
                    wait_time = self._calculate_backoff(
                        attempt,
                        config.get("backoff_factor", 2),
                        config.get("initial_wait", 30)
                    )
                    
                    await self._log_retry_attempt(error_type, e, attempt, wait_time, *args)
                    await asyncio.sleep(wait_time)
                    last_error = e
        
        return wrapper
    
    def _calculate_backoff(self, attempt: int, factor: float, initial: int) -> int:
        """Calculate exponential backoff with jitter."""
        import random
        base_wait = initial * (factor ** (attempt - 1))
        jitter = random.uniform(0.8, 1.2)  # ±20% jitter
        return int(base_wait * jitter)
```

### 3. Dead Letter Queue Implementation

#### 3.1 DLQ Structure

```python
# Redis keys for DLQ
DLQ_KEY = "cs:dlq:jobs"           # Sorted set of failed job IDs
DLQ_DETAILS = "cs:dlq:details:{}" # Hash of failure details

class DeadLetterQueue:
    def __init__(self, redis_conn):
        self.redis = redis_conn
    
    async def add_failed_job(
        self,
        job_id: str,
        error_type: str,
        error_message: str,
        attempts: int,
        original_payload: dict
    ):
        """Add a permanently failed job to DLQ."""
        timestamp = time.time()
        
        # Add to sorted set (score = timestamp)
        self.redis.zadd(DLQ_KEY, {job_id: timestamp})
        
        # Store failure details
        details_key = DLQ_DETAILS.format(job_id)
        self.redis.hset(details_key, mapping={
            "error_type": error_type,
            "error_message": error_message,
            "attempts": attempts,
            "failed_at": timestamp,
            "payload": json.dumps(original_payload)
        })
        
        # Expire after 30 days
        self.redis.expire(details_key, 2592000)
    
    async def get_failed_jobs(self, limit: int = 100) -> List[dict]:
        """Retrieve recent failed jobs."""
        job_ids = self.redis.zrevrange(DLQ_KEY, 0, limit - 1)
        
        jobs = []
        for job_id in job_ids:
            details = self.redis.hgetall(DLQ_DETAILS.format(job_id))
            if details:
                jobs.append({
                    "job_id": job_id,
                    **{k: v.decode() if isinstance(v, bytes) else v 
                       for k, v in details.items()}
                })
        
        return jobs
    
    async def retry_failed_job(self, job_id: str) -> bool:
        """Manually retry a job from DLQ."""
        details = self.redis.hgetall(DLQ_DETAILS.format(job_id))
        if not details:
            return False
        
        # Re-enqueue the job
        payload = json.loads(details[b"payload"])
        enqueue_job_with_retry(job_queue, job_id, payload)
        
        # Remove from DLQ
        self.redis.zrem(DLQ_KEY, job_id)
        self.redis.delete(DLQ_DETAILS.format(job_id))
        
        return True
```

### 4. User Notification System

#### 4.1 Job Status Updates

```python
class JobStatusUpdater:
    def __init__(self, redis_conn, storage_client):
        self.redis = redis_conn
        self.storage = storage_client
    
    async def update_job_failure(
        self,
        job_id: str,
        error_type: str,
        error_message: str,
        is_permanent: bool
    ):
        """Update job status with failure information."""
        # Update Redis
        job_key = f"cs:job:{job_id}"
        self.redis.hset(job_key, mapping={
            "state": "FAILED" if is_permanent else "RETRYING",
            "error": json.dumps({
                "type": error_type,
                "message": self._sanitize_error_message(error_message),
                "is_permanent": is_permanent,
                "timestamp": datetime.utcnow().isoformat()
            }),
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Update manifest in GCS
        await self._update_gcs_manifest(job_id, error_type, error_message, is_permanent)
    
    def _sanitize_error_message(self, message: str) -> str:
        """Remove sensitive information from error messages."""
        # Remove file paths
        message = re.sub(r'\/[\w\/\-\.]+', '[PATH]', message)
        # Remove IPs
        message = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', message)
        # Remove API keys
        message = re.sub(r'[A-Za-z0-9]{32,}', '[REDACTED]', message)
        return message
```

#### 4.2 User-Facing Error Messages

```python
ERROR_MESSAGES = {
    "NetworkTimeout": "The video processing timed out. We'll retry automatically.",
    "RateLimitExceeded": "We've hit our processing limit. Your video will be processed soon.",
    "InvalidInput": "This video cannot be processed. It may be private or deleted.",
    "VideoExceedsLimits": "This video exceeds our current processing limits (6+ hours or 10GB+).",
    "QuotaExceeded": "You've reached your plan's monthly limit. Please upgrade or wait for reset.",
    "AuthenticationFailure": "We couldn't access this video. Please check if it's publicly available.",
    "TemporaryServiceError": "Our processing service is temporarily unavailable. Retrying...",
    "ResourceConstraint": "This video requires more resources than available. Moving to priority queue.",
    "UnknownError": "An unexpected error occurred. Our team has been notified."
}

# Special handling for ultra-long videos
ULTRA_LONG_VIDEO_STRATEGIES = {
    "6_to_8_hours": {
        "max_retries": 1,
        "processing_tier": "compute-engine-high-memory",
        "chunk_strategy": "adaptive",
        "model": "gemini-flash"  # Force efficient model
    },
    "8_plus_hours": {
        "max_retries": 0,
        "processing_tier": "manual-review",
        "notification": "admin",
        "message": "Please contact support for videos over 8 hours"
    }
}
```

### 5. Monitoring and Alerting

#### 5.1 Metrics Collection

```python
class FailureMetrics:
    def __init__(self, monitoring_client):
        self.monitoring = monitoring_client
    
    async def record_failure(
        self,
        error_type: str,
        is_permanent: bool,
        video_duration: Optional[int] = None
    ):
        """Record failure metrics."""
        labels = {
            "error_type": error_type,
            "is_permanent": str(is_permanent),
            "duration_bucket": self._get_duration_bucket(video_duration)
        }
        
        # Increment failure counter
        self.monitoring.increment(
            "clipscribe.worker.failures",
            labels=labels
        )
        
        # Record failure rate
        self.monitoring.gauge(
            "clipscribe.worker.failure_rate",
            value=await self._calculate_failure_rate(),
            labels={"window": "5m"}
        )
    
    def _get_duration_bucket(self, duration: Optional[int]) -> str:
        if not duration:
            return "unknown"
        elif duration < 300:
            return "0-5min"
        elif duration < 900:
            return "5-15min"
        elif duration < 2700:
            return "15-45min"
        else:
            return "45min+"
```

#### 5.2 Alert Configuration

```yaml
# Cloud Monitoring Alert Policies
alerts:
  - name: high-failure-rate
    condition: |
      rate(clipscribe.worker.failures[5m]) > 0.1
    duration: 5m
    notification:
      - email
      - slack
    
  - name: dlq-growing
    condition: |
      rate(clipscribe.dlq.size[10m]) > 10
    duration: 10m
    notification:
      - email
      - pagerduty
    
  - name: specific-error-spike
    condition: |
      rate(clipscribe.worker.failures{error_type="RateLimitExceeded"}[5m]) > 5
    duration: 5m
    notification:
      - email
    actions:
      - reduce_worker_concurrency
```

### 6. Implementation Guidelines

#### 6.1 Testing Strategy

**Unit Tests:**
```python
@pytest.mark.asyncio
async def test_error_classification():
    classifier = ErrorClassifier()
    
    # Test retriable errors
    error = Exception("Connection timeout while downloading")
    error_type, is_retriable, config = classifier.classify_error(error)
    assert error_type == "NetworkTimeout"
    assert is_retriable is True
    assert config["max_retries"] == 3
    
    # Test non-retriable errors
    error = Exception("Video is private")
    error_type, is_retriable, _ = classifier.classify_error(error)
    assert error_type == "InvalidInput"
    assert is_retriable is False
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_retry_with_backoff(mock_redis):
    handler = RetryHandler(ErrorClassifier())
    attempts = []
    
    @handler.with_retry
    async def flaky_operation():
        attempts.append(time.time())
        if len(attempts) < 3:
            raise Exception("Connection timeout")
        return "success"
    
    result = await flaky_operation()
    assert result == "success"
    assert len(attempts) == 3
    
    # Verify backoff timing
    assert attempts[1] - attempts[0] >= 30  # First retry
    assert attempts[2] - attempts[1] >= 60  # Second retry
```

#### 6.2 Rollout Plan

1. **Phase 1**: Deploy error classification without retry (monitor only)
2. **Phase 2**: Enable retry for NetworkTimeout errors only
3. **Phase 3**: Enable retry for all retriable categories
4. **Phase 4**: Activate DLQ and user notifications

## Success Metrics

- **Retry Success Rate**: >60% of retried jobs succeed
- **False Positive Rate**: <5% of non-retriable errors are misclassified
- **User Experience**: <2% of jobs end in permanent failure
- **Cost Efficiency**: <$0.10 average retry cost per job

## Risk Mitigation

1. **Retry Storms**: Exponential backoff and jitter prevent thundering herd
2. **Infinite Loops**: Max retry limits and DLQ prevent endless retries
3. **Cost Explosion**: Retry limits and monitoring alerts cap expenses
4. **Data Loss**: All failures logged with full context for recovery

## Beta Phase Implementation

### Alpha Phase (Month 1-2)
- Basic retry for network timeouts only
- Manual monitoring of failures
- Direct notification to admin for all failures
- Enhanced logging for debugging

### Beta Phase (Month 3-4)
- Full error classification system
- User-visible error messages
- Feedback collection on failures
- DLQ implementation for analysis

### Production Phase (Month 6+)
- Complete retry strategy
- Automated failure recovery
- User self-service retry options
- Full monitoring and alerting

## Future Enhancements

1. **Smart Retry**: ML-based retry prediction
2. **User Retry Options**: Allow users to force retry with different settings
3. **Batch Recovery**: Admin tools for bulk DLQ processing
4. **Circuit Breakers**: Temporarily disable processing for systemic failures
