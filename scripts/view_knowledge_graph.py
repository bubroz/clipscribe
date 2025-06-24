#!/usr/bin/env python3
"""
Quick viewer for ClipScribe knowledge graphs using matplotlib.

This creates a simple visualization while you set up Gephi.
"""

import json
import sys
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import argparse


def visualize_graph(json_path: Path, max_nodes: int = 50):
    """Create a quick visualization of the knowledge graph."""
    
    # Load graph
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Create NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes and edges
    for node in data['nodes'][:max_nodes]:  # Limit for readability
        G.add_node(node['id'], type=node.get('type', 'unknown'))
    
    for edge in data['edges']:
        if edge['source'] in G and edge['target'] in G:
            G.add_edge(edge['source'], edge['target'], 
                      predicate=edge.get('predicate', 'related'))
    
    # Create layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Set up the plot
    plt.figure(figsize=(16, 12))
    
    # Color nodes by type
    color_map = {
        'PERSON': '#FF6B6B',
        'ORGANIZATION': '#4ECDC4',
        'LOCATION': '#45B7D1',
        'EVENT': '#F7DC6F',
        'CONCEPT': '#BB8FCE',
        'unknown': '#95A5A6'
    }
    
    node_colors = [color_map.get(G.nodes[node].get('type', 'unknown'), '#95A5A6') 
                   for node in G.nodes()]
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, alpha=0.8)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
    
    # Draw edges with labels
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                          arrowsize=10, alpha=0.5, width=1)
    
    # Add title and stats
    plt.title(f"Knowledge Graph from: {json_path.parent.name}\n"
              f"Showing {len(G.nodes())} of {data['node_count']} nodes, "
              f"{len(G.edges())} of {data['edge_count']} edges", 
              fontsize=14, pad=20)
    
    # Add legend
    legend_elements = []
    for entity_type, color in color_map.items():
        if any(G.nodes[n].get('type') == entity_type for n in G.nodes()):
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                            label=entity_type, markersize=10,
                                            markerfacecolor=color))
    
    plt.legend(handles=legend_elements, loc='upper right', title='Entity Types')
    
    plt.axis('off')
    plt.tight_layout()
    
    # Save and show
    output_path = json_path.with_suffix('.preview.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved preview to: {output_path}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Quick viewer for ClipScribe knowledge graphs"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to knowledge_graph.json file"
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=50,
        help="Maximum nodes to display (default: 50)"
    )
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"❌ Error: File not found: {args.input_file}")
        sys.exit(1)
    
    print(f"📊 Visualizing: {args.input_file}")
    visualize_graph(args.input_file, args.max_nodes)


if __name__ == "__main__":
    main() 