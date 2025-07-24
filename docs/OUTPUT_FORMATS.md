# ClipScribe Output Formats

*Last Updated: July 6, 2025 - v2.19.0 Enhanced Metadata*

ClipScribe generates a comprehensive set of structured output files for each processed video, all organized within a timestamped directory.

## Directory Structure

```
output/
└── YYYYMMDD_platform_videoId/
    ├── transcript.txt          # Plain text transcript
    ├── transcript.json         # Full structured data with all analysis
    ├── metadata.json           # Lightweight video and processing metadata
    ├── entities.json           # All extracted entities (from all sources)
    ├── entities.csv            # Entities in CSV format for spreadsheets
    ├── entity_sources.json     # Entity source tracking (SpaCy/GLiNER/REBEL)
    ├── entity_sources.csv      # Entity sources in CSV format
    ├── entity_analysis.xlsx    # NEW v2.12.0: Multi-sheet Excel analysis report
    ├── relationships.json      # All extracted entity relationships
    ├── relationships.csv       # Relationships in CSV format for spreadsheets
    ├── knowledge_graph.json    # Graph data (nodes and edges)
    ├── knowledge_graph.gexf    # Gephi-compatible graph file for visualization
    ├── facts.txt               # Top 100 key facts with source annotations
    ├── report.md               # Interactive Markdown intelligence report
    ├── chimera_format.json     # Chimera Researcher compatible format
    └── manifest.json           # File index with SHA256 checksums
```

## File Formats

### transcript.txt
A simple plain text file containing the full transcript. Ideal for quick reading or ingestion into other systems.

### transcript.json
The most comprehensive single-file output. It's a structured JSON file containing:
- The full transcript with word-level or sentence-level segments.
- Complete video metadata (title, URL, duration, etc.).
- All analysis results: summary, key points, topics, entities, and relationships.
- Detailed processing information, including cost, time, and models used.

### metadata.json
A lightweight JSON file providing high-level information at a glance:
- Basic video info (title, channel, duration).
- Core processing details (cost, time).
- Key statistics (word count, entity count, relationship count).

## Core Output Files

### entities.json

Contains all extracted entities with **enhanced metadata** (v2.19.0):
- **Comprehensive extraction**: Targets 100% completeness, not arbitrary numbers
- **Fixed quality filters**: No longer removes 70% of valid entities
- **Quality-focused extraction**: Honest results without AI theater confidence scoring
- **Multi-source attribution**: Shows which extractors found each entity

```json
{
  "entities": [
    {
      "name": "Trump",
      "type": "PERSON", 
  
      "source": ["GLiNER+Gemini+SpaCy"],  // Multi-source validation
      "mention_count": 1,
      "context_windows": [...],
      "aliases": ["President Trump"]
    }
  ]
}
```

### relationships.json

Contains entity relationships with **evidence chains** (v2.19.0):
- **All relationships captured**: Now properly uses 50+ Gemini relationships (was bug)
- **Evidence-backed**: Each relationship has supporting quotes and timestamps
- **Contradiction detection**: Identifies conflicting information
- **Typical output**: 52+ relationships per news video

```json
{
  "relationships": [
    {
      "subject": "forecaster",
      "predicate": "expect_increase_of", 
      "object": "125,000 non-farm payrolls",
  
      "evidence_chain": [
        "direct_quote='...forecaster expect an increase of 125,000 non-farm payrolls in May...' timestamp='00:00:00'"
      ],
      "contradictions": [],
      "supporting_mentions": 1
    }
  ]
}
```

### entities.csv / entities.json
A complete list of all entities extracted from the video.
- **`entities.json`**: Detailed JSON output with `name`, `type`, `source`, and raw `properties`.
- **`entities.csv`**: A spreadsheet-friendly format containing the most important fields.
- **Source Tracking**: Both formats include the source of the entity (e.g., `SpaCy`, `GLiNER`, `REBEL`) for pipeline transparency.

### entity_sources.json / entity_sources.csv
Detailed breakdown of which extraction method found each entity.
- **`entity_sources.json`**: Complete analysis with counts by source and full entity details.
- **`entity_sources.csv`**: Simple spreadsheet format for quick analysis.
- **Pipeline Transparency**: Shows exactly how many entities came from SpaCy (basic NER), GLiNER (custom), or REBEL (relationships).
- **Quality Analysis**: Helps identify which extraction methods are most effective for different content types.

### entity_analysis.xlsx (**NEW in v2.12.0**)
Professional multi-sheet Excel analysis report with comprehensive data breakdown.
- **Summary Sheet**: Key metrics, entity counts, and quality statistics.
- **Source Distribution Sheet**: Detailed breakdown of extraction method performance with percentages.
- **Entity Types Sheet**: Complete entity type analysis sorted by frequency.
- **Per-Video Analysis Sheet**: Individual video metrics for batch processing results.
- **Professional Formatting**: Clean, readable layouts with proper headers and data types.
- **One-Click Generation**: Available through Streamlit interface and CLI tools.

### relationships.json / relationships.csv
A list of all semantic relationships (subject-predicate-object triples) extracted.
- **`relationships.json`**: Structured JSON with full context for each relationship.
- **`relationships.csv`**: A spreadsheet-friendly format.
- **Context is Key**: Includes the snippet of text from which the relationship was extracted, allowing for easy verification.

### knowledge_graph.json / knowledge_graph.gexf
These files represent the knowledge graph built from the extracted entities and relationships.
- **`knowledge_graph.json`**: A JSON representation of the graph's nodes and edges, suitable for programmatic use. Includes graph metrics like density and component count.
- **`knowledge_graph.gexf`**: A file ready for direct import into graph visualization software like [Gephi](https://gephi.org). It includes pre-set colors and sizes for nodes to facilitate immediate analysis.

### facts.txt
A human-readable list of the top 100 most important facts extracted from the video.
- **Source Annotated**: Each fact is prefixed with its source (e.g., `[Relationship]`, `[Key Point]`, `[Entity Property]`) for clarity.
- **Diverse Insights**: Facts are interleaved from different sources to provide a well-rounded summary of the video's content.

### report.md
**Enhanced in v2.5.4** - A professional, interactive intelligence report written in Markdown.
- **Interactive Diagrams**: Features auto-generated **Mermaid diagrams** for:
  - Knowledge graph visualization (top relationships).
  - Entity type distribution (pie chart).
- **Collapsible Sections**: Uses `<details>` tags for all major sections, making large reports easy to navigate.
- **Visual Dashboards**: Includes a "Quick Stats" dashboard with emoji-based bar charts and a relationship type distribution table.
- **Rich Formatting**: Uses emoji and tables for a highly scannable and visually appealing summary.
- **How to View**: For the best experience, view this file in a Markdown viewer that supports Mermaid, such as GitHub, GitLab, or the Cursor editor.

### chimera_format.json
A standardized JSON format designed for seamless integration with the [Chimera Researcher](https://github.com/bubroz/chimera-researcher) ecosystem.

### manifest.json
An inventory of all files generated for the video.
- **File Index**: Lists all created files with their format, size, and description.
- **Data Integrity**: **NEW in v2.5.4** - Includes a **SHA256 checksum** for each file, allowing you to verify file integrity.
- **Processing Stats**: Contains a summary of the extraction process, including entity counts and graph metrics.

## Example Output

```bash
# After processing a video:
output/20250624_youtube_UjDpW_SOrlw/
├── entities.csv (4.2 KB)
├── entities.json (21.1 KB)
├── facts.txt (6.4 KB)
├── knowledge_graph.gexf (99.4 KB)
├── knowledge_graph.json (43.3 KB)
├── manifest.json (3.1 KB)
├── metadata.json (2.3 KB)
├── relationships.csv (29.4 KB)
├── relationships.json (53.2 KB)
├── report.md (14.4 KB)
├── transcript.json (214.6 KB)
└── transcript.txt (28.5 KB)
```

## Multi-Video Collection Outputs (v2.15.0)

When processing multiple videos as a collection, ClipScribe generates additional synthesis outputs:

```
output/
└── collection_id/
    ├── timeline.json                    # Consolidated timeline with temporal intelligence
    ├── collection_intelligence.json     # Complete multi-video analysis data
    ├── unified_knowledge_graph.gexf     # Combined knowledge graph for Gephi
    ├── information_flow_map.json        # Concept evolution tracking  
    ├── information_flow_summary.md      # Human-readable flow analysis
    ├── concept_flows/                   # Individual concept flow files
    │   ├── video_1_concepts.json
    │   ├── video_2_concepts.json
    │   └── ...
    ├── information_flow_map.json        # Concept evolution tracking
    ├── information_flow_summary.md      # Human-readable concept analysis
    └── concept_flows/                   # Individual video flow files
        ├── video1_0.json
        ├── video2_1.json
        └── ...
```

### New Synthesis Files (v2.15.0)

#### knowledge_panels.json / knowledge_panels_summary.md
**Knowledge Panels** provide entity-centric intelligence synthesis across the entire collection:
- **Comprehensive Profiles**: Detailed analysis for the top 15 most significant entities
- **Rich Metadata**: Activities, quotes, relationships, and strategic insights for each entity
- **Cross-Video Synthesis**: Tracks how entities appear and evolve across videos
- **Human-Readable Summary**: Beautiful markdown report with entity profiles

#### information_flow_map.json / information_flow_summary.md
**Information Flow Maps** track concept evolution across video sequences:
- **6-Level Maturity Model**: Tracks concepts from "mentioned" to "evolved"
- **Dependency Analysis**: Maps how concepts build upon each other
- **Evolution Paths**: Traces concept journeys across the collection
- **Learning Progression**: Identifies curriculum patterns and knowledge gaps

#### entity_panels/ and concept_flows/ directories
- **Individual Files**: Separate JSON files for each entity panel and concept flow
- **Easy Access**: Enables targeted analysis of specific entities or videos
- **Modular Structure**: Facilitates integration with other tools and workflows

## Format Changes

### v2.18.17 TimelineJS Export (2025-07-01)
- **timeline_js.json**: NEW TimelineJS3-compatible timeline export for Timeline v2.0 data
- **Interactive Visualization**: Beautiful, interactive timeline visualization support
- **Media Integration**: Automatic YouTube thumbnail extraction with timestamp links
- **Date Precision**: Support for exact, day, month, and year-level date precision

### v2.15.0 Synthesis Features (2025-06-27)
- **knowledge_panels.json/md**: NEW entity-centric intelligence synthesis with comprehensive profiles
- **information_flow_map.json/md**: NEW concept evolution tracking across video sequences
- **entity_panels/ directory**: Individual JSON files for each significant entity
- **concept_flows/ directory**: Per-video concept flow analysis files
- **Complete Integration**: All synthesis features fully integrated with human-readable summaries

### v2.12.0 Enhancements
- **entity_analysis.xlsx**: NEW multi-sheet Excel analysis reports with professional formatting.
- **Advanced Visualizations**: Interactive Plotly charts for entity source analysis (CLI and Streamlit).
- **Enhanced CSV Formatting**: Improved CSV exports with source breakdowns and detailed metrics.
- **Performance Dashboard**: Dedicated Streamlit tab for comprehensive system monitoring.

### v2.10.1 Enhancements
- **entity_sources.json/csv**: Files providing detailed breakdown of which extraction method found each entity.
- **Model Caching**: Significant performance improvements for batch processing through model reuse.
- **Error Handling**: Improved retry logic for download failures and better error recovery.

### v2.5.4 Enhancements
- **report.md**: Became fully interactive with Mermaid diagrams and collapsible sections.
- **manifest.json**: Upgraded checksums from MD5 to **SHA256** for enhanced security and added checksums for all files.
- **facts.txt**: Now includes source annotations for each fact.
- **entities.json**: Now includes entities from all sources for consistency.

### Previous Versions
- **v2.5.1**: Added `entities.csv`, `relationships.csv`, and the initial `report.md`.
- **v2.3**: Removed SRT/VTT subtitle formats and added the `knowledge_graph.gexf` format.

## Converting Existing Outputs

If you need to generate the latest output formats from older processing runs, you can use the scripts in the `scripts/` directory. For example, to create a `chimera_format.json` file:

```bash
poetry run python scripts/convert_to_chimera.py output/YYYYMMDD_platform_videoId
```

## Enterprise Exports
Supports bulk CSV/Excel for large collections
