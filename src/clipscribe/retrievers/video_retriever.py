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

from ..models import VideoIntelligence, VideoTranscript, KeyPoint, Entity, Topic, Relationship, MultiVideoIntelligence
from .universal_video_client import UniversalVideoClient
from .transcriber import GeminiFlashTranscriber
from ..utils.filename import create_output_filename, create_output_structure, extract_platform_from_url
from ..extractors import HybridEntityExtractor, AdvancedHybridExtractor
from ..config.settings import Settings
from ..utils.file_utils import calculate_sha256

logger = logging.getLogger(__name__)


class VideoIntelligenceRetriever:
    """
    Main retriever class for video intelligence extraction.
    
    Supports 1800+ video platforms via yt-dlp.
    Uses Gemini 2.5 Flash for transcription.
    """
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None,
        use_advanced_extraction: bool = True,
        domain: Optional[str] = None,
        mode: str = "audio",
        use_cache: bool = True,
        output_dir: Optional[str] = None,
        output_formats: Optional[List[str]] = None,
        enhance_transcript: bool = False,
        progress_tracker: Optional[Any] = None,
        performance_monitor: Optional[Any] = None,
        progress_hook: Optional[Any] = None
    ):
        """
        Initialize the video intelligence retriever.
        
        Args:
            cache_dir: Directory for caching results
            use_advanced_extraction: Use REBEL+GLiNER extraction
            domain: Domain for specialized extraction
            mode: Processing mode ("audio", "video", "auto")
            use_cache: Whether to use cached results
            output_dir: Directory for output files
            output_formats: List of output formats
            enhance_transcript: Whether to enhance transcript
            progress_tracker: Progress tracking instance
            performance_monitor: Performance monitoring instance
            progress_hook: Progress hook for progress updates
        """
        self.cache_dir = cache_dir or ".video_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.mode = mode
        self.use_cache = use_cache
        self.output_dir = output_dir
        self.output_formats = output_formats or ["txt"]
        self.enhance_transcript = enhance_transcript
        self.clean_graph = False  # Will be set by CLI if --clean-graph is used
        self.use_advanced_extraction = use_advanced_extraction  # Store this as instance variable
        self.progress_tracker = progress_tracker
        self.performance_monitor = performance_monitor
        self.progress_hook = progress_hook
        
        # Get settings
        settings = Settings()
        
        # Initialize clients
        self.video_client = UniversalVideoClient()
        self.transcriber = GeminiFlashTranscriber(performance_monitor=performance_monitor)
        
        # Initialize mode detector if using auto mode
        if mode == "auto":
            from .video_mode_detector import VideoModeDetector
            self.mode_detector = VideoModeDetector()
        else:
            self.mode_detector = None
        
        # Choose entity extractor based on advanced extraction setting
        if use_advanced_extraction:
            logger.info("Using advanced extraction with REBEL+GLiNER :-)")
            try:
                from ..extractors.advanced_hybrid_extractor import AdvancedHybridExtractor
                self.entity_extractor = AdvancedHybridExtractor(
                    use_gliner=True,
                    use_rebel=True,
                    use_llm=True,
                    api_key=settings.google_api_key  # Pass API key for GeminiPool
                )
            except ImportError:
                logger.warning("Advanced extractors not available, falling back to hybrid")
                from ..extractors.hybrid_extractor import HybridEntityExtractor
                self.entity_extractor = HybridEntityExtractor()
        else:
            logger.info("Using basic hybrid extraction")
            from ..extractors.hybrid_extractor import HybridEntityExtractor
            self.entity_extractor = HybridEntityExtractor()
        
        self.domain = domain
        
        # Processing statistics
        self.videos_processed = 0
        self.total_cost = 0.0
    
    async def search(
        self, 
        query: str, 
        max_results: int = 5,
        site: str = "youtube"
    ) -> List[VideoIntelligence]:
        """
        Search for videos and analyze them.
        
        Currently supports YouTube search. For other platforms,
        use process_url() with direct URLs.
        
        Args:
            query: Search query
            max_results: Maximum number of videos to process
            site: Site to search (currently only 'youtube')
            
        Returns:
            List of VideoIntelligence objects ready for Chimera
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
            
            # Process videos in parallel
            tasks = [
                self._process_video(video.url)
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
        Process a video from ANY supported platform (1800+ sites).
        
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
            VideoIntelligence object or None if failed
        """
        # Check if URL is supported
        if not self.video_client.is_supported_url(video_url):
            logger.error(f"URL not supported by yt-dlp: {video_url}")
            return None
            
        if self.progress_hook:
            self.progress_hook({"description": "Downloading media..."})
        
        return await self._process_video(video_url, progress_state)
    
    async def _process_video(self, video_url: str, progress_state: Optional[Dict[str, Any]] = None) -> Optional[VideoIntelligence]:
        """Process a single video URL."""
        try:
            total_steps = 4  # download, transcribe, extract, facts
            current_step = 0

            def _update_progress(description: str):
                nonlocal current_step
                current_step += 1
                progress_percentage = int((current_step / total_steps) * 100)
                if self.progress_hook:
                    self.progress_hook({"description": description, "progress": progress_percentage})
                elif progress_state and self.progress_tracker:
                    self.progress_tracker.update_phase(progress_state, description.lower().replace(" ", "_"), description)

            # Check cache first
            cache_key = self._get_cache_key(video_url)
            if self.use_cache:
                cached_result = self._load_from_cache(cache_key)
                if cached_result:
                    logger.info(f"Using cached result for: {video_url}")
                    if self.progress_tracker and progress_state:
                        self.progress_tracker.log_info("Using cached result")
                    return cached_result
            
            logger.info(f"Processing video: {video_url}")
            
            _update_progress("Downloading media")
            # Determine processing mode
            processing_mode = self.mode
            if self.mode == "auto" and self.mode_detector:
                # Auto-detect best mode based on video content
                # For now, use filename heuristics (full detection would need video sample)
                if any(keyword in video_url.lower() for keyword in ["tutorial", "code", "presentation", "slides"]):
                    processing_mode = "video"
                    logger.info("Auto-detected video mode (likely has visual content)")
                else:
                    processing_mode = "audio"
                    logger.info("Auto-detected audio mode (likely talking head)")
            
            # Download media based on mode
            if processing_mode == "video":
                logger.info("Downloading full video for visual analysis...")
                if self.progress_tracker:
                    self.progress_tracker.log_info("Downloading full video for visual analysis...")
                media_file, metadata = await self.video_client.download_video(
                    video_url,
                    output_dir=self.cache_dir
                )
            else:
                logger.info("Downloading audio only (fast & efficient)...")
                if self.progress_tracker:
                    self.progress_tracker.log_info("Downloading audio only (fast & efficient)...")
                media_file, metadata = await self.video_client.download_audio(
                    video_url,
                    output_dir=self.cache_dir
                )
            
            try:
                _update_progress("Transcribing media")
                # Transcribe and analyze based on mode
                if processing_mode == "video":
                    analysis = await self.transcriber.transcribe_video(
                        media_file,
                        metadata.duration
                    )
                else:
                    analysis = await self.transcriber.transcribe_audio(
                        media_file,
                        metadata.duration
                    )
                
                # Log mode used and update cost tracker
                logger.info(f"Transcribed using {processing_mode} mode, cost: ${analysis['processing_cost']:.4f}")
                if self.progress_tracker:
                    self.progress_tracker.update_cost(analysis['processing_cost'])
                
                # Update cost tracking
                self.total_cost += analysis['processing_cost']
                self.videos_processed += 1
                
                # Generate segments from transcript
                segments = self._generate_segments(
                    analysis['transcript'],
                    metadata.duration,
                    segment_length=30  # 30-second segments
                )
                
                # Create VideoTranscript object with segments
                transcript = VideoTranscript(
                    full_text=analysis['transcript'],
                    segments=segments,  # Now populated!
                    language=analysis.get('language', 'en'),
                    confidence=analysis.get('confidence_score', 0.95)
                )
                
                # Convert key points to KeyPoint objects
                key_points = []
                for kp in analysis.get('key_points', []):
                    key_points.append(KeyPoint(
                        timestamp=kp.get('timestamp', 0),
                        text=kp.get('text', ''),
                        importance=kp.get('importance', 0.8),
                        context=kp.get('context')
                    ))
                
                # Convert topics to Topic objects if they're strings
                topics = []
                raw_topics = analysis.get('topics', [])
                for topic in raw_topics:
                    if isinstance(topic, str):
                        # Convert string to Topic object
                        topics.append(Topic(
                            name=topic,
                            confidence=0.85  # Default confidence for Gemini-extracted topics
                        ))
                    elif isinstance(topic, dict):
                        # Already a dict, convert to Topic
                        topics.append(Topic(
                            name=topic.get('name', ''),
                            confidence=topic.get('confidence', 0.85)
                        ))
                    else:
                        # Already a Topic object
                        topics.append(topic)
                
                # Create initial VideoIntelligence object
                video_intelligence = VideoIntelligence(
                    metadata=metadata,
                    transcript=transcript,
                    summary=analysis['summary'],
                    key_points=key_points,
                    entities=[],  # Will be populated by extractor
                    topics=topics,
                    sentiment=None,
                    confidence_score=analysis.get('confidence_score', 0.95),
                    processing_time=analysis['processing_time'],
                    processing_cost=analysis['processing_cost']
                )
                
                # Run intelligence extraction if requested
                if self.use_advanced_extraction and hasattr(self.entity_extractor, 'extract_all'):
                    _update_progress("Extracting intelligence")
                    logger.info(f"Extracting intelligence with advanced extractor (domain={self.domain})...")
                    try:
                        # Advanced extraction now runs here, for each video
                        video_intelligence = await self.entity_extractor.extract_all(
                            video_intelligence, domain=self.domain
                        )
                        
                        # Optional: Clean the graph with Gemini
                        if video_intelligence.knowledge_graph and self.clean_graph:
                            logger.info("Cleaning knowledge graph with AI...")
                            if self.progress_tracker and progress_state:
                                self.progress_tracker.update_phase(progress_state, "clean", "Cleaning knowledge graph...")
                            
                            from ..extractors.graph_cleaner import GraphCleaner
                            cleaner = GraphCleaner()
                            video_intelligence = await cleaner.clean_knowledge_graph(video_intelligence)
                            logger.info("Knowledge graph cleaned successfully :-)")

                    except Exception as e:
                        logger.error(f"Advanced intelligence extraction failed: {e}", exc_info=True)
                        if self.progress_tracker:
                            self.progress_tracker.log_error(f"Advanced extraction failed: {e}")
                
                # Update cost with extraction costs
                if hasattr(self.entity_extractor, 'get_total_cost'):
                    video_intelligence.processing_cost += self.entity_extractor.get_total_cost()
                
                # Cache the result
                self._save_to_cache(cache_key, video_intelligence)
                
                # Record performance metrics if monitor is enabled
                if self.performance_monitor:
                    self.performance_monitor.record_metric(
                        "extraction_quality",
                        {
                            "entities": len(video_intelligence.entities),
                            "relationships": len(getattr(video_intelligence, 'relationships', [])),
                            "key_points": len(video_intelligence.key_points),
                            "duration": video_intelligence.metadata.duration,
                        },
                        platform=extract_platform_from_url(video_url),
                        video_title=video_intelligence.metadata.title
                    )

                return video_intelligence
                
            finally:
                # Clean up media file
                try:
                    os.remove(media_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to process video {video_url}: {e}")
            if self.progress_tracker:
                self.progress_tracker.log_error(f"Failed to process video: {e}")
            return None
    
    def _get_cache_key(self, video_url: str) -> str:
        """Generate cache key from URL."""
        # Simple hash of URL
        import hashlib
        return hashlib.md5(video_url.encode()).hexdigest()
    
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
        """Get processing statistics."""
        return {
            "videos_processed": self.videos_processed,
            "total_cost": self.total_cost,
            "average_cost": self.total_cost / max(1, self.videos_processed),
            "cache_dir": self.cache_dir,
            "supported_sites": "1800+ (via yt-dlp)"
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
        
        segments = []
        
        for i in range(0, len(words), int(words_per_segment)):
            # Calculate time boundaries
            start_time = (i / len(words)) * duration
            end_time = min(((i + words_per_segment) / len(words)) * duration, duration)
            
            # Get segment text
            segment_words = words[i:int(i + words_per_segment)]
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

        self._create_manifest_file(video, paths)

        logger.info(f"Saved all formats to: {paths['directory']}")
        return paths

    def _get_video_metadata_dict(self, video: VideoIntelligence) -> Dict[str, Any]:
        """Extracts video metadata into a dictionary."""
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
                "confidence": video.transcript.confidence
            },
            "analysis": {
                "summary": video.summary,
                "key_points": [kp.dict() for kp in video.key_points],
                "entities": [e.dict() for e in video.entities],
                "topics": [t.dict() if hasattr(t, 'dict') else {"name": t.name, "confidence": t.confidence} for t in video.topics],
                "sentiment": video.sentiment
            },
            "processing": {
                "cost": video.processing_cost,
                "time": video.processing_time,
                "processed_at": datetime.now().isoformat(),
                "model": "gemini-1.5-flash",
                "extractor": "advanced_hybrid_v2.2" if hasattr(self.entity_extractor, 'extract_all') else "basic_hybrid"
            }
        }
        if hasattr(video, 'relationships') and video.relationships:
            full_data["relationships"] = [r.dict() for r in video.relationships]
        if hasattr(video, 'knowledge_graph') and video.knowledge_graph:
            full_data["knowledge_graph"] = video.knowledge_graph
        if hasattr(video, 'key_moments') and video.key_moments:
            full_data["key_facts"] = video.key_moments
        if hasattr(video, 'processing_stats') and video.processing_stats:
            full_data["extraction_stats"] = video.processing_stats
        
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
        all_entities = list(video.entities) + list(getattr(video, 'custom_entities', []))
        
        # Entities JSON
        entities_data = {
            "video_url": video.metadata.url,
            "video_title": video.metadata.title,
            "entities": [
                {
                    "name": e.name,
                    "type": e.type,
                    "confidence": e.confidence,
                    "source": getattr(e, 'source', 'unknown'),
                    "properties": e.properties,
                    "timestamp": e.timestamp
                } for e in all_entities
            ],
            "topics": [t.dict() if hasattr(t, 'dict') else {"name": t.name, "confidence": t.confidence} for t in video.topics],
            "key_facts": [kp.text for kp in video.key_points[:5]]
        }
        with open(paths["entities"], 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, indent=2)

        # Entities CSV
        entities_csv_path = paths["directory"] / "entities.csv"
        with open(entities_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "type", "confidence", "source", "timestamp"])
            for entity in all_entities:
                writer.writerow([
                    entity.name,
                    entity.type,
                    getattr(entity, 'confidence', 0.0),
                    getattr(entity, 'source', 'unknown'),
                    getattr(entity, 'timestamp', '')
                ])
        paths["entities_csv"] = entities_csv_path
        logger.info(f"Saved {len(all_entities)} entities to JSON and CSV :-)")

    def _save_relationships_files(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves relationships.json and relationships.csv if they exist."""
        if not hasattr(video, 'relationships') or not video.relationships:
            return

        # Relationships JSON
        relationships_path = paths["directory"] / "relationships.json"
        relationships_data = {
            "video_url": video.metadata.url,
            "video_title": video.metadata.title,
            "relationships": [r.dict() for r in video.relationships],
            "total_count": len(video.relationships)
        }
        with open(relationships_path, 'w', encoding='utf-8') as f:
            json.dump(relationships_data, f, default=str, indent=2)
        paths["relationships"] = relationships_path

        # Relationships CSV
        relationships_csv_path = paths["directory"] / "relationships.csv"
        with open(relationships_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["subject", "predicate", "object", "confidence", "context"])
            for rel in video.relationships:
                # Safe handling of context field that might be None
                context = getattr(rel, 'context', '') or ''
                context_truncated = context[:100] if context else ''
                
                writer.writerow([
                    rel.subject,
                    rel.predicate,
                    rel.object,
                    getattr(rel, 'confidence', 0.0),
                    context_truncated
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
                f.write(f"{i}. [{source}] {fact['fact']} (confidence: {fact['confidence']:.2f})\n")
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
        entity_map = {e.name: e for e in all_entities_for_graph}
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
                    f.write(f"| {entity.name} | {conf_bar} {conf:.2f} | {source} |\n")
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
            ("chimera_format.json", "JSON", "Chimera-compatible format")
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
            "chimera": {"path": "chimera_format.json", "format": "json", "description": "Chimera-compatible format"}
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
            json.dump(manifest, f, indent=2)

    def _save_chimera_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves the Chimera-compatible format file."""
        chimera_path = paths["directory"] / "chimera_format.json"
        chimera_data = self._to_chimera_format(video)
        with open(chimera_path, 'w', encoding='utf-8') as f:
            json.dump(chimera_data, f, indent=2)
        paths["chimera"] = chimera_path
    
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
                "processing_cost": video.processing_cost
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
                "name": entity.name,
                "type": entity.type,
                "confidence": round(entity.confidence, 3),
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
                "average_confidence": round(sum(e['confidence'] for e in entities_with_sources) / len(entities_with_sources), 3) if entities_with_sources else 0,
                "high_confidence_entities": len([e for e in entities_with_sources if e['confidence'] > 0.8]),
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
            fieldnames = ['name', 'type', 'confidence', 'source', 'extraction_methods', 'aliases', 'is_normalized']
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

        # 4. Save Knowledge Panels (NEW v2.14.0)
        if collection.knowledge_panels:
            # Save complete knowledge panels collection
            panels_path = collection_path / "knowledge_panels.json"
            with open(panels_path, 'w', encoding='utf-8') as f:
                f.write(collection.knowledge_panels.model_dump_json(indent=2))
            saved_paths["knowledge_panels"] = panels_path
            logger.info(f"Saved knowledge panels to {panels_path}")
            
            # Save individual entity panels as separate files for easy access
            panels_dir = collection_path / "entity_panels"
            panels_dir.mkdir(exist_ok=True)
            
            for panel in collection.knowledge_panels.panels:
                panel_filename = f"{panel.entity_name.replace(' ', '_').replace('/', '_').lower()}.json"
                panel_path = panels_dir / panel_filename
                with open(panel_path, 'w', encoding='utf-8') as f:
                    f.write(panel.model_dump_json(indent=2))
            
            saved_paths["entity_panels_dir"] = panels_dir
            logger.info(f"Saved {len(collection.knowledge_panels.panels)} individual entity panels to {panels_dir}")
            
            # Save a human-readable summary of all panels
            panels_summary_path = collection_path / "knowledge_panels_summary.md"
            self._save_knowledge_panels_summary(collection.knowledge_panels, panels_summary_path)
            saved_paths["panels_summary"] = panels_summary_path

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
                flow_filename = f"{flow.video_id}_{flow.video_index}.json"
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

    def _save_knowledge_panels_summary(self, panels_collection, output_path: Path):
        """Generate a human-readable markdown summary of all knowledge panels."""
        from clipscribe.models import KnowledgePanelCollection
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Knowledge Panels Summary: {panels_collection.collection_title}\n\n")
            f.write(f"**Collection ID:** {panels_collection.collection_id}\n")
            f.write(f"**Created:** {panels_collection.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Entities:** {panels_collection.total_entities}\n")
            f.write(f"**High Confidence Entities:** {panels_collection.high_confidence_entities}\n\n")
            
            # Collection-level analysis
            f.write("## 📊 Collection Analysis\n\n")
            f.write("### Panel Summary\n")
            f.write(f"{panels_collection.panel_summary}\n\n")
            
            f.write("### Key Entities Analysis\n")
            f.write(f"{panels_collection.key_entities_analysis}\n\n")
            
            if panels_collection.entity_network_insights:
                f.write("### Entity Network Insights\n")
                for insight in panels_collection.entity_network_insights:
                    f.write(f"- {insight}\n")
                f.write("\n")
            
            # Individual entity panels
            f.write("## 🎯 Individual Entity Profiles\n\n")
            
            # Sort panels by significance
            sorted_panels = sorted(panels_collection.panels, 
                                 key=lambda p: (p.source_videos_count, p.total_mentions, p.confidence_score), 
                                 reverse=True)
            
            for i, panel in enumerate(sorted_panels, 1):
                # Panel header
                f.write(f"### {i}. {panel.entity_name} ({panel.entity_type})\n\n")
                
                # Quick stats
                f.write("**Quick Stats:**\n")
                f.write(f"- **Videos:** {panel.source_videos_count}\n")
                f.write(f"- **Total Mentions:** {panel.total_mentions}\n")
                f.write(f"- **Confidence:** {panel.confidence_score:.2f}\n")
                f.write(f"- **Synthesis Quality:** {panel.synthesis_quality}\n\n")
                
                # Executive summary
                f.write("**Executive Summary:**\n")
                f.write(f"{panel.executive_summary}\n\n")
                
                # Key attributes
                if panel.key_attributes:
                    f.write("**Key Attributes:**\n")
                    for attr, value in panel.key_attributes.items():
                        f.write(f"- **{attr}:** {value}\n")
                    f.write("\n")
                
                # Aliases
                if panel.aliases_and_names and len(panel.aliases_and_names) > 1:
                    f.write("**Alternative Names:**\n")
                    aliases = [name for name in panel.aliases_and_names if name != panel.entity_name]
                    if aliases:
                        f.write(f"{', '.join(aliases)}\n\n")
                
                # Top activities
                if panel.activities:
                    f.write("**Top Activities:**\n")
                    for activity in panel.activities[:3]:  # Top 3
                        f.write(f"- {activity.description} *(from {activity.video_title})*\n")
                    if len(panel.activities) > 3:
                        f.write(f"- ... and {len(panel.activities) - 3} more activities\n")
                    f.write("\n")
                
                # Key relationships
                if panel.relationships:
                    f.write("**Key Relationships:**\n")
                    for rel in panel.relationships[:5]:  # Top 5
                        f.write(f"- **{rel.related_entity}** ({rel.relationship_type}) - strength: {rel.relationship_strength:.2f}\n")
                    if len(panel.relationships) > 5:
                        f.write(f"- ... and {len(panel.relationships) - 5} more relationships\n")
                    f.write("\n")
                
                # Strategic insights
                if panel.strategic_insights:
                    f.write("**Strategic Insights:**\n")
                    for insight in panel.strategic_insights:
                        f.write(f"- {insight}\n")
                    f.write("\n")
                
                # Information gaps
                if panel.information_gaps:
                    f.write("**Information Gaps:**\n")
                    for gap in panel.information_gaps:
                        f.write(f"- {gap}\n")
                    f.write("\n")
                
                f.write("---\n\n")
            
            # Footer
            f.write("## 📁 Files Generated\n\n")
            f.write("- `knowledge_panels.json` - Complete structured data for all panels\n")
            f.write("- `entity_panels/` - Individual JSON files for each entity\n")
            f.write("- `knowledge_panels_summary.md` - This human-readable summary\n\n")
            
            f.write("---\n")
            f.write(f"*Generated by ClipScribe v2.14.0 Knowledge Panels on {panels_collection.created_at.strftime('%Y-%m-%d at %H:%M:%S')}*\n")
        
        logger.info(f"Saved knowledge panels summary to {output_path}") 

    def _save_information_flow_summary(self, flow_map, output_path: Path):
        """Generate a human-readable markdown summary of information flow maps."""
        from clipscribe.models import InformationFlowMap
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Information Flow Map: {flow_map.collection_title}\n\n")
            f.write(f"**Collection ID:** {flow_map.collection_id}\n")
            f.write(f"**Created:** {flow_map.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Videos:** {flow_map.total_videos}\n")
            f.write(f"**Concepts Tracked:** {flow_map.total_concepts}\n")
            f.write(f"**Flow Patterns Identified:** {flow_map.total_flow_patterns}\n\n")
            
            # Collection-level analysis
            f.write("## 📊 Flow Analysis Summary\n\n")
            f.write("### Overall Flow Pattern\n")
            f.write(f"{flow_map.flow_pattern_summary}\n\n")
            
            f.write("### Learning Progression Analysis\n")
            f.write(f"{flow_map.learning_progression_analysis}\n\n")
            
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
                    f.write(f"**Theme:** {cluster.cluster_theme}\n")
                    f.write(f"**Concepts:** {', '.join(cluster.concepts)}\n")
                    f.write(f"**Average Maturity:** {cluster.average_maturity:.2f}\n\n")
            
            # Evolution paths
            if flow_map.evolution_paths:
                f.write("## 📈 Concept Evolution Paths\n\n")
                # Sort by significance (video span × maturity evolution)
                sorted_paths = sorted(flow_map.evolution_paths, 
                                    key=lambda p: (p.video_span * (p.final_maturity - p.initial_maturity)), 
                                    reverse=True)
                
                for i, path in enumerate(sorted_paths[:10], 1):  # Top 10 paths
                    f.write(f"### {i}. {path.concept_name}\n")
                    f.write(f"**Evolution:** {path.initial_maturity_level} → {path.final_maturity_level}\n")
                    f.write(f"**Video Span:** {path.video_span} videos\n")
                    f.write(f"**Maturity Change:** +{path.final_maturity - path.initial_maturity:.1f}\n")
                    
                    # Show evolution stages
                    if path.evolution_stages:
                        f.write("**Journey:**\n")
                        for stage in path.evolution_stages:
                            f.write(f"- Video {stage['video_index']}: {stage['maturity_level']} "
                                   f"(maturity: {stage['maturity_score']:.1f})\n")
                    f.write("\n")
                
                if len(flow_map.evolution_paths) > 10:
                    f.write(f"*... and {len(flow_map.evolution_paths) - 10} more evolution paths*\n\n")
            
            # Individual video flows
            f.write("## 📹 Video-by-Video Information Flows\n\n")
            for i, flow in enumerate(flow_map.information_flows):
                f.write(f"### Video {flow.video_index + 1}: {flow.video_title}\n")
                
                # Quick stats
                f.write("**Quick Stats:**\n")
                f.write(f"- **Concepts Introduced:** {len(flow.concepts_introduced)}\n")
                f.write(f"- **Concepts Developed:** {len(flow.concepts_developed)}\n")
                f.write(f"- **Concepts Concluded:** {len(flow.concepts_concluded)}\n")
                f.write(f"- **Total Dependencies:** {len(flow.concept_dependencies)}\n\n")
                
                # Concept details
                if flow.concepts_introduced:
                    f.write("**New Concepts Introduced:**\n")
                    for concept in flow.concepts_introduced[:5]:
                        f.write(f"- **{concept.name}** ({concept.maturity_level}) - {concept.context[:100]}...\n")
                    if len(flow.concepts_introduced) > 5:
                        f.write(f"- ... and {len(flow.concepts_introduced) - 5} more\n")
                    f.write("\n")
                
                if flow.concepts_developed:
                    f.write("**Concepts Further Developed:**\n")
                    for concept in flow.concepts_developed[:5]:
                        f.write(f"- **{concept.name}** → {concept.maturity_level}\n")
                    if len(flow.concepts_developed) > 5:
                        f.write(f"- ... and {len(flow.concepts_developed) - 5} more\n")
                    f.write("\n")
                
                # Key dependencies
                if flow.concept_dependencies:
                    f.write("**Key Concept Dependencies:**\n")
                    for dep in flow.concept_dependencies[:3]:
                        f.write(f"- {dep.from_concept} → {dep.to_concept} ({dep.dependency_type})\n")
                    if len(flow.concept_dependencies) > 3:
                        f.write(f"- ... and {len(flow.concept_dependencies) - 3} more dependencies\n")
                    f.write("\n")
                
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