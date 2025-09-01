"""
Worker Server for ClipScribe - HTTP wrapper for Cloud Run worker service.

This module provides an HTTP interface for the worker service, allowing it to run
on Cloud Run while processing jobs from the Redis queue.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import redis
import uvicorn

from .worker import _process_payload
from ..config.settings import Settings
from .monitoring import get_metrics_collector, get_alert_manager, get_health_checker, setup_default_alerts
from .retry_manager import get_retry_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ClipScribe Worker",
    version="1.0.0",
    docs_url=None,  # Disable docs for security
    redoc_url=None
)

# Add CORS middleware for health checks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Redis connection and monitoring components
redis_conn: Optional[redis.Redis] = None
metrics_collector = None
alert_manager = None
health_checker = None
retry_manager = None

def get_redis_conn() -> redis.Redis:
    """Get Redis connection with singleton pattern."""
    global redis_conn
    if redis_conn is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_conn = redis.from_url(redis_url)
    return redis_conn

def get_monitoring_components():
    """Get or initialize monitoring components."""
    global metrics_collector, alert_manager, health_checker, retry_manager

    if metrics_collector is None:
        metrics_collector = get_metrics_collector(get_redis_conn())
        alert_manager = get_alert_manager(get_redis_conn())
        health_checker = get_health_checker(get_redis_conn())
        retry_manager = get_retry_manager(get_redis_conn())

        # Setup default alerts
        setup_default_alerts(alert_manager)

    return metrics_collector, alert_manager, health_checker, retry_manager

def _request_id() -> str:
    """Generate a simple request ID."""
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

@app.middleware("http")
async def add_request_id_header(request, call_next):
    """Add request ID to all responses."""
    response = await call_next(request)
    if "X-Request-ID" not in response.headers:
        response.headers["X-Request-ID"] = _request_id()
    return response

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for Cloud Run."""
    try:
        # Get monitoring components
        metrics, alerts, health, retry_mgr = get_monitoring_components()

        # Check Redis connectivity
        conn = get_redis_conn()
        conn.ping()

        # Check GCS access
        from google.cloud import storage
        client = storage.Client()
        bucket_name = os.getenv("GCS_BUCKET")
        gcs_status = "not_configured"
        if bucket_name:
            bucket = client.bucket(bucket_name)
            bucket.reload()
            gcs_status = "healthy"

        # Get queue status
        queue_status = await get_queue_status()

        # Get active alerts
        active_alerts = alerts.get_active_alerts()

        # Collect system metrics
        metrics.collect_system_metrics()
        metrics.collect_application_metrics(conn)

        # Perform comprehensive health check
        health_status = health.perform_health_check()

        # Check for critical alerts
        critical_alerts = [alert for alert in active_alerts if alert.get('severity') == 'critical']

        overall_status = "healthy"
        if health_status["overall_status"] != "healthy" or critical_alerts:
            overall_status = "degraded"
        elif active_alerts:
            overall_status = "warning"

        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "redis": True,
            "gcs": gcs_status,
            "system_health": health_status,
            "queue_status": queue_status,
            "active_alerts_count": len(active_alerts),
            "critical_alerts_count": len(critical_alerts),
            "version": "1.0.0"
        }

        # Include alerts if any
        if active_alerts:
            response["active_alerts"] = active_alerts[:5]  # Limit to 5 most recent

        return response

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "redis": False,
            "gcs": "unknown"
        }

@app.post("/process-job")
async def process_job(request: dict, background_tasks: BackgroundTasks):
    """
    Process a job from Cloud Tasks.
    
    Expected payload:
    {
        "job_id": "...",
        "payload": {
            "url": "...",
            "options": {}
        }
    }
    """
    try:
        # Extract job info from Cloud Tasks payload
        job_id = request.get("job_id")
        payload = request.get("payload", {})
        
        if not job_id:
            raise HTTPException(status_code=400, detail="Missing job_id")
        
        logger.info(f"Received job from Cloud Tasks: {job_id}")
        
        # Update job status in Redis
        conn = get_redis_conn()
        job_key = f"cs:job:{job_id}"
        
        # Check if job exists
        if not conn.exists(job_key):
            # Create job entry if it doesn't exist
            conn.hset(job_key, mapping={
                "job_id": job_id,
                "state": "PROCESSING",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
        else:
            # Update existing job
            conn.hset(job_key, mapping={
                "state": "PROCESSING",
                "updated_at": datetime.utcnow().isoformat()
            })
        
        # Process in background
        background_tasks.add_task(process_job_background, job_id, payload)
        
        # Return 200 OK for Cloud Tasks
        return {
            "status": "processing_started",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to start job processing: {e}")
        # Return 500 to trigger Cloud Tasks retry
        raise HTTPException(status_code=500, detail=str(e))

async def process_job_background(job_id: str, payload: Dict[str, Any]):
    """Process job in background and update status."""
    conn = get_redis_conn()
    job_key = f"cs:job:{job_id}"

    try:
        logger.info(f"Starting background processing for job: {job_id}")

        # Process the payload
        await _process_payload(job_id, payload)

        # Update job status to completed
        conn.hset(job_key, mapping={
            "state": "COMPLETED",
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        })

        logger.info(f"Successfully completed job: {job_id}")

    except Exception as e:
        logger.error(f"Job processing failed for {job_id}: {e}")

        # Update job status to failed
        conn.hset(job_key, mapping={
            "state": "FAILED",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
            "failed_at": datetime.utcnow().isoformat()
        })

@app.get("/queue-status")
async def get_queue_status():
    """Get current queue status for monitoring."""
    try:
        conn = get_redis_conn()

        # Get queue lengths
        queue_info = {}
        for queue_name in ["cs:queue:short", "cs:queue:long"]:
            try:
                length = conn.llen(queue_name)
                queue_info[queue_name] = length
            except:
                queue_info[queue_name] = 0

        # Get active job count (approximate)
        active_jobs = 0
        try:
            # Count jobs in processing state
            pattern = "cs:job:*"
            for key in conn.scan_iter(pattern):
                state = conn.hget(key, "state")
                if state and state.decode() == "PROCESSING":
                    active_jobs += 1
        except:
            active_jobs = -1  # Error indicator

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "queues": queue_info,
            "active_jobs": active_jobs,
            "redis_available": True
        }

    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "redis_available": False
        }

@app.get("/metrics")
async def get_metrics():
    """Get current metrics in Prometheus format."""
    try:
        metrics, _, _, _ = get_monitoring_components()

        # Collect current metrics
        lines = ["# ClipScribe Worker Metrics"]
        lines.append(f"# Generated at {datetime.utcnow().isoformat()}")

        # System metrics
        metrics.collect_system_metrics()
        for name in ["cpu_usage_percent", "memory_usage_percent", "disk_usage_percent"]:
            value = metrics.get_metric(name)
            if value is not None:
                lines.append(f"clipscribe_{name} {value:.2f}")

        # Application metrics
        metrics.collect_application_metrics(get_redis_conn())
        for name in ["queue_short_length", "queue_long_length", "active_jobs"]:
            value = metrics.get_metric(name)
            if value is not None:
                lines.append(f"clipscribe_{name} {value}")

        return "\n".join(lines) + "\n"

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return f"# Error collecting metrics: {e}\n"

@app.get("/alerts")
async def get_alerts():
    """Get current active alerts."""
    try:
        _, alert_manager, _, _ = get_monitoring_components()
        alerts = alert_manager.get_active_alerts()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_alerts": alerts,
            "total_count": len(alerts)
        }

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "active_alerts": [],
            "total_count": 0
        }

@app.get("/dead-letter-queue")
async def get_dead_letter_queue(limit: int = 10):
    """Get contents of dead letter queue for failed jobs."""
    try:
        _, _, _, retry_manager = get_monitoring_components()
        dead_letters = retry_manager.get_dead_letter_queue(limit)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "dead_letters": dead_letters,
            "total_count": len(dead_letters)
        }

    except Exception as e:
        logger.error(f"Failed to get dead letter queue: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "dead_letters": [],
            "total_count": 0
        }

@app.post("/retry-job")
async def retry_job(job_id: str):
    """Manually retry a failed job from dead letter queue."""
    try:
        _, _, _, retry_manager = get_monitoring_components()

        # Reset retry state for the job
        retry_manager.reset_retry_state(job_id)

        # Get job payload from Redis
        conn = get_redis_conn()
        job_key = f"cs:job:{job_id}"
        payload_str = conn.get(job_key)

        if not payload_str:
            raise HTTPException(status_code=404, detail="Job not found")

        payload = json.loads(payload_str.decode())

        # Reset job state to QUEUED
        conn.hset(job_key, mapping={
            "state": "QUEUED",
            "updated_at": datetime.utcnow().isoformat(),
            "error": None
        })

        logger.info(f"Manually retrying job: {job_id}")

        return {
            "status": "retry_queued",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/warm-up")
async def warm_up(background_tasks: BackgroundTasks):
    """Warm up the worker by loading models and establishing connections."""
    try:
        logger.info("Starting worker warm-up")

        # Run warm-up tasks in background
        background_tasks.add_task(perform_warm_up)

        return {
            "status": "warming_up",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Warm-up failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_warm_up():
    """Perform actual warm-up tasks."""
    try:
        # Load models
        logger.info("Loading ML models...")
        from ..extractors.model_manager import ModelManager
        manager = ModelManager()
        # This will trigger lazy loading of models

        # Test GCS connection
        logger.info("Testing GCS connection...")
        from google.cloud import storage
        client = storage.Client()
        bucket_name = os.getenv("GCS_BUCKET")
        if bucket_name:
            bucket = client.bucket(bucket_name)
            bucket.reload()

        # Test Redis connection
        logger.info("Testing Redis connection...")
        conn = get_redis_conn()
        conn.ping()

        logger.info("Warm-up completed successfully")

    except Exception as e:
        logger.error(f"Warm-up task failed: {e}")

def main():
    """Main entry point for the worker server."""
    import argparse

    parser = argparse.ArgumentParser(description="ClipScribe Worker Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")

    args = parser.parse_args()

    logger.info(f"Starting worker server on {args.host}:{args.port}")

    # Start the server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info"
    )

if __name__ == "__main__":
    main()
