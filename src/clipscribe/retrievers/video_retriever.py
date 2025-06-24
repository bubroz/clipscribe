"""ClipScribe Video Intelligence Retriever - Process videos from ANY platform."""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import json
from pathlib import Path
import networkx as nx

from ..models import VideoIntelligence, VideoTranscript, KeyPoint, Entity, Topic, Relationship
from .universal_video_client import UniversalVideoClient
from .transcriber import GeminiFlashTranscriber
from ..utils.filename import create_output_filename, create_output_structure, extract_platform_from_url
from ..extractors import HybridEntityExtractor, AdvancedHybridExtractor

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
        enhance_transcript: bool = False
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
        
        # Initialize clients
        self.video_client = UniversalVideoClient()
        self.transcriber = GeminiFlashTranscriber()
        
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
                    api_key=settings.GOOGLE_API_KEY  # Pass API key for GeminiPool
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
    
    async def process_url(self, video_url: str) -> Optional[VideoIntelligence]:
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
            
        Returns:
            VideoIntelligence object or None if failed
        """
        # Check if URL is supported
        if not self.video_client.is_supported_url(video_url):
            logger.error(f"URL not supported by yt-dlp: {video_url}")
            return None
            
        return await self._process_video(video_url)
    
    async def _process_video(self, video_url: str) -> Optional[VideoIntelligence]:
        """Process a single video URL."""
        try:
            # Check cache first
            cache_key = self._get_cache_key(video_url)
            if self.use_cache:
                cached_result = self._load_from_cache(cache_key)
                if cached_result:
                    logger.info(f"Using cached result for: {video_url}")
                    return cached_result
            
            logger.info(f"Processing video: {video_url}")
            
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
                media_file, metadata = await self.video_client.download_video(
                    video_url,
                    output_dir=self.cache_dir
                )
            else:
                logger.info("Downloading audio only (fast & efficient)...")
                media_file, metadata = await self.video_client.download_audio(
                    video_url,
                    output_dir=self.cache_dir
                )
            
            try:
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
                
                # Log mode used
                logger.info(f"Transcribed using {processing_mode} mode, cost: ${analysis['processing_cost']:.4f}")
                
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
                if self.use_advanced_extraction:
                    logger.info(f"Extracting intelligence with advanced extractor (domain={self.domain})...")
                    try:
                        if hasattr(self.entity_extractor, 'extract_all'):
                            # Advanced extraction with relationships and knowledge graph
                            video_intelligence = await self.entity_extractor.extract_all(video_intelligence, domain=self.domain)
                            
                            # Optional: Clean the graph with Gemini
                            if hasattr(video_intelligence, 'knowledge_graph') and video_intelligence.knowledge_graph:
                                # Clean if explicitly requested OR if graph is large and messy
                                should_clean = self.clean_graph or (
                                    video_intelligence.knowledge_graph.get('node_count', 0) > 100 and
                                    len(getattr(video_intelligence, 'relationships', [])) > 150
                                )
                                
                                if should_clean:
                                    try:
                                        from ..extractors.graph_cleaner import GraphCleaner
                                        cleaner = GraphCleaner()
                                        video_intelligence = await cleaner.clean_knowledge_graph(video_intelligence)
                                        logger.info("Knowledge graph cleaned with AI :-)")
                                    except Exception as e:
                                        logger.warning(f"Graph cleaning failed: {e}, using uncleaned graph")
                        
                        logger.info(
                            f"Extraction complete: {len(video_intelligence.entities)} basic entities, "
                            f"{len(getattr(video_intelligence, 'custom_entities', []))} custom entities, "
                            f"{len(getattr(video_intelligence, 'relationships', []))} relationships, "
                            f"{getattr(video_intelligence.knowledge_graph, 'node_count', 0) if hasattr(video_intelligence, 'knowledge_graph') else 0} graph nodes :-)"
                        )
                    except Exception as e:
                        logger.error(f"Entity extraction failed: {e}")
                        # Continue without entities rather than failing completely
                
                # Update cost with extraction costs
                if hasattr(self.entity_extractor, 'get_total_cost'):
                    video_intelligence.processing_cost += self.entity_extractor.get_total_cost()
                
                # Cache the result
                self._save_to_cache(cache_key, video_intelligence)
                
                return video_intelligence
                
            finally:
                # Clean up media file
                try:
                    os.remove(media_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to process video {video_url}: {e}")
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
        Save video data in all formats with structured directory.
        
        Creates a machine-readable directory structure:
        - {date}_{platform}_{video_id}/
            - transcript.txt (plain text)
            - transcript.json (full data)
            - metadata.json (video metadata)
            - entities.json (extracted entities)
            - manifest.json (file index)
            
        Args:
            video: VideoIntelligence object
            output_dir: Base output directory
            include_chimera_format: Include Chimera-compatible format
            
        Returns:
            Dictionary of file types to paths
        """
        # Create metadata dict
        metadata = {
            "title": video.metadata.title,
            "url": video.metadata.url,
            "channel": video.metadata.channel,
            "duration": video.metadata.duration,
            "published_at": video.metadata.published_at.isoformat() if video.metadata.published_at else None,
            "view_count": video.metadata.view_count,
            "description": video.metadata.description
        }
        
        # Create directory structure
        paths = create_output_structure(metadata, output_dir)
        
        # Save transcript in all formats
        # 1. Plain text
        with open(paths["transcript_txt"], 'w', encoding='utf-8') as f:
            f.write(video.transcript.full_text)
        
        # 2. Full JSON (includes everything)
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
        
        # Add v2.2 features if available
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
        
        # 3. Metadata file (lighter than full JSON)
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
        
        # 6. Entities file (for knowledge graph)
        entities_data = {
            "video_url": video.metadata.url,
            "video_title": video.metadata.title,
            "entities": [
                {
                    "name": e.name,
                    "type": e.type,
                    "confidence": e.confidence,
                    "properties": e.properties,
                    "timestamp": e.timestamp
                } for e in video.entities
            ],
            "topics": [t.dict() if hasattr(t, 'dict') else {"name": t.name, "confidence": t.confidence} for t in video.topics],
            "key_facts": [kp.text for kp in video.key_points[:5]]  # Top 5 key points
        }
        
        with open(paths["entities"], 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, indent=2)
        
        # 7. Relationships file (NEW in v2.2)
        if hasattr(video, 'relationships') and video.relationships:
            relationships_path = paths["directory"] / "relationships.json"
            relationships_data = {
                "video_url": video.metadata.url,
                "video_title": video.metadata.title,
                "relationships": [
                    {
                        "subject": r.subject,
                        "predicate": r.predicate,
                        "object": r.object,
                        "confidence": r.confidence,
                        "context": r.context
                    } for r in video.relationships
                ],
                "total_count": len(video.relationships)
            }
            with open(relationships_path, 'w', encoding='utf-8') as f:
                json.dump(relationships_data, f, indent=2)
            paths["relationships"] = relationships_path
            logger.info(f"Saved {len(video.relationships)} relationships :-)")
        
        # 8. Knowledge Graph file (NEW in v2.2)
        if hasattr(video, 'knowledge_graph') and video.knowledge_graph:
            graph_path = paths["directory"] / "knowledge_graph.json"
            with open(graph_path, 'w', encoding='utf-8') as f:
                json.dump(video.knowledge_graph, f, indent=2)
            paths["knowledge_graph"] = graph_path
            logger.info(
                f"Saved knowledge graph with {video.knowledge_graph.get('node_count', 0)} nodes "
                f"and {video.knowledge_graph.get('edge_count', 0)} edges :-)"
            )
            
            # Generate GEXF file for Gephi
            gexf_path = paths["directory"] / "knowledge_graph.gexf"
            try:
                # Create GEXF manually to ensure correct format
                gexf_content = self._generate_gexf_content(video.knowledge_graph)
                with open(gexf_path, 'w', encoding='utf-8') as f:
                    f.write(gexf_content)
                paths["gexf"] = gexf_path
                logger.info(f"Saved GEXF file for Gephi visualization :-)")
            except Exception as e:
                logger.warning(f"Failed to generate GEXF: {e}")
        
        # 9. Facts file (NEW in v2.2)
        if hasattr(video, 'key_moments') and video.key_moments:
            facts_path = paths["directory"] / "facts.txt"
            with open(facts_path, 'w', encoding='utf-8') as f:
                f.write("# Key Facts Extracted from Video\n\n")
                f.write(f"Video: {video.metadata.title}\n")
                f.write(f"URL: {video.metadata.url}\n")
                f.write(f"Extracted: {datetime.now().isoformat()}\n\n")
                
                for i, fact in enumerate(video.key_moments, 1):
                    f.write(f"{i}. {fact['fact']} (confidence: {fact['confidence']:.2f})\n")
            paths["facts"] = facts_path
            logger.info(f"Saved {len(video.key_moments)} key facts :-)")
        
        # 10. Manifest file (index of all files)
        manifest = {
            "version": "2.2",
            "created_at": datetime.now().isoformat(),
            "video": {
                "title": video.metadata.title,
                "url": video.metadata.url,
                "platform": extract_platform_from_url(video.metadata.url)
            },
            "extraction_stats": video.processing_stats if hasattr(video, 'processing_stats') else {},
            "files": {
                "transcript_txt": {
                    "path": "transcript.txt",
                    "format": "plain_text",
                    "size": os.path.getsize(paths["transcript_txt"])
                },
                "transcript_json": {
                    "path": "transcript.json",
                    "format": "json",
                    "size": os.path.getsize(paths["transcript_json"])
                },
                "metadata": {
                    "path": "metadata.json",
                    "format": "json",
                    "size": os.path.getsize(paths["metadata"])
                },
                "entities": {
                    "path": "entities.json",
                    "format": "json",
                    "size": os.path.getsize(paths["entities"])
                }
            }
        }
        
        # Add new v2.2 files to manifest if they exist
        if "relationships" in paths:
            manifest["files"]["relationships"] = {
                "path": "relationships.json",
                "format": "json",
                "size": os.path.getsize(paths["relationships"]),
                "count": len(video.relationships) if hasattr(video, 'relationships') else 0
            }
        
        if "knowledge_graph" in paths:
            manifest["files"]["knowledge_graph"] = {
                "path": "knowledge_graph.json",
                "format": "json",
                "size": os.path.getsize(paths["knowledge_graph"]),
                "nodes": video.knowledge_graph.get('node_count', 0) if hasattr(video, 'knowledge_graph') else 0,
                "edges": video.knowledge_graph.get('edge_count', 0) if hasattr(video, 'knowledge_graph') else 0
            }
        
        if "gexf" in paths:
            manifest["files"]["knowledge_graph_gexf"] = {
                "path": "knowledge_graph.gexf",
                "format": "gexf",
                "size": os.path.getsize(paths["gexf"]),
                "description": "Gephi-compatible graph file"
            }
        
        if "facts" in paths:
            manifest["files"]["facts"] = {
                "path": "facts.txt",
                "format": "plain_text",
                "size": os.path.getsize(paths["facts"]),
                "count": len(video.key_moments) if hasattr(video, 'key_moments') else 0
            }
        
        with open(paths["manifest"], 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        # 8. Chimera-compatible format (if requested)
        if include_chimera_format:
            chimera_path = paths["directory"] / "chimera_format.json"
            chimera_data = self._to_chimera_format(video)
            with open(chimera_path, 'w', encoding='utf-8') as f:
                json.dump(chimera_data, f, indent=2)
            paths["chimera"] = chimera_path
        
        logger.info(f"Saved all formats to: {paths['directory']}")
        
        return paths
    
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
        gexf_content += '<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:viz="http://www.gexf.net/1.2draft/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd" version="1.2">\n'
        gexf_content += '  <meta lastmodifieddate="' + datetime.now().strftime('%Y-%m-%d') + '">\n'
        gexf_content += '    <creator>ClipScribe</creator>\n'
        gexf_content += '    <description>Knowledge graph extracted from video content</description>\n'
        gexf_content += '  </meta>\n'
        gexf_content += '  <graph mode="static" defaultedgetype="directed">\n'
        gexf_content += '    <attributes class="node">\n'
        gexf_content += '      <attribute id="0" title="Type" type="string"/>\n'
        gexf_content += '      <attribute id="1" title="Confidence" type="float"/>\n'
        gexf_content += '    </attributes>\n'
        gexf_content += '    <attributes class="edge">\n'
        gexf_content += '      <attribute id="0" title="Predicate" type="string"/>\n'
        gexf_content += '      <attribute id="1" title="Confidence" type="float"/>\n'
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
            gexf_content += f'        <viz:color r="{int(hex_color[1:3], 16)}" g="{int(hex_color[3:5], 16)}" b="{int(hex_color[5:7], 16)}" a="1.0"/>\n'
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