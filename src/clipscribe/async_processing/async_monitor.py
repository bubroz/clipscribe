"""
Async monitor orchestrator for non-blocking video processing.

Coordinates monitor, queue, and worker pool.
"""

import asyncio
import logging
from typing import List, Optional
from pathlib import Path

from .video_queue import AsyncVideoQueue
from .worker_pool import VideoWorkerPool
from ..monitors.channel_monitor import ChannelMonitor

logger = logging.getLogger(__name__)


class AsyncMonitorOrchestrator:
    """
    Orchestrate async video monitoring and processing.
    
    Components:
    - Channel monitor (RSS detection)
    - Video queue (task management)
    - Worker pool (concurrent processing)
    """
    
    def __init__(
        self,
        channel_ids: List[str],
        max_workers: int = 10,
        output_dir: str = "output/monitored"
    ):
        """
        Initialize orchestrator.
        
        Args:
            channel_ids: YouTube channel IDs to monitor
            max_workers: Number of concurrent workers (default: 10)
            output_dir: Output directory for processed videos
        """
        self.channel_ids = channel_ids
        self.max_workers = max_workers
        self.output_dir = output_dir
        
        # Initialize components
        self.video_queue = AsyncVideoQueue(max_size=100)
        self.worker_pool = VideoWorkerPool(
            max_workers=max_workers,
            output_dir=output_dir
        )
        self.channel_monitor = ChannelMonitor(channel_ids)
        
        self.running = False
        
        logger.info(f"AsyncMonitorOrchestrator initialized: {len(channel_ids)} channels, {max_workers} workers")
    
    async def start(self, check_interval: int = 60):
        """
        Start async monitoring and processing.
        
        Args:
            check_interval: Seconds between RSS checks (default: 60)
        """
        logger.info("🚀 Starting Async Monitor Orchestrator")
        self.running = True
        
        # Start worker pool
        await self.worker_pool.start(self.video_queue)
        
        # Start monitor loop
        logger.info(f"📡 Starting monitor loop: checking every {check_interval}s")
        
        try:
            while self.running:
                try:
                    # Check for new videos (non-blocking)
                    new_videos = await self.channel_monitor.check_for_new_videos()
                    
                    # Queue new videos (instant)
                    for video in new_videos:
                        await self.video_queue.enqueue(video, priority=0)
                        logger.info(f"🆕 Queued: {video['title']}")
                    
                    # Log status
                    status = self.get_status()
                    logger.info(
                        f"📊 Status: queue={status['queue_size']}, "
                        f"processing={status['processing']}, "
                        f"completed={status['completed']}, "
                        f"failed={status['failed']}"
                    )
                    
                    # Wait for next check
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"Monitor loop error: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
                    
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop orchestrator gracefully."""
        logger.info("Stopping orchestrator...")
        self.running = False
        
        # Stop worker pool
        await self.worker_pool.stop()
        
        logger.info("Orchestrator stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        queue_status = self.video_queue.get_status()
        
        return {
            'queue_size': queue_status['queue_size'],
            'processing': queue_status['processing'],
            'completed': queue_status['completed'],
            'failed': queue_status['failed'],
            'workers': len(self.worker_pool.workers),
            'channels': len(self.channel_ids)
        }

