# Async Monitor Architecture Investigation

## Current Problem Analysis

### Current Synchronous Architecture
```
Monitor Loop → Detect Video → Process Video (BLOCKS) → Wait → Repeat
```

**Blocking Points:**
1. **Video Download**: 30-60 seconds (audio + video)
2. **Voxtral Transcription**: 2-15 minutes (depends on length)
3. **Grok Intelligence Extraction**: 5-30 minutes (32 chunks × 6 min each)
4. **X Draft Generation**: 1-2 minutes
5. **GCS Upload**: 30-60 seconds
6. **Telegram Notification**: 1-2 seconds

**Total Processing Time**: 8-60 minutes per video
**Monitor Interval**: 30-600 seconds (0.5-10 minutes)

### The Core Issue
The monitor callback `process_new_video()` is **synchronous** and blocks the entire monitor loop. When a long video (like PBS News Hour) takes 3.5 hours to process, the monitor can't detect new videos during that time.

## Proposed Async Architecture

### Design Principles
1. **Non-blocking Detection**: Monitor loop never blocks
2. **Concurrent Processing**: Multiple videos processed simultaneously
3. **Queue-based**: Videos queued for processing, not processed inline
4. **Resource Management**: Limit concurrent processing to prevent overload
5. **Fault Tolerance**: Failed videos don't stop the monitor

### New Architecture
```
Monitor Loop (Non-blocking) → Video Queue → Worker Pool → Results
     ↓                           ↓            ↓
Detect Videos              Queue Videos   Process Videos
Every 30s                   (Instant)      (Concurrent)
```

## Implementation Plan

### 1. Async Video Queue System

```python
import asyncio
from asyncio import Queue
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class VideoTask:
    video_info: Dict[str, Any]
    priority: int = 0
    queued_at: datetime = None
    retry_count: int = 0
    max_retries: int = 3

class AsyncVideoQueue:
    def __init__(self, max_size: int = 100):
        self.queue = Queue(maxsize=max_size)
        self.processing = {}  # video_id -> task
        self.completed = {}   # video_id -> result
        self.failed = {}      # video_id -> error
    
    async def enqueue(self, video_info: Dict[str, Any], priority: int = 0):
        """Add video to processing queue."""
        task = VideoTask(
            video_info=video_info,
            priority=priority,
            queued_at=datetime.now()
        )
        await self.queue.put(task)
        logger.info(f"Queued video: {video_info['title']}")
    
    async def dequeue(self) -> VideoTask:
        """Get next video for processing."""
        return await self.queue.get()
    
    def mark_processing(self, video_id: str, task: VideoTask):
        """Mark video as being processed."""
        self.processing[video_id] = task
    
    def mark_completed(self, video_id: str, result: Any):
        """Mark video as completed."""
        if video_id in self.processing:
            del self.processing[video_id]
        self.completed[video_id] = result
    
    def mark_failed(self, video_id: str, error: Exception):
        """Mark video as failed."""
        if video_id in self.processing:
            del self.processing[video_id]
        self.failed[video_id] = error
```

### 2. Worker Pool System

```python
class VideoWorkerPool:
    def __init__(self, max_workers: int = 3, retriever_factory: Callable = None):
        self.max_workers = max_workers
        self.workers = []
        self.retriever_factory = retriever_factory
        self.semaphore = asyncio.Semaphore(max_workers)
        self.running = False
    
    async def start(self, video_queue: AsyncVideoQueue):
        """Start worker pool."""
        self.running = True
        self.video_queue = video_queue
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} video workers")
    
    async def stop(self):
        """Stop worker pool."""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("Worker pool stopped")
    
    async def _worker(self, worker_name: str):
        """Worker task that processes videos from queue."""
        logger.info(f"{worker_name} started")
        
        while self.running:
            try:
                # Get next video task
                task = await self.video_queue.dequeue()
                video_info = task.video_info
                video_id = video_info['video_id']
                
                # Mark as processing
                self.video_queue.mark_processing(video_id, task)
                
                # Process with semaphore (limit concurrency)
                async with self.semaphore:
                    result = await self._process_video(task)
                    
                    if result:
                        self.video_queue.mark_completed(video_id, result)
                        logger.info(f"{worker_name} completed: {video_info['title']}")
                    else:
                        self.video_queue.mark_failed(video_id, Exception("Processing failed"))
                        logger.error(f"{worker_name} failed: {video_info['title']}")
                
            except asyncio.CancelledError:
                logger.info(f"{worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"{worker_name} error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
        
        logger.info(f"{worker_name} stopped")
    
    async def _process_video(self, task: VideoTask) -> Optional[Any]:
        """Process a single video."""
        video_info = task.video_info
        
        try:
            # Create retriever instance
            retriever = self.retriever_factory()
            
            # Process video
            result = await retriever.process_url(video_info['url'])
            
            if result:
                # Generate X draft if needed
                if hasattr(retriever, 'generate_x_content'):
                    output_path = Path(retriever.output_dir) / f"20251001_youtube_{video_info['video_id']}"
                    x_draft = await retriever.generate_x_content(result, output_path)
                    if x_draft:
                        logger.info(f"X draft generated: {x_draft['directory']}")
                
                return result
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            return None
```

### 3. Non-blocking Monitor Loop

```python
class AsyncChannelMonitor:
    def __init__(self, channel_ids: List[str], video_queue: AsyncVideoQueue):
        self.channel_ids = channel_ids
        self.video_queue = video_queue
        self.monitor = ChannelMonitor(channel_ids)
        self.running = False
    
    async def start_monitoring(self, interval: int = 60):
        """Start non-blocking monitor loop."""
        self.running = True
        logger.info(f"Starting async monitor: checking every {interval}s")
        
        while self.running:
            try:
                # Check for new videos (non-blocking)
                new_videos = await self.monitor.check_for_new_videos()
                
                # Queue new videos (instant)
                for video in new_videos:
                    await self.video_queue.enqueue(video, priority=0)
                    logger.info(f"🆕 New video queued: {video['title']}")
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
        
        self.running = False
    
    def stop_monitoring(self):
        """Stop monitor loop."""
        self.running = False
```

### 4. Main Orchestrator

```python
class AsyncMonitorOrchestrator:
    def __init__(self, channel_ids: List[str], max_workers: int = 3):
        self.channel_ids = channel_ids
        self.video_queue = AsyncVideoQueue(max_size=100)
        self.worker_pool = VideoWorkerPool(max_workers=max_workers)
        self.monitor = AsyncChannelMonitor(channel_ids, self.video_queue)
    
    async def start(self, interval: int = 60):
        """Start the complete async monitoring system."""
        logger.info("Starting Async Monitor Orchestrator")
        
        # Start worker pool
        await self.worker_pool.start(self.video_queue)
        
        # Start monitor loop
        monitor_task = asyncio.create_task(
            self.monitor.start_monitoring(interval)
        )
        
        try:
            # Wait for monitor to run
            await monitor_task
        except KeyboardInterrupt:
            logger.info("Shutting down orchestrator...")
        finally:
            # Stop worker pool
            await self.worker_pool.stop()
            logger.info("Orchestrator stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'queue_size': self.video_queue.queue.qsize(),
            'processing': len(self.video_queue.processing),
            'completed': len(self.video_queue.completed),
            'failed': len(self.video_queue.failed),
            'workers': len(self.worker_pool.workers)
        }
```

## Benefits of Async Architecture

### 1. Non-blocking Detection
- Monitor checks every 30-60 seconds regardless of processing time
- New videos detected immediately
- No missed videos due to long processing

### 2. Concurrent Processing
- Multiple videos processed simultaneously
- Configurable worker count (default: 3)
- Semaphore limits resource usage

### 3. Fault Tolerance
- Failed videos don't stop the monitor
- Retry mechanism for transient failures
- Error tracking and reporting

### 4. Resource Management
- Queue size limits prevent memory issues
- Worker pool prevents CPU overload
- Configurable concurrency limits

### 5. Monitoring & Observability
- Real-time status of queue, processing, completed, failed
- Worker health monitoring
- Performance metrics

## Implementation Steps

### Phase 1: Core Async Components
1. **AsyncVideoQueue**: Queue system for video tasks
2. **VideoWorkerPool**: Worker pool for concurrent processing
3. **AsyncChannelMonitor**: Non-blocking monitor loop

### Phase 2: Integration
1. **AsyncMonitorOrchestrator**: Main orchestrator
2. **CLI Integration**: Update monitor command
3. **Configuration**: Worker count, queue size, intervals

### Phase 3: Advanced Features
1. **Priority Queue**: High-priority videos processed first
2. **Retry Logic**: Automatic retry for failed videos
3. **Health Monitoring**: Worker health checks
4. **Metrics**: Processing time, success rate, queue depth

### Phase 4: Production Features
1. **Persistence**: Queue state saved to disk
2. **Recovery**: Resume processing after restart
3. **Scaling**: Dynamic worker scaling
4. **Alerting**: Notifications for failures

## Performance Expectations

### Current (Synchronous)
- **Detection Interval**: 30-600 seconds
- **Processing**: 1 video at a time
- **Blocking**: Monitor stops during processing
- **Throughput**: 1 video per 8-60 minutes

### New (Async)
- **Detection Interval**: 30-60 seconds (consistent)
- **Processing**: 3 videos concurrently
- **Non-blocking**: Monitor never stops
- **Throughput**: 3 videos per 8-60 minutes (3x improvement)

## Migration Strategy

### 1. Backward Compatibility
- Keep existing monitor command working
- Add new async monitor as separate command
- Gradual migration path

### 2. Testing
- Unit tests for async components
- Integration tests for full workflow
- Load testing with multiple videos

### 3. Rollout
- Deploy async monitor alongside existing
- A/B test with subset of channels
- Full migration after validation

## Conclusion

The async architecture solves the core blocking problem while providing significant performance improvements. The implementation is complex but provides a robust foundation for scalable video monitoring.

**Key Benefits:**
- ✅ Non-blocking video detection
- ✅ Concurrent video processing
- ✅ Fault tolerance
- ✅ Resource management
- ✅ 3x throughput improvement

**Implementation Effort:**
- **Complexity**: High (requires async programming expertise)
- **Time**: 2-3 weeks for full implementation
- **Risk**: Medium (async programming complexity)
- **Value**: High (solves core scalability issue)
