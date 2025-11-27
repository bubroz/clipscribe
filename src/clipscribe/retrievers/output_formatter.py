"""Output Formatter Module - Handles all file saving and formatting."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..config.settings import Settings
from ..models import VideoIntelligence
from ..utils.file_utils import calculate_sha256
from ..utils.filename import create_output_filename, create_output_structure

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handles all output formatting and file saving operations."""

    def __init__(self):
        """Initialize the output formatter."""
        pass

    def save_transcript(
        self, video: VideoIntelligence, output_dir: str = None, formats: List[str] = ["txt"]
    ) -> Dict[str, Path]:
        """
        Save transcript with meaningful filename.

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
                output_file = create_output_filename(video.metadata.title, "txt", output_dir)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(video.transcript.full_text)
                saved_files["txt"] = output_file

            elif format_type == "json":
                # Save full JSON with metadata
                output_file = create_output_filename(video.metadata.title, "json", output_dir)
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(video.dict(), f, default=str, indent=2)
                saved_files["json"] = output_file

        return saved_files

    def save_all_formats(
        self,
        video: VideoIntelligence,
        output_dir: str = "output",
        include_chimera_format: bool = True,
    ) -> Dict[str, Path]:
        """
        Save video data in all formats with a structured directory.

        Args:
            video: VideoIntelligence object.
            output_dir: Base output directory.
            include_chimera_format: Include Chimera-compatible format.

        Returns:
            Dictionary of file types to paths.
        """
        metadata = self._get_video_metadata_dict(video)
        paths = create_output_structure(metadata, output_dir)

        self._save_transcript_files(video, paths, metadata)
        self._save_metadata_file(video, paths, metadata)
        self._save_entities_files(video, paths)
        self._save_relationships_files(video, paths)

        # Knowledge graph
        self._save_knowledge_graph_files(video, paths)
        self._save_facts_file(video, paths)
        self._save_report_file(video, paths)

        # Chimera format deprecated - use structured JSON formats instead
        # if include_chimera_format:
        #     self._save_chimera_file(video, paths)

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
            "published_at": (
                video.metadata.published_at.isoformat() if video.metadata.published_at else None
            ),
            "view_count": video.metadata.view_count,
            "description": video.metadata.description,
        }

    def _save_transcript_files(
        self, video: VideoIntelligence, paths: Dict[str, Path], metadata: Dict[str, Any]
    ):
        """Saves transcript.txt and transcript.json."""
        # 1. Plain text
        with open(paths["transcript_txt"], "w", encoding="utf-8") as f:
            f.write(video.transcript.full_text)

        # 2. Full JSON
        full_data = self._create_full_transcript_data(video, metadata)

        with open(paths["transcript_json"], "w", encoding="utf-8") as f:
            json.dump(full_data, f, default=str, indent=2)

    def _create_full_transcript_data(
        self, video: VideoIntelligence, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive transcript data dictionary."""
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
                        "name": e.name if hasattr(e, "name") else e.get("name", ""),
                        "type": e.type if hasattr(e, "type") else e.get("type", ""),
                        "extraction_sources": getattr(e, "extraction_sources", []),
                        "mention_count": getattr(e, "mention_count", 1),
                        "context_windows": (
                            [cw.dict() for cw in getattr(e, "context_windows", [])]
                            if hasattr(e, "context_windows")
                            else []
                        ),
                        "aliases": getattr(e, "aliases", []),
                    }
                    for e in video.entities
                ],
                "topics": [
                    t.dict() if hasattr(t, "dict") else {"name": t.name} for t in video.topics
                ],
                "sentiment": video.sentiment,
            },
            "processing": {
                "cost": video.processing_cost,
                "time": video.processing_time,
                "processed_at": datetime.now().isoformat(),
                "model": "voxtral-grok",
                "extractor": (
                    "advanced_hybrid_v2.2" if hasattr(video, "entity_extractor") else "basic_hybrid"
                ),
            },
        }

        # Add dates if available
        if hasattr(video, "dates") and video.dates:
            full_data["dates"] = video.dates
        if hasattr(video, "processing_stats") and video.processing_stats:
            if "dates" in video.processing_stats:
                full_data["dates"] = video.processing_stats["dates"]
            if "visual_dates" in video.processing_stats:
                full_data["visual_dates"] = video.processing_stats["visual_dates"]

        # Add relationships if available
        if hasattr(video, "relationships") and video.relationships:
            full_data["relationships"] = [r.dict() for r in video.relationships]

        # Add other optional fields
        if hasattr(video, "knowledge_graph") and video.knowledge_graph:
            full_data["knowledge_graph"] = video.knowledge_graph
        if hasattr(video, "key_moments") and video.key_moments:
            full_data["key_facts"] = video.key_moments
        if hasattr(video, "processing_stats") and video.processing_stats:
            full_data["extraction_stats"] = video.processing_stats
        if hasattr(video, "timeline_v2") and video.timeline_v2:
            full_data["timeline_v2"] = video.timeline_v2

        return full_data

    def _save_metadata_file(
        self, video: VideoIntelligence, paths: Dict[str, Path], metadata: Dict[str, Any]
    ):
        """Saves metadata.json."""
        with open(paths["metadata"], "w", encoding="utf-8") as f:
            json.dump(
                {
                    "video": metadata,
                    "processing": {
                        "cost": video.processing_cost,
                        "time": video.processing_time,
                        "processed_at": datetime.now().isoformat(),
                        "clipscribe_version": "2.0.0",
                    },
                    "statistics": {
                        "transcript_length": len(video.transcript.full_text),
                        "word_count": len(video.transcript.full_text.split()),
                        "entity_count": len(video.entities),
                        "key_point_count": len(video.key_points),
                        "topic_count": len(video.topics),
                    },
                },
                f,
                indent=2,
            )

    def _save_entities_files(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves entities.json."""
        all_entities = video.entities

        # Entities JSON
        entities_data = {
            "video_url": video.metadata.url,
            "video_title": video.metadata.title,
            "entities": [
                {
                    "name": e.name,
                    "type": e.type,
                    "source": getattr(e, "extraction_sources", getattr(e, "source", "unknown")),
                    "properties": getattr(e, "properties", None),
                    "timestamp": getattr(e, "timestamp", None),
                    "mention_count": getattr(e, "mention_count", 1),
                    "context_windows": [cw.dict() for cw in getattr(e, "context_windows", [])],
                    "aliases": getattr(e, "aliases", []),
                    "temporal_distribution": [
                        td.dict() for td in getattr(e, "temporal_distribution", [])
                    ],
                }
                for e in all_entities
            ],
            "topics": [t.dict() if hasattr(t, "dict") else {"name": t.name} for t in video.topics],
            "key_facts": [kp.text for kp in video.key_points[:5]],
        }

        with open(paths["entities"], "w", encoding="utf-8") as f:
            json.dump(entities_data, f, indent=2)

    def _save_relationships_files(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves relationships.json."""
        if not hasattr(video, "relationships"):
            video.relationships = []

        # Relationships JSON
        relationships_path = paths["directory"] / "relationships.json"
        relationships_data = {
            "video_url": video.metadata.url,
            "video_title": video.metadata.title,
            "relationships": [
                {
                    "subject": rel.subject,
                    "predicate": rel.predicate,
                    "object": rel.object,
                    "properties": getattr(rel, "properties", {}),
                    "context": getattr(rel, "context", None),
                    "evidence_chain": getattr(rel, "evidence_chain", []),
                    "contradictions": getattr(rel, "contradictions", []),
                    "extraction_source": getattr(rel, "extraction_source", "unknown"),
                }
                for rel in video.relationships
            ],
            "total_count": len(video.relationships),
        }

        with open(relationships_path, "w", encoding="utf-8") as f:
            json.dump(relationships_data, f, default=str, indent=2)
        paths["relationships"] = relationships_path

    def _save_knowledge_graph_files(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves knowledge_graph.json and knowledge_graph.gexf if they exist."""
        if not hasattr(video, "knowledge_graph") or not video.knowledge_graph:
            return

        if video.knowledge_graph is None:
            return

        # Knowledge Graph JSON
        graph_path = paths["directory"] / "knowledge_graph.json"
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(video.knowledge_graph, f, indent=2)
        paths["knowledge_graph"] = graph_path

        settings = Settings()

        if settings.export_graph_formats:
            # Knowledge Graph GEXF (for Gephi visualization)
            try:
                from ..retrievers.knowledge_graph_builder import KnowledgeGraphBuilder

                kg_builder = KnowledgeGraphBuilder()
                gexf_content = kg_builder.generate_gexf_content(video.knowledge_graph)

                gexf_path = paths["directory"] / "knowledge_graph.gexf"
                with open(gexf_path, "w", encoding="utf-8") as f:
                    f.write(gexf_content)
                paths["knowledge_graph_gexf"] = gexf_path
            except Exception as e:
                logger.warning(f"Could not generate GEXF file: {e}")

            # Knowledge Graph GraphML (for yEd, Cytoscape, etc.)
            try:
                from ..retrievers.knowledge_graph_builder import KnowledgeGraphBuilder

                kg_builder = KnowledgeGraphBuilder()
                graphml_content = kg_builder.generate_graphml_content(video.knowledge_graph)

                graphml_path = paths["directory"] / "knowledge_graph.graphml"
                with open(graphml_path, "w", encoding="utf-8") as f:
                    f.write(graphml_content)
                paths["knowledge_graph_graphml"] = graphml_path
            except Exception as e:
                logger.warning(f"Could not generate GraphML file: {e}")
        else:
            logger.info("Graph format exports disabled (export_graph_formats=False)")

        node_count = video.knowledge_graph.get("node_count", 0)
        edge_count = video.knowledge_graph.get("edge_count", 0)
        logger.info(f"Saved knowledge graph with {node_count} nodes and {edge_count} edges")

    def _save_facts_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves facts.json with extracted facts from relationships and key points."""
        facts = []

        # Generate facts from relationships
        if hasattr(video, "relationships") and video.relationships:
            for rel in video.relationships:
                if rel.subject and rel.object:  # Only include complete relationships
                    fact = {
                        "fact": f"{rel.subject} {rel.predicate} {rel.object}",
                        "type": "relationship",
                        "confidence": getattr(rel, "confidence", 0.8),
                        "evidence": (
                            rel.properties.get("evidence", "") if hasattr(rel, "properties") else ""
                        ),
                        "source": getattr(rel, "source", "grok_analysis"),
                    }
                    facts.append(fact)

        # Add facts from key points if available
        if hasattr(video, "key_points") and video.key_points:
            for kp in video.key_points:
                fact = {
                    "fact": kp.text if hasattr(kp, "text") else str(kp),
                    "type": "key_point",
                    "confidence": getattr(kp, "confidence", 0.7),
                    "timestamp": getattr(kp, "timestamp", 0),
                    "source": "analysis",
                }
                facts.append(fact)

        # Save facts as JSON
        facts_path = paths["directory"] / "facts.json"
        with open(facts_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "video_url": video.metadata.url,
                    "video_title": video.metadata.title,
                    "extraction_date": datetime.now().isoformat(),
                    "fact_count": len(facts),
                    "facts": facts,
                },
                f,
                indent=2,
                default=str,
            )
        paths["facts"] = facts_path

    def _save_report_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Generates and saves the markdown report (placeholder for future executive summary)."""
        markdown_path = paths["directory"] / "report.md"
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(f"# Video Intelligence Report: {video.metadata.title}\n\n")
            f.write(f"**URL**: {video.metadata.url}\n")
            f.write(f"**Channel**: {video.metadata.channel}\n")
            minutes, seconds = divmod(int(video.metadata.duration), 60)
            f.write(f"**Duration**: {minutes}:{seconds:02d}\n")
            f.write(f"**Processed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Processing Cost**: ${video.processing_cost:.4f}\n\n")
            f.write("## Executive Summary (TBD)\n\n")
            f.write(
                "This is a placeholder for the full executive summary. Future enhancements will include:\n"
            )
            f.write("- Detailed analysis summary\n")
            f.write("- Key insights and findings\n")
            f.write("- Risk assessments\n")
            f.write("- Actionable recommendations\n")
            f.write("- Visual data representations\n\n")

            # Add basic stats
            f.write("## Quick Stats\n\n")
            f.write(f"- **Transcript Length**: {len(video.transcript.full_text)} characters\n")
            f.write(f"- **Entities Found**: {len(video.entities)}\n")
            f.write(f"- **Key Points**: {len(video.key_points)}\n")
            f.write(f"- **Topics**: {len(video.topics)}\n")
            if hasattr(video, "relationships"):
                f.write(f"- **Relationships**: {len(video.relationships)}\n")

            # Add key entities
            if video.entities:
                f.write("\n## Key Entities\n\n")
                for entity in video.entities[:5]:  # Show top 5 entities
                    f.write(f"- **{entity.name}** ({entity.type})\n")

        paths["report"] = markdown_path

    def _save_chimera_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Saves the Chimera-compatible format file."""
        chimera_path = paths["directory"] / "chimera_format.json"
        chimera_data = self._to_chimera_format(video)
        with open(chimera_path, "w", encoding="utf-8") as f:
            json.dump(chimera_data, f, indent=2, default=str)
        paths["chimera"] = chimera_path

    def _to_chimera_format(self, video: VideoIntelligence) -> Dict[str, Any]:
        """Convert VideoIntelligence to Chimera's format."""
        return {
            "type": "video",
            "source": "video_intelligence",
            "url": video.metadata.url,
            "title": video.metadata.title,
            "content": video.transcript.full_text,
            "summary": video.summary,
            "metadata": {
                "channel": video.metadata.channel,
                "duration": video.metadata.duration,
                "published_at": (
                    video.metadata.published_at.isoformat() if video.metadata.published_at else None
                ),
                "view_count": video.metadata.view_count,
                "key_points": [kp.dict() for kp in video.key_points],
                "entities": [e.dict() for e in video.entities],
                "topics": [
                    t.dict() if hasattr(t, "dict") else {"name": t.name, "confidence": t.confidence}
                    for t in video.topics
                ],
                "sentiment": video.sentiment,
                "processing_cost": video.processing_cost,
                "timeline_v2": video.timeline_v2 if hasattr(video, "timeline_v2") else None,
            },
        }

    def _create_manifest_file(self, video: VideoIntelligence, paths: Dict[str, Path]):
        """Creates the manifest.json file."""
        manifest = {
            "version": "2.3",
            "created_at": datetime.now().isoformat(),
            "video": {
                "title": video.metadata.title,
                "url": video.metadata.url,
                "platform": "unknown",  # Would need platform detection logic
            },
            "extraction_stats": (
                video.processing_stats if hasattr(video, "processing_stats") else {}
            ),
            "timeline_v2": video.timeline_v2 if hasattr(video, "timeline_v2") else None,
            "files": {},
        }

        file_definitions = {
            "transcript_txt": {"path": "transcript.txt", "format": "plain_text"},
            "transcript_json": {"path": "transcript.json", "format": "json"},
            "metadata": {"path": "metadata.json", "format": "json"},
            "entities": {"path": "entities.json", "format": "json"},
            "relationships": {"path": "relationships.json", "format": "json"},
            "knowledge_graph": {"path": "knowledge_graph.json", "format": "json"},
            "facts": {"path": "facts.txt", "format": "plain_text"},
            "report": {"path": "report.md", "format": "markdown"},
            "chimera": {"path": "chimera_format.json", "format": "json"},
        }

        for key, definition in file_definitions.items():
            if key in paths and paths[key].exists():
                file_path = paths[key]
                file_entry = {
                    "path": definition["path"],
                    "format": definition["format"],
                    "size": file_path.stat().st_size,
                    "sha256": calculate_sha256(file_path),
                }
                manifest["files"][key] = file_entry

        with open(paths["manifest"], "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
