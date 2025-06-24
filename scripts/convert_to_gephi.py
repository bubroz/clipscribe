#!/usr/bin/env python3
"""
Convert ClipScribe knowledge graphs to Gephi GEXF format.

Usage:
    python scripts/convert_to_gephi.py output/20250624_youtube_668oKOJ43_E/knowledge_graph.json
    
This will create a .gexf file that can be opened in Gephi.
"""

import json
import sys
from pathlib import Path
import networkx as nx
from datetime import datetime
import argparse


def load_clipscribe_graph(json_path: Path) -> dict:
    """Load ClipScribe knowledge graph from JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_to_networkx(graph_data: dict) -> nx.DiGraph:
    """Convert ClipScribe format to NetworkX graph."""
    G = nx.DiGraph()
    
    # Track node types for coloring
    node_types = {}
    
    # Add nodes with attributes
    for node in graph_data['nodes']:
        node_id = node['id']
        node_type = node.get('type', 'unknown')
        confidence = node.get('confidence', 0.9)
        
        # Map entity types to colors
        color_map = {
            'PERSON': '#FF6B6B',        # Red
            'ORGANIZATION': '#4ECDC4',   # Teal
            'LOCATION': '#45B7D1',       # Blue
            'EVENT': '#F7DC6F',          # Yellow
            'CONCEPT': '#BB8FCE',        # Purple
            'TECHNOLOGY': '#52BE80',     # Green
            'DATE': '#F39C12',           # Orange
            'MONEY': '#85C1E2',          # Light Blue
            'unknown': '#95A5A6'         # Gray
        }
        
        G.add_node(
            node_id,
            label=node_id,
            type=node_type,
            confidence=confidence,
            size=20 + (confidence * 30),  # Size based on confidence
            color=color_map.get(node_type, color_map['unknown']),
            viz={'color': {'r': int(color_map.get(node_type, '#95A5A6')[1:3], 16),
                          'g': int(color_map.get(node_type, '#95A5A6')[3:5], 16),
                          'b': int(color_map.get(node_type, '#95A5A6')[5:7], 16),
                          'a': 1.0}}
        )
        node_types[node_id] = node_type
    
    # Add edges with attributes
    for edge in graph_data['edges']:
        source = edge['source']
        target = edge['target']
        predicate = edge.get('predicate', 'related_to')
        confidence = edge.get('confidence', 0.9)
        
        # Edge weight based on confidence
        weight = confidence
        
        G.add_edge(
            source,
            target,
            label=predicate,
            weight=weight,
            confidence=confidence,
            predicate=predicate
        )
    
    # Add graph metadata
    G.graph['name'] = 'ClipScribe Knowledge Graph'
    G.graph['description'] = f"Extracted on {datetime.now().isoformat()}"
    if 'node_count' in graph_data:
        G.graph['node_count'] = graph_data['node_count']
    if 'edge_count' in graph_data:
        G.graph['edge_count'] = graph_data['edge_count']
    
    return G


def save_gexf(G: nx.DiGraph, output_path: Path):
    """Save NetworkX graph as GEXF file for Gephi."""
    nx.write_gexf(G, output_path)
    print(f"✓ Saved GEXF file to: {output_path}")


def save_graphml(G: nx.DiGraph, output_path: Path):
    """Save NetworkX graph as GraphML file (alternative format)."""
    nx.write_graphml(G, output_path)
    print(f"✓ Saved GraphML file to: {output_path}")


def print_stats(G: nx.DiGraph):
    """Print graph statistics."""
    print("\n📊 Graph Statistics:")
    print(f"  • Nodes: {G.number_of_nodes()}")
    print(f"  • Edges: {G.number_of_edges()}")
    print(f"  • Density: {nx.density(G):.3f}")
    
    # Node type distribution
    node_types = nx.get_node_attributes(G, 'type')
    type_counts = {}
    for node, node_type in node_types.items():
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
    
    print("\n📌 Entity Types:")
    for entity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {entity_type}: {count}")
    
    # Most connected nodes
    degree_dict = dict(G.degree())
    top_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print("\n🔗 Most Connected Entities:")
    for node, degree in top_nodes:
        node_type = G.nodes[node].get('type', 'unknown')
        print(f"  • {node} ({node_type}): {degree} connections")


def main():
    parser = argparse.ArgumentParser(
        description="Convert ClipScribe knowledge graphs to Gephi format"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to ClipScribe knowledge_graph.json file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path (default: same name with .gexf extension)"
    )
    parser.add_argument(
        "--format",
        choices=["gexf", "graphml", "both"],
        default="gexf",
        help="Output format (default: gexf)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print graph statistics"
    )
    
    args = parser.parse_args()
    
    # Check input file
    if not args.input_file.exists():
        print(f"❌ Error: File not found: {args.input_file}")
        sys.exit(1)
    
    # Load graph
    print(f"📂 Loading knowledge graph from: {args.input_file}")
    try:
        graph_data = load_clipscribe_graph(args.input_file)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        sys.exit(1)
    
    # Convert to NetworkX
    print("🔄 Converting to NetworkX format...")
    G = convert_to_networkx(graph_data)
    
    # Determine output path
    if args.output:
        output_base = args.output.with_suffix('')
    else:
        output_base = args.input_file.with_suffix('')
    
    # Save in requested format(s)
    if args.format in ["gexf", "both"]:
        gexf_path = Path(str(output_base) + ".gexf")
        save_gexf(G, gexf_path)
    
    if args.format in ["graphml", "both"]:
        graphml_path = Path(str(output_base) + ".graphml")
        save_graphml(G, graphml_path)
    
    # Print statistics if requested
    if args.stats:
        print_stats(G)
    
    print("\n✅ Conversion complete!")
    print("\n📝 Next steps:")
    print("1. Open Gephi (download from https://gephi.org)")
    print("2. File → Open → Select the .gexf file")
    print("3. In Overview tab:")
    print("   - Run 'Force Atlas 2' layout")
    print("   - Apply 'Modularity' for community detection")
    print("   - Size nodes by 'Degree' in Ranking panel")
    print("4. Switch to Preview tab to export high-quality images")


if __name__ == "__main__":
    main() 