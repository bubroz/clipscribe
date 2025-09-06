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
from ..config.settings import Settings
from ..utils.logging import setup_logging

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
        
        logger.info("VideoIntelligenceRetrieverV2 initialized with Voxtral-Grok pipeline")
    
    async def process_url(self, video_url: str) -> Optional[VideoIntelligence]:
        """
        Process a video URL with the uncensored pipeline.
        
        Args:
            video_url: URL of the video to process
            
        Returns:
            VideoIntelligence object or None if failed
        """
        start_time = time.time()
        
        try:
            # Phase 1: Download
            self.on_phase_start("Downloading", "Fetching video...")
            audio_path, metadata = await self._download_video(video_url)
            if not audio_path:
                return None
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
            
            logger.info(f"✅ Processing complete: {result.metadata.title}")
            logger.info(f"   Cost: ${processing_cost:.4f}")
            logger.info(f"   Time: {processing_time:.1f}s")
            logger.info(f"   Output: {saved_files.get('directory')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            self.on_error("Processing", str(e))
            return None
    
    async def _download_video(self, video_url: str) -> tuple[Optional[Path], Optional[VideoMetadata]]:
        """Download video and extract metadata."""
        try:
            # Check if URL is supported
            if not self.video_client.is_supported_url(video_url):
                logger.error(f"URL not supported: {video_url}")
                self.on_error("Downloading", "URL not supported")
                return None, None
            
            # Download audio
            audio_path, metadata = await self.video_client.download_audio(video_url)
            
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
            
            return Path(audio_path), metadata
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self.on_error("Downloading", str(e))
            return None, None
    
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
        timestamp = datetime.now().strftime("%Y%m%d")
        video_id = result.metadata.url.split('/')[-1].split('?')[0]
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
        return await self._save_outputs(result)
