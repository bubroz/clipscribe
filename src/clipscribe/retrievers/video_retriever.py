"""ClipScribe Video Intelligence Retriever - Process videos from ANY platform."""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Callable, Union
from pathlib import Path

from ..models import VideoIntelligence, MultiVideoIntelligence
from .video_processor import VideoProcessor
from ..config.settings import Settings, TemporalIntelligenceLevel, VideoRetentionPolicy
from ..utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class VideoIntelligenceRetriever:
    """
    Main retriever class for video intelligence extraction with v2.17.0 Enhanced Temporal Intelligence.

    Features:
    - Enhanced Temporal Intelligence extraction (300% more temporal data)
    - Video Retention System with cost optimization
    - Direct video-to-Gemini processing
    - Support for 1800+ video platforms via yt-dlp
    - Modular architecture with focused components
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
        performance_monitor: Optional["PerformanceMonitor"] = None,
        use_flash: bool = False,
        cookies_from_browser: Optional[str] = None,
        settings: Optional[Settings] = None,
        api_key: Optional[str] = None,
        on_phase_start: Optional[Callable[[str, str], None]] = None,
        on_phase_complete: Optional[Callable[[str, float], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
        on_phase_log: Optional[Callable[[str, float], None]] = None,
    ):
        """Initialize the retriever with modular components."""
        self.use_pro = not use_flash
        self.settings = settings or Settings()

        # Initialize the modular video processor
        self.processor = VideoProcessor(
            cache_dir=cache_dir,
            use_advanced_extraction=use_advanced_extraction,
            domain=domain,
            mode=mode,
            use_cache=use_cache,
            output_dir=output_dir,
            enhance_transcript=enhance_transcript,
            performance_monitor=performance_monitor,
            use_pro=self.use_pro,
            cookies_from_browser=cookies_from_browser,
            settings=self.settings,
            api_key=api_key,
            on_phase_start=on_phase_start,
            on_phase_complete=on_phase_complete,
            on_error=on_error,
            on_phase_log=on_phase_log,
        )

        logger.info(f"Video Retention Policy: {self.settings.video_retention_policy}")

    async def search(
        self, query: str, max_results: int = 5, site: str = "youtube"
    ) -> List[VideoIntelligence]:
        """
        Search for videos and analyze them with v2.17.0 Enhanced Temporal Intelligence.

        Args:
            query: Search query
            max_results: Maximum number of videos to process
            site: Site to search (currently only 'youtube')

        Returns:
            List of VideoIntelligence objects with enhanced temporal intelligence
        """
        try:
            logger.info(f"Searching for videos: {query}")

            # Search for videos using the downloader
            videos = await asyncio.get_event_loop().run_in_executor(
                None, self.processor.downloader.search_videos, query, max_results, site
            )

            if not videos:
                logger.warning(f"No videos found for query: {query}")
                return []

            # Process videos in parallel with enhanced temporal intelligence
            tasks = [self.processor.process_url(video.url) for video in videos]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out errors
            intelligence_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Failed to process video: {result}")
                elif result:
                    intelligence_results.append(result)

            return intelligence_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def process_url(self, video_url: str) -> Optional[VideoIntelligence]:
        """
        Process a video from ANY supported platform.
        """
        return await self.processor.process_url(video_url)

    def get_stats(self) -> Dict[str, Any]:
        """Get enhanced processing statistics for v2.17.0."""
        return self.processor.get_stats()

    def get_saved_files(
        self, video: VideoIntelligence, output_dir: str = "output"
    ) -> Dict[str, Path]:
        """Gets the expected paths for saved files without actually saving them."""
        metadata = self._get_video_metadata_dict(video)
        return create_output_structure(metadata, output_dir)

    def _get_video_metadata_dict(self, video: VideoIntelligence) -> Dict[str, Any]:
        """Extracts video metadata into a dictionary."""
        if video is None or video.metadata is None:
            logger.warning("Video or metadata is None, using default values")
            return {
                "title": "Unknown",
                "url": "Unknown",
                "channel": "Unknown",
                "duration": 0,
                "published_at": None,
                "view_count": None,
                "description": None,
            }

        return {
            "title": video.metadata.title,
            "url": video.metadata.url,
            "channel": video.metadata.channel,
            "duration": video.metadata.duration,
            "published_at": (
                video.metadata.published_at.isoformat() if video.metadata.published_at else None
            ),
            "view_count": video.metadata.view_count,
            "description": video.metadata.description,
        }

    # Chimera-compatible interface methods

    async def retrieve(self, query: str, max_results: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Chimera-compatible retrieve method.

        Returns results in Chimera's expected format.
        """
        # Check if query is a URL
        if query.startswith(("http://", "https://")):
            # Process single URL
            result = await self.process_url(query)
            if result:
                return [self.processor.output_formatter._to_chimera_format(result)]
            return []
        else:
            # Search for videos
            results = await self.search(query, max_results)
            return [self.processor.output_formatter._to_chimera_format(r) for r in results]

    # Legacy method aliases for backward compatibility
    async def _process_video_enhanced(
        self, video_url: str, cookies_from_browser: Optional[str] = None
    ) -> Optional[VideoIntelligence]:
        """Legacy method - delegates to the new processor."""
        return await self.processor.process_url(video_url)

    async def _process_video(self, video_url: str) -> Optional[VideoIntelligence]:
        """Legacy method - redirects to enhanced processing."""
        return await self._process_video_enhanced(video_url)

    def _determine_enhanced_processing_mode(self, video_url: str) -> str:
        """Determine the best processing mode for v2.17.0 Enhanced Temporal Intelligence."""
        # This logic is now handled by the VideoProcessor's internal settings and mode.
        # This method is effectively deprecated and will be removed.
        if self.processor.mode in ["video", "audio"]:
            return self.processor.mode
        if self.processor.mode == "auto":
            temporal_config = self.settings.get_temporal_intelligence_config()
            if temporal_config["level"] == TemporalIntelligenceLevel.ENHANCED:
                return "enhanced"
            elif temporal_config["level"] == TemporalIntelligenceLevel.MAXIMUM:
                return "video"
            else:
                return "audio"
        return "enhanced"

    def _get_cache_key(self, video_url: str) -> str:
        """Generate cache key from URL."""
        # This logic is now handled internally by the VideoProcessor's caching mechanism.
        # This method is effectively deprecated and will be removed.
        from ..utils.stable_id import generate_unversioned_digest
        temporal_config = self.settings.get_temporal_intelligence_config()
        cache_data = f"{self._normalized_url(video_url)}_{temporal_config['level']}"
        return generate_unversioned_digest(cache_data, algo="sha256", length=24)

    def _normalized_url(self, url: str) -> str:
        """Normalize URL for consistent caching."""
        # This logic is now handled internally by the VideoProcessor's caching mechanism.
        # This method is effectively deprecated and will be removed.
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
        try:
            p = urlparse(url)
            netloc = p.netloc.lower()
            scheme = (p.scheme or "http").lower()
            query = urlencode(sorted(parse_qsl(p.query)), doseq=True)
            return urlunparse((scheme, netloc, p.path, p.params, query, ""))
        except Exception:
            return url

    def _load_from_cache(self, cache_key: str) -> Optional[VideoIntelligence]:
        """Load result from cache."""
        # This logic is now handled internally by the VideoProcessor's caching mechanism.
        # This method is effectively deprecated and will be removed.
        cache_file = Path(self.processor.downloader.cache_dir) / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                result = VideoIntelligence.parse_obj(data)
                result.is_from_cache = True
                return result
            except Exception:
                pass
        return None

    def _save_to_cache(self, cache_key: str, result: VideoIntelligence):
        """Save result to cache."""
        # This logic is now handled internally by the VideoProcessor's caching mechanism.
        # This method is effectively deprecated and will be removed.
        cache_file = Path(self.processor.downloader.cache_dir) / f"{cache_key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(result.dict(), f, default=str, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def _create_video_intelligence_object(self, metadata, analysis):
        """Helper to create the VideoIntelligence object from raw analysis."""
        # This method is now delegated to VideoProcessor's internal helper.
        # This method is effectively deprecated and will be removed.
        transcript = VideoTranscript(
            full_text=analysis.get("transcript", ""),
            segments=self.processor.transcriber._generate_segments(analysis.get("transcript", ""), metadata.duration),
            language=analysis.get("language", "en"),
            confidence=analysis.get("confidence_score", 0.95),
        )

        video_intelligence = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary=analysis.get("summary", ""),
            key_points=[KeyPoint(**kp) for kp in analysis.get("key_points", [])],
            entities=[],
            topics=[Topic(name=t) for t in analysis.get("topics", [])],
            relationships=[],
            processing_cost=analysis.get("processing_cost", 0.0),
        )
        video_intelligence.processing_stats["gemini_entities"] = analysis.get("entities", [])
        video_intelligence.processing_stats["gemini_relationships"] = analysis.get(
            "relationships", []
        )
        return video_intelligence

    def save_transcript(
        self, video: VideoIntelligence, output_dir: str = None, formats: List[str] = ["txt"]
    ) -> Dict[str, Path]:
        """Save transcript in specified formats."""
        return self.processor.save_transcript(video, output_dir, formats)

    def save_all_formats(
        self,
        video: VideoIntelligence,
        output_dir: str = "output",
        include_chimera_format: bool = True,
    ) -> Dict[str, Path]:
        """Save video data in all supported formats."""
        return self.processor.save_all_formats(video, output_dir, include_chimera_format)

    def get_saved_files(self, video: VideoIntelligence) -> Dict[str, Path]:
        """Get paths to all saved files for a video."""
        # This would need to be implemented based on the output formatter
        # For now, return empty dict as placeholder
        return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.processor.get_stats()

    def retrieve(self, query: str, **kwargs) -> Any:
        """Legacy retrieve method for backward compatibility."""
        return self.search(query, **kwargs)

    def save_collection_outputs(
        self, collection: MultiVideoIntelligence, output_dir: str = "output"
    ) -> Dict[str, Path]:
        """
        Saves the synthesized outputs from a multi-video collection.
        This creates a dedicated directory for the collection and saves
        the consolidated timeline, unified knowledge graph, and the full
        collection intelligence object.
        Args:
            collection: The MultiVideoIntelligence object containing all unified data.
            output_dir: The base directory to save the output folder in.
        Returns:
            A dictionary of the paths to the saved files.
        """
        # This method's logic is now handled by the OutputFormatter or a new CollectionOutputFormatter.
        # This method is effectively deprecated and will be removed.
        # For now, we'll delegate to a placeholder or raise an error if not implemented.
        logger.warning("save_collection_outputs is deprecated and its logic has been moved.")
        # This would ideally delegate to a new CollectionOutputFormatter
        # For now, we'll just return an empty dict or raise an error.
        return {}
