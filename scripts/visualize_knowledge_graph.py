#!/usr/bin/env python3
"""
Create beautiful, interactive knowledge graph visualizations from ClipScribe output.

Much prettier than Gephi! :-)
"""

import json
import sys
from pathlib import Path
from pyvis.network import Network
import argparse
from collections import defaultdict

def create_interactive_graph(knowledge_graph_path: str, output_path: str = None):
    """Create an interactive HTML visualization of the knowledge graph."""
    
    # Load the knowledge graph
    with open(knowledge_graph_path, 'r') as f:
        kg_data = json.load(f)
    
    # Create network with dark theme
    net = Network(
        height="800px", 
        width="100%", 
        bgcolor="#1a1a1a",
        font_color="white",
        notebook=False,
        directed=True
    )
    
    # Configure physics for better layout
    net.barnes_hut(
        gravity=-80000,
        central_gravity=0.3,
        spring_length=250,
        spring_strength=0.001,
        damping=0.09
    )
    
    # Color scheme by entity type (more vibrant than Gephi!)
    color_map = {
        'PERSON': '#FF6B6B',          # Coral red
        'ORG': '#4ECDC4',             # Turquoise  
        'ORGANIZATION': '#4ECDC4',     # Turquoise
        'GPE': '#45B7D1',             # Sky blue
        'LOCATION': '#45B7D1',         # Sky blue
        'LOC': '#45B7D1',             # Sky blue
        'EVENT': '#F7DC6F',           # Golden yellow
        'DATE': '#F39C12',            # Orange
        'TIME': '#F39C12',            # Orange
        'MONEY': '#85C1E2',           # Light blue
        'PERCENT': '#BB8FCE',         # Lavender
        'FAC': '#52BE80',             # Mint green
        'PRODUCT': '#EC7063',         # Salmon
        'LAW': '#AF7AC5',             # Purple
        'LANGUAGE': '#5DADE2',        # Blue
        'WORK_OF_ART': '#F1948A',     # Pink
        'NORP': '#73C6B6',            # Teal
        'CONCEPT': '#BB8FCE',         # Lavender
        'TECHNOLOGY': '#52BE80',       # Mint green
        'unknown': '#95A5A6'          # Gray
    }
    
    # Track node degrees for sizing
    node_degrees = defaultdict(int)
    
    # Count connections
    for edge in kg_data.get('edges', []):
        node_degrees[edge['source']] += 1
        node_degrees[edge['target']] += 1
    
    # Add nodes with dynamic sizing
    added_nodes = set()
    for node in kg_data.get('nodes', []):
        node_id = str(node['id'])
        if node_id not in added_nodes:
            node_type = node.get('type', 'unknown')
            confidence = node.get('confidence', 0.9)
            
            # Size based on connections (more connections = bigger node)
            degree = node_degrees[node_id]
            size = 20 + min(degree * 5, 80)  # 20-100 range
            
            # Get color
            color = color_map.get(node_type, color_map['unknown'])
            
            # Add node with hover info
            net.add_node(
                node_id,
                label=node_id,
                color=color,
                size=size,
                title=f"{node_id}<br>Type: {node_type}<br>Confidence: {confidence:.2f}<br>Connections: {degree}",
                font={'size': max(12, min(degree * 2, 24))},  # Scale font with importance
                borderWidth=2,
                borderWidthSelected=4
            )
            added_nodes.add(node_id)
    
    # Add edges with styling
    edge_counts = defaultdict(lambda: defaultdict(int))
    for edge in kg_data.get('edges', []):
        source = str(edge['source'])
        target = str(edge['target'])
        predicate = edge.get('predicate', 'related_to')
        confidence = edge.get('confidence', 0.9)
        
        # Skip if nodes don't exist
        if source not in added_nodes or target not in added_nodes:
            continue
        
        # Track duplicate edges
        edge_counts[source][target] += 1
        count = edge_counts[source][target]
        
        # Style edges based on confidence
        if confidence > 0.8:
            edge_color = "rgba(255, 255, 255, 0.6)"
            width = 2
        else:
            edge_color = "rgba(255, 255, 255, 0.3)"
            width = 1
        
        # Add edge with hover showing predicate
        net.add_edge(
            source, 
            target,
            title=f"{predicate}<br>Confidence: {confidence:.2f}",
            color=edge_color,
            width=width,
            arrows="to",
            smooth={
                "enabled": True,
                "type": "curvedCW" if count > 1 else "dynamic",
                "roundness": 0.2 * count  # Curve more for multiple edges
            }
        )
    
    # Configure additional options
    net.set_options("""
    {
        "nodes": {
            "font": {
                "strokeWidth": 3,
                "strokeColor": "#000000"
            },
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.5)",
                "size": 10,
                "x": 5,
                "y": 5
            }
        },
        "edges": {
            "shadow": {
                "enabled": false
            },
            "smooth": {
                "type": "dynamic"
            }
        },
        "physics": {
            "barnesHut": {
                "avoidOverlap": 0.5
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "hideEdgesOnDrag": true,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """)
    
    # Generate output path
    if not output_path:
        input_path = Path(knowledge_graph_path)
        output_path = input_path.parent / "knowledge_graph_interactive.html"
    
    # Save the visualization
    net.save_graph(str(output_path))
    
    # Add custom CSS to make it even prettier
    with open(output_path, 'r') as f:
        html_content = f.read()
    
    custom_css = """
    <style>
        body {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        #mynetwork {
            border: 2px solid #333;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
        .vis-navigation {
            background: rgba(255, 255, 255, 0.1) !important;
            border-radius: 5px !important;
        }
        .vis-button {
            background: rgba(255, 255, 255, 0.2) !important;
            border: none !important;
            color: white !important;
        }
        .vis-button:hover {
            background: rgba(255, 255, 255, 0.3) !important;
        }
        h1 {
            color: white;
            text-align: center;
            font-weight: 300;
            margin-bottom: 30px;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
        }
        .stats {
            color: #aaa;
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
        }
    </style>
    """
    
    # Add title and stats
    title_html = f"""
    <h1>ClipScribe Knowledge Graph Visualization</h1>
    <div class="stats">
        {len(kg_data.get('nodes', []))} entities • {len(kg_data.get('edges', []))} relationships
    </div>
    """
    
    # Insert custom styling
    html_content = html_content.replace('<head>', f'<head>{custom_css}')
    html_content = html_content.replace('<body>', f'<body>{title_html}')
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"✨ Beautiful interactive graph saved to: {output_path}")
    print(f"📊 Stats: {len(kg_data.get('nodes', []))} nodes, {len(kg_data.get('edges', []))} edges")
    print("\n🎯 Interaction tips:")
    print("  - Click and drag nodes to rearrange")
    print("  - Hover over nodes/edges for details")
    print("  - Scroll to zoom in/out")
    print("  - Double-click to focus on a node")
    print("  - Use navigation controls on the left")

def main():
    parser = argparse.ArgumentParser(description="Create beautiful knowledge graph visualizations")
    parser.add_argument("knowledge_graph", help="Path to knowledge_graph.json file")
    parser.add_argument("-o", "--output", help="Output HTML file path")
    
    args = parser.parse_args()
    
    if not Path(args.knowledge_graph).exists():
        print(f"Error: {args.knowledge_graph} not found")
        sys.exit(1)
    
    create_interactive_graph(args.knowledge_graph, args.output)

if __name__ == "__main__":
    main() 