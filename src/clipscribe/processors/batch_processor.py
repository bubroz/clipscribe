#!/usr/bin/env python3
"""
ClipScribe Batch Processor

Handles parallel processing of multiple videos with intelligent job queuing,
resource management, and comprehensive error recovery.

Key Features:
- Parallel video processing with configurable concurrency
- Job queuing and status tracking
- Resource optimization (memory, API calls)
- Comprehensive error handling and recovery
- Progress monitoring and reporting
"""

import asyncio
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Gemini removed - using Voxtral-Grok pipeline
from ..retrievers.universal_video_client import UniversalVideoClient

logger = logging.getLogger(__name__)


class BatchJobStatus(Enum):
    """Batch job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


class ProcessingPriority(Enum):
    """Processing priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BatchJob:
    """Represents a single video processing job within a batch."""

    job_id: str
    video_url: str
    priority: ProcessingPriority
    status: BatchJobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    processing_time: Optional[float] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to strings
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        # Convert datetime objects to ISO strings
        data["created_at"] = self.created_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchJob":
        """Create job from dictionary."""
        # Convert strings back to enums
        data["priority"] = ProcessingPriority(data["priority"])
        data["status"] = BatchJobStatus(data["status"])
        # Convert ISO strings back to datetime
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


@dataclass
class BatchResult:
    """Results summary for a completed batch."""

    batch_id: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_processing_time: float
    average_processing_time: float
    total_cost: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    output_directory: str = ""
    jobs: List[BatchJob] = None

    def __post_init__(self):
        if self.jobs is None:
            self.jobs = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        data["jobs"] = [job.to_dict() for job in self.jobs]
        return data


class BatchProcessor:
    """
    Main batch processor for handling multiple video processing jobs.

    Features:
    - Configurable concurrency limits
    - Priority-based job scheduling
    - Resource monitoring and optimization
    - Comprehensive error handling and recovery
    - Progress tracking and reporting
    """

    def __init__(
        self,
        max_concurrent_jobs: int = 5,
        output_dir: str = "output/batch",
        enable_caching: bool = True,
        retry_failed_jobs: bool = True,
    ):
        """
        Initialize the batch processor.

        Args:
            max_concurrent_jobs: Maximum number of jobs to process concurrently
            output_dir: Base directory for batch outputs
            enable_caching: Whether to enable video caching
            retry_failed_jobs: Whether to retry failed jobs automatically
        """
        # Create output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        # Transcriber removed - using Voxtral-Grok pipeline
        self.transcriber = None
        self.video_client = UniversalVideoClient()

        # Job management
        self.active_jobs: Dict[str, BatchJob] = {}
        self.completed_jobs: List[BatchJob] = []
        self.failed_jobs: List[BatchJob] = []

        # Resource management
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)

        logger.info(f"Initialized BatchProcessor with max_concurrent_jobs={max_concurrent_jobs}")

    async def process_batch(
        self,
        video_urls: List[str],
        batch_id: Optional[str] = None,
        priority: ProcessingPriority = ProcessingPriority.NORMAL,
    ) -> BatchResult:
        """
        Process a batch of video URLs.

        Args:
            video_urls: List of video URLs to process
            batch_id: Optional batch identifier (auto-generated if not provided)
            priority: Processing priority for all jobs in this batch

        Returns:
            BatchResult: Comprehensive results summary
        """
        if not batch_id:
            batch_id = f"batch_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting batch processing: {batch_id} with {len(video_urls)} videos")

        # Create batch directory
        batch_dir = self.output_dir / batch_id
        batch_dir.mkdir(exist_ok=True)

        # Create jobs
        jobs = []
        for url in video_urls:
            job = BatchJob(
                job_id=f"{batch_id}_job_{uuid.uuid4().hex[:6]}",
                video_url=url,
                priority=priority,
                status=BatchJobStatus.PENDING,
                created_at=datetime.now(),
                metadata={"batch_id": batch_id},
            )
            jobs.append(job)

        # Initialize result tracking
        start_time = time.time()
        result = BatchResult(
            batch_id=batch_id,
            total_jobs=len(jobs),
            completed_jobs=0,
            failed_jobs=0,
            total_processing_time=0.0,
            average_processing_time=0.0,
            total_cost=0.0,
            created_at=datetime.now(),
            output_directory=str(batch_dir),
            jobs=jobs,
        )

        # Save initial batch status
        self._save_batch_status(result)

        try:
            # Process jobs with controlled concurrency
            tasks = []
            for job in jobs:
                task = asyncio.create_task(self._process_single_job(job, batch_dir))
                tasks.append(task)

            # Wait for all jobs to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            # Update final results
            result.completed_at = datetime.now()
            result.total_processing_time = time.time() - start_time

            # Calculate final statistics
            completed_jobs = [j for j in jobs if j.status == BatchJobStatus.COMPLETED]
            failed_jobs = [j for j in jobs if j.status == BatchJobStatus.FAILED]

            result.completed_jobs = len(completed_jobs)
            result.failed_jobs = len(failed_jobs)
            result.total_cost = sum(j.metadata.get("cost", 0) for j in completed_jobs if j.metadata)

            if completed_jobs:
                processing_times = [j.processing_time for j in completed_jobs if j.processing_time]
                if processing_times:
                    result.average_processing_time = sum(processing_times) / len(processing_times)

            # Save final results
            self._save_batch_results(result)

            logger.info(
                f"Batch {batch_id} completed: {result.completed_jobs}/{result.total_jobs} successful"
            )

            return result

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            result.completed_at = datetime.now()
            result.failed_jobs = len(jobs)  # Assume all failed if we crash
            self._save_batch_results(result)
            raise

    async def _process_single_job(self, job: BatchJob, batch_dir: Path) -> None:
        """
        Process a single video job with error handling and retries.

        Args:
            job: The job to process
            batch_dir: Directory to save job outputs
        """
        async with self.semaphore:
            job.started_at = datetime.now()
            job.status = BatchJobStatus.RUNNING

            try:
                logger.info(f"Processing job {job.job_id}: {job.video_url}")

                # Create job-specific output directory
                job_output_dir = batch_dir / job.job_id
                job_output_dir.mkdir(exist_ok=True)

                # Process the video
                start_time = time.time()

                # Download video
                logger.info(f"Downloading audio for job {job.job_id}")
                audio_path, metadata = await self.video_client.download_audio(job.video_url)

                if not audio_path or not Path(audio_path).exists():
                    raise Exception(f"Failed to download audio for {job.video_url}")

                # Process with transcriber
                logger.info(f"Analyzing content for job {job.job_id}")
                duration = getattr(metadata, "duration", 0)
                result = await self.transcriber.transcribe_audio(
                    audio_file=str(audio_path), duration=int(duration)
                )

                # Save results
                logger.info(f"Saving results for job {job.job_id}")

                # Save individual job results
                job_output_path = job_output_dir / "results.json"
                with open(job_output_path, "w") as f:
                    json.dump(result, f, indent=2, default=str)

                # Update job metadata
                processing_time = time.time() - start_time
                job.processing_time = processing_time
                job.completed_at = datetime.now()
                job.status = BatchJobStatus.COMPLETED
                job.output_path = str(job_output_path)
                job.metadata = {
                    "cost": result.get("processing_cost", 0),
                    "entity_count": len(result.get("entities", [])),
                    "relationship_count": len(result.get("relationships", [])),
                    "transcript_length": len(result.get("transcript", "")),
                }

                logger.info(f"Job {job.job_id} completed successfully in {processing_time:.2f}s")

            except Exception as e:
                logger.error(f"Job {job.job_id} failed: {e}")
                job.error_message = str(e)
                job.retry_count += 1

                # Check if we should retry
                if self.retry_failed_jobs and job.retry_count < job.max_retries:
                    logger.info(
                        f"Retrying job {job.job_id} (attempt {job.retry_count + 1}/{job.max_retries})"
                    )
                    job.status = BatchJobStatus.PENDING
                    # Add back to queue with delay
                    await asyncio.sleep(2**job.retry_count)  # Exponential backoff
                    await self._process_single_job(job, batch_dir)
                else:
                    job.status = BatchJobStatus.FAILED
                    job.completed_at = datetime.now()

    def _save_batch_status(self, result: BatchResult) -> None:
        """Save current batch status to file."""
        status_file = self.output_dir / result.batch_id / "batch_status.json"
        with open(status_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

    def _save_batch_results(self, result: BatchResult) -> None:
        """Save final batch results to file."""
        results_file = self.output_dir / result.batch_id / "batch_results.json"
        with open(results_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

    async def get_batch_status(self, batch_id: str) -> Optional[BatchResult]:
        """Get the current status of a batch."""
        status_file = self.output_dir / batch_id / "batch_status.json"
        if status_file.exists():
            with open(status_file, "r") as f:
                data = json.load(f)
            return BatchResult(**data)
        return None

    async def get_batch_results(self, batch_id: str) -> Optional[BatchResult]:
        """Get the final results of a completed batch."""
        results_file = self.output_dir / batch_id / "batch_results.json"
        if results_file.exists():
            with open(results_file, "r") as f:
                data = json.load(f)
            return BatchResult(**data)
        return None

    def cleanup_old_batches(self, days_old: int = 30) -> int:
        """Clean up batches older than specified days."""
        cleaned_count = 0
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)

        for batch_dir in self.output_dir.iterdir():
            if batch_dir.is_dir():
                # Check if directory is old enough
                if batch_dir.stat().st_mtime < cutoff_time:
                    import shutil

                    shutil.rmtree(batch_dir)
                    cleaned_count += 1
                    logger.info(f"Cleaned up old batch: {batch_dir.name}")

        return cleaned_count
