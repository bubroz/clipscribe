#!/usr/bin/env python3
"""
Create stunning 3D knowledge graph visualizations using Plotly.

For when you want that extra wow factor! :-)
"""

import json
import sys
from pathlib import Path
import plotly.graph_objects as go
import networkx as nx
from collections import defaultdict
import numpy as np

def create_3d_graph(knowledge_graph_path: str, output_path: str = None):
    """Create a 3D interactive graph visualization."""
    
    # Load the knowledge graph
    with open(knowledge_graph_path, 'r') as f:
        kg_data = json.load(f)
    
    # Create NetworkX graph for layout
    G = nx.DiGraph()
    
    # Add nodes and edges
    for node in kg_data.get('nodes', []):
        G.add_node(node['id'], **node)
    
    for edge in kg_data.get('edges', []):
        if edge['source'] in G.nodes and edge['target'] in G.nodes:
            G.add_edge(edge['source'], edge['target'], **edge)
    
    # Use spring layout for 3D positions
    pos = nx.spring_layout(G, dim=3, k=2, iterations=50)
    
    # Extract node positions
    node_x = []
    node_y = []
    node_z = []
    node_text = []
    node_color = []
    node_size = []
    
    # Color map
    color_map = {
        'PERSON': '#FF6B6B',
        'ORG': '#4ECDC4',
        'ORGANIZATION': '#4ECDC4',
        'GPE': '#45B7D1',
        'LOCATION': '#45B7D1',
        'LOC': '#45B7D1',
        'EVENT': '#F7DC6F',
        'DATE': '#F39C12',
        'unknown': '#95A5A6'
    }
    
    # Count connections for sizing
    node_degrees = defaultdict(int)
    for edge in kg_data.get('edges', []):
        node_degrees[edge['source']] += 1
        node_degrees[edge['target']] += 1
    
    for node in G.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        
        # Get node data
        node_data = G.nodes[node]
        node_type = node_data.get('type', 'unknown')
        confidence = node_data.get('confidence', 0.9)
        degree = node_degrees[node]
        
        # Node styling
        node_text.append(f"{node}<br>Type: {node_type}<br>Connections: {degree}")
        node_color.append(color_map.get(node_type, color_map['unknown']))
        node_size.append(10 + min(degree * 3, 40))
    
    # Create node trace
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        text=[node for node in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=2, color='white'),
            opacity=0.9
        ),
        textfont=dict(size=10, color='white')
    )
    
    # Extract edge positions
    edge_x = []
    edge_y = []
    edge_z = []
    edge_text = []
    
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
        
        edge_data = G.edges[edge]
        predicate = edge_data.get('predicate', 'related_to')
        edge_text.append(f"{edge[0]} → {edge[1]}<br>{predicate}")
    
    # Create edge trace
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(width=1, color='rgba(125, 125, 125, 0.5)'),
        hoverinfo='none'
    )
    
    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    
    # Update layout for dark theme
    fig.update_layout(
        title={
            'text': f"ClipScribe 3D Knowledge Graph<br><sub>{len(G.nodes)} entities • {len(G.edges)} relationships</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': 'white'}
        },
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=60),
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        scene=dict(
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            zaxis=dict(showgrid=False, zeroline=False, visible=False),
            bgcolor='#1a1a1a'
        ),
        height=800
    )
    
    # Add camera controls
    camera = dict(
        eye=dict(x=1.5, y=1.5, z=1.5),
        center=dict(x=0, y=0, z=0)
    )
    fig.update_layout(scene_camera=camera)
    
    # Generate output path
    if not output_path:
        input_path = Path(knowledge_graph_path)
        output_path = input_path.parent / "knowledge_graph_3d.html"
    
    # Save with custom config
    config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan3d', 'select3d', 'lasso3d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'knowledge_graph_3d',
            'height': 1080,
            'width': 1920,
            'scale': 2
        }
    }
    
    fig.write_html(
        str(output_path),
        config=config,
        include_plotlyjs='cdn',
        div_id="graph3d"
    )
    
    # Add custom CSS to the HTML
    with open(output_path, 'r') as f:
        html_content = f.read()
    
    custom_html = """
    <style>
        body {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
        }
        #graph3d {
            height: 100vh;
        }
        .modebar {
            background: rgba(255, 255, 255, 0.1) !important;
            border-radius: 5px;
            padding: 5px;
        }
        .modebar-btn {
            color: white !important;
        }
    </style>
    <script>
        // Rotate camera on load
        setTimeout(function() {
            var graphDiv = document.getElementById('graph3d');
            var camera = graphDiv._fullLayout.scene._scene.getCamera();
            
            function rotate() {
                camera.eye.x = 1.5 * Math.cos(Date.now() * 0.0001);
                camera.eye.y = 1.5 * Math.sin(Date.now() * 0.0001);
                Plotly.relayout(graphDiv, {'scene.camera': camera});
                requestAnimationFrame(rotate);
            }
            
            // Start rotation (user can stop by interacting)
            var rotating = true;
            graphDiv.on('plotly_relayout', function() {
                rotating = false;
            });
            
            function conditionalRotate() {
                if (rotating) rotate();
                else setTimeout(conditionalRotate, 100);
            }
            conditionalRotate();
        }, 500);
    </script>
    """
    
    html_content = html_content.replace('</body>', custom_html + '</body>')
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"🌟 3D visualization saved to: {output_path}")
    print(f"📊 Graph has {len(G.nodes)} nodes and {len(G.edges)} edges")
    print("\n🎮 Controls:")
    print("  - Click and drag to rotate")
    print("  - Scroll to zoom")
    print("  - Double-click to reset view")
    print("  - Hover over nodes for details")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create 3D knowledge graph visualizations")
    parser.add_argument("knowledge_graph", help="Path to knowledge_graph.json file")
    parser.add_argument("-o", "--output", help="Output HTML file path")
    
    args = parser.parse_args()
    
    if not Path(args.knowledge_graph).exists():
        print(f"Error: {args.knowledge_graph} not found")
        sys.exit(1)
    
    create_3d_graph(args.knowledge_graph, args.output)

if __name__ == "__main__":
    main() 