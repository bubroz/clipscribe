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
- 🔴 **PERSON**: Red nodes (Trump, Biden, etc.)
- 🟦 **ORGANIZATION**: Blue nodes (Pentagon, NATO, etc.)
- 🟡 **LOCATION**: Yellow nodes (Iran, Washington, etc.)
- 🟣 **EVENT**: Purple nodes (Summit, Election, etc.)
- 🟢 **CONCEPT**: Green nodes (Policy, Strategy, etc.)

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

Remember: Knowledge graphs reveal hidden connections in video content that would be impossible to see in raw transcripts :-) 