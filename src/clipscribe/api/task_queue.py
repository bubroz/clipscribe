"""
Google Cloud Tasks integration for ClipScribe job queueing.

This module provides a robust queueing system using Google Cloud Tasks,
which handles retries, backoff, and delivery guarantees automatically.

Updated to support Cloud Run Jobs instead of Services for better timeout handling.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from google.cloud import run_v2, tasks_v2
from google.protobuf import duration_pb2, timestamp_pb2

logger = logging.getLogger(__name__)


class TaskQueueManager:
    """Manages job queueing with Google Cloud Tasks and Cloud Run Jobs."""

    def __init__(self):
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
        self.location = os.getenv("TASK_QUEUE_LOCATION", "us-central1")
        self.short_queue = os.getenv("SHORT_VIDEO_QUEUE", "clipscribe-short")
        self.long_queue = os.getenv("LONG_VIDEO_QUEUE", "clipscribe-long")
        self.worker_url = os.getenv(
            "WORKER_URL", "https://clipscribe-worker-16459511304.us-central1.run.app"
        )
        self.vm_worker_url = os.getenv("VM_WORKER_URL", "")  # For future Compute Engine worker

        # Cloud Run Job names
        self.flash_job_name = os.getenv("FLASH_JOB_NAME", "clipscribe-worker-flash")
        self.pro_job_name = os.getenv("PRO_JOB_NAME", "clipscribe-worker-pro")

        try:
            self.client = tasks_v2.CloudTasksClient()
            self.jobs_client = run_v2.JobsClient()
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            self.client = None
            self.jobs_client = None

    def create_queue_if_not_exists(self, queue_name: str) -> bool:
        """Create a Cloud Tasks queue if it doesn't exist."""
        if not self.client:
            return False

        parent = f"projects/{self.project}/locations/{self.location}"
        queue_path = f"{parent}/queues/{queue_name}"

        try:
            # Check if queue exists
            self.client.get_queue(request={"name": queue_path})
            return True
        except Exception:
            # Queue doesn't exist, create it
            try:
                queue = tasks_v2.Queue(
                    name=queue_path,
                    rate_limits=tasks_v2.RateLimits(
                        max_dispatches_per_second=10,
                        max_concurrent_dispatches=100,
                    ),
                    retry_config=tasks_v2.RetryConfig(
                        max_attempts=5,
                        min_backoff=duration_pb2.Duration(seconds=10),
                        max_backoff=duration_pb2.Duration(seconds=300),
                        max_doublings=3,
                    ),
                )
                self.client.create_queue(request={"parent": parent, "queue": queue})
                logger.info(f"Created queue: {queue_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to create queue {queue_name}: {e}")
                return False

    def trigger_cloud_run_job(
        self, job_id: str, payload: Dict[str, Any], use_pro_model: bool = False
    ) -> Optional[str]:
        """
        Trigger a Cloud Run Job to process the video.

        Args:
            job_id: Unique job identifier
            payload: Job payload data
            use_pro_model: Whether to use Pro model (True) or Flash (False)

        Returns:
            Execution name if successful, None otherwise
        """
        if not self.jobs_client:
            logger.error("Cloud Run Jobs client not initialized")
            return None

        try:
            # Select the appropriate job
            job_name = self.pro_job_name if use_pro_model else self.flash_job_name

            # Full job resource name
            job_resource = f"projects/{self.project}/locations/{self.location}/jobs/{job_name}"

            logger.info(f"Triggering Cloud Run Job: {job_resource}")
            logger.info(f"Job ID: {job_id}, Payload: {json.dumps(payload)[:200]}...")

            # Build overrides with environment variables
            container_override = run_v2.RunJobRequest.Overrides.ContainerOverride(
                env=[
                    run_v2.EnvVar(name="JOB_ID", value=job_id),
                    run_v2.EnvVar(name="JOB_PAYLOAD", value=json.dumps(payload)),
                    run_v2.EnvVar(name="JOB_SOURCE", value="task"),
                ],
                args=["--job-source", "task"],
            )

            overrides = run_v2.RunJobRequest.Overrides(
                container_overrides=[container_override],
            )

            # Create execution request
            request = run_v2.RunJobRequest(
                name=job_resource,
                overrides=overrides,
            )

            # Execute the job - this returns an Operation (LRO)
            operation = self.jobs_client.run_job(request=request)

            # Get execution identifier from the operation
            # The Operation object has .name directly for the operation resource name
            # We also check .metadata for execution details
            if hasattr(operation, "name") and operation.name:
                execution_name = operation.name
            elif hasattr(operation, "metadata") and hasattr(operation.metadata, "name"):
                execution_name = operation.metadata.name
            else:
                execution_name = f"job-{job_id}"  # Fallback identifier

            logger.info(f"Triggered Cloud Run Job execution: {execution_name}")
            logger.info(f"Job: {job_name}, Model: {'Pro' if use_pro_model else 'Flash'}")

            return execution_name

        except Exception as e:
            import traceback

            logger.error(f"Failed to trigger Cloud Run Job: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return None

    def enqueue_job(
        self,
        job_id: str,
        payload: Dict[str, Any],
        estimated_duration: int = 0,
        delay_seconds: int = 0,
        use_pro_model: bool = False,
    ) -> Optional[str]:
        """
        Enqueue a job to the appropriate Cloud Tasks queue or trigger Cloud Run Job.

        Args:
            job_id: Unique job identifier
            payload: Job payload data
            estimated_duration: Estimated video duration in seconds
            delay_seconds: Delay before processing (for rate limiting)
            use_pro_model: Whether to use Pro model (True) or Flash (False)

        Returns:
            Task name or execution name if successful, None otherwise
        """
        # Check if we should use Cloud Run Jobs (preferred for long videos)
        use_cloud_run_jobs = os.getenv("USE_CLOUD_RUN_JOBS", "true").lower() == "true"

        if use_cloud_run_jobs:
            # Use Cloud Run Jobs for better timeout handling
            return self.trigger_cloud_run_job(job_id, payload, use_pro_model)

        # Fallback to HTTP tasks (legacy mode)
        if not self.client:
            logger.error("Cloud Tasks client not initialized")
            return None

        # Determine which queue to use based on duration
        if estimated_duration > 2700:  # >45 minutes
            queue_name = self.long_queue
            target_url = self.vm_worker_url or self.worker_url
        else:
            queue_name = self.short_queue
            target_url = self.worker_url

        # Ensure queue exists
        if not self.create_queue_if_not_exists(queue_name):
            return None

        # Create task
        parent = self.client.queue_path(self.project, self.location, queue_name)

        task = tasks_v2.Task(
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"{target_url}/process-job",
                headers={
                    "Content-Type": "application/json",
                    "X-CloudTasks-TaskName": job_id,
                },
                body=json.dumps(
                    {
                        "job_id": job_id,
                        "payload": payload,
                        "enqueued_at": datetime.utcnow().isoformat(),
                    }
                ).encode(),
            ),
        )

        # Set task name for idempotency
        task.name = f"{parent}/tasks/{job_id}"

        # Add delay if specified
        if delay_seconds > 0:
            scheduled_time = timestamp_pb2.Timestamp()
            scheduled_time.FromDatetime(datetime.utcnow() + timedelta(seconds=delay_seconds))
            task.schedule_time = scheduled_time

        try:
            response = self.client.create_task(
                request={
                    "parent": parent,
                    "task": task,
                }
            )
            logger.info(f"Created task: {response.name}")
            return response.name
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Task {job_id} already exists")
                return f"{parent}/tasks/{job_id}"
            logger.error(f"Failed to create task: {e}")
            return None

    def delete_task(self, task_name: str) -> bool:
        """Delete a task from the queue."""
        if not self.client:
            return False

        try:
            self.client.delete_task(request={"name": task_name})
            logger.info(f"Deleted task: {task_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            return False

    def pause_queue(self, queue_name: str) -> bool:
        """Pause a queue to stop processing."""
        if not self.client:
            return False

        queue_path = self.client.queue_path(self.project, self.location, queue_name)

        try:
            queue = self.client.get_queue(request={"name": queue_path})
            queue.state = tasks_v2.Queue.State.PAUSED
            self.client.update_queue(request={"queue": queue})
            logger.info(f"Paused queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause queue: {e}")
            return False

    def resume_queue(self, queue_name: str) -> bool:
        """Resume a paused queue."""
        if not self.client:
            return False

        queue_path = self.client.queue_path(self.project, self.location, queue_name)

        try:
            queue = self.client.get_queue(request={"name": queue_path})
            queue.state = tasks_v2.Queue.State.RUNNING
            self.client.update_queue(request={"queue": queue})
            logger.info(f"Resumed queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume queue: {e}")
            return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues."""
        if not self.client:
            return {"error": "Client not initialized"}

        stats = {}
        for queue_name in [self.short_queue, self.long_queue]:
            try:
                queue_path = self.client.queue_path(self.project, self.location, queue_name)
                queue = self.client.get_queue(request={"name": queue_path})

                # List tasks to get count
                tasks = list(self.client.list_tasks(request={"parent": queue_path}))

                stats[queue_name] = {
                    "state": queue.state.name,
                    "task_count": len(tasks),
                    "rate_limits": {
                        "max_dispatches_per_second": queue.rate_limits.max_dispatches_per_second,
                        "max_concurrent_dispatches": queue.rate_limits.max_concurrent_dispatches,
                    },
                }
            except Exception as e:
                stats[queue_name] = {"error": str(e)}

        return stats


# Singleton instance
_task_queue_manager = None


def get_task_queue_manager() -> TaskQueueManager:
    """Get the singleton TaskQueueManager instance."""
    global _task_queue_manager
    if _task_queue_manager is None:
        _task_queue_manager = TaskQueueManager()
    return _task_queue_manager
