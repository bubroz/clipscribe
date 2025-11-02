"""
ClipScribe Video Intelligence Retriever v2 - Uses Voxtral-Grok HybridProcessor.
This is the main VideoIntelligenceRetriever using Voxtral-Grok pipeline.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import time

from ..models import VideoIntelligence, VideoMetadata
from ..core_data import CoreData, ProcessingInfo
from ..processors.hybrid_processor import HybridProcessor
from ..retrievers.universal_video_client import UniversalVideoClient
from ..retrievers.output_formatter import OutputFormatter
from ..retrievers.knowledge_graph_builder import KnowledgeGraphBuilder
from ..exporters.x_exporter import XContentGenerator
from ..exporters.tweet_styles import TweetStyleGenerator
from ..config.settings import Settings
from ..utils.logger_setup import setup_logging
from ..utils.processing_tracker import ProcessingTracker
from ..notifications.telegram_notifier import TelegramNotifier
from ..storage.gcs_uploader import GCSUploader

logger = logging.getLogger(__name__)


class VideoIntelligenceRetrieverV2:
    """
    Main retriever using the Voxtral-Grok pipeline.
    NO MORE GEMINI! This uses the uncensored HybridProcessor.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        use_cache: bool = True,
        settings: Optional[Settings] = None,
        on_phase_start: Optional[Callable[[str, str], None]] = None,
        on_phase_complete: Optional[Callable[[str, float], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
        **kwargs  # Ignore legacy parameters
    ):
        """
        Initialize the V2 retriever with HybridProcessor.
        
        Args:
            output_dir: Directory for outputs
            use_cache: Whether to cache transcripts
            settings: Configuration settings
            on_phase_start: Phase start callback
            on_phase_complete: Phase complete callback
            on_error: Error callback
        """
        self.settings = settings or Settings()
        self.output_dir = Path(output_dir or self.settings.output_dir)
        self.use_cache = use_cache
        
        # Callbacks
        self.on_phase_start = on_phase_start or (lambda p, m: None)
        self.on_phase_complete = on_phase_complete or (lambda p, c: None)
        self.on_error = on_error or (lambda p, e: None)
        
        # Initialize components
        self.video_client = UniversalVideoClient()
        self.processor = HybridProcessor(
            voxtral_model="voxtral-mini-2507",  # Best for transcription
            grok_model="grok-4-0709",  # Latest Grok-4
            cache_transcripts=use_cache
        )
        self.output_formatter = OutputFormatter()
        self.kg_builder = KnowledgeGraphBuilder()
        
        # Processing tracker for deduplication
        self.tracker = ProcessingTracker()
        
        # X content generators
        self.x_generator = XContentGenerator()
        self.style_generator = TweetStyleGenerator()
        
        # Store thumbnail and video from last download (for X drafts)
        self._last_thumbnail = None
        self._last_video = None
        
        # Telegram notifier (optional)
        self.telegram = TelegramNotifier()
        
        # GCS uploader (optional)
        self.gcs = GCSUploader()
        
        logger.info("VideoIntelligenceRetrieverV2 initialized with Voxtral-Grok pipeline")
    
    async def process_local_file(self, file_path: str, filename: Optional[str] = None) -> Optional[VideoIntelligence]:
        """
        Process a local video/audio file (for direct uploads).
        
        Args:
            file_path: Path to local video/audio file
            filename: Original filename (for metadata)
            
        Returns:
            VideoIntelligence object or None if failed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        start_time = time.time()
        
        try:
            # Create minimal metadata for local file
            from datetime import datetime
            import subprocess
            import tempfile
            
            metadata = VideoMetadata(
                url=f"local_upload:{file_path.name}",
                title=filename or file_path.stem,
                channel="Local Upload",
                channel_id="upload",
                published_at=datetime.now(),
                duration=0,  # Will be detected by processor
                video_id=file_path.stem[:11]  # Use filename as video_id
            )
            
            # Extract audio from video if it's a video file
            audio_path = file_path
            if file_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv']:
                logger.info(f"Extracting audio from video file: {file_path.name}")
                
                # Create temp audio file
                temp_audio = Path(tempfile.mkdtemp()) / f"{file_path.stem}.mp3"
                
                # Extract audio with ffmpeg
                cmd = [
                    'ffmpeg', '-i', str(file_path),
                    '-vn',  # No video
                    '-acodec', 'libmp3lame',
                    '-q:a', '2',  # Good quality
                    '-y',  # Overwrite
                    str(temp_audio)
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"ffmpeg failed: {stderr.decode()}")
                    raise Exception(f"Audio extraction failed: {stderr.decode()[:200]}")
                
                audio_path = temp_audio
                logger.info(f"✓ Audio extracted to: {temp_audio}")
            
            # Phase 1: Process with HybridProcessor (Voxtral + Grok)
            self.on_phase_start("Processing", "Transcribing uploaded file...")
            result = await self.processor.process_video(
                str(audio_path),
                metadata.__dict__ if hasattr(metadata, '__dict__') else metadata
            )
            
            # Calculate cost
            processing_time = time.time() - start_time
            processing_cost = 0.03  # Flat rate for uploads (no duration metadata yet)
            self.on_phase_complete("Processing", processing_cost)
            
            # Update processing info
            result.processing_cost = processing_cost
            result.processing_time = processing_time
            
            # Phase 2: Save outputs
            self.on_phase_start("Saving", "Writing output files...")
            saved_files = self._save_outputs(result)
            self.on_phase_complete("Saving", 0.0)
            
            # Store output directory
            result._output_directory = str(saved_files.get('directory'))
            
            logger.info(f"✅ Local file processing complete: {filename or file_path.name}")
            logger.info(f"   Cost: ${processing_cost:.4f}")
            logger.info(f"   Time: {processing_time:.1f}s")
            logger.info(f"   Output: {saved_files.get('directory')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Local file processing failed: {e}", exc_info=True)
            self.on_error("Processing", str(e))
            return None
    
    async def process_url(self, video_url: str, force_reprocess: bool = False) -> Optional[VideoIntelligence]:
        """
        Process a video URL with the uncensored pipeline.
        
        Args:
            video_url: URL of the video to process (or local file path for uploads)
            force_reprocess: If True, process even if already completed
            
        Returns:
            VideoIntelligence object or None if failed
        """
        # Detect if this is a local file path instead of URL
        if video_url.startswith('/') or video_url.startswith('./') or Path(video_url).exists():
            logger.info(f"Detected local file path, using process_local_file(): {video_url}")
            return await self.process_local_file(video_url, filename=Path(video_url).name)
        
        # Extract video ID for tracking
        video_id = self._extract_video_id(video_url)
        
        # Check if already processed
        if not force_reprocess and video_id and self.tracker.is_processed(video_id):
            output_location = self.tracker.get_output_location(video_id)
            logger.info(f"✓ Video {video_id} already processed. Output: {output_location}")
            logger.info("  Use --force to reprocess. Skipping...")
            return None  # Could load from output_location if needed
        
        # Mark as processing
        if video_id:
            self.tracker.mark_processing(video_id, video_url, status="downloading")
        
        start_time = time.time()
        temp_thumbnail = None  # Store thumbnail from temp dir
        temp_video = None  # Store full video for X posting
        
        try:
            # Phase 1: Download
            self.on_phase_start("Downloading", "Fetching video...")
            audio_path, metadata, temp_thumbnail, temp_video = await self._download_video(video_url)
            if not audio_path:
                return None
            
            # Store thumbnail and video for later X draft generation
            self._last_thumbnail = temp_thumbnail
            self._last_video = temp_video
            
            self.on_phase_complete("Downloading", 0.0)
            
            # Phase 2: Process with HybridProcessor (Voxtral + Grok)
            self.on_phase_start("Processing", "Transcribing with Voxtral...")
            result = await self.processor.process_video(
                str(audio_path),
                metadata.__dict__ if hasattr(metadata, '__dict__') else metadata
            )
            
            # Calculate cost
            processing_time = time.time() - start_time
            processing_cost = self._calculate_cost(metadata.duration)
            self.on_phase_complete("Processing", processing_cost)
            
            # Phase 3: Build knowledge graph
            self.on_phase_start("Building Graph", "Creating knowledge graph...")
            if hasattr(result, 'knowledge_graph'):
                # Already has graph from HybridProcessor
                pass
            else:
                # Build it if needed
                result.knowledge_graph = self.kg_builder.build_knowledge_graph(
                    result.entities,
                    result.relationships
                )
            self.on_phase_complete("Building Graph", 0.0)
            
            # Update processing info
            result.processing_cost = processing_cost
            result.processing_time = processing_time
            
            # Phase 4: Save outputs
            self.on_phase_start("Saving", "Writing output files...")
            saved_files = self._save_outputs(result)
            self.on_phase_complete("Saving", 0.0)
            
            # Store output directory for X draft generation
            result._output_directory = str(saved_files.get('directory'))
            
            logger.info(f"✅ Processing complete: {result.metadata.title}")
            logger.info(f"   Cost: ${processing_cost:.4f}")
            logger.info(f"   Time: {processing_time:.1f}s")
            logger.info(f"   Output: {saved_files.get('directory')}")
            
            # Mark as completed in tracker
            if video_id:
                self.tracker.mark_completed(
                    video_id,
                    output_dir=str(saved_files.get('directory')),
                    metadata={
                        'title': result.metadata.title,
                        'cost': processing_cost,
                        'processing_time': processing_time,
                        'entity_count': len(result.entities),
                        'relationship_count': len(result.relationships)
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            self.on_error("Processing", str(e))
            
            # Mark as failed in tracker
            if video_id:
                self.tracker.mark_failed(video_id, str(e))
            
            return None
    
    async def _download_video(self, video_url: str) -> tuple[Optional[Path], Optional[VideoMetadata], Optional[Path], Optional[Path]]:
        """Download video and extract metadata. Returns (audio_path, metadata, thumbnail_path, video_path)."""
        try:
            # Skip URL validation check - let download attempt with fallbacks handle it
            # The download_audio method has curl-cffi impersonation + Playwright fallback
            # which is more reliable than the validation check
            
            # Download audio (for transcription)
            try:
                audio_path, metadata = await self.video_client.download_audio(video_url)
            except Exception as download_error:
                # Check if it's a premiere/upcoming video
                error_msg = str(download_error)
                if 'Premieres in' in error_msg or 'live event will begin in' in error_msg:
                    logger.warning(f"Video is upcoming premiere/livestream: {video_url}")
                    logger.info("Will be available after premiere - skipping for now")
                    self.on_error("Downloading", "Video not yet available (premiere/livestream)")
                    return None, None, None, None
                else:
                    # Real download error - re-raise
                    raise
            
            # Find thumbnail and video file in temp
            temp_dir = Path(audio_path).parent
            video_id = self._extract_video_id(video_url)
            temp_thumbnail = None
            temp_video = None
            
            if video_id and temp_dir.exists():
                # Find thumbnail
                for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    thumbnails = list(temp_dir.glob(f'*{video_id}*{ext}'))
                    if thumbnails:
                        temp_thumbnail = thumbnails[0]
                        logger.info(f"Found thumbnail: {temp_thumbnail.name}")
                        break
                
                # Download full video for X posting (parallel with processing)
                logger.info("Downloading full video for X posting...")
                temp_video = await self.video_client.download_video_file(video_url, str(temp_dir))
                if temp_video:
                    temp_video = Path(temp_video)
            
            # Convert to VideoMetadata if needed
            if not isinstance(metadata, VideoMetadata):
                metadata = VideoMetadata(
                    url=video_url,
                    title=metadata.get('title', 'Unknown'),
                    channel=metadata.get('channel'),
                    duration=metadata.get('duration', 0),
                    platform=metadata.get('platform', 'youtube'),
                    published_at=metadata.get('published_at'),
                    view_count=metadata.get('view_count'),
                    description=metadata.get('description'),
                    thumbnail_url=metadata.get('thumbnail')
                )
            
            # Filter out Shorts by duration (≤60 seconds)
            if metadata.duration and metadata.duration <= 60:
                logger.warning(f"Skipping Short (duration={metadata.duration}s): {metadata.title}")
                self.on_error("Downloading", f"Video is a Short ({metadata.duration}s)")
                return None, None, None, None
            
            return Path(audio_path), metadata, temp_thumbnail, temp_video
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self.on_error("Downloading", str(e))
            return None, None, None, None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        if 'watch?v=' in url:
            return url.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        return None
    
    def _calculate_cost(self, duration: float) -> float:
        """
        Calculate processing cost for Voxtral + Grok.
        
        Based on actual costs:
        - Voxtral: ~$0.015-0.03 per video
        - Grok-4: ~$0.005-0.01 per video
        Total: ~$0.02-0.04 per video
        """
        # Simple estimate based on duration
        minutes = duration / 60
        
        # Voxtral cost (scales with duration)
        voxtral_cost = 0.015 + (minutes * 0.002)
        
        # Grok cost (mostly fixed for extraction)
        grok_cost = 0.008
        
        return voxtral_cost + grok_cost
    
    def _save_outputs(self, result: VideoIntelligence) -> Dict[str, Any]:
        """
        Save outputs using the new CoreData model.
        """
        # Convert objects to dictionaries for Pydantic
        video_metadata_dict = {
            "video_id": result.metadata.video_id,
            "title": result.metadata.title,
            "channel": result.metadata.channel,
            "channel_id": getattr(result.metadata, 'channel_id', None),
            "duration": result.metadata.duration,
            "platform": getattr(result.metadata, 'platform', 'youtube'),
            "url": result.metadata.url,
            "published_at": getattr(result.metadata, 'published_at', None),
            "view_count": getattr(result.metadata, 'view_count', None),
            "description": getattr(result.metadata, 'description', None),
            "thumbnail_url": getattr(result.metadata, 'thumbnail_url', None),
            "tags": getattr(result.metadata, 'tags', [])
        }

        # Convert entities to dictionaries
        entities_dict = []
        for entity in result.entities:
            entities_dict.append({
                "name": entity.name,
                "type": entity.type,
                "confidence": getattr(entity, 'confidence', 1.0),
                "description": getattr(entity, 'description', None),
                "aliases": getattr(entity, 'aliases', []),
                "context_windows": getattr(entity, 'context_windows', []),
                "temporal_distribution": getattr(entity, 'temporal_distribution', []),
                "extraction_sources": getattr(entity, 'extraction_sources', ["hybrid_processor"]),
                "mention_count": max(getattr(entity, 'mention_count', 1), 1),
                "canonical_form": getattr(entity, 'canonical_form', entity.name)
            })

        # Convert relationships to dictionaries
        relationships_dict = []
        for rel in result.relationships:
            relationships_dict.append({
                "subject": rel.subject,
                "predicate": rel.predicate,
                "object": rel.object,
                "confidence": getattr(rel, 'confidence', 1.0),
                "evidence_chain": getattr(rel, 'evidence_chain', []),
                "temporal_context": getattr(rel, 'temporal_context', None),
                "extraction_sources": getattr(rel, 'extraction_sources', ["hybrid_processor"])
            })

        # Convert to CoreData for consolidated output
        core_data = CoreData(
            video_metadata=video_metadata_dict,
            processing_info={
                "model": "voxtral-grok",
                "cost": result.processing_cost,
                "processing_time": result.processing_time,
                "pipeline_version": "v2.51.0"
            },
            transcript_segments=[{
                "text": result.transcript.text if hasattr(result.transcript, 'text') else str(result.transcript),
                "start_time": 0,
                "end_time": result.metadata.duration
            }],
            entities=entities_dict,
            relationships=relationships_dict,
            topics=[str(topic) if hasattr(topic, 'name') else str(topic) for topic in (result.topics if hasattr(result, 'topics') else [])],
            key_points=result.key_points if hasattr(result, 'key_points') else [],
            summary=result.summary if hasattr(result, 'summary') else None
        )
        
        # Generate output directory name
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Include time for uniqueness
        
        # Extract video ID properly
        video_id = result.metadata.video_id if hasattr(result.metadata, 'video_id') and result.metadata.video_id else self._extract_video_id(result.metadata.url) or "unknown"
        
        platform_name = getattr(result.metadata, 'platform', 'youtube')
        output_subdir = self.output_dir / f"{timestamp}_{platform_name}_{video_id}"
        
        # Save all files
        saved_files = core_data.save(output_subdir)
        saved_files['directory'] = output_subdir
        
        # Optional: Save GEXF/GraphML if configured
        if self.settings.export_graph_formats:
            try:
                # GEXF
                gexf_content = self.kg_builder.generate_gexf_content(core_data.knowledge_graph)
                gexf_path = output_subdir / "knowledge_graph.gexf"
                with open(gexf_path, 'w') as f:
                    f.write(gexf_content)
                saved_files['knowledge_graph_gexf'] = gexf_path
                
                # GraphML
                graphml_content = self.kg_builder.generate_graphml_content(core_data.knowledge_graph)
                graphml_path = output_subdir / "knowledge_graph.graphml"
                with open(graphml_path, 'w') as f:
                    f.write(graphml_content)
                saved_files['knowledge_graph_graphml'] = graphml_path
            except Exception as e:
                logger.warning(f"Could not generate graph formats: {e}")
        
        return saved_files
    
    def save_collection_outputs(self, multi_result, output_dir: str) -> Dict[str, Any]:
        """
        Save multi-video collection outputs.

        Args:
            multi_result: MultiVideoIntelligence object from MultiVideoProcessor
            output_dir: Directory to save outputs

        Returns:
            Dict with saved file paths
        """
        from ..models import MultiVideoIntelligence

        if not isinstance(multi_result, MultiVideoIntelligence):
            logger.error(f"Expected MultiVideoIntelligence, got {type(multi_result)}")
            return {}

        try:
            # Create collection output directory
            collection_dir = Path(output_dir) / f"collection_{multi_result.collection_id}"
            collection_dir.mkdir(parents=True, exist_ok=True)

            saved_files = {}

            # Save unified entities
            if multi_result.unified_entities:
                entities_file = collection_dir / "unified_entities.json"
                entities_data = [entity.dict() for entity in multi_result.unified_entities]
                with open(entities_file, 'w', encoding='utf-8') as f:
                    json.dump(entities_data, f, indent=2, ensure_ascii=False)
                saved_files['unified_entities'] = str(entities_file)

            # Save cross-video relationships
            if multi_result.cross_video_relationships:
                relationships_file = collection_dir / "cross_video_relationships.json"
                relationships_data = [rel.dict() for rel in multi_result.cross_video_relationships]
                with open(relationships_file, 'w', encoding='utf-8') as f:
                    json.dump(relationships_data, f, indent=2, ensure_ascii=False)
                saved_files['cross_video_relationships'] = str(relationships_file)

            # Save unified knowledge graph
            if multi_result.unified_knowledge_graph:
                kg_file = collection_dir / "unified_knowledge_graph.json"
                with open(kg_file, 'w', encoding='utf-8') as f:
                    json.dump(multi_result.unified_knowledge_graph, f, indent=2, ensure_ascii=False)
                saved_files['unified_knowledge_graph'] = str(kg_file)

            # Save collection summary
            summary_file = collection_dir / "collection_summary.md"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"# {multi_result.collection_title}\n\n")
                f.write(f"**Collection ID:** {multi_result.collection_id}\n")
                f.write(f"**Videos:** {len(multi_result.video_ids)}\n")
                f.write(f"**Unified Entities:** {len(multi_result.unified_entities)}\n")
                f.write(f"**Cross-Video Relationships:** {len(multi_result.cross_video_relationships)}\n")
                f.write(f"**Total Cost:** ${multi_result.total_processing_cost:.4f}\n")
                f.write(f"**Processing Time:** {multi_result.total_processing_time:.1f}s\n\n")
                f.write("## Summary\n\n")
                f.write(multi_result.collection_summary + "\n\n")
                f.write("## Key Insights\n\n")
                for insight in multi_result.key_insights:
                    f.write(f"- {insight}\n")
            saved_files['collection_summary'] = str(summary_file)

            # Save collection metadata
            metadata_file = collection_dir / "collection_metadata.json"
            metadata = {
                "collection_id": multi_result.collection_id,
                "collection_type": multi_result.collection_type.value,
                "collection_title": multi_result.collection_title,
                "created_at": multi_result.created_at.isoformat(),
                "video_ids": multi_result.video_ids,
                "processing_stats": multi_result.processing_stats,
                "quality_metrics": {
                    "entity_resolution_quality": multi_result.entity_resolution_quality,
                    "narrative_coherence": multi_result.narrative_coherence,
                    "information_completeness": multi_result.information_completeness
                }
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            saved_files['collection_metadata'] = str(metadata_file)

            logger.info(f"Collection outputs saved to {collection_dir}")
            saved_files['directory'] = str(collection_dir)

            return saved_files

        except Exception as e:
            logger.error(f"Failed to save collection outputs: {e}")
            return {}

    async def save_all_formats(self, result: VideoIntelligence, output_dir: str) -> Dict[str, Any]:
        """Legacy compatibility method."""
        return self._save_outputs(result)

    async def generate_x_content(
        self, 
        result: VideoIntelligence, 
        output_dir: Path,
        temp_thumbnail: Optional[Path] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate X-ready content (tweet draft + thumbnail).
        
        Args:
            result: Processing result with entities/relationships
            output_dir: Where to save X draft
            temp_thumbnail: Optional path to thumbnail in temp directory
            
        Returns:
            Dict with paths to tweet.txt and thumbnail.jpg
        """
        try:
            logger.info("Generating X content draft...")
            
            # Generate sticky summary
            summary = await self.x_generator.generate_sticky_summary(
                title=result.metadata.title,
                entities=result.entities,
                relationships=result.relationships
            )
            
            # Copy thumbnail from temp to output if provided
            thumbnail_in_output = None
            if temp_thumbnail and temp_thumbnail.exists():
                import shutil
                thumbnail_in_output = output_dir / temp_thumbnail.name
                shutil.copy(temp_thumbnail, thumbnail_in_output)
                logger.info(f"Copied thumbnail to output: {thumbnail_in_output}")
            
            # Save X draft
            draft_files = self.x_generator.save_x_draft(
                summary=summary,
                video_url=result.metadata.url,
                thumbnail_path=str(thumbnail_in_output) if thumbnail_in_output else None,
                output_dir=output_dir
            )
            
            logger.info(f"✅ X draft ready: {draft_files['directory']}")
            
            # Generate all 3 tweet styles
            logger.info("Generating 3 tweet styles...")
            tweet_styles = await self.style_generator.generate_all_styles(
                title=result.metadata.title,
                summary=result.summary,
                entities=result.entities,
                relationships=result.relationships
            )
            
            # Upload to GCS with all styles
            draft_url = await self.gcs.upload_draft(
                draft_id=f"{result.metadata.video_id}_{int(time.time())}",
                executive_summary=result.summary,
                tweet_styles=tweet_styles,
                video_title=result.metadata.title,
                video_url=result.metadata.url,
                entities=result.entities,
                relationships=result.relationships,
                thumbnail_path=thumbnail_in_output,
                video_path=self._last_video
            )
            
            # Send Telegram notification
            if draft_url:
                # Use the first style's length for notification
                first_style_length = len(tweet_styles.get('analyst', ''))
                
                await self.telegram.notify_draft_ready(
                    title=result.metadata.title,
                    entity_count=len(result.entities),
                    relationship_count=len(result.relationships),
                    char_count=first_style_length,
                    draft_url=draft_url
                )
            
            return draft_files
            
        except Exception as e:
            logger.warning(f"X content generation failed: {e}")
            return None
