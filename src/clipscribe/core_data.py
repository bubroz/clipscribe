"""
Core data models with Pydantic validation for ClipScribe outputs.
Consolidates entities, relationships, and metadata into a single source of truth.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Evidence(BaseModel):
    """Evidence supporting an extraction."""

    quote: str
    timestamp: Optional[float] = Field(None, ge=0.0)
    source: str = Field(default="grok-4-fast-reasoning")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class Entity(BaseModel):
    """Standardized entity model."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    type: str = Field(default="UNKNOWN")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    mention_count: int = Field(default=1, ge=1)
    aliases: List[str] = Field(default_factory=list)
    canonical_form: str = Field(default="")
    evidence: List[Evidence] = Field(default_factory=list)
    extraction_sources: List[str] = Field(default_factory=lambda: ["grok-4-fast-reasoning"])
    temporal_distribution: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("canonical_form", mode="before")
    @classmethod
    def set_canonical_form(cls, v, info):
        """Auto-set canonical form if not provided."""
        if not v and "name" in info.data:
            return info.data["name"]
        return v

    @field_validator("type")
    @classmethod
    def normalize_type(cls, v):
        """Normalize entity types to uppercase."""
        return v.upper()


class Relationship(BaseModel):
    """Standardized relationship model."""

    model_config = ConfigDict(str_strip_whitespace=True)

    subject: str
    predicate: str
    object: str
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    extraction_source: str = Field(default="grok-4-fast-reasoning")
    contradictions: List[str] = Field(default_factory=list)

    def to_fact(self) -> str:
        """Convert to fact string."""
        return f"{self.subject} {self.predicate} {self.object}"


class VideoMetadata(BaseModel):
    """Standardized video metadata."""

    model_config = ConfigDict(str_strip_whitespace=True)

    url: str
    title: str
    channel: Optional[str] = None
    duration: float = Field(ge=0.0)
    platform: str = Field(default="youtube")
    published_at: Optional[datetime] = None
    view_count: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None

    @field_validator("published_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from various formats."""
        if isinstance(v, str):
            # Handle ISO format
            if "T" in v:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            # Handle YYYYMMDD format
            elif len(v) == 8 and v.isdigit():
                return datetime.strptime(v, "%Y%m%d")
        return v


class ProcessingInfo(BaseModel):
    """Processing metadata."""

    model_config = ConfigDict(str_strip_whitespace=True)

    model: str = Field(default="voxtral-grok")
    cost: float = Field(ge=0.0)
    processing_time: float = Field(ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    pipeline_version: str = Field(default="v2.50.0")


class TranscriptSegment(BaseModel):
    """Transcript segment for chunked storage."""

    text: str
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)
    speaker: Optional[str] = None


class CoreData(BaseModel):
    """
    Core consolidated data model - single source of truth.
    All other files reference or derive from this.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    # Core data
    video_metadata: VideoMetadata
    processing_info: ProcessingInfo
    transcript_segments: List[TranscriptSegment] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

    # Derived data
    topics: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

    @property
    def full_transcript(self) -> str:
        """Reconstruct full transcript from segments."""
        return " ".join(seg.text for seg in self.transcript_segments)

    @property
    def facts(self) -> List[str]:
        """Generate facts from relationships."""
        return [rel.to_fact() for rel in self.relationships]

    @property
    def knowledge_graph(self) -> Dict[str, Any]:
        """Generate knowledge graph structure."""
        nodes = [
            {
                "id": entity.canonical_form or entity.name,
                "label": entity.name,
                "type": entity.type,
                "confidence": entity.confidence,
                "mention_count": entity.mention_count,
            }
            for entity in self.entities
        ]

        edges = [
            {
                "source": rel.subject,
                "target": rel.object,
                "predicate": rel.predicate,
                "confidence": rel.confidence,
            }
            for rel in self.relationships
        ]

        return {"nodes": nodes, "edges": edges}

    def save(self, output_dir: Union[str, Path]) -> Dict[str, Path]:
        """
        Save core data and generate all derived files.

        Returns:
            Dictionary of saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # 1. Save core.json (single source of truth)
        core_path = output_dir / "core.json"
        with open(core_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, default=str)
        saved_files["core"] = core_path

        # 2. Save transcript.txt (plain text)
        transcript_path = output_dir / "transcript.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(self.full_transcript)
        saved_files["transcript_txt"] = transcript_path

        # 3. Save metadata.json (lightweight)
        metadata_path = output_dir / "metadata.json"
        metadata_dict = {
            **self.video_metadata.model_dump(),
            **self.processing_info.model_dump(),
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, indent=2, default=str)
        saved_files["metadata"] = metadata_path

        # 4. Save knowledge_graph.json
        graph_path = output_dir / "knowledge_graph.json"
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_graph, f, indent=2)
        saved_files["knowledge_graph"] = graph_path

        # 5. Save report.md (human-readable)
        report_path = output_dir / "report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(self._generate_report())
        saved_files["report"] = report_path

        return saved_files

    def _generate_report(self) -> str:
        """Generate markdown report."""
        report = f"""# Video Intelligence Report: {self.video_metadata.title}

**URL**: {self.video_metadata.url}
**Channel**: {self.video_metadata.channel or 'Unknown'}
**Duration**: {self.video_metadata.duration:.0f}s
**Processed**: {self.processing_info.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Cost**: ${self.processing_info.cost:.4f}

## Summary
{self.summary or 'No summary available.'}

## Key Entities ({len(self.entities)})
"""
        for entity in sorted(self.entities, key=lambda e: e.mention_count, reverse=True)[:10]:
            report += f"- **{entity.name}** ({entity.type}): {entity.mention_count} mentions\n"

        report += f"\n## Key Relationships ({len(self.relationships)})\n"
        for rel in self.relationships[:10]:
            report += f"- {rel.to_fact()}\n"

        if self.key_points:
            report += "\n## Key Points\n"
            for point in self.key_points[:5]:
                report += f"- {point}\n"

        return report

    @classmethod
    def from_legacy_files(cls, directory: Union[str, Path]) -> "CoreData":
        """
        Load from legacy ClipScribe output files.
        Handles truncations and inconsistencies.
        """
        directory = Path(directory)

        # Load what we can from various files
        core_data = {}

        # Try to load metadata
        metadata_path = directory / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                meta = json.load(f)
                core_data["video_metadata"] = VideoMetadata(
                    url=meta.get("url", ""),
                    title=meta.get("title", ""),
                    channel=meta.get("channel"),
                    duration=meta.get("duration", 0),
                    platform=meta.get("platform", "youtube"),
                )
                core_data["processing_info"] = ProcessingInfo(
                    model=meta.get("model", "unknown"),
                    cost=meta.get("processing_cost", 0),
                    processing_time=meta.get("processing_time", 0),
                )

        # Load entities with deduplication
        entities_path = directory / "entities.json"
        if entities_path.exists():
            with open(entities_path) as f:
                entities_data = json.load(f)
                seen = set()
                entities = []
                for e in entities_data.get("entities", []):
                    if e["name"] not in seen:
                        entities.append(Entity(**e))
                        seen.add(e["name"])
                core_data["entities"] = entities

        # Load relationships
        relationships_path = directory / "relationships.json"
        if relationships_path.exists():
            with open(relationships_path) as f:
                rel_data = json.load(f)
                core_data["relationships"] = [
                    Relationship(**r) for r in rel_data.get("relationships", [])
                ]

        # Load transcript (handle truncation)
        transcript_path = directory / "transcript.txt"
        if transcript_path.exists():
            with open(transcript_path) as f:
                text = f.read()
                # Create single segment if not chunked
                core_data["transcript_segments"] = [
                    TranscriptSegment(
                        text=text,
                        start_time=0,
                        end_time=core_data.get("video_metadata", {}).get("duration", 0),
                    )
                ]

        return cls(**core_data)
