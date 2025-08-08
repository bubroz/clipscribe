# ClipScribe Output Formats

*Last Updated: July 31, 2025 - v2.22.2 Stable*

ClipScribe generates a comprehensive set of structured output files for each processed video, all organized within a timestamped directory. **All formats validated and working in v2.22.2**.

## Directory Structure (v2.22.2 Validated )

```
output/
└── YYYYMMDD_platform_videoId/
    ├── transcript.txt          # Plain text transcript
    ├── transcript.json         # Full structured data with all analysis
    ├── metadata.json           # Lightweight video and processing metadata
    ├── entities.json           #  24-59 entities (FIXED: now saved properly)
    ├── entities.csv            #  Entities in CSV format for spreadsheets
    ├── entity_sources.json     #  Entity source tracking and normalization
    ├── entity_sources.csv      #  Entity sources in CSV format
    ├── relationships.json      #  53+ relationships (FIXED: now saved properly)
    ├── relationships.csv       #  Relationships in CSV format for spreadsheets
    ├── knowledge_graph.gexf    #  Gephi-compatible (FIXED: 60 nodes, 53 edges)
    ├── report.md               #  Human-readable intelligence report
    ├── chimera_format.json     #  Integration format for external tools
    └── manifest.json           #  File index with processing metadata
```

## Quality Control Options (v2.22.2)

### High Quality (Default - Gemini 2.5 Pro)
- **Cost**: ~$0.017/video (~$0.02/minute) 
- **Entities**: 30-60 per video with superior accuracy
- **Relationships**: 50+ per video with detailed evidence chains
- **Processing**: Professional-grade extraction, our recommended default.

### Standard Quality (--use-flash - Gemini 2.5 Flash)
- **Cost**: ~$0.003/video (~$0.0035/minute)
- **Entities**: 20-30 per video with good accuracy
- **Relationships**: 40-60 per video with basic evidence
- **Processing**: Faster, cost-effective for high volume or when speed is a priority.

## Critical Fixes in v2.20.4

###  RESOLVED: Output Pipeline Issues
- **Fixed**: Entities/relationships arrays were empty in output files
- **Fixed**: Missing knowledge_graph.gexf generation
- **Fixed**: Advanced extraction pipeline not running
- **Validated**: All output formats now working end-to-end

###  Confirmed Working Examples
Based on validated news content processing:
- **entities.json**: 24+ normalized entities
- **relationships.json**: 53+ relationships with evidence chains
- **knowledge_graph.gexf**: 60+ nodes for Gephi visualization

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

### entities.json  WORKING
Contains all extracted entities with **validated working pipeline** (v2.22.2):
- **Quality extraction**: 24-59 entities per video depending on content
- **Proper normalization**: Raw extractions deduplicated intelligently (59→24)
- **Multi-source attribution**: Shows extraction sources (Gemini, SpaCy, etc.)
- **Fixed pipeline**: Entities now properly saved to final output files

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
