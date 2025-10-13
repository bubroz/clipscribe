# Output Formats

*Last Updated: September 5, 2025*
*Related: [CLI Reference](CLI_REFERENCE.md) | [Visualizing Graphs](VISUALIZING_GRAPHS.md)*

ClipScribe generates structured output files containing transcripts, entities, relationships, and knowledge graphs extracted from video content.

## Table of Contents
- [Output Directory Structure](#output-directory-structure)
- [Core Output Files](#core-output-files)
- [Optional Graph Formats](#optional-graph-formats)
- [Legacy Format Migration](#legacy-format-migration)

## Output Directory Structure

```
output/
├── YYYYMMDD_platform_videoId/     # Individual video outputs
│   ├── core.json                   # Single source of truth (all data)
│   ├── transcript.txt              # Plain text transcript
│   ├── metadata.json               # Video and processing metadata
│   ├── knowledge_graph.json        # Graph structure for visualization
│   └── report.md                   # Human-readable summary
│
├── collections/                    # Multi-video collections
│   └── YYYYMMDD_collection_name/
│       ├── series_analysis.json
│       └── individual_videos/
│
└── video_archive/                  # Archived videos (retention policy)
    └── retention_log.json
```

## Core Output Files

### 1. core.json (Primary Data File)
**Single source of truth containing all extracted data**

```json
{
  "video_metadata": {
    "url": "https://youtube.com/watch?v=...",
    "title": "Video Title",
    "channel": "Channel Name",
    "duration": 172.0,
    "platform": "youtube",
    "published_at": "2025-08-15T12:43:42+00:00",
    "view_count": 1591
  },
  "processing_info": {
    "model": "voxtral-grok",
    "cost": 0.0234,
    "processing_time": 45.2,
    "timestamp": "2025-09-05T10:30:00",
    "pipeline_version": "v2.51.0"
  },
  "transcript_segments": [
    {
      "text": "Segment text...",
      "start_time": 0.0,
      "end_time": 30.0,
      "speaker": null
    }
  ],
  "entities": [
    {
      "name": "Entity Name",
      "type": "PERSON",
      "confidence": 0.95,
      "mention_count": 3,
      "aliases": [],
      "canonical_form": "Entity Name",
      "evidence": [
        {
          "quote": "Direct quote mentioning entity",
          "timestamp": 15.5,
          "source": "grok-4",
          "confidence": 0.9
        }
      ],
      "extraction_sources": ["grok-4"],
      "temporal_distribution": []
    }
  ],
  "relationships": [
    {
      "subject": "Entity A",
      "predicate": "relates to",
      "object": "Entity B",
      "confidence": 0.85,
      "evidence": [
        {
          "quote": "Supporting quote",
          "timestamp": 45.0,
          "source": "grok-4",
          "confidence": 0.85
        }
      ],
      "extraction_source": "grok-4",
      "contradictions": []
    }
  ],
  "topics": ["Topic 1", "Topic 2"],
  "key_points": ["Key insight 1", "Key insight 2"],
  "summary": "Brief summary of video content"
}
```

### 2. transcript.txt
**Plain text transcript for easy reading and searching**

```text
This is the full transcript text extracted from the video.
It contains all spoken content without timestamps or formatting.
```

### 3. metadata.json
**Lightweight metadata for quick reference**

```json
{
  "url": "https://youtube.com/watch?v=...",
  "title": "Video Title",
  "channel": "Channel Name",
  "duration": 172,
  "platform": "youtube",
  "published_at": "2025-08-15T12:43:42+00:00",
  "view_count": 1591,
  "model": "voxtral-grok",
  "cost": 0.0234,
  "processing_time": 45.2,
  "timestamp": "2025-09-05T10:30:00",
  "pipeline_version": "v2.51.0",
  "entity_count": 25,
  "relationship_count": 18
}
```

### 4. knowledge_graph.json
**Graph structure for visualization tools**

```json
{
  "nodes": [
    {
      "id": "Entity Name",
      "label": "Entity Name",
      "type": "PERSON",
      "confidence": 0.95,
      "mention_count": 3
    }
  ],
  "edges": [
    {
      "source": "Entity A",
      "target": "Entity B",
      "predicate": "relates to",
      "confidence": 0.85
    }
  ]
}
```

### 5. report.md
**Human-readable markdown report**

```markdown
# Video Intelligence Report: Video Title

**URL**: https://youtube.com/watch?v=...
**Channel**: Channel Name
**Duration**: 172s
**Processed**: 2025-09-05 10:30:00
**Cost**: $0.0234

## Summary
Brief summary of the video content...

## Key Entities (25)
- **Entity 1** (PERSON): 5 mentions
- **Entity 2** (ORGANIZATION): 3 mentions

## Key Relationships (18)
- Entity A relates to Entity B
- Entity C works with Entity D

## Key Points
- Important insight 1
- Important insight 2
```

## Optional Graph Formats

Enable with environment variable: `EXPORT_GRAPH_FORMATS=true`

### GEXF Format (Gephi)
**knowledge_graph.gexf** - For import into Gephi network visualization tool

### GraphML Format (yEd, Cytoscape)
**knowledge_graph.graphml** - For import into yEd or Cytoscape

## Legacy Format Migration

### Files No Longer Generated (v2.51.0+)
- `entities.json` - Merged into core.json
- `relationships.json` - Merged into core.json
- `entities.csv` - Removed (redundant)
- `relationships.csv` - Removed (redundant)
- `facts.json` - Derived from relationships in core.json
- `manifest.json` - Merged into core.json
- `chimera_format.json` - Removed (unused)
- `transcript.json` - Redundant with core.json

### Migration Path
To migrate from legacy outputs:
```python
from clipscribe.core_data import CoreData

# Load legacy files into new format
core_data = CoreData.from_legacy_files("output/old_video_dir/")

# Save in new consolidated format
core_data.save("output/new_video_dir/")
```

## Data Quality Features

### Validation
- **Pydantic Models**: Type-safe validation for all data
- **Confidence Scores**: Normalized 0.0-1.0 floats
- **Timestamps**: ISO 8601 format
- **Entity Types**: Uppercase normalization

### Automatic Fixes
- Dynamic mention counting via regex
- Evidence preservation with quotes and timestamps
- Relationship fact generation
- Confidence score adjustment based on evidence

### Output Validator
Run validation on any output directory:
```python
from clipscribe.validators.output_validator import OutputValidator

validator = OutputValidator()
report = validator.validate_directory("output/video_dir/")
fixes = validator.fix_common_issues("output/video_dir/")
```

## Configuration

### Environment Variables
```bash
# Optional graph exports
EXPORT_GRAPH_FORMATS=true  # Enable GEXF/GraphML generation

# Output directory
OUTPUT_DIR=output  # Default output location
```

### Settings
```python
from clipscribe.config.settings import Settings

settings = Settings()
settings.export_graph_formats = True  # Enable optional formats
settings.output_dir = "custom_output"  # Custom output location
```