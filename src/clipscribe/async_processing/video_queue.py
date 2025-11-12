"""
Async video queue for non-blocking processing.

Separates video detection from processing, enabling concurrent workers.
"""

import asyncio
import logging
from asyncio import PriorityQueue
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass(order=True)
class VideoTask:
    """Video processing task."""

    priority: int = field(compare=True)
    video_info: Dict[str, Any] = field(compare=False)
    queued_at: datetime = field(default_factory=datetime.now, compare=False)
    retry_count: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)


class AsyncVideoQueue:
    """
    Async queue for video processing tasks.

    Features:
    - Priority-based ordering
    - Concurrent access
    - Status tracking
    - Retry management
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize async video queue.

        Args:
            max_size: Maximum queue size (prevents memory issues)
        """
        self.queue = PriorityQueue(maxsize=max_size)
        self.processing = {}  # video_id -> task
        self.completed = {}  # video_id -> result
        self.failed = {}  # video_id -> error

        logger.info(f"AsyncVideoQueue initialized: max_size={max_size}")

    async def enqueue(self, video_info: Dict[str, Any], priority: int = 0):
        """
        Add video to processing queue.

        Args:
            video_info: Video metadata (url, title, etc.)
            priority: Priority level (0=normal, negative=high, positive=low)
        """
        task = VideoTask(priority=priority, video_info=video_info)

        await self.queue.put(task)
        logger.info(f"Queued video ({priority=}): {video_info.get('title', 'Unknown')}")

    async def dequeue(self) -> VideoTask:
        """
        Get next video for processing.

        Blocks if queue is empty.
        Returns highest priority task first.
        """
        task = await self.queue.get()
        return task

    def mark_processing(self, video_id: str, task: VideoTask):
        """Mark video as being processed."""
        self.processing[video_id] = task
        logger.debug(f"Marked as processing: {video_id}")

    def mark_completed(self, video_id: str, result: Any):
        """Mark video as completed."""
        if video_id in self.processing:
            del self.processing[video_id]
        self.completed[video_id] = result
        logger.info(f"Marked as completed: {video_id}")

    def mark_failed(self, video_id: str, error: Exception):
        """Mark video as failed."""
        if video_id in self.processing:
            task = self.processing[video_id]
            del self.processing[video_id]

            # Retry if under max retries
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                asyncio.create_task(self.queue.put(task))
                logger.warning(
                    f"Requeuing {video_id} (retry {task.retry_count}/{task.max_retries})"
                )
            else:
                self.failed[video_id] = error
                logger.error(f"Marked as failed: {video_id}")

    def get_status(self) -> Dict[str, Any]:
        """Get queue status."""
        return {
            "queue_size": self.queue.qsize(),
            "processing": len(self.processing),
            "completed": len(self.completed),
            "failed": len(self.failed),
        }
