# Output Formats Guide

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

### entities.json / entities.csv
A complete list of all entities extracted from the video.
- **`entities.json`**: Detailed JSON output with `name`, `type`, `confidence`, `source`, and raw `properties`.
- **`entities.csv`**: A spreadsheet-friendly format containing the most important fields.
- **Source Tracking**: Both formats include the source of the entity (e.g., `SpaCy`, `GLiNER`, `LLM`) for pipeline transparency.

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
- **Rich Formatting**: Uses emoji, confidence indicators (🟩🟨🟥), and tables for a highly scannable and visually appealing summary.
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

## Format Changes

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
