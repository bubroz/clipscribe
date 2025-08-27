"""Video Processor Module - Main orchestrator for video intelligence extraction."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path

from ..models import VideoIntelligence
from .video_downloader import VideoDownloader
from .video_transcriber import VideoTranscriber
from .knowledge_graph_builder import KnowledgeGraphBuilder
from .output_formatter import OutputFormatter
from .video_retention_manager import VideoRetentionManager
from ..config.settings import VideoRetentionPolicy, Settings
from ..utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Main orchestrator for video intelligence extraction.

    Coordinates the download, transcription, entity extraction, knowledge graph building,
    and output formatting processes.
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        use_advanced_extraction: bool = True,
        domain: Optional[str] = None,
        mode: str = "auto",
        use_cache: bool = True,
        output_dir: Optional[str] = None,
        enhance_transcript: bool = False,
        performance_monitor: Optional[PerformanceMonitor] = None,
        use_pro: bool = True,
        cookies_from_browser: Optional[str] = None,
        settings: Optional[Settings] = None,
        api_key: Optional[str] = None,
        on_phase_start: Optional[Callable[[str, str], None]] = None,
        on_phase_complete: Optional[Callable[[str, float], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
        on_phase_log: Optional[Callable[[str, float], None]] = None,
    ):
        """Initialize the video processor with all components."""
        self.settings = settings or Settings()

        # Initialize component modules
        self.downloader = VideoDownloader(
            cache_dir=cache_dir,
            cookies_from_browser=cookies_from_browser
        )

        self.transcriber = VideoTranscriber(
            use_pro=use_pro,
            performance_monitor=performance_monitor,
            api_key=api_key
        )

        self.kg_builder = KnowledgeGraphBuilder()

        self.output_formatter = OutputFormatter()

        # Entity extractor (conditional)
        self.entity_extractor = None
        if use_advanced_extraction:
            try:
                from ..extractors.advanced_hybrid_extractor import AdvancedHybridExtractor
                self.entity_extractor = AdvancedHybridExtractor()
                logger.info("Using advanced entity extraction")
            except ImportError:
                logger.warning("AdvancedHybridExtractor not available, using basic extraction")

        # Retention manager
        self.retention_manager = VideoRetentionManager(self.settings)

        # Configuration
        self.domain = domain
        self.mode = mode
        self.use_cache = use_cache
        self.output_dir = output_dir
        self.enhance_transcript = enhance_transcript
        self.performance_monitor = performance_monitor

        # Callbacks
        self.on_phase_start = on_phase_start or (lambda _name, _status: None)
        self.on_phase_complete = on_phase_complete or (lambda _name, _cost: None)
        self.on_error = on_error or (lambda _name, _error: None)
        self.on_phase_log = on_phase_log or (lambda _name, _duration: None)
        self.use_advanced_extraction = use_advanced_extraction

        # Stats
        self.videos_processed = 0
        self.total_cost = 0.0

    def is_supported_url(self, video_url: str) -> bool:
        """Check if a video URL is supported."""
        return self.downloader.is_supported_url(video_url)

    async def process_url(self, video_url: str) -> Optional[VideoIntelligence]:
        """
        Process a single video URL through the complete pipeline.

        Args:
            video_url: URL of the video to process

        Returns:
            VideoIntelligence object or None if failed
        """
        if not self.is_supported_url(video_url):
            logger.error(f"URL not supported: {video_url}")
            self.on_error("Downloading", f"URL not supported: {video_url}")
            return None

        try:
            return await self._process_video_pipeline(video_url)
        except Exception as e:
            logger.error(f"Exception in process_url: {e}", exc_info=True)
            self.on_error("Processing", str(e))
            return None

    async def _process_video_pipeline(self, video_url: str) -> Optional[VideoIntelligence]:
        """Execute the complete video processing pipeline."""
        start_time = time.monotonic()

        # Phase 1: Download video
        self.on_phase_start("Downloading", "In Progress...")
        phase_start = time.monotonic()

        try:
            media_file, metadata = await self.downloader.download_video(video_url)
            self.on_phase_complete("Downloading", 0.0)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self.on_error("Downloading", str(e))
            return None
        finally:
            self.on_phase_log("Downloading", time.monotonic() - phase_start)

        # Phase 2: Transcribe video
        self.on_phase_start("Transcribing", "In Progress...")
        phase_start = time.monotonic()

        try:
            analysis = await self.transcriber.transcribe_video(
                media_file, metadata, metadata.duration
            )
            transcription_cost = self.transcriber.get_transcription_cost(analysis)
            self.on_phase_complete("Transcribing", transcription_cost)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            self.on_error("Transcribing", str(e))
            return None
        finally:
            self.on_phase_log("Transcribing", time.monotonic() - phase_start)

        # Create initial VideoIntelligence object
        transcript = self.transcriber.create_transcript_object(analysis, metadata.duration)
        video_intelligence = self._create_video_intelligence(metadata, analysis, transcript)

        # Phase 3: Extract entities (if available)
        if self.entity_extractor:
            self.on_phase_start("Extracting Intelligence", "In Progress...")
            phase_start = time.monotonic()

            try:
                video_intelligence = await self.entity_extractor.extract_all(
                    video_intelligence, domain=self.domain
                )
                self.on_phase_complete("Extracting Intelligence", 0.0)
            except Exception as e:
                logger.warning(f"Entity extraction failed: {e}")
                # Continue without entity extraction
            finally:
                self.on_phase_log("Extracting Intelligence", time.monotonic() - phase_start)

        # Phase 4: Build knowledge graph
        if video_intelligence.entities:
            self.on_phase_start("Building Knowledge Graph", "In Progress...")
            phase_start = time.monotonic()

            try:
                video_intelligence = self.kg_builder.build_knowledge_graph(video_intelligence)
                self.on_phase_complete("Building Knowledge Graph", 0.0)
            except Exception as e:
                logger.warning(f"Knowledge graph building failed: {e}")
            finally:
                self.on_phase_log("Building Knowledge Graph", time.monotonic() - phase_start)

        # Phase 5: Handle video retention
        self.on_phase_start("Video Retention", "Applying Policy...")
        phase_start = time.monotonic()

        try:
            retention_result = await self.retention_manager.handle_video_retention(
                Path(media_file), video_intelligence
            )
            video_intelligence.processing_stats["retention_decision"] = retention_result
            self.on_phase_complete("Video Retention", 0.0)
        except Exception as e:
            logger.warning(f"Video retention failed: {e}")
        finally:
            self.on_phase_log("Video Retention", time.monotonic() - phase_start)

        # Clean up temp file
        await self.downloader.cleanup_temp_file(
            Path(media_file),
            self.settings.video_retention_policy,
            self.retention_manager
        )

        # Phase 6: Save results
        self.on_phase_start("Saving Results", "In Progress...")
        phase_start = time.monotonic()

        try:
            saved_files = self.save_all_formats(
                video_intelligence,
                self.output_dir,
                include_chimera_format=True
            )
            video_intelligence.processing_stats["saved_files"] = saved_files
            self.on_phase_complete("Saving Results", 0.0)
        except Exception as e:
            logger.warning(f"Saving results failed: {e}")
        finally:
            self.on_phase_log("Saving Results", time.monotonic() - phase_start)

        # Update stats
        self.videos_processed += 1
        self.total_cost += video_intelligence.processing_cost

        logger.info(f"Successfully processed: {metadata.title}")
        return video_intelligence

    def _create_video_intelligence(
        self, metadata, analysis, transcript
    ) -> VideoIntelligence:
        """Create VideoIntelligence object from raw data."""
        from ..models import VideoTranscript, VideoIntelligence, KeyPoint, Topic

        video_intelligence = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary=analysis.get("summary", ""),
            key_points=[KeyPoint(**kp) for kp in analysis.get("key_points", [])],
            entities=[],  # Will be populated by entity extractor
            topics=[Topic(name=t) for t in analysis.get("topics", [])],
            relationships=[],  # Will be populated by entity extractor
            processing_cost=self.transcriber.get_transcription_cost(analysis),
        )

        # Store entities in processing_stats so AdvancedHybridExtractor can find them
        video_intelligence.processing_stats["gemini_entities"] = analysis.get("entities", [])
        video_intelligence.processing_stats["gemini_relationships"] = analysis.get("relationships", [])

        return video_intelligence

    def save_transcript(
        self, video: VideoIntelligence, output_dir: str = None, formats: List[str] = ["txt"]
    ) -> Dict[str, Path]:
        """Save transcript in specified formats."""
        return self.output_formatter.save_transcript(video, output_dir, formats)

    def save_all_formats(
        self,
        video: VideoIntelligence,
        output_dir: str = "output",
        include_chimera_format: bool = True,
    ) -> Dict[str, Path]:
        """Save video data in all supported formats."""
        return self.output_formatter.save_all_formats(
            video, output_dir, include_chimera_format
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        retention_stats = self.retention_manager.get_retention_stats()

        return {
            "videos_processed": self.videos_processed,
            "total_cost": self.total_cost,
            "average_cost": self.total_cost / max(1, self.videos_processed),
            "cache_dir": self.downloader.cache_dir,
            "supported_sites": "1800+ (via yt-dlp)",
            "video_retention_policy": self.settings.video_retention_policy,
            "retention_stats": retention_stats,
        }

    def _call_callback(self, callback, *args, **kwargs):
        """Helper method to safely call callback functions."""
        if callback:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Callback execution failed: {e}")
