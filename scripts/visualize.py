#!/usr/bin/env python3
"""
Create beautiful, interactive knowledge graph visualizations from ClipScribe output.

This is a unified script that combines filtering, 2D, and 3D visualization.
"""

import json
import sys
from pathlib import Path
from pyvis.network import Network
import argparse
from collections import defaultdict
import subprocess

# --- 3D Visualization Logic (from visualize_knowledge_graph_plotly.py) ---
def create_3d_graph(knowledge_graph_path: str, output_path: str = None):
    """Create a 3D interactive graph visualization using Plotly."""
    try:
        import plotly.graph_objects as go
        import networkx as nx
    except ImportError:
        print("❌ Error: Plotly and NetworkX are required for 3D visualization.")
        print("Please run: pip install plotly networkx")
        sys.exit(1)

    # Load the knowledge graph
    with open(knowledge_graph_path, 'r') as f:
        kg_data = json.load(f)

    # Create NetworkX graph for layout
    G = nx.DiGraph()
    for node in kg_data.get('nodes', []):
        G.add_node(node['id'], **node)
    for edge in kg_data.get('edges', []):
        if edge['source'] in G.nodes and edge['target'] in G.nodes:
            G.add_edge(edge['source'], edge['target'], **edge)

    pos = nx.spring_layout(G, dim=3, k=2, iterations=50)
    
    node_x, node_y, node_z, node_text, node_color, node_size = [], [], [], [], [], []
    color_map = {
        'PERSON': '#FF6B6B', 'ORG': '#4ECDC4', 'ORGANIZATION': '#4ECDC4',
        'GPE': '#45B7D1', 'LOCATION': '#45B7D1', 'LOC': '#45B7D1',
        'EVENT': '#F7DC6F', 'DATE': '#F39C12', 'unknown': '#95A5A6'
    }
    node_degrees = defaultdict(int)
    for edge in kg_data.get('edges', []):
        node_degrees[edge['source']] += 1
        node_degrees[edge['target']] += 1

    for node in G.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        node_data = G.nodes[node]
        node_type = node_data.get('type', 'unknown')
        degree = node_degrees[node]
        node_text.append(f"{node}<br>Type: {node_type}<br>Connections: {degree}")
        node_color.append(color_map.get(node_type, color_map['unknown']))
        node_size.append(10 + min(degree * 3, 40))

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        text=[node for node in G.nodes()],
        textposition="top center",
        hoverinfo='text', hovertext=node_text,
        marker=dict(size=node_size, color=node_color, line=dict(width=2, color='white'))
    )
    
    edge_x, edge_y, edge_z = [], [], []
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(x=edge_x, y=edge_y, z=edge_z, mode='lines', line=dict(width=1, color='#888'), hoverinfo='none')

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"ClipScribe 3D Knowledge Graph<br><sub>{len(G.nodes)} nodes • {len(G.edges)} edges</sub>",
        title_font_size=24, showlegend=False, hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=40),
        scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
        paper_bgcolor='#1a1a1a', font_color='white'
    )
    
    if not output_path:
        input_path = Path(knowledge_graph_path)
        output_path = input_path.parent / "knowledge_graph_3d.html"
    
    fig.write_html(str(output_path), config={'displaylogo': False})
    print(f"🌟 3D visualization saved to: {output_path}")


# --- 2D Visualization Logic (from visualize_knowledge_graph.py) ---
def create_2d_graph(knowledge_graph_path: str, output_path: str = None):
    """Create an interactive 2D HTML visualization of the knowledge graph."""
    with open(knowledge_graph_path, 'r') as f:
        kg_data = json.load(f)
    
    net = Network(height="800px", width="100%", bgcolor="#1a1a1a", font_color="white", directed=True)
    net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=250, spring_strength=0.001, damping=0.09)
    
    color_map = {
        'PERSON': '#FF6B6B', 'ORG': '#4ECDC4', 'ORGANIZATION': '#4ECDC4',
        'GPE': '#45B7D1', 'LOCATION': '#45B7D1', 'LOC': '#45B7D1',
        'EVENT': '#F7DC6F', 'DATE': '#F39C12', 'CONCEPT': '#BB8FCE', 'unknown': '#95A5A6'
    }
    
    node_degrees = defaultdict(int)
    for edge in kg_data.get('edges', []):
        node_degrees[edge['source']] += 1
        node_degrees[edge['target']] += 1
    
    added_nodes = set()
    for node in kg_data.get('nodes', []):
        node_id, node_type = str(node['id']), node.get('type', 'unknown')
        if node_id not in added_nodes:
            degree = node_degrees[node_id]
            size = 20 + min(degree * 5, 80)
            color = color_map.get(node_type, color_map['unknown'])
            net.add_node(node_id, label=node_id, color=color, size=size, title=f"{node_id}<br>Type: {node_type}<br>Connections: {degree}")
            added_nodes.add(node_id)
            
    for edge in kg_data.get('edges', []):
        source, target, predicate = str(edge['source']), str(edge['target']), edge.get('predicate', 'related_to')
        if source in added_nodes and target in added_nodes:
            net.add_edge(source, target, title=predicate, color="rgba(255, 255, 255, 0.6)", width=2, arrows="to")
            
    net.set_options("""
    {"interaction": {"navigationButtons": true, "keyboard": true}}
    """)
    
    if not output_path:
        input_path = Path(knowledge_graph_path)
        output_path = input_path.parent / "knowledge_graph_interactive.html"
        
    net.save_graph(str(output_path))
    print(f"✨ 2D Interactive graph saved to: {output_path}")


# --- Main Controller ---
def main():
    parser = argparse.ArgumentParser(
        description="Filter and visualize knowledge graphs from ClipScribe.",
        epilog="Example: python visualize.py output/VIDEO/knowledge_graph.json --aggressive --3d",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("input", help="Input knowledge_graph.json file")
    
    # Visualization options
    parser.add_argument("--3d", dest="three_d", action="store_true", help="Create 3D visualization instead of 2D")
    parser.add_argument("--2d", dest="two_d", action="store_true", help="Create 2D visualization (default)")

    # Filtering options
    parser.add_argument("--no-filter", action="store_true", help="Skip filtering, just visualize")
    parser.add_argument("--aggressive", action="store_true", help="Use aggressive filtering (min 3 connections, 0.75 confidence)")
    parser.add_argument("--moderate", action="store_true", help="Use moderate filtering (min 1 connection, 0.65 confidence)")
    parser.add_argument("-m", "--min-connections", type=int, help="Override minimum connections threshold")
    parser.add_argument("-c", "--confidence", type=float, help="Override confidence threshold")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        sys.exit(1)
        
    # --- Filtering Step ---
    if args.no_filter:
        filtered_path = input_path
        print("🎯 Skipping filtering, visualizing original graph.")
    else:
        filter_cmd = [sys.executable, str(Path(__file__).parent / "filter_knowledge_graph.py"), str(input_path)]
        
        if args.aggressive:
            filter_cmd.extend(["--aggressive"])
            print("🧹 Using aggressive filtering...")
        elif args.moderate:
            filter_cmd.extend(["--min-connections", "1", "--confidence", "0.65"])
            print("🧹 Using moderate filtering...")
            
        if args.min_connections is not None:
            filter_cmd.extend(["--min-connections", str(args.min_connections)])
        if args.confidence is not None:
            filter_cmd.extend(["--confidence", str(args.confidence)])
            
        print(f"📊 Filtering {input_path.name}...")
        result = subprocess.run(filter_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Filtering failed: {result.stderr}")
            sys.exit(1)
        print(result.stdout)
        filtered_path = input_path.parent / "knowledge_graph_filtered.json"
        
    # --- Visualization Step ---
    if args.three_d:
        print("\n🎨 Creating 3D visualization...")
        create_3d_graph(str(filtered_path))
    else: # Default to 2D
        print("\n🎨 Creating 2D visualization...")
        create_2d_graph(str(filtered_path))

if __name__ == "__main__":
    main() 