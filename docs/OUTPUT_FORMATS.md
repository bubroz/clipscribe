# ClipScribe Output Formats

*Last Updated: September 4, 2025 - v2.50.0*

ClipScribe generates a comprehensive set of structured output files for each processed video, all organized within a timestamped directory.

## Directory Structure

```
output/
└── YYYYMMDD_platform_videoId/
    ├── transcript.txt          # Plain text transcript
    ├── transcript.json         # Full structured data with all analysis
    ├── metadata.json           # Lightweight video and processing metadata
    ├── entities.json           # Entities with real mention counts (not hardcoded)
    ├── relationships.json      # Relationships with evidence chains
    ├── knowledge_graph.json    # Raw graph data for programmatic use
    ├── knowledge_graph.gexf    # Gephi-compatible (optional - set export_graph_formats=True)
    ├── knowledge_graph.graphml # yEd/Cytoscape compatible (optional - set export_graph_formats=True)
    ├── facts.json              # Derived facts from relationships
    ├── report.md               # Human-readable report (placeholder for executive summary)
    └── manifest.json           # File index with processing metadata
```

## Current Pipeline: Voxtral -> Grok-4

### Uncensored Intelligence (Default)
- **Transcription**: Voxtral (Mistral) - Superior WER and cost efficiency
- **Intelligence Extraction**: Grok-4 (xAI) - Bypasses all Gemini safety filters
- **Cost**: ~$0.02-0.04 per video (any length)
- **Quality**: Professional-grade extraction for sensitive content analysis

### Legacy Gemini Pipeline (Available)
- **Transcription**: Gemini multimodal (variable quality)
- **Intelligence Extraction**: Gemini 2.5 Pro/Flash
- **Cost**: $0.0035-0.02 per minute
- **Limitations**: Safety filters may censor sensitive content

## Optimizations (v2.50.0)

### Output Streamlining
- **Removed**: CSV exports (entities.csv, relationships.csv) - use JSON for structured data
- **Optional**: GEXF/GraphML exports (set `export_graph_formats=True` in settings)
- **Deprecated**: chimera_format.json - replaced by structured JSON formats
- **Reduced**: Output files from ~14 to ~10-11, cutting ~30% generation overhead

### Data Quality Improvements
- **Fixed**: Mention counts now reflect actual transcript occurrences (was hardcoded to 1)
- **Removed**: Arbitrary confidence scores from entities/relationships
- **Enhanced**: report.md as placeholder for future executive summary
- **Improved**: Evidence chains and relationship traceability

### Configuration
Set `export_graph_formats=True` in `src/clipscribe/config/settings.py` to enable:
- `knowledge_graph.gexf` (Gephi visualization)
- `knowledge_graph.graphml` (yEd/Cytoscape visualization)

## Critical Fixes in v2.20.4

### RESOLVED: Output Pipeline Issues
- **Fixed**: Entities/relationships arrays were empty in output files
- **Fixed**: Missing knowledge_graph.gexf generation
- **Fixed**: Advanced extraction pipeline not running
- **Validated**: All output formats now working end-to-end

### Confirmed Working Examples
Based on validated controversial content processing:
- **entities.json**: 26+ entities with real mention counts
- **relationships.json**: 19+ relationships with evidence chains
- **facts.json**: 19+ derived facts from relationships

## File Formats

### transcript.txt
A simple plain text file containing the full transcript. Ideal for quick reading or ingestion into other systems.

### transcript.json
The most comprehensive single-file output. Contains:
- Full transcript with segments and metadata
- Complete video information (title, URL, duration, platform)
- All analysis results: summary, key points, topics, entities, relationships
- Processing details: cost, model used, quality level selected

### metadata.json
Lightweight JSON file with processing overview:
- Basic video info (title, channel, duration, platform)
- Processing details (cost, time, model used: Flash vs Pro)
- Statistics (entity count, relationship count, confidence metrics)

## File Details

### 1. `transcript.txt` - Raw Transcript
- Plain text with optional timestamps
- Example: "[00:01] Speaker: Hello world"
- Parse with: `with open('transcript.txt') as f: text = f.read()`

### 2. `transcript.json` - Complete Intelligence
- Schema: {'transcript': str, 'entities': List[Dict], 'relationships': List[Dict], ...}
- Example Access: `import json; data = json.load(open('transcript.json')); len(data['entities'])`

## Core Output Files

### entities.json
Contains extracted entities with normalization and multi-source attribution (Gemini + targeted local augmentations where applicable).

```json
{
  "video_url": "https://www.youtube.com/watch?v=...",
  "video_title": "Video Title",
  "entities": [
```

## For Data Scientists
- Load graphs: `import networkx as nx; g = nx.read_gexf('knowledge_graph.gexf')`
- Analyze entities: Use pandas for CSV: `import pandas as pd; df = pd.read_csv('entities.csv')`
- Custom Scripts: See examples/structured_output_demo.py
