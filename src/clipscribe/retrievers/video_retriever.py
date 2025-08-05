"""ClipScribe Video Intelligence Retriever - Process videos from ANY platform."""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import json
from pathlib import Path
import networkx as nx
import csv
from collections import defaultdict

from ..models import VideoIntelligence, VideoTranscript, KeyPoint, Entity, Topic, Relationship, MultiVideoIntelligence
from .universal_video_client import UniversalVideoClient
from .transcriber import GeminiFlashTranscriber
from .video_retention_manager import VideoRetentionManager
from ..utils.filename import create_output_filename, create_output_structure, extract_platform_from_url
from ..config.settings import Settings, TemporalIntelligenceLevel, VideoRetentionPolicy
from ..utils.file_utils import calculate_sha256
# Timeline features permanently discontinued per strategic pivot

logger = logging.getLogger(__name__)


class VideoIntelligenceRetriever:
    """
    Main retriever class for video intelligence extraction with v2.17.0 Enhanced Temporal Intelligence.
    
    Features:
    - Enhanced Temporal Intelligence extraction (300% more temporal data)
    - Video Retention System with cost optimization
    - Direct video-to-Gemini processing
    - Support for 1800+ video platforms via yt-dlp
    """
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None,
        use_advanced_extraction: bool = True,
        domain: Optional[str] = None,
        mode: str = "auto",  # Changed default to auto for v2.17.0
        use_cache: bool = True,
        output_dir: Optional[str] = None,
        use_timeline_extractor: bool = False,
        enhance_transcript: bool = False,
        performance_monitor: Optional['PerformanceMonitor'] = None,
        cost_tracker: Optional['CostTracker'] = None,
        use_flash: bool = False,
        live_progress: Optional[Any] = None,
        phases: Optional[List[Dict]] = None
    ):
        """Initialize the retriever."""
        self.use_pro = not use_flash  # Invert the flag

        self.cache_dir = Path(cache_dir or "cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.domain = domain
        self.mode = mode
        self.use_cache = use_cache
        self.output_dir = output_dir
        self.enhance_transcript = enhance_transcript
        self.clean_graph = False  # Default to False, set via CLI
        self.performance_monitor = performance_monitor
        self.cost_tracker = cost_tracker
        self.live_progress = live_progress
        self.phases = phases
        
        self.use_advanced_extraction = use_advanced_extraction  # BUG FIX: Store the advanced extraction flag!
        
        # Get v2.17.0 settings
        self.settings = Settings()
        self.temporal_config = self.settings.get_temporal_intelligence_config()
        
        # Initialize video retention manager
        self.retention_manager = VideoRetentionManager(self.settings)
        
        # Initialize clients
        self.video_client = UniversalVideoClient()
        self.transcriber = GeminiFlashTranscriber(
            performance_monitor=performance_monitor,
            use_pro=self.use_pro
        )
        
        # Initialize mode detector for auto mode (v2.17.0 enhancement)
        if mode == "auto":
            from .video_mode_detector import VideoModeDetector
            self.mode_detector = VideoModeDetector()
        else:
            self.mode_detector = None
        
        # Choose entity extractor based on advanced extraction setting
        if use_advanced_extraction:
            logger.info("Using advanced extraction with trust_gemini mode :-)")
            try:
                from ..extractors.advanced_hybrid_extractor import AdvancedHybridExtractor
                self.entity_extractor = AdvancedHybridExtractor()
            except ImportError:
                logger.error("AdvancedHybridExtractor not found. Please check installation.")
                self.entity_extractor = None
        else:
            self.entity_extractor = None
        
        # Timeline Intelligence v2.0 Components DISCONTINUED per strategic pivot
        logger.info("Timeline features discontinued - focusing on core intelligence extraction")
        
        # Processing statistics
        self.videos_processed = 0
        self.total_cost = 0.0
        
        logger.info(f"v2.17.0 Enhanced Temporal Intelligence: {self.temporal_config['level']}")
        logger.info(f"Video Retention Policy: {self.settings.video_retention_policy}")
    
    async def search(
        self, 
        query: str, 
        max_results: int = 5,
        site: str = "youtube"
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
            
            # Search for videos
            videos = await self.video_client.search_videos(
                query=query,
                max_results=max_results,
                site=site
            )
            
            if not videos:
                logger.warning(f"No videos found for query: {query}")
                return []
            
            # Process videos in parallel with enhanced temporal intelligence
            tasks = [
                self._process_video_enhanced(video.url)
                for video in videos
            ]
            
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
    
    async def process_url(self, video_url: str, progress_state: Optional[Dict[str, Any]] = None) -> Optional[VideoIntelligence]:
        """
        Process a video from ANY supported platform with v2.17.0 Enhanced Temporal Intelligence.
        
        Enhanced features:
        - Enhanced temporal intelligence extraction
        - Visual temporal cues from video content
        - Smart video retention management
        - Direct video-to-Gemini processing
        
        Supports:
        - YouTube, Vimeo, Dailymotion
        - Twitter/X, TikTok, Instagram
        - BBC, CNN, TED, NBC
        - SoundCloud, Bandcamp
        - Twitch, Reddit
        - And 1800+ more!
        
        Args:
            video_url: URL from any supported video platform
            progress_state: Optional progress tracking state
            
        Returns:
            VideoIntelligence object with enhanced temporal intelligence or None if failed
        """
        # Check if URL is supported
        if not self.video_client.is_supported_url(video_url):
            logger.error(f"URL not supported by yt-dlp: {video_url}")
            return None
            
        if hasattr(self, 'progress_hook') and self.progress_hook:
            self.progress_hook({"description": "Processing with Enhanced Temporal Intelligence..."})
        
        try:
            logger.info(f"Starting _process_video_enhanced for URL: {video_url}")
            result = await self._process_video_enhanced(video_url)
            logger.info(f"_process_video_enhanced returned: {result is not None}")
            return result
        except Exception as e:
            logger.error(f"Exception in process_url: {e}", exc_info=True)
            return None
    
    def _update_progress(self, phase_index: int, status: str, progress: Optional[str] = None, cost: Optional[float] = None):
        """Update the live progress table in the CLI."""
        if self.live_progress and self.phases:
            try:
                phase = self.phases[phase_index]
                phase["status"] = status
                if progress is not None:
                    phase["progress"] = progress
                if cost is not None:
                    self.cost_tracker.add_cost(cost, "processing")
                
                # Always update cost from the central tracker
                phase["cost"] = f"${self.cost_tracker.current_cost:.4f}"

                # Rich-Live needs a new table object to render the update
                def get_updated_table():
                    table = Table(show_header=True, header_style="bold magenta", box=box.MINIMAL)
                    table.add_column("Phase", style="cyan")
                    table.add_column("Status")
                    table.add_column("Progress", style="yellow")
                    table.add_column("Cost", style="green")
                    for p in self.phases:
                        table.add_row(p["name"], p["status"], p["progress"], p["cost"])
                    return table
                
                self.live_progress.update(get_updated_table())
            except Exception as e:
                logger.error(f"Failed to update progress: {e}")

    async def _process_video_enhanced(self, video_url: str) -> Optional[VideoIntelligence]:
        """Process a single video, handling large files by splitting."""
        # Phase 0: Downloading
        if self.phases and self.refresh_display:
            self.phases[0]["status"] = "In Progress"
            self.phases[0]["progress"] = "10%"
            self.refresh_display()
        
        cache_key = self._get_cache_key(video_url)
        if self.use_cache:
            cached_result = self._load_from_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached result for: {video_url}")
                if self.phases and self.refresh_display:
                    self.phases[0]["status"] = "✓ Cached"
                    self.phases[0]["progress"] = "100%"
                    self.refresh_display()
                return cached_result
        
        processing_mode = await self._determine_enhanced_processing_mode(video_url)
        if processing_mode in ["video", "enhanced"]:
            media_file, metadata = await self.video_client.download_video(video_url, output_dir=self.cache_dir)
        else:
            media_file, metadata = await self.video_client.download_audio(video_url, output_dir=self.cache_dir)
        if self.phases and self.refresh_display:
            self.phases[0]["status"] = "✓ Complete"
            self.phases[0]["progress"] = "100%"
            self.refresh_display()
        
        media_path = Path(media_file)
        try:
            # Phase 1: Transcribing
            if self.phases and self.refresh_display:
                self.phases[1]["status"] = "In Progress"
                self.phases[1]["progress"] = "0%"
                self.refresh_display()

            # Check if the video is large and needs splitting
            if metadata.duration > 900:  # 15 minutes threshold
                analysis = await self.transcriber.transcribe_large_video(media_file, metadata.duration)
            else:
                if processing_mode in ["video", "enhanced"]:
                    analysis = await self.transcriber.transcribe_video(media_file, metadata.duration)
                else:
                    analysis = await self.transcriber.transcribe_audio(media_file, metadata.duration)

            if not analysis or "error" in analysis:
                raise Exception(f"Transcription failed: {analysis.get('error', 'Unknown error')}")

            self.cost_tracker.add_cost(analysis.get('processing_cost', 0.0), "transcription")
            if self.phases and self.refresh_display:
                self.phases[1]["status"] = "✓ Complete"
                self.phases[1]["progress"] = "100%"
                self.refresh_display()

            video_intelligence = self._create_video_intelligence_object(metadata, analysis)

            # Subsequent phases...
            # Phase 2: Extracting Intelligence
            if self.use_advanced_extraction and self.entity_extractor:
                if self.phases and self.refresh_display:
                    self.phases[2]["status"] = "In Progress"
                    self.phases[2]["progress"] = "0%"
                    self.refresh_display()
                video_intelligence = await self.entity_extractor.extract_all(video_intelligence, domain=self.domain)
                if self.phases and self.refresh_display:
                    self.phases[2]["status"] = "✓ Complete"
                    self.phases[2]["progress"] = "100%"
                    self.refresh_display()

            # Phase 3: Building Knowledge Graph
            if video_intelligence.entities and video_intelligence.relationships:
                if self.phases and self.refresh_display:
                    self.phases[3]["status"] = "In Progress"
                    self.phases[3]["progress"] = "0%"
                    self.refresh_display()
                video_intelligence = self._build_knowledge_graph(video_intelligence)
                if self.phases and self.refresh_display:
                    self.phases[3]["status"] = "✓ Complete"
                    self.phases[3]["progress"] = "100%"
                    self.refresh_display()
            else:
                if self.phases and self.refresh_display:
                    self.phases[3]["status"] = "✓ Skipped"
                    self.phases[3]["progress"] = "100%"
                    self.refresh_display()

            # Phase 4: Managing Video Retention
            if self.phases and self.refresh_display:
                self.phases[4]["status"] = "In Progress"
                self.phases[4]["progress"] = "0%"
                self.refresh_display()
            retention_result = await self.retention_manager.handle_video_retention(media_path, video_intelligence)
            video_intelligence.processing_stats['retention_decision'] = retention_result
            if self.phases and self.refresh_display:
                self.phases[4]["status"] = "✓ Complete"
                self.phases[4]["progress"] = "100%"
                self.refresh_display()
            
            self._save_to_cache(cache_key, video_intelligence)
            return video_intelligence
        finally:
            if media_path.exists():
                try:
                    os.remove(media_path)
                except OSError as e:
                    logger.warning(f"Could not remove temp file {media_path}: {e}")

    def _create_video_intelligence_object(self, metadata, analysis):
        """Helper to create the VideoIntelligence object from raw analysis."""
        transcript = VideoTranscript(
            full_text=analysis.get('transcript', ''),
            segments=self._generate_segments(analysis.get('transcript', ''), metadata.duration),
            language=analysis.get('language', 'en'),
            confidence=analysis.get('confidence_score', 0.95)
        )
        
        video_intelligence = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary=analysis.get('summary', ''),
            key_points=[KeyPoint(**kp) for kp in analysis.get('key_points', [])],
            entities=[],
            topics=[Topic(name=t) for t in analysis.get('topics', [])],
            relationships=[],
            processing_cost=analysis.get('processing_cost', 0.0)
        )
        video_intelligence.processing_stats['gemini_entities'] = analysis.get('entities', [])
        video_intelligence.processing_stats['gemini_relationships'] = analysis.get('relationships', [])
        return video_intelligence
    
    async def _determine_enhanced_processing_mode(self, video_url: str) -> str:
        """Determine the best processing mode for v2.17.0 Enhanced Temporal Intelligence."""
        
        # If mode is explicitly set, use it
        if self.mode in ["video", "audio"]:
            return self.mode
        
        # For auto mode, use enhanced intelligence
        if self.mode == "auto":
            # Use temporal intelligence level to determine mode
            if self.temporal_config['level'] == TemporalIntelligenceLevel.ENHANCED:
                # Enhanced mode uses video processing for visual temporal cues
                return "enhanced"
            elif self.temporal_config['level'] == TemporalIntelligenceLevel.MAXIMUM:
                # Maximum mode uses full video processing
                return "video"
            else:
                # Standard mode uses audio processing
                return "audio"
        
        # Default enhanced processing
        return "enhanced"
    
    # Keep existing methods unchanged
    async def _process_video(self, video_url: str, progress_state: Optional[Dict[str, Any]] = None) -> Optional[VideoIntelligence]:
        """Legacy method - redirects to enhanced processing."""
        return await self._process_video_enhanced(video_url, progress_state)
    
    def _get_cache_key(self, video_url: str) -> str:
        """Generate cache key from URL."""
        import hashlib
        # Include temporal intelligence level in cache key for v2.17.0
        cache_data = f"{video_url}_{self.temporal_config['level']}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[VideoIntelligence]:
        """Load result from cache."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return VideoIntelligence.parse_obj(data)
            except:
                pass
        
        return None
    
    def _save_to_cache(self, cache_key: str, result: VideoIntelligence):
        """Save result to cache."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(result.dict(), f, default=str, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get enhanced processing statistics for v2.17.0."""
        retention_stats = self.retention_manager.get_retention_stats()
        
        return {
            "videos_processed": self.videos_processed,
            "total_cost": self.total_cost,
            "average_cost": self.total_cost / max(1, self.videos_processed),
            "cache_dir": self.cache_dir,
            "supported_sites": "1800+ (via yt-dlp)",
            # v2.17.0 Enhanced stats
            "temporal_intelligence_level": self.temporal_config['level'],
            "temporal_intelligence_enabled": self.temporal_config['level'] != TemporalIntelligenceLevel.STANDARD,
            "video_retention_policy": self.settings.video_retention_policy,
            "retention_stats": retention_stats
        }
    
    def save_transcript(
        self, 
        video: VideoIntelligence, 
        output_dir: str = None,
        formats: List[str] = ["txt"]
    ) -> Dict[str, Path]:
        """
        Save transcript with meaningful filename based on video title.
        
        Args:
            video: VideoIntelligence object with transcript
            output_dir: Directory to save files (default: current directory)
            formats: List of formats to save (txt, json)
            
        Returns:
            Dictionary of format -> Path for saved files
        """
        saved_files = {}
        
        for format_type in formats:
            if format_type == "txt":
                # Save plain text
                output_file = create_output_filename(
                    video.metadata.title, 
                    "txt", 
                    output_dir
                )
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(video.transcript.full_text)
                saved_files["txt"] = output_file
                
            elif format_type == "json":
                # Save full JSON with metadata
                output_file = create_output_filename(
                    video.metadata.title, 
                    "json", 
                    output_dir
                )
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(video.dict(), f, default=str, indent=2)
                saved_files["json"] = output_file
        
        return saved_files
    
    def _generate_segments(
        self, 
        text: str, 
        duration: int, 
        segment_length: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Generate time-based segments from transcript.
        
        Args:
            text: Full transcript text
            duration: Video duration in seconds
            segment_length: Target segment length in seconds
            
        Returns:
            List of segment dictionaries with start, end, and text
        """
        if not text:
            return []
            
        # Split text into words
        words = text.split()
        if not words:
            return []
            
        # Calculate words per segment
        total_segments = max(1, duration // segment_length)
        words_per_segment = len(words) / total_segments
        
        # Ensure the step for the range is at least 1
        segment_word_count = max(1, int(words_per_segment))
        
        segments = []
        
        for i in range(0, len(words), segment_word_count):
            # Calculate time boundaries
            start_time = (i / len(words)) * duration
            end_time = min(((i + segment_word_count) / len(words)) * duration, duration)
            
            # Get segment text
            segment_words = words[i:i + segment_word_count]
            segment_text = ' '.join(segment_words)
            
            if segment_text.strip():  # Only add non-empty segments
                segments.append({
                    "start": round(start_time, 2),
                    "end": round(end_time, 2),
                    "text": segment_text.strip()
                })
        
        # Ensure last segment ends at video duration
        if segments:
            segments[-1]["end"] = duration
        
        logger.info(f"Generated {len(segments)} segments from {duration}s video")
        return segments
    
    def save_all_formats(
        self,
        video: VideoIntelligence,
        output_dir: str = "output",
        include_chimera_format: bool = True
    ) -> Dict[str, Path]:
        """
        Save video data in all formats with a structured directory.

        Orchestrates the saving of multiple file formats by calling dedicated
        private methods for each format.

        Args:
            video: VideoIntelligence object.
            output_dir: Base output directory.
            include_chimera_format: Include Chimera-compatible format.

        Returns:
            Dictionary of file types to paths.
        """
        # Debug logging to track knowledge graph state
        logger.debug(f"save_all_formats called with video.knowledge_graph: {hasattr(video, 'knowledge_graph')} / {getattr(video, 'knowledge_graph', None) is not None}")
        
        metadata = self._get_video_metadata_dict(video)
        paths = create_output_structure(metadata, output_dir)

        self._save_transcript_files(video, paths, metadata)
        self._save_metadata_file(video, paths, metadata)
        self._save_entities_files(video, paths)
        self._save_entity_sources_file(video, paths)  # New method to track entity sources
        self._save_relationships_files(video, paths)
        
        # Debug before knowledge graph save
        logger.debug(f"About to save knowledge graph. Exists: {hasattr(video, 'knowledge_graph')}, Not None: {getattr(video, 'knowledge_graph', None) is not None}")
        
        self._save_knowledge_graph_files(video, paths)
        self._save_facts_file(video, paths)
        self._save_report_file(video, paths)
        if include_chimera_format:
            self._save_chimera_file(video, paths)
        # Save TimelineJS if Timeline v2.0 data exists
        self._save_timelinejs_file(video, paths)

        self._create_manifest_file(video, paths)

        logger.info(f"Saved all formats to: {paths['directory']}")
        return paths

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
            "published_at": video.metadata.published_at.isoformat() if video.metadata.published_at else None,
            "view_count": video.metadata.view_count,
            "description": video.metadata.description,
        }

    def _save_transcript_files(self, video: VideoIntelligence, paths: Dict[str, Path], metadata: Dict[str, Any]):
        """Saves transcript.txt and transcript.json."""
        # 1. Plain text
        with open(paths["transcript_txt"], 'w', encoding='utf-8') as f:
            f.write(video.transcript.full_text)

        # 2. Full JSON
        full_data = {
            "metadata": metadata,
            "transcript": {
                "full_text": video.transcript.full_text,
                "segments": video.transcript.segments,
                "language": video.transcript.language,

            },
            "analysis": {
                "summary": video.summary,
                "key_points": [kp.dict() for kp in video.key_points],
                "entities": [
                    {
                        # Handle both Entity/EnhancedEntity (has .entity) and dict format (has 'name')
                        "entity": e.entity if hasattr(e, 'entity') else e.get('name', ''),
                        "type": e.type if hasattr(e, 'type') else e.get('type', ''),

                        "extraction_sources": getattr(e, 'extraction_sources', []),
                        "mention_count": getattr(e, 'mention_count', 1),
                        "context_windows": [cw.dict() for cw in getattr(e, 'context_windows', [])] if hasattr(e, 'context_windows') else [],
                        "aliases": getattr(e, 'aliases', [])
                    } for e in video.entities
                ],
                "topics": [t.dict() if hasattr(t, 'dict') else {"name": t.name} for t in video.topics],
                "sentiment": video.sentiment
            },
            "processing": {
                "cost": video.processing_cost,
                "time": video.processing_time,
                "processed_at": datetime.now().isoformat(),
                "model": "gemini-2.5-flash",
                "extractor": "advanced_hybrid_v2.2" if hasattr(self.entity_extractor, 'extract_all') else "basic_hybrid"
            }
        }
        
        # ADD DATES FIELD (Phase 1 fix)
        if hasattr(video, 'dates') and video.dates:
            full_data["dates"] = video.dates
        # Also check processing_stats for dates
        if hasattr(video, 'processing_stats') and video.processing_stats:
            if 'dates' in video.processing_stats:
                full_data["dates"] = video.processing_stats['dates']
            if 'visual_dates' in video.processing_stats:
                full_data["visual_dates"] = video.processing_stats['visual_dates']
        if hasattr(video, 'relationships') and video.relationships:
            full_data["relationships"] = [r.dict() for r in video.relationships]
        if hasattr(video, 'knowledge_graph') and video.knowledge_graph:
            full_data["knowledge_graph"] = video.knowledge_graph
        if hasattr(video, 'key_moments') and video.key_moments:
            full_data["key_facts"] = video.key_moments
        if hasattr(video, 'processing_stats') and video.processing_stats:
            full_data["extraction_stats"] = video.processing_stats
        if hasattr(video, 'timeline_v2') and video.timeline_v2:
            full_data["timeline_v2"] = video.timeline_v2
        
        with open(paths["transcript_json"], 'w', encoding='utf-8') as f:
            json.dump(full_data, f, default=str, indent=2)

    def _save_metadata_file(self, video: VideoIntelligence, paths: Dict[str, Path], metadata: Dict[str, Any]):
        """Saves metadata.json."""
        with open(paths["metadata"], 'w', encoding='utf-8') as f:
            json.dump({
                "video": metadata,
                "processing": {
                    "cost": video.processing_cost,
                    "time": video.processing_time,
                    "processed_at": datetime.now().isoformat(),
                    "clipscribe_version": "2.0.0"
                },
                "statistics": {
                    "transcript_length": len(video.transcript.full_text),
                    "word_count": len(video.transcript.full_text.split()),
                    "entity_count": len(video.entities),
                    "key_point_count": len(video.key_points),
                    "topic_count": len(video.topics)
                }
            }, f, indent=2)

    def _save_entities_files(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves entities.json and entities.csv."""
        # Use only the enhanced entities from the advanced extractor, NOT the initial Gemini entities
        all_entities = video.entities
        
        # Log entity sources for debugging
        entity_sources = defaultdict(int)
        for e in all_entities:
            if hasattr(e, 'extraction_sources'):
                for source in e.extraction_sources:
                    entity_sources[source] += 1
            elif hasattr(e, 'source'):
                entity_sources[e.source] += 1
            else:
                entity_sources['unknown'] += 1
        logger.info(f"Entity sources: {dict(entity_sources)}")
        
        # Entities JSON
        entities_data = {
            "video_url": video.metadata.url,
            "video_title": video.metadata.title,
            "entities": [
                {
                    "name": e.entity,
                    "type": e.type,

                    "source": getattr(e, 'extraction_sources', getattr(e, 'source', 'unknown')),
                    "properties": getattr(e, 'properties', None),
                    "timestamp": getattr(e, 'timestamp', None),
                    "mention_count": getattr(e, 'mention_count', 1),
                    "context_windows": [cw.dict() for cw in getattr(e, 'context_windows', [])],
                    "aliases": getattr(e, 'aliases', [])
                } for e in all_entities
            ],
            "topics": [t.dict() if hasattr(t, 'dict') else {"name": t.name} for t in video.topics],
            "key_facts": [kp.text for kp in video.key_points[:5]]
        }
        with open(paths["entities"], 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, indent=2)

        # Entities CSV
        entities_csv_path = paths["directory"] / "entities.csv"
        with open(entities_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "type", "source", "timestamp", "mention_count"])
            for entity in all_entities:
                writer.writerow([
                    entity.entity,
                    entity.type,

                    getattr(entity, 'extraction_sources', getattr(entity, 'source', 'unknown')),
                    getattr(entity, 'timestamp', ''),
                    getattr(entity, 'mention_count', 1)
                ])
        paths["entities_csv"] = entities_csv_path
        logger.info(f"Saved {len(all_entities)} entities to JSON and CSV :-)")

    def _save_relationships_files(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves relationships.json and relationships.csv."""
        if not hasattr(video, 'relationships'):
            video.relationships = []
            
        # Relationships JSON with enhanced metadata
        relationships_path = paths["directory"] / "relationships.json"
        relationships_data = {
            "video_url": video.metadata.url,
            "video_title": video.metadata.title,
            "relationships": [
                {
                    "subject": rel.subject,
                    "predicate": rel.predicate, 
                    "object": rel.object,

                    "properties": getattr(rel, 'properties', {}),
                    "context": getattr(rel, 'context', None),
                    "evidence_chain": getattr(rel, 'evidence_chain', []),
                    "contradictions": getattr(rel, 'contradictions', []),

                    "extraction_source": getattr(rel, 'extraction_source', 'unknown')
                } for rel in video.relationships
            ],
            "total_count": len(video.relationships),
            "relationships_with_evidence": sum(1 for rel in video.relationships if hasattr(rel, 'evidence_chain') and rel.evidence_chain),
            "total_evidence_pieces": sum(len(getattr(rel, 'evidence_chain', [])) for rel in video.relationships)
        }
        with open(relationships_path, 'w', encoding='utf-8') as f:
            json.dump(relationships_data, f, default=str, indent=2)
        paths["relationships"] = relationships_path

        # Relationships CSV with evidence count
        relationships_csv_path = paths["directory"] / "relationships.csv"
        with open(relationships_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["subject", "predicate", "object", "context", "evidence_count"])
            for rel in video.relationships:
                # Safe handling of context field that might be None
                context = getattr(rel, 'context', '') or ''
                context_truncated = context[:100] if context else ''
                evidence_count = len(getattr(rel, 'evidence_chain', []))
                
                writer.writerow([
                    rel.subject,
                    rel.predicate,
                    rel.object,

                    context_truncated,
                    evidence_count
                ])
        paths["relationships_csv"] = relationships_csv_path
        logger.info(f"Saved {len(video.relationships)} relationships to JSON and CSV :-)")

    def _save_knowledge_graph_files(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves knowledge_graph.json and knowledge_graph.gexf if they exist."""
        if not hasattr(video, 'knowledge_graph') or not video.knowledge_graph:
            logger.debug("No knowledge graph to save")
            return

        # Additional safety check - ensure knowledge_graph is not None
        if video.knowledge_graph is None:
            logger.warning("Knowledge graph is None, skipping save")
            return

        # Knowledge Graph JSON
        graph_path = paths["directory"] / "knowledge_graph.json"
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(video.knowledge_graph, f, indent=2)
        paths["knowledge_graph"] = graph_path
        
        # Safe access to knowledge graph properties
        node_count = video.knowledge_graph.get('node_count', 0) if isinstance(video.knowledge_graph, dict) else 0
        edge_count = video.knowledge_graph.get('edge_count', 0) if isinstance(video.knowledge_graph, dict) else 0
        
        logger.info(
            f"Saved knowledge graph with {node_count} nodes "
            f"and {edge_count} edges :-)"
        )

        # GEXF for Gephi
        gexf_path = paths["directory"] / "knowledge_graph.gexf"
        try:
            gexf_content = self._generate_gexf_content(video.knowledge_graph)
            with open(gexf_path, 'w', encoding='utf-8') as f:
                f.write(gexf_content)
            paths["gexf"] = gexf_path
            logger.info("Saved GEXF file for Gephi visualization :-)")
        except Exception as e:
            logger.warning(f"Failed to generate GEXF: {e}")

    def _save_facts_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves facts.txt if key moments exist."""
        if not hasattr(video, 'key_moments') or not video.key_moments:
            return

        facts_path = paths["directory"] / "facts.txt"
        with open(facts_path, 'w', encoding='utf-8') as f:
            f.write("# Key Facts Extracted from Video\n\n")
            f.write(f"Video: {video.metadata.title}\n")
            f.write(f"URL: {video.metadata.url}\n")
            f.write(f"Extracted: {datetime.now().isoformat()}\n\n")
            for i, fact in enumerate(video.key_moments, 1):
                source = fact.get('source', 'Fact')
                f.write(f"{i}. [{source}] {fact['fact']}\n")
        paths["facts"] = facts_path
        logger.info(f"Saved {len(video.key_moments)} key facts :-)")

    def _save_report_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Generates and saves the markdown report."""
        markdown_path = paths["directory"] / "report.md"
        with open(markdown_path, 'w', encoding='utf-8') as f:
            self._write_report_header(f, video)
            self._write_report_dashboard(f, video)
            self._write_report_topics(f, video)
            self._write_report_knowledge_graph(f, video)
            self._write_report_entity_analysis(f, video)
            self._write_report_relationship_network(f, video)
            self._write_report_key_insights(f, video)
            self._write_report_file_index(f, paths)
            self._write_report_footer(f, video)
        paths["report"] = markdown_path
        logger.info("Generated enhanced markdown report :-)")

    def _write_report_header(self, f, video: VideoIntelligence):
        """Writes the header section of the markdown report."""
        f.write(f"# Video Intelligence Report: {video.metadata.title}\n\n")
        f.write(f"**URL**: {video.metadata.url}\n")
        f.write(f"**Channel**: {video.metadata.channel}\n")
        minutes, seconds = divmod(int(video.metadata.duration), 60)
        f.write(f"**Duration**: {minutes}:{seconds:02d}\n")
        published_date = video.metadata.published_at.strftime('%Y-%m-%d') if video.metadata.published_at else 'Unknown'
        f.write(f"**Published**: {published_date}\n")
        f.write(f"**Processed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        cost = video.processing_cost
        cost_emoji = "🟢" if cost < 0.10 else ("🟡" if cost < 0.50 else "🔴")
        f.write(f"**Processing Cost**: {cost_emoji} ${cost:.4f}\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"{video.summary}\n\n")

    def _write_report_dashboard(self, f, video: VideoIntelligence):
        """Writes the quick stats dashboard section."""
        f.write("## 📊 Quick Stats Dashboard\n\n")
        f.write('<details open>\n<summary><b>Click to toggle stats</b></summary>\n\n')
        f.write("| Metric | Count | Visualization |\n")
        f.write("|--------|-------|---------------|\n")
        
        stats = {
            "Transcript Length": (len(video.transcript.full_text), "chars", "█", 2000),
            "Word Count": (len(video.transcript.full_text.split()), "words", "█", 500),
            "Entities Extracted": (len(video.entities) + len(getattr(video, 'custom_entities', [])), "", "🔵", 10),
            "Relationships Found": (len(getattr(video, 'relationships', [])), "", "🔗", 10),
            "Key Points": (len(video.key_points), "", "📌", 3),
            "Topics": (len(video.topics), "", "🏷️", 1)
        }
        if hasattr(video, 'knowledge_graph') and video.knowledge_graph:
            stats["Graph Nodes"] = (video.knowledge_graph.get('node_count', 0), "", "⭕", 10)
            stats["Graph Edges"] = (video.knowledge_graph.get('edge_count', 0), "", "➡️", 10)

        for name, (count, unit, icon, scale) in stats.items():
            bar = icon * min(20, int(count / scale)) if scale > 0 else icon * min(count, 10)
            f.write(f"| {name} | {count:,} {unit} | {bar} |\n")
            
        f.write("\n</details>\n\n")

    def _write_report_topics(self, f, video: VideoIntelligence):
        """Writes the topics section of the report."""
        f.write("## 🏷️ Main Topics\n\n")
        f.write('<details>\n<summary><b>View all topics</b></summary>\n\n')
        for i, topic in enumerate(video.topics[:15], 1):
            topic_name = topic.name if hasattr(topic, 'name') else topic
            f.write(f"{i}. {topic_name}\n")
        if len(video.topics) > 15:
            f.write(f"\n*... and {len(video.topics) - 15} more topics*\n")
        f.write("\n</details>\n\n")

    def _write_report_knowledge_graph(self, f, video: VideoIntelligence):
        """Writes the Mermaid knowledge graph visualization."""
        if not hasattr(video, 'relationships') or not video.relationships:
            return

        f.write("## 🕸️ Knowledge Graph Visualization\n\n")
        f.write('<details>\n<summary><b>Interactive relationship diagram (Mermaid)</b></summary>\n\n')
        f.write("```mermaid\ngraph TD\n    %% Top Entity Relationships\n")

        all_entities_for_graph = list(getattr(video, 'entities', [])) + list(getattr(video, 'custom_entities', []))
        entity_map = {e.entity: e for e in all_entities_for_graph}
        top_relationships = sorted(video.relationships, key=lambda r: getattr(r, 'confidence', 0), reverse=True)

        shown_relationships, relationships_to_render = set(), []
        for rel in top_relationships:
            subject_clean = rel.subject.replace('"', '').replace("'", "").replace(" ", "_")
            predicate_clean = rel.predicate.replace('"', '').replace("'", "")
            object_clean = rel.object.replace('"', '').replace("'", "").replace(" ", "_")
            rel_key = f"{subject_clean}-{predicate_clean}-{object_clean}"
            if rel_key not in shown_relationships:
                shown_relationships.add(rel_key)
                relationships_to_render.append(rel)
                f.write(f'    {subject_clean} -->|"{predicate_clean}"| {object_clean}\n')
            if len(relationships_to_render) >= 20:
                break

        f.write("\n    %% Styling\n")
        styled_nodes = set()
        for rel in relationships_to_render:
            subject_clean = rel.subject.replace('"', '').replace("'", "").replace(" ", "_")
            object_clean = rel.object.replace('"', '').replace("'", "").replace(" ", "_")
            for node_name, clean_name in [(rel.subject, subject_clean), (rel.object, object_clean)]:
                if clean_name not in styled_nodes and node_name in entity_map:
                    node_type = entity_map[node_name].type.lower()
                    if node_type in ['person', 'organization', 'location', 'product']:
                        f.write(f"    class {clean_name} {node_type}Class\n")
                    styled_nodes.add(clean_name)

        f.write("    classDef personClass fill:#ff9999,stroke:#333,stroke-width:2px\n")
        f.write("    classDef organizationClass fill:#99ccff,stroke:#333,stroke-width:2px\n")
        f.write("    classDef locationClass fill:#99ff99,stroke:#333,stroke-width:2px\n")
        f.write("    classDef productClass fill:#ffcc99,stroke:#333,stroke-width:2px\n")
        f.write("```\n\n")
        f.write("*Note: This diagram shows the top 20 relationships. For the complete graph, use the GEXF file with Gephi.*\n")
        f.write("\n</details>\n\n")

    def _write_report_entity_analysis(self, f, video: VideoIntelligence):
        """Writes the entity analysis section with Mermaid pie chart."""
        f.write("## 🔍 Entity Analysis\n\n")
        all_entities = list(getattr(video, 'entities', [])) + list(getattr(video, 'custom_entities', []))
        if not all_entities:
            return

        entities_by_type = {}
        for entity in all_entities:
            entities_by_type.setdefault(entity.type, []).append(entity)

        f.write("### Entity Type Distribution\n\n")
        f.write("```mermaid\npie title Entity Distribution\n")
        sorted_types = sorted(entities_by_type.items(), key=lambda x: len(x[1]), reverse=True)
        for entity_type, entities in sorted_types[:8]:
            f.write(f'    "{entity_type}" : {len(entities)}\n')
        if len(sorted_types) > 8:
            others = sum(len(e) for _, e in sorted_types[8:])
            f.write(f'    "Others" : {others}\n')
        f.write("```\n\n")

        type_emoji_map = {'PERSON': '👤', 'ORGANIZATION': '🏢', 'LOCATION': '📍', 'PRODUCT': '📦', 'EVENT': '📅', 'DATE': '📆', 'MONEY': '💰', 'software': '💻', 'api': '🔌', 'platform': '🌐', 'framework': '🛠️', 'model': '🤖', 'channel': '📺'}
        for entity_type in sorted(entities_by_type.keys()):
            entities = sorted(entities_by_type[entity_type], key=lambda e: getattr(e, 'confidence', 0), reverse=True)
            type_emoji = type_emoji_map.get(entity_type, '🏷️')
            f.write(f"\n<details>\n<summary><b>{type_emoji} {entity_type} ({len(entities)} found)</b></summary>\n\n")
            if entities:
                f.write("| Name | Confidence | Source |\n|------|------------|--------|\n")
                for entity in entities[:15]:
                    conf = getattr(entity, 'confidence', 0.0)
                    source = getattr(entity, 'source', 'SpaCy')
                    conf_bar = '🟩' if conf > 0.8 else ('🟨' if conf > 0.6 else '🟥')
                    f.write(f"| {entity.entity} | {conf_bar} {conf:.2f} | {source} |\n")
                if len(entities) > 15:
                    f.write(f"\n*... and {len(entities) - 15} more {entity_type.lower()} entities*\n")
            f.write("\n</details>\n")

    def _write_report_relationship_network(self, f, video: VideoIntelligence):
        """Writes the relationship network analysis section."""
        if not hasattr(video, 'relationships') or not video.relationships:
            return

        f.write("\n## 🔗 Relationship Network\n\n")
        rel_types = {}
        for rel in video.relationships:
            rel_types[rel.predicate] = rel_types.get(rel.predicate, 0) + 1
        
        f.write("<details>\n<summary><b>Relationship type distribution</b></summary>\n\n")
        f.write("| Predicate | Count | Percentage |\n|-----------|--------|------------|\n")
        total_rels = len(video.relationships)
        for pred, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True)[:15]:
            percentage = (count / total_rels) * 100
            bar = '█' * int(percentage / 5)
            f.write(f"| {pred} | {count} | {bar} {percentage:.1f}% |\n")
        f.write("\n</details>\n\n")

        f.write("<details>\n<summary><b>Key relationships (top 30)</b></summary>\n\n")
        for i, rel in enumerate(sorted(video.relationships, key=lambda r: getattr(r, 'confidence', 0), reverse=True)[:30], 1):
            conf = getattr(rel, 'confidence', 0.0)
            conf_emoji = '🟩' if conf > 0.8 else ('🟨' if conf > 0.6 else '🟥')
            f.write(f"{i}. **{rel.subject}** *{rel.predicate}* **{rel.object}** {conf_emoji} ({conf:.2f})\n")
        f.write("\n</details>\n\n")

    def _write_report_key_insights(self, f, video: VideoIntelligence):
        """Writes the key insights section."""
        f.write("## 💡 Key Insights\n\n")
        f.write("<details open>\n<summary><b>Top 10 key points</b></summary>\n\n")
        top_points = sorted(video.key_points, key=lambda p: getattr(p, 'importance', 0.5), reverse=True)[:10]
        for i, point in enumerate(top_points, 1):
            importance = getattr(point, 'importance', 0.5)
            imp_emoji = '🔴' if importance > 0.8 else ('🟡' if importance > 0.6 else '⚪')
            f.write(f"{i}. {imp_emoji} {point.text}\n")
        f.write("\n</details>\n\n")

    def _write_report_file_index(self, f, paths: Dict[str, Path]):
        """Writes the generated files index."""
        f.write("## 📁 Generated Files\n\n")
        f.write("<details>\n<summary><b>Click to see all files</b></summary>\n\n")
        f.write("| File | Format | Size | Description |\n")
        f.write("|------|--------|------|-------------|\n")
        
        file_info = [
            ("transcript.txt", "TXT", "Plain text transcript"),
            ("transcript.json", "JSON", "Full structured data"),
            ("entities.csv", "CSV", "All entities in spreadsheet format"),
            ("relationships.csv", "CSV", "All relationships in spreadsheet format"),
            ("knowledge_graph.json", "JSON", "Complete graph structure"),
            ("knowledge_graph.gexf", "GEXF", "Import into Gephi for visualization"),
            ("metadata.json", "JSON", "Video metadata and statistics"),
            ("manifest.json", "JSON", "File index with checksums"),
            ("report.md", "Markdown", "This report"),
            ("chimera_format.json", "JSON", "Chimera-compatible format"),
            ("timeline_js.json", "JSON", "TimelineJS3 visualization data")
        ]
        
        for filename, fmt, desc in file_info:
            file_path = paths["directory"] / filename
            if file_path.exists():
                size = os.path.getsize(file_path)
                size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
                f.write(f"| `{filename}` | {fmt} | {size_str} | {desc} |\n")
        f.write("\n</details>\n\n")

    def _write_report_footer(self, f, video: VideoIntelligence):
        """Writes the report footer."""
        f.write("---\n")
        version = video.processing_stats.get('version', '2.6.0') if hasattr(video, 'processing_stats') else '2.6.0'
        f.write(f"*Generated by ClipScribe v{version} on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*\n")
        f.write("\n💡 **Tip**: This markdown file supports Mermaid diagrams. View it in a compatible editor for interactive diagrams.\n")

    def _create_manifest_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Creates the manifest.json file."""
        manifest = {
            "version": "2.3",
            "created_at": datetime.now().isoformat(),
            "video": {
                "title": video.metadata.title,
                "url": video.metadata.url,
                "platform": extract_platform_from_url(video.metadata.url)
            },
            "extraction_stats": video.processing_stats if hasattr(video, 'processing_stats') else {},
            "timeline_v2": video.timeline_v2 if hasattr(video, 'timeline_v2') else None,
            "files": {}
        }
        
        file_definitions = {
            "transcript_txt": {"path": "transcript.txt", "format": "plain_text"},
            "transcript_json": {"path": "transcript.json", "format": "json"},
            "metadata": {"path": "metadata.json", "format": "json"},
            "entities": {"path": "entities.json", "format": "json"},
            "relationships": {"path": "relationships.json", "format": "json", "count_attr": "relationships"},
            "knowledge_graph": {"path": "knowledge_graph.json", "format": "json"},
            "gexf": {"path": "knowledge_graph.gexf", "format": "gexf", "description": "Gephi-compatible graph file"},
            "facts": {"path": "facts.txt", "format": "plain_text", "count_attr": "key_moments"},
            "entities_csv": {"path": "entities.csv", "format": "csv", "description": "All entities in CSV format"},
            "relationships_csv": {"path": "relationships.csv", "format": "csv", "description": "All relationships in CSV format"},
            "report": {"path": "report.md", "format": "markdown", "description": "Human-readable intelligence report"},
            "chimera": {"path": "chimera_format.json", "format": "json", "description": "Chimera-compatible format"},
            "timeline_js": {"path": "timeline_js.json", "format": "json", "description": "TimelineJS3-compatible timeline visualization"}
        }

        for key, definition in file_definitions.items():
            if key in paths and paths[key].exists():
                file_path = paths[key]
                file_entry = {
                    "path": definition["path"],
                    "format": definition["format"],
                    "size": os.path.getsize(file_path),
                    "sha256": calculate_sha256(file_path)
                }
                if "description" in definition:
                    file_entry["description"] = definition["description"]
                if "count_attr" in definition and hasattr(video, definition["count_attr"]):
                    file_entry["count"] = len(getattr(video, definition["count_attr"]))
                
                manifest["files"][key] = file_entry

        with open(paths["manifest"], 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, default=str)

    def _save_chimera_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves the Chimera-compatible format file."""
        chimera_path = paths["directory"] / "chimera_format.json"
        chimera_data = self._to_chimera_format(video)
        with open(chimera_path, 'w', encoding='utf-8') as f:
            json.dump(chimera_data, f, indent=2, default=str)
        paths["chimera"] = chimera_path
    
    def _save_timelinejs_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves timeline_js.json in TimelineJS3 format if Timeline v2.0 data exists."""
        # Check if Timeline v2.0 data exists
        if not hasattr(video, 'timeline_v2') or not video.timeline_v2:
            logger.debug("No Timeline v2.0 data to convert to TimelineJS format")
            return
        try:
            # Get timeline events from the timeline_v2 data
            timeline_events = video.timeline_v2.get('events', [])
            if not timeline_events:
                logger.debug("No timeline events found in Timeline v2.0 data")
                return
            # Import TimelineJSFormatter from utils
            from clipscribe.utils.timeline_js_formatter import TimelineJSFormatter
            from clipscribe.timeline.models import ConsolidatedTimeline, TemporalEvent
            # Convert raw events to TemporalEvent objects
            temporal_events = []
            for event_data in timeline_events:
                if not isinstance(event_data, dict):
                    continue
                # Parse date
                date_value = event_data.get('date', datetime.now().isoformat())
                if isinstance(date_value, str):
                    parsed_date = datetime.fromisoformat(date_value.replace(' ', 'T'))
                elif isinstance(date_value, datetime):
                    parsed_date = date_value
                else:
                    parsed_date = datetime.now()
                temporal_event = TemporalEvent(
                    event_id=event_data.get('event_id', f"event_{len(temporal_events)}"),
                    content_hash=event_data.get('content_hash', ''),
                    date=parsed_date,
                    date_precision=event_data.get('date_precision', 'approximate'),
                    date_confidence=event_data.get('date_confidence', 0.5),
                    extracted_date_text=event_data.get('extracted_date_text', ''),
                    date_source=event_data.get('date_source', 'unknown'),
                    description=event_data.get('description', ''),
                    event_type=event_data.get('event_type', 'inferred'),
                    involved_entities=event_data.get('involved_entities', []),
                    source_videos=[video.metadata.url],
                    video_timestamps={video.metadata.url: event_data.get('timestamp', 0)},
                    chapter_context=event_data.get('chapter_context'),
                    extraction_method=event_data.get('extraction_method', 'timeline_v2'),
                    confidence=event_data.get('confidence', 0.7),
                    validation_status=event_data.get('validation_status', 'unverified')
                )
                temporal_events.append(temporal_event)
            if not temporal_events:
                logger.debug("No valid temporal events to convert")
                return
            # Create consolidated timeline
            consolidated_timeline = ConsolidatedTimeline(
                events=temporal_events,
                video_sources=[video.metadata.url]
            )
            # Use TimelineJSFormatter to convert
            formatter = TimelineJSFormatter()
            timeline_js = formatter.format_timeline(consolidated_timeline, title=video.metadata.title, description=video.summary)
            # Save to timeline_js.json
            timeline_js_path = paths["directory"] / "timeline_js.json"
            with open(timeline_js_path, 'w', encoding='utf-8') as f:
                json.dump(timeline_js, f, indent=2, default=str)
            paths["timeline_js"] = timeline_js_path
            logger.info(f"Saved TimelineJS3 format to {timeline_js_path}")
        except Exception as e:
            logger.warning(f"Failed to generate TimelineJS format: {e}")
            # Don't fail the entire process if TimelineJS export fails
    
    # Chimera-compatible interface methods
    
    async def retrieve(
        self,
        query: str,
        max_results: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Chimera-compatible retrieve method.
        
        Returns results in Chimera's expected format.
        """
        # Check if query is a URL
        if query.startswith(('http://', 'https://')):
            # Process single URL
            result = await self.process_url(query)
            if result:
                return [self._to_chimera_format(result)]
            return []
        else:
            # Search for videos
            results = await self.search(query, max_results)
            return [self._to_chimera_format(r) for r in results]
    
    def _to_chimera_format(self, video: VideoIntelligence) -> Dict[str, Any]:
        """Convert VideoIntelligence to Chimera's format."""
        return {
            "type": "video",
            "source": "video_intelligence",
            "url": video.metadata.url,
            "title": video.metadata.title,
            "content": video.transcript.full_text,  # Changed to full_text
            "summary": video.summary,
            "metadata": {
                "channel": video.metadata.channel,
                "duration": video.metadata.duration,
                "published_at": video.metadata.published_at.isoformat() if video.metadata.published_at else None,
                "view_count": video.metadata.view_count,
                "key_points": [kp.dict() for kp in video.key_points],
                "entities": [e.dict() for e in video.entities],
                "topics": [t.dict() if hasattr(t, 'dict') else {"name": t.name, "confidence": t.confidence} for t in video.topics],
                "sentiment": video.sentiment,
                "processing_cost": video.processing_cost,
                "timeline_v2": video.timeline_v2 if hasattr(video, 'timeline_v2') else None
            }
        }
    
    def _generate_gexf_content(self, knowledge_graph: Dict[str, Any]) -> str:
        """Generate GEXF content from knowledge graph."""
        from xml.sax.saxutils import escape
        
        gexf_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        gexf_content += '<gexf xmlns="http://www.gexf.net/1.3" xmlns:viz="http://www.gexf.net/1.3/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://gexf.net/1.3 http://gexf.net/1.3/gexf.xsd" version="1.3">\n'
        gexf_content += '  <meta lastmodifieddate="' + datetime.now().strftime('%Y-%m-%d') + '">\n'
        gexf_content += '    <creator>ClipScribe</creator>\n'
        gexf_content += '    <description>Knowledge graph extracted from video content</description>\n'
        gexf_content += '  </meta>\n'
        gexf_content += '  <graph mode="static" defaultedgetype="directed">\n'
        gexf_content += '    <attributes class="node">\n'
        gexf_content += '      <attribute id="0" title="Type" type="string"/>\n'
        gexf_content += '      <attribute id="1" title="Confidence" type="double"/>\n'
        gexf_content += '    </attributes>\n'
        gexf_content += '    <attributes class="edge">\n'
        gexf_content += '      <attribute id="0" title="Predicate" type="string"/>\n'
        gexf_content += '      <attribute id="1" title="Confidence" type="double"/>\n'
        gexf_content += '    </attributes>\n'
        gexf_content += '    <nodes>\n'
        
        # Color map for entity types
        color_map = {
            'PERSON': '#FF6B6B',        # Red
            'ORGANIZATION': '#4ECDC4',   # Teal
            'LOCATION': '#45B7D1',       # Blue
            'EVENT': '#F7DC6F',          # Yellow
            'CONCEPT': '#BB8FCE',        # Purple
            'TECHNOLOGY': '#52BE80',     # Green
            'DATE': '#F39C12',           # Orange
            'MONEY': '#85C1E2',          # Light Blue
            'unknown': '#95A5A6'         # Gray
        }
        
        # Add nodes with attributes
        for node in knowledge_graph.get('nodes', []):
            node_id = escape(str(node['id']))
            node_type = node.get('type', 'unknown')
            confidence = node.get('confidence', 0.9)
            
            # Get color for node type
            hex_color = color_map.get(node_type, color_map['unknown'])
            
            gexf_content += f'      <node id="{node_id}" label="{node_id}">\n'
            gexf_content += f'        <attvalues>\n'
            gexf_content += f'          <attvalue for="0" value="{escape(node_type)}"/>\n'
            gexf_content += f'          <attvalue for="1" value="{confidence}"/>\n'
            gexf_content += f'        </attvalues>\n'
            gexf_content += f'        <viz:color hex="{hex_color}" a="1.0"/>\n'
            gexf_content += f'        <viz:size value="{20 + (confidence * 30)}"/>\n'
            gexf_content += f'      </node>\n'
        
        gexf_content += '    </nodes>\n'
        gexf_content += '    <edges>\n'
        
        # Add edges with attributes
        for i, edge in enumerate(knowledge_graph.get('edges', [])):
            source = escape(str(edge['source']))
            target = escape(str(edge['target']))
            predicate = escape(str(edge.get('predicate', 'related_to')))
            confidence = edge.get('confidence', 0.9)
            
            gexf_content += f'      <edge id="{i}" source="{source}" target="{target}" weight="{confidence}">\n'
            gexf_content += f'        <attvalues>\n'
            gexf_content += f'          <attvalue for="0" value="{predicate}"/>\n'
            gexf_content += f'          <attvalue for="1" value="{confidence}"/>\n'
            gexf_content += f'        </attvalues>\n'
            gexf_content += f'      </edge>\n'
        
        gexf_content += '    </edges>\n'
        gexf_content += '  </graph>\n'
        gexf_content += '</gexf>\n'
        
        return gexf_content 

    def _save_entity_sources_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Save a detailed file showing which extraction method found each entity."""
        entities_with_sources = []
        
        # Track entities by source (including combined sources from normalization)
        sources = {
            "SpaCy": [],
            "GLiNER": [], 
            "REBEL": [],
            "SpaCy+GLiNER": [],
            "SpaCy+REBEL": [],
            "GLiNER+REBEL": [],
            "SpaCy+GLiNER+REBEL": [],
            "Unknown": []
        }
        
        normalization_stats = {
            "total_normalized": 0,
            "entities_with_multiple_sources": 0,
            "entities_with_aliases": 0
        }
        
        for entity in video.entities:
            # Determine source from properties
            source = "Unknown"
            aliases = []
            original_names = []
            
            if hasattr(entity, 'properties') and entity.properties:
                # Check for multiple sources (from entity normalization)
                if 'sources' in entity.properties:
                    source_list = entity.properties['sources']
                    source = '+'.join(sorted(source_list))
                    normalization_stats["entities_with_multiple_sources"] += 1
                elif 'source' in entity.properties:
                    source = entity.properties['source']
                else:
                    source = 'SpaCy'  # Default assumption
                    
                # Get aliases if available (from normalization)
                if 'aliases' in entity.properties:
                    aliases = entity.properties['aliases']
                    if aliases:
                        normalization_stats["entities_with_aliases"] += 1
                        
                # Get original names if available
                if 'original_names' in entity.properties:
                    original_names = entity.properties['original_names']
            
            entity_info = {
                "name": entity.entity,
                "type": entity.type,

                "source": source,
                "extraction_methods": source.split('+') if '+' in source else [source],
                "aliases": aliases,
                "original_names": original_names,
                "is_normalized": '+' in source or bool(aliases)
            }
            
            if entity_info["is_normalized"]:
                normalization_stats["total_normalized"] += 1
            
            entities_with_sources.append(entity_info)
            
            # Add to appropriate source bucket
            if source in sources:
                sources[source].append(entity_info)
            else:
                sources["Unknown"].append(entity_info)
        
        # Create comprehensive summary
        summary = {
            "total_entities": len(entities_with_sources),
            "normalization_applied": True,
            "normalization_stats": normalization_stats,
            "by_source": {
                source: {
                    "count": len(items),
                    "percentage": round((len(items) / len(entities_with_sources)) * 100, 1) if entities_with_sources else 0
                }
                for source, items in sources.items() if items
            },
            "by_type": {},
            "extraction_methods": {
                "SpaCy": "Basic Named Entity Recognition (free, local)",
                "GLiNER": "Custom entity detection (local model)", 
                "REBEL": "Relationship extraction (local model)",
                "Combined": "Entities found by multiple methods and normalized"
            },
            "quality_metrics": {


                "normalized_entities": normalization_stats["total_normalized"]
            }
        }
        
        # Count by type
        for entity in video.entities:
            entity_type = entity.type
            summary["by_type"][entity_type] = summary["by_type"].get(entity_type, 0) + 1
        
        # Save detailed JSON
        output_file = paths['entity_sources_json']
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": summary,
                "all_entities": entities_with_sources,
                "by_source": {k: v for k, v in sources.items() if v}
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved enhanced entity sources to {output_file}")
        
        # Save CSV for analysis
        csv_file = paths['entity_sources_csv']
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['name', 'type', 'source', 'extraction_methods', 'aliases', 'is_normalized']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for entity in entities_with_sources:
                # Convert lists to strings for CSV
                csv_entity = entity.copy()
                csv_entity['extraction_methods'] = '|'.join(entity['extraction_methods'])
                csv_entity['aliases'] = '|'.join(entity['aliases']) if entity['aliases'] else ''
                del csv_entity['original_names']  # Too complex for CSV
                writer.writerow(csv_entity)
        
        logger.info(f"Saved entity sources CSV to {csv_file} with normalization info")

    def save_collection_outputs(
        self,
        collection: MultiVideoIntelligence,
        output_dir: str = "output"
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
        # Create a directory for the collection using its unique ID
        collection_path = Path(output_dir) / collection.collection_id
        collection_path.mkdir(parents=True, exist_ok=True)
        
        saved_paths = {"directory": collection_path}

        # 1. Save the Consolidated Timeline
        if collection.consolidated_timeline:
            timeline_path = collection_path / "timeline.json"
            with open(timeline_path, 'w', encoding='utf-8') as f:
                # Pydantic's model_dump_json is great for this
                f.write(collection.consolidated_timeline.model_dump_json(indent=2))
            saved_paths["timeline"] = timeline_path
            logger.info(f"Saved consolidated timeline to {timeline_path}")

        # 2. Save the full collection intelligence object
        collection_intelligence_path = collection_path / "collection_intelligence.json"
        with open(collection_intelligence_path, 'w', encoding='utf-8') as f:
            f.write(collection.model_dump_json(indent=2))
        saved_paths["collection_intelligence"] = collection_intelligence_path
        logger.info(f"Saved full collection intelligence to {collection_intelligence_path}")
        
        # 3. Save the Unified Knowledge Graph (if it exists)
        if collection.unified_knowledge_graph:
            # GEXF for Gephi
            gexf_path = collection_path / "unified_knowledge_graph.gexf"
            try:
                # We can reuse the existing GEXF generator
                gexf_content = self._generate_gexf_content(collection.unified_knowledge_graph)
                with open(gexf_path, 'w', encoding='utf-8') as f:
                    f.write(gexf_content)
                saved_paths["unified_gexf"] = gexf_path
                logger.info(f"Saved unified GEXF file to {gexf_path}")
            except Exception as e:
                logger.warning(f"Failed to generate unified GEXF: {e}")

        # Knowledge panels removed - functionality moved to Chimera

        # 5. Save Information Flow Maps (NEW v2.14.0)
        if collection.information_flow_map:
            # Save complete information flow map
            flow_map_path = collection_path / "information_flow_map.json"
            with open(flow_map_path, 'w', encoding='utf-8') as f:
                f.write(collection.information_flow_map.model_dump_json(indent=2))
            saved_paths["information_flow_map"] = flow_map_path
            logger.info(f"Saved information flow map to {flow_map_path}")
            
            # Save individual concept flows as separate files for easy access
            flows_dir = collection_path / "concept_flows"
            flows_dir.mkdir(exist_ok=True)
            
            for flow in collection.information_flow_map.information_flows:
                # Use source_node.video_id since InformationFlow doesn't have video_id directly
                flow_filename = f"{flow.source_node.video_id}_{flow.flow_id}.json"
                flow_path = flows_dir / flow_filename
                with open(flow_path, 'w', encoding='utf-8') as f:
                    f.write(flow.model_dump_json(indent=2))
            
            saved_paths["concept_flows_dir"] = flows_dir
            logger.info(f"Saved {len(collection.information_flow_map.information_flows)} individual concept flows to {flows_dir}")
            
            # Save a human-readable summary of information flows
            flow_summary_path = collection_path / "information_flow_summary.md"
            self._save_information_flow_summary(collection.information_flow_map, flow_summary_path)
            saved_paths["flow_summary"] = flow_summary_path

        logger.info(f"All collection outputs saved to: {collection_path}")
        return saved_paths

    # Knowledge panels summary method removed - functionality moved to Chimera 

    def _save_information_flow_summary(self, flow_map, output_path: Path):
        """Generate a human-readable markdown summary of information flow maps."""
        from clipscribe.models import InformationFlowMap
        
        # Calculate unique video count from concept nodes
        unique_videos = set()
        for node in flow_map.concept_nodes:
            unique_videos.add(node.video_id)
        actual_video_count = len(unique_videos)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Information Flow Map: {flow_map.collection_title}\n\n")
            f.write(f"**Collection ID:** {flow_map.collection_id}\n")
            f.write(f"**Created:** {flow_map.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Videos:** {actual_video_count}\n")  # Fixed: use actual video count
            f.write(f"**Concepts Tracked:** {flow_map.total_concepts}\n")
            f.write(f"**Flow Patterns Identified:** {flow_map.total_flows}\n\n")
            
            # Collection-level analysis
            f.write("## 📊 Flow Analysis Summary\n\n")
            f.write("### Overall Flow Pattern\n")
            f.write(f"{flow_map.flow_summary}\n\n")
            
            f.write("### Learning Progression Analysis\n")
            f.write(f"{flow_map.learning_progression}\n\n")
            
            if flow_map.strategic_insights:
                f.write("### Strategic Insights\n")
                for insight in flow_map.strategic_insights:
                    f.write(f"- {insight}\n")
                f.write("\n")
            
            # Concept clusters
            if flow_map.concept_clusters:
                f.write("## 🔄 Concept Clusters\n\n")
                for i, cluster in enumerate(flow_map.concept_clusters, 1):
                    f.write(f"### Cluster {i}: {cluster.cluster_name}\n")
                    f.write(f"**Theme:** {cluster.cluster_name}\n")
                    f.write(f"**Concepts:** {', '.join(cluster.core_concepts)}\n")
                    f.write(f"**Coherence Score:** {cluster.coherence_score:.2f}\n\n")
            
            # Evolution paths
            if flow_map.evolution_paths:
                f.write("## 📈 Concept Evolution Paths\n\n")
                # Sort by significance (number of evolution nodes and coherence)
                sorted_paths = sorted(flow_map.evolution_paths, 
                                    key=lambda p: (len(p.evolution_nodes) * p.evolution_coherence), 
                                    reverse=True)
                
                for i, path in enumerate(sorted_paths[:10], 1):  # Top 10 paths
                    f.write(f"### {i}. {path.concept_name}\n")
                    f.write(f"**Evolution Nodes:** {len(path.evolution_nodes)} stages\n")
                    f.write(f"**Coherence Score:** {path.evolution_coherence:.2f}\n")
                    f.write(f"**Completeness:** {path.completeness_score:.2f}\n")
                    f.write(f"**Understanding Depth:** {path.understanding_depth:.2f}\n")
                    
                    # Show evolution summary
                    if path.evolution_summary:
                        f.write(f"**Summary:** {path.evolution_summary}\n")
                    
                    # Show key transformations
                    if path.key_transformations:
                        f.write("**Key Transformations:**\n")
                        for transformation in path.key_transformations[:3]:
                            f.write(f"- {transformation}\n")
                    f.write("\n")
                
                if len(flow_map.evolution_paths) > 10:
                    f.write(f"*... and {len(flow_map.evolution_paths) - 10} more evolution paths*\n\n")
            
            # Information flows analysis
            f.write("## 📹 Information Flow Analysis\n\n")
            
            # Group flows by source video for organization
            flows_by_video = {}
            for flow in flow_map.information_flows:
                source_video = flow.source_node.video_id
                if source_video not in flows_by_video:
                    flows_by_video[source_video] = {
                        'title': flow.source_node.video_title,
                        'flows': []
                    }
                flows_by_video[source_video]['flows'].append(flow)
            
            # Display flows by video
            for video_id, video_data in flows_by_video.items():
                f.write(f"### Video: {video_data['title']}\n")
                f.write(f"**Video ID:** {video_id}\n")
                f.write(f"**Information Flows Originating:** {len(video_data['flows'])}\n\n")
                
                # Show key flows from this video
                for flow in video_data['flows'][:5]:  # Show top 5 flows
                    f.write(f"**Flow:** {flow.source_node.concept_name} → {flow.target_node.concept_name}\n")
                    f.write(f"- **Type:** {flow.flow_type}\n")
                    f.write(f"- **Quality:** {flow.flow_quality:.2f}\n")
                    f.write(f"- **Information Transferred:** {flow.information_transferred}\n")
                    f.write(f"- **Target Video:** {flow.target_node.video_title}\n\n")
                
                if len(video_data['flows']) > 5:
                    f.write(f"*... and {len(video_data['flows']) - 5} more flows from this video*\n\n")
                
                f.write("---\n\n")
            
            # Information gaps
            if flow_map.information_gaps:
                f.write("## ⚠️ Information Gaps Identified\n\n")
                for gap in flow_map.information_gaps:
                    f.write(f"- {gap}\n")
                f.write("\n")
            
            # Footer
            f.write("## 📁 Files Generated\n\n")
            f.write("- `information_flow_map.json` - Complete structured flow data\n")
            f.write("- `concept_flows/` - Individual flow files for each video\n")
            f.write("- `information_flow_summary.md` - This human-readable summary\n\n")
            
            f.write("## 🎯 How to Use This Analysis\n\n")
            f.write("1. **Curriculum Design:** Use evolution paths to structure learning sequences\n")
            f.write("2. **Content Planning:** Identify gaps where concepts need more development\n")
            f.write("3. **Research Synthesis:** Track how ideas evolve across multiple sources\n")
            f.write("4. **Knowledge Management:** Understand concept dependencies and relationships\n\n")
            
            f.write("---\n")
            f.write(f"*Generated by ClipScribe v2.14.0 Information Flow Maps on {flow_map.created_at.strftime('%Y-%m-%d at %H:%M:%S')}*\n")
        
        logger.info(f"Saved information flow summary to {output_path}") 

    def _build_knowledge_graph(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """Build knowledge graph from entities and relationships."""
        import networkx as nx
        
        G = nx.DiGraph()
        
        # Add entities as nodes
        for entity in video_intel.entities:
            # Handle both Entity and EnhancedEntity objects
            entity_name = getattr(entity, 'entity', getattr(entity, 'name', str(entity)))
            entity_type = getattr(entity, 'type', 'unknown')
            entity_confidence = getattr(entity, 'confidence', 0.9)
            
            G.add_node(
                entity_name,
                type=entity_type,
                confidence=entity_confidence
            )
        
        # Add relationships as edges
        for rel in video_intel.relationships:
            subject = getattr(rel, 'subject', rel.get('subject') if isinstance(rel, dict) else None)
            obj = getattr(rel, 'object', rel.get('object') if isinstance(rel, dict) else None)
            predicate = getattr(rel, 'predicate', rel.get('predicate') if isinstance(rel, dict) else 'related_to')
            confidence = getattr(rel, 'confidence', rel.get('confidence', 0.9) if isinstance(rel, dict) else 0.9)
            
            if subject and obj:
                G.add_edge(
                    subject,
                    obj,
                    predicate=predicate,
                    confidence=confidence
                )
        
        # Convert to serializable format
        video_intel.knowledge_graph = {
            "nodes": [
                {
                    "id": node,
                    "type": data.get("type", "unknown"),
                    "confidence": data.get("confidence", 0.9)
                }
                for node, data in G.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "predicate": data.get("predicate", "related_to"),
                    "confidence": data.get("confidence", 0.9)
                }
                for u, v, data in G.edges(data=True)
            ],
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges()
        }
        
        logger.info(f"Built knowledge graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return video_intel