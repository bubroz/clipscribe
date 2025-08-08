# Visualizing ClipScribe Knowledge Graphs

*Last Updated: June 24, 2025 at 1:40 AM PDT*

ClipScribe's v2.2 Advanced Intelligence Extraction creates rich knowledge graphs from video transcripts. This guide shows you how to visualize them using Gephi and other tools.

## Quick Start

After transcribing a video with ClipScribe, you'll find a `knowledge_graph.json` file in the output directory. Here's how to visualize it:

### Option 1: Gephi (Recommended for Large Graphs)

1. **Convert to Gephi format**:
```bash
poetry run python scripts/convert_to_gephi.py output/*/knowledge_graph.json --stats
```

2. **Download and install Gephi**:
   - Visit https://gephi.org
   - Download for your platform
   - Install and launch

3. **Import the graph**:
   - File → Open → Select the `.gexf` file
   - Click OK on the import report

4. **Apply layout**:
   - In Overview tab, go to Layout panel
   - Select "Force Atlas 2"
   - Check "Prevent Overlap"
   - Click Run for 10-20 seconds
   - Click Stop when it looks good

5. **Color by entity type**:
   - Go to Partition panel
   - Select Nodes → Choose "type"
   - Click Apply

6. **Size by importance**:
   - Go to Ranking panel
   - Select Nodes → Choose "Degree"
   - Set min size: 10, max size: 50
   - Click Apply

7. **Export beautiful visualizations**:
   - Switch to Preview tab
   - Adjust settings (show labels, edge thickness, etc.)
   - Click Refresh
   - Export as PNG/PDF/SVG

### Option 2: Quick Python Viewer

For a quick preview without installing Gephi:

```bash
poetry run python scripts/view_knowledge_graph.py output/*/knowledge_graph.json
```

This creates a simple matplotlib visualization showing up to 50 nodes.

## Understanding the Graph

### Node Types (Color Coded)
-  **PERSON**: Red nodes (Trump, Biden, etc.)
-  **ORGANIZATION**: Blue nodes (Pentagon, NATO, etc.)
-  **LOCATION**: Yellow nodes (Iran, Washington, etc.)
-  **EVENT**: Purple nodes (Summit, Election, etc.)
-  **CONCEPT**: Green nodes (Policy, Strategy, etc.)

### Edge Types (Relationships)
- **Solid lines**: High confidence relationships (>0.8)
- **Dashed lines**: Medium confidence (0.5-0.8)
- **Dotted lines**: Low confidence (<0.5)

### Node Size
- Larger nodes = More connections (higher degree)
- Key entities appear larger

## Advanced Gephi Techniques

### 1. Community Detection
- Statistics → Modularity → Run
- Partition → Nodes → Modularity Class
- Apply to see topic clusters

### 2. Find Key Players
- Statistics → Betweenness Centrality → Run
- Ranking → Nodes → Betweenness Centrality
- Size nodes by centrality to find bridges

### 3. Time-based Analysis
If your video has timestamps:
- Data Laboratory → Create time interval column
- Enable timeline at bottom
- Animate through the video's progression

### 4. Filtering
- Filters → Degree Range
- Set minimum degree to hide isolated nodes
- Union/Intersection for complex queries

## Example Graphs

### Pentagon Briefing Analysis
```
Nodes: 165
Edges: 155
Key Entities: Iran (8 connections), Trump (6), Pentagon (5)
Communities: 4 main topics (Iran nuclear, NATO, China, Defense policy)
```

### Tech Presentation Analysis  
```
Nodes: 89
Edges: 134
Key Entities: AI (15 connections), Google (12), OpenAI (10)
Communities: 3 clusters (Companies, Technologies, Concepts)
```

## Tips for Better Visualizations

1. **Start simple**: Use Force Atlas 2 with default settings
2. **Remove noise**: Filter nodes with degree < 2
3. **Use colors wisely**: Partition by type or community
4. **Label selectively**: Show labels only for high-degree nodes
5. **Export high-res**: Use Preview tab, not screenshots

## Troubleshooting

**Graph too cluttered?**
- Increase Force Atlas 2 "Scaling" parameter
- Filter low-degree nodes
- Use "Prevent Overlap"

**Can't see labels?**
- Preview → Node Labels → Show Labels
- Adjust font size in Preview Settings

**Performance issues?**
- Reduce "Iterations" in layout
- Use "LinLog mode" for large graphs
- Consider filtering before layout

## Alternative Tools

### For Developers
- **D3.js**: Web-based, interactive
- **Cytoscape.js**: Rich features, plugins
- **NetworkX + Plotly**: Python interactive plots

### For Researchers  
- **Cytoscape**: Bioinformatics-focused
- **NodeXL**: Excel integration
- **yEd**: Automatic layouts

### For Quick Sharing
- **Flourish**: Online, no install
- **RAWGraphs**: Web-based, privacy-focused
- **Kumu**: Collaborative, story-telling

## Next Steps

1. Try different layouts (Yifan Hu, Fruchterman Reingold)
2. Experiment with filters and statistics
3. Create presentation-ready exports
4. Share your visualizations!

Remember: Knowledge graphs reveal hidden connections in video content that would be impossible to see in raw transcripts 

## Built-in Beautiful Visualizations (NEW!)

### 1. Interactive 2D Network (Pyvis)
The prettiest option! Creates an interactive HTML file with:
- Nodes colored by entity type
- Sizes based on importance (connections)
- Smooth animations and physics
- Dark theme that looks professional

```bash
# Basic usage
poetry run python scripts/visualize_knowledge_graph.py output/YOUR_VIDEO_ID/knowledge_graph.json

# Custom output path
poetry run python scripts/visualize_knowledge_graph.py output/YOUR_VIDEO_ID/knowledge_graph.json -o my_graph.html
```

**Features:**
- Click and drag nodes to rearrange
- Hover for entity details
- Scroll to zoom
- Double-click to focus on a node
- Navigation controls included

### 2. 3D Rotating Graph (Plotly)
For that extra wow factor! Creates a 3D visualization that auto-rotates:

```bash
# Create 3D visualization
poetry run python scripts/visualize_knowledge_graph_plotly.py output/YOUR_VIDEO_ID/knowledge_graph.json
```

**Features:**
- Full 3D rotation and zoom
- Auto-rotating camera (stops when you interact)
- Export to high-res PNG
- Smooth performance even with large graphs

## Output Formats

### GEXF Format (For Gephi)
ClipScribe automatically generates `.gexf` files that work with Gephi:

```
output/
└── 20240625_youtube_VIDEO_ID/
    └── knowledge_graph.gexf    # Import this into Gephi
```

### Knowledge Graph JSON
The raw data for custom visualizations:

```json
{
  "nodes": [
    {
      "id": "Joe Biden",
      "type": "PERSON",
      "confidence": 0.95
    }
  ],
  "edges": [
    {
      "source": "Joe Biden",
      "target": "United States",
      "predicate": "president of",
      "confidence": 0.9
    }
  ]
}
```

## Gephi Import (If You Must)

Yes, Gephi is "kinda booty" as you said, but here's how to make it less ugly:

1. **Import**: File → Open → Select `.gexf` file
2. **Layout**: 
   - Run "Force Atlas 2" with these settings:
     - Scaling: 10.0
     - Gravity: 1.0
     - Run for ~30 seconds
   - Then run "Noverlap" to prevent overlaps
3. **Appearance**:
   - Nodes → Color → Attribute → Type
   - Nodes → Size → Attribute → Confidence
   - Edges → Color → Grayscale
4. **Preview**:
   - Background: Black
   - Show Labels: Yes
   - Label Font: White
   - Edge thickness: 0.5

## Quick Comparison

| Tool | Beauty | Ease of Use | Performance | Export Options |
|------|--------|-------------|-------------|----------------|
| Pyvis | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | HTML |
| Plotly 3D | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | HTML, PNG |
| Gephi | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | Many formats |

## Creating Custom Visualizations

You can use the `knowledge_graph.json` file with any visualization library:

### Python Example with NetworkX and Matplotlib
```python
import json
import networkx as nx
import matplotlib.pyplot as plt

# Load the graph
with open('knowledge_graph.json', 'r') as f:
    data = json.load(f)

# Create NetworkX graph
G = nx.DiGraph()
for node in data['nodes']:
    G.add_node(node['id'], **node)
for edge in data['edges']:
    G.add_edge(edge['source'], edge['target'], 
               label=edge['predicate'])

# Visualize
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue')
plt.show()
```

### JavaScript with D3.js
The knowledge graph JSON is directly compatible with D3.js force-directed graphs.

## Tips for Large Graphs

For videos with 100+ entities:
1. Use the Pyvis visualizer - it handles large graphs well
2. Filter by confidence: Only show high-confidence relationships
3. Focus on specific entity types (e.g., only PERSON and ORG)
4. Use the 3D visualization for better spatial distribution

## Troubleshooting

**Graph looks too cluttered?**
- Increase the minimum confidence threshold
- Filter out common entities like dates
- Use the 3D visualization for better spacing

**Can't see all labels?**
- Zoom in on specific areas
- Adjust font sizes in the visualization scripts
- Export to high-res image and view separately

Remember: The built-in visualizers are much prettier than Gephi! 

## Visualizing Knowledge Graphs

ClipScribe provides a powerful, unified script to visualize your extracted knowledge graphs in both 2D and 3D.

### Quick Visualization

To create a beautiful, interactive 2D graph, use the `visualize.py` script.

```bash
# Basic 2D visualization
poetry run python scripts/visualize.py output/YOUR_VIDEO_ID/knowledge_graph.json
```

This will generate an `knowledge_graph_interactive.html` file in the same directory.

### Filtering and Visualizing

You can filter out noise and visualize in one step. This is highly recommended for cleaner graphs, especially with news content.

```bash
# Filter with moderate settings and visualize
poetry run python scripts/visualize.py output/YOUR_VIDEO_ID/knowledge_graph.json --moderate

# Filter aggressively and visualize
poetry run python scripts/visualize.py output/YOUR_VIDEO_ID/knowledge_graph.json --aggressive
```

This creates a `knowledge_graph_filtered.json` and then visualizes it.

### 3D Visualization

For an impressive 3D visualization, use the `--3d` flag.

```bash
# Create a 3D graph (after filtering)
poetry run python scripts/visualize.py output/YOUR_VIDEO_ID/knowledge_graph.json --moderate --3d
```

This will generate a `knowledge_graph_3d.html` file.

### Advanced Options

The visualization script has several options to customize the output. Run `poetry run python scripts/visualize.py --help` to see them all.

## Using Gephi

For more advanced, scientific-grade analysis and visualization, you can use the generated `.gexf` file with [Gephi](https://gephi.org/).

1.  Run ClipScribe to generate a `knowledge_graph.gexf` file.
2.  Open Gephi.
3.  Go to `File > Open` and select your `.gexf` file.
4.  Use Gephi's layout algorithms (like ForceAtlas2) and appearance settings to style your graph. 

## Example Graph
See test_pbs_july20_v2.19.6_fg/20250722_youtube_J3fPtqCHGBc/knowledge_graph_interactive.html for successful output 