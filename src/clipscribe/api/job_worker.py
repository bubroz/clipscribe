#!/usr/bin/env python3
"""
Cloud Run Job Worker for ClipScribe.

This worker runs as a Cloud Run Job, processing video intelligence extraction
tasks without the timeout limitations of Cloud Run Services.

Cloud Run Jobs provide:
- 24-hour timeout (vs 60 minutes for Services)
- Full CPU allocation throughout execution (no throttling)
- Automatic retry on failure
- Cost-effective for long-running tasks
"""

import os
import sys
import json
import asyncio
import logging
import tempfile
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import argparse

import redis
from google.cloud import storage
from google.cloud import tasks_v2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = Path(os.getenv("VIDEO_CACHE_DIR", "/tmp/clipscribe_cache"))
CACHE_MAX_SIZE_GB = int(os.getenv("CACHE_MAX_SIZE_GB", "50"))
CACHE_MAX_AGE_DAYS = int(os.getenv("CACHE_MAX_AGE_DAYS", "7"))


class VideoCache:
    """Manages local video cache to avoid re-downloading."""
    
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Video cache initialized at: {self.cache_dir}")
    
    def get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL."""
        cache_key = self.get_cache_key(url)
        return self.cache_dir / f"{cache_key}.mp4"
    
    def exists(self, url: str) -> bool:
        """Check if video is cached."""
        cache_path = self.get_cache_path(url)
        if cache_path.exists():
            # Check age
            age_days = (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).days
            if age_days <= CACHE_MAX_AGE_DAYS:
                return True
            else:
                logger.info(f"Cache expired for {url} ({age_days} days old)")
                cache_path.unlink()
        return False
    
    def get(self, url: str) -> Optional[Path]:
        """Get cached video path if exists."""
        if self.exists(url):
            return self.get_cache_path(url)
        return None
    
    def put(self, url: str, video_path: Path) -> Path:
        """Store video in cache."""
        cache_path = self.get_cache_path(url)
        try:
            shutil.copy2(video_path, cache_path)
            logger.info(f"Cached video for {url} at {cache_path}")
            self.cleanup_if_needed()
            return cache_path
        except Exception as e:
            logger.error(f"Failed to cache video: {e}")
            return video_path
    
    def cleanup_if_needed(self):
        """Clean up old cache files if size exceeds limit."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.mp4"))
        max_size = CACHE_MAX_SIZE_GB * 1024 * 1024 * 1024
        
        if total_size > max_size:
            # Sort by modification time (oldest first)
            files = sorted(
                self.cache_dir.glob("*.mp4"),
                key=lambda f: f.stat().st_mtime
            )
            
            # Remove oldest files until under limit
            for f in files:
                if total_size <= max_size:
                    break
                size = f.stat().st_size
                f.unlink()
                total_size -= size
                logger.info(f"Removed old cache file: {f.name}")


class CloudRunJobWorker:
    """Worker for processing ClipScribe jobs in Cloud Run Jobs."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.gcs_bucket = os.getenv("GCS_BUCKET", "clipscribe-outputs")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "prismatic-iris-429006-g6")
        self.location = os.getenv("TASK_QUEUE_LOCATION", "us-central1")
        
        # Model selection - Voxtral + Grok pipeline
        self.model_name = "voxtral-grok-pipeline"

        # Initialize connections
        self.redis_conn = redis.from_url(self.redis_url)
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        self.tasks_client = tasks_v2.CloudTasksClient()

        # Initialize cache
        self.cache = VideoCache()

        logger.info(f"Worker initialized with model: {self.model_name}")
    
    async def process_job(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single job.
        
        Args:
            job_id: Unique job identifier
            payload: Job payload with URL and options
            
        Returns:
            Job result with artifacts
        """
        start_time = datetime.utcnow()
        result = {
            "job_id": job_id,
            "status": "processing",
            "started_at": start_time.isoformat(),
            "model": self.model_name,
            "artifacts": []
        }
        
        try:
            # Update job status
            self.update_job_status(job_id, "PROCESSING", {"model": self.model_name})
            
            # Extract URL from payload
            url = payload.get("url")
            if not url:
                raise ValueError("No URL provided in payload")
            
            logger.info(f"Processing job {job_id}: {url}")
            
            # Check cache first
            cached_video = self.cache.get(url)
            
            if cached_video:
                logger.info(f"Using cached video for {url}")
                video_path = cached_video
                metadata = self.get_cached_metadata(url)
            else:
                # Download video
                logger.info(f"Downloading video: {url}")
                video_path, metadata = await self.download_video(url)
                
                # Cache the video
                self.cache.put(url, video_path)
                self.save_metadata_to_cache(url, metadata)
            
            # Process with selected model
            logger.info(f"Processing with {self.model_name}")
            analysis_result = await self.process_video(video_path, metadata)
            
            # Upload results to GCS
            logger.info("Uploading results to GCS")
            artifacts = await self.upload_results(job_id, analysis_result)
            
            # Update result
            result["status"] = "completed"
            result["completed_at"] = datetime.utcnow().isoformat()
            result["artifacts"] = artifacts
            result["processing_time_seconds"] = (
                datetime.utcnow() - start_time
            ).total_seconds()
            result["cost_estimate"] = self.calculate_cost(metadata.get("duration", 0))
            
            # Update job status
            self.update_job_status(job_id, "COMPLETED", result)
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["failed_at"] = datetime.utcnow().isoformat()
            
            # Update job status
            self.update_job_status(job_id, "FAILED", {"error": str(e)})
            
            raise
        
        return result
    
    async def download_video(self, url: str) -> Tuple[Path, Dict[str, Any]]:
        """Download video and extract metadata."""
        from clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
        
        client = EnhancedUniversalVideoClient()
        tmpdir = tempfile.mkdtemp()
        
        try:
            # Download audio/video
            media_path, metadata = await client.download_audio(url, output_dir=tmpdir)
            
            # Convert metadata to dict
            metadata_dict = {
                "title": getattr(metadata, "title", "Unknown"),
                "duration": int(getattr(metadata, "duration", 0) or 0),
                "uploader": getattr(metadata, "uploader", "Unknown"),
                "description": getattr(metadata, "description", ""),
                "upload_date": getattr(metadata, "upload_date", ""),
                "view_count": getattr(metadata, "view_count", 0),
            }
            
            return Path(media_path), metadata_dict
            
        except Exception as e:
            # Cleanup on failure
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise
    
    async def process_video(
        self,
        video_path: Path,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process video with Voxtral-Grok pipeline."""
        from clipscribe.retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2

        # Use the main CLI pipeline
        retriever = VideoIntelligenceRetrieverV2()
        result = await retriever.process_url(metadata.get("url", ""))

        if result:
            # Convert to expected format
            analysis = {
                "transcript": result.transcript.raw_text if hasattr(result.transcript, 'raw_text') else str(result.transcript),
                "entities": [entity.dict() if hasattr(entity, 'dict') else entity for entity in (result.entities or [])],
                "relationships": [rel.dict() if hasattr(rel, 'dict') else rel for rel in (result.relationships or [])],
                "metadata": metadata,
                "model_used": self.model_name,
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            return analysis
        else:
            raise ValueError("Failed to process video with Voxtral-Grok pipeline")
    
    async def upload_results(
        self, 
        job_id: str, 
        analysis: Dict[str, Any]
    ) -> list:
        """Upload analysis results to GCS."""
        artifacts = []
        
        # Create job folder
        job_folder = f"jobs/{job_id}"
        
        # Upload main analysis JSON
        analysis_blob = self.bucket.blob(f"{job_folder}/analysis.json")
        analysis_blob.upload_from_string(
            json.dumps(analysis, indent=2),
            content_type="application/json"
        )
        artifacts.append({
            "type": "analysis",
            "path": f"gs://{self.gcs_bucket}/{job_folder}/analysis.json",
            "content_type": "application/json"
        })
        
        # Extract and upload individual components
        components = [
            ("transcript", analysis.get("transcript", {})),
            ("entities", {"entities": analysis.get("entities", [])}),
            ("relationships", {"relationships": analysis.get("relationships", [])}),
            ("metadata", analysis.get("metadata", {}))
        ]
        
        for name, data in components:
            if data:
                blob = self.bucket.blob(f"{job_folder}/{name}.json")
                blob.upload_from_string(
                    json.dumps(data, indent=2),
                    content_type="application/json"
                )
                artifacts.append({
                    "type": name,
                    "path": f"gs://{self.gcs_bucket}/{job_folder}/{name}.json",
                    "content_type": "application/json"
                })
        
        logger.info(f"Uploaded {len(artifacts)} artifacts for job {job_id}")
        return artifacts
    
    def update_job_status(
        self, 
        job_id: str, 
        status: str, 
        data: Dict[str, Any] = None
    ):
        """Update job status in Redis."""
        job_key = f"cs:job:{job_id}"
        
        job_data = {
            "job_id": job_id,
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        if data:
            job_data.update(data)
        
        self.redis_conn.set(job_key, json.dumps(job_data))
        
        # Set expiry (7 days)
        self.redis_conn.expire(job_key, 7 * 24 * 60 * 60)
    
    def calculate_cost(self, duration_seconds: int) -> float:
        """Calculate processing cost based on Voxtral + Grok pricing."""
        duration_minutes = duration_seconds / 60

        # Voxtral + Grok pricing
        # Voxtral: ~$0.015 per video + $0.002 per minute
        # Grok: ~$0.008 per video + $0.001 per minute
        base_cost = 0.023  # Base cost for both services
        per_minute_cost = 0.003  # Combined per-minute cost

        return round(base_cost + (duration_minutes * per_minute_cost), 4)
    
    def get_cached_metadata(self, url: str) -> Dict[str, Any]:
        """Get cached metadata for URL."""
        cache_key = self.cache.get_cache_key(url)
        metadata_path = self.cache.cache_dir / f"{cache_key}.metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path) as f:
                return json.load(f)
        
        return {}
    
    def save_metadata_to_cache(self, url: str, metadata: Dict[str, Any]):
        """Save metadata to cache."""
        cache_key = self.cache.get_cache_key(url)
        metadata_path = self.cache.cache_dir / f"{cache_key}.metadata.json"
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    async def run(self, job_source: str = "queue"):
        """
        Main run loop for the worker.
        
        Args:
            job_source: Where to get jobs from ("queue", "task", or job_id)
        """
        logger.info(f"Worker starting with job source: {job_source}")
        
        if job_source == "queue":
            # Process jobs from Redis queue
            await self.process_queue()
        elif job_source == "task":
            # Process single job from Cloud Tasks (via environment)
            job_id = os.getenv("JOB_ID")
            payload_str = os.getenv("JOB_PAYLOAD", "{}")
            
            if not job_id:
                raise ValueError("JOB_ID environment variable not set")
            
            payload = json.loads(payload_str)
            await self.process_job(job_id, payload)
        else:
            # Process specific job by ID
            job_key = f"cs:job:{job_source}"
            job_data = self.redis_conn.get(job_key)
            
            if not job_data:
                raise ValueError(f"Job {job_source} not found")
            
            job_info = json.loads(job_data)
            await self.process_job(job_source, job_info.get("payload", {}))
    
    async def process_queue(self):
        """Process jobs from Redis queue continuously."""
        queue_names = ["cs:queue:short", "cs:queue:long"]
        
        while True:
            job_found = False
            
            for queue_name in queue_names:
                # Pop job from queue
                job_data = self.redis_conn.lpop(queue_name)
                
                if job_data:
                    job_found = True
                    try:
                        job_info = json.loads(job_data)
                        job_id = job_info.get("job_id")
                        payload = job_info.get("payload", {})
                        
                        logger.info(f"Processing job from {queue_name}: {job_id}")
                        await self.process_job(job_id, payload)
                        
                    except Exception as e:
                        logger.error(f"Failed to process job: {e}")
                        # Could implement retry logic here
            
            if not job_found:
                # No jobs available, wait a bit
                await asyncio.sleep(5)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ClipScribe Cloud Run Job Worker")
    parser.add_argument(
        "--job-source",
        default="queue",
        help="Job source: 'queue', 'task', or specific job_id"
    )
    parser.add_argument(
        "--use-pro",
        action="store_true",
        help="Legacy option - no longer used (Voxtral-Grok pipeline)"
    )
    
    args = parser.parse_args()
    
    # Override model selection if specified
    if args.use_pro:
        os.environ["USE_PRO_MODEL"] = "true"
    
    # Create and run worker
    worker = CloudRunJobWorker()
    await worker.run(args.job_source)


if __name__ == "__main__":
    asyncio.run(main())
