"""
Worker pool for concurrent video processing.

Manages multiple workers processing videos from the queue.
"""

import asyncio
import logging
from typing import Optional, Callable, List, Any, Dict
from pathlib import Path

from .video_queue import AsyncVideoQueue, VideoTask
from ..retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2

logger = logging.getLogger(__name__)


class VideoWorkerPool:
    """
    Pool of workers for concurrent video processing.
    
    Features:
    - Configurable worker count
    - Concurrent processing with resource limits
    - Automatic error handling
    - Worker health monitoring
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        output_dir: str = "output/monitored"
    ):
        """
        Initialize worker pool.
        
        Args:
            max_workers: Number of concurrent workers (default: 10)
            output_dir: Output directory for processed videos
        """
        self.max_workers = max_workers
        self.output_dir = output_dir
        self.workers = []
        self.video_queue: Optional[AsyncVideoQueue] = None
        self.running = False
        
        # Semaphore to limit concurrency
        self.semaphore = asyncio.Semaphore(max_workers)
        
        logger.info(f"VideoWorkerPool initialized: {max_workers} workers")
    
    async def start(self, video_queue: AsyncVideoQueue):
        """
        Start worker pool.
        
        Args:
            video_queue: Video queue to process from
        """
        self.running = True
        self.video_queue = video_queue
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} video workers")
    
    async def stop(self):
        """Stop worker pool gracefully."""
        logger.info("Stopping worker pool...")
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Worker pool stopped")
    
    async def _worker(self, worker_name: str):
        """
        Worker task that processes videos from queue.
        
        Args:
            worker_name: Worker identifier
        """
        logger.info(f"{worker_name} started")
        
        while self.running:
            try:
                # Get next video task from queue
                task = await self.video_queue.dequeue()
                video_info = task.video_info
                video_id = video_info['video_id']
                
                logger.info(f"{worker_name} processing: {video_info['title']}")
                
                # Mark as processing
                self.video_queue.mark_processing(video_id, task)
                
                # Process with semaphore (limit concurrency)
                async with self.semaphore:
                    result = await self._process_video(worker_name, task)
                    
                    if result:
                        self.video_queue.mark_completed(video_id, result)
                        logger.info(f"{worker_name} ✅ Completed: {video_info['title']}")
                    else:
                        self.video_queue.mark_failed(video_id, Exception("Processing failed"))
                        logger.error(f"{worker_name} ❌ Failed: {video_info['title']}")
                
            except asyncio.CancelledError:
                logger.info(f"{worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"{worker_name} error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
        
        logger.info(f"{worker_name} stopped")
    
    async def _process_video(self, worker_name: str, task: VideoTask) -> Optional[Any]:
        """
        Process a single video.
        
        Args:
            worker_name: Worker identifier
            task: Video task to process
            
        Returns:
            Processing result or None if failed
        """
        video_info = task.video_info
        
        try:
            # Create retriever instance for this worker
            retriever = VideoIntelligenceRetrieverV2(output_dir=self.output_dir)
            
            # Process video
            logger.info(f"{worker_name} downloading: {video_info['title']}")
            result = await retriever.process_url(video_info['url'])
            
            if result:
                # Generate X draft (includes 3 styles)
                logger.info(f"{worker_name} generating X draft...")
                # X draft generation happens inside process_url if --with-x-draft
                # For async workers, we need to call it manually
                # This will be handled by the orchestrator
                
                return result
            
        except Exception as e:
            logger.error(f"{worker_name} processing failed: {e}")
            return None

