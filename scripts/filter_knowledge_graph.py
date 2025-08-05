#!/usr/bin/env python3
"""
Filter and clean knowledge graphs to remove noise and improve visualization quality.

This helps create cleaner, more meaningful visualizations 
"""

import json
import sys
from pathlib import Path
import argparse
from collections import defaultdict

# Generic terms that shouldn't be nodes
GENERIC_TERMS = {
    'country', 'location', 'participant', 'organization', 'person', 
    'entity', 'place', 'thing', 'object', 'subject', 'event',
    'program', 'project', 'system', 'process', 'method',
    'official', 'member', 'group', 'team', 'department',
    'area', 'region', 'zone', 'territory', 'state',
    'report', 'document', 'statement', 'announcement',
    'week', 'month', 'year', 'time', 'period', 'date'
}

# Common predicates that shouldn't be nodes
PREDICATE_TERMS = {
    'appointed by', 'officeholder', 'position held', 'office held by',
    'located in', 'part of', 'member of', 'affiliated with',
    'president of', 'capital of', 'contains', 'has', 'is', 'was',
    'diplomatic relation', 'related to', 'connected to',
    'founded by', 'owned by', 'created by', 'managed by',
    'succeeded by', 'preceded by', 'replaced by',
    'instance of', 'type of', 'kind of', 'category of',
    'participant in', 'involved in', 'engaged in',
    'ally', 'adversary', 'partner', 'rival'
}

# Phrases that indicate extraction errors
NOISE_PATTERNS = [
    'has directed and made clear',
    'sources and methods',
    'cannot have a nuclear',
    'stealth bomber',
    'sub', 'pub', 'mil',  # Common abbreviation artifacts
    'located in the administrative territorial entity',
    'office held by head of',
    'shares border with',
    'next to body of water'
]

def should_filter_node(node_id, node_data):
    """Determine if a node should be filtered out."""
    node_id_lower = node_id.lower().strip()
    
    # Filter single letters or very short generic terms
    if len(node_id) <= 2 and not node_id.isupper():
        return True
    
    # Filter generic terms
    if node_id_lower in GENERIC_TERMS:
        return True
    
    # Filter predicates appearing as nodes
    if node_id_lower in PREDICATE_TERMS:
        return True
    
    # Filter noise patterns
    for pattern in NOISE_PATTERNS:
        if pattern in node_id_lower:
            return True
    
    # Filter nodes that are just numbers or codes
    if node_id.replace('-', '').replace('.', '').isdigit():
        return True
    
    # Filter nodes with very low confidence (likely errors)
    confidence = node_data.get('confidence', 1.0)
    if confidence < 0.5:
        return True
    
    # Keep nodes with high degree (many connections) even if they seem generic
    # This will be calculated later
    
    return False

def merge_similar_nodes(nodes):
    """Merge nodes that are variations of the same entity."""
    merge_map = {}
    
    # Common variations to merge
    variations = [
        ("Iran's nuclear program", "Iranian nuclear program"),
        ("U.S.", "US", "United States"),
        ("President Trump", "Donald Trump", "Trump"),
        ("President Biden", "Joe Biden", "Biden"),
        ("N. Korea", "North Korea", "DPRK"),
        ("S. Korea", "South Korea", "Republic of Korea"),
    ]
    
    for group in variations:
        primary = group[0]
        for variant in group[1:]:
            merge_map[variant] = primary
    
    # Also merge nodes that differ only by case or punctuation
    node_ids = [n['id'] for n in nodes]
    for i, node1 in enumerate(node_ids):
        for node2 in node_ids[i+1:]:
            if node1.lower().replace(' ', '').replace('-', '') == node2.lower().replace(' ', '').replace('-', ''):
                if len(node1) > len(node2):
                    merge_map[node2] = node1
                else:
                    merge_map[node1] = node2
    
    return merge_map

def filter_knowledge_graph(kg_data, min_connections=0, confidence_threshold=0.6):
    """Filter and clean the knowledge graph."""
    # First pass: count connections for each node
    node_degrees = defaultdict(int)
    for edge in kg_data.get('edges', []):
        node_degrees[edge['source']] += 1
        node_degrees[edge['target']] += 1
    
    # Get merge mapping
    merge_map = merge_similar_nodes(kg_data.get('nodes', []))
    
    # Filter nodes
    filtered_nodes = []
    kept_node_ids = set()
    
    for node in kg_data.get('nodes', []):
        node_id = node['id']
        
        # Apply merge mapping
        if node_id in merge_map:
            continue  # Skip merged nodes
        
        # Check if we should filter this node
        if should_filter_node(node_id, node):
            # Keep high-degree nodes even if they seem generic
            if node_degrees[node_id] < 3:
                continue
        
        # Apply confidence threshold
        if node.get('confidence', 1.0) < confidence_threshold:
            continue
        
        # Apply minimum connections filter
        if node_degrees[node_id] < min_connections:
            continue
        
        filtered_nodes.append(node)
        kept_node_ids.add(node_id)
    
    # Filter edges
    filtered_edges = []
    for edge in kg_data.get('edges', []):
        source = edge['source']
        target = edge['target']
        
        # Apply merge mapping
        if source in merge_map:
            source = merge_map[source]
        if target in merge_map:
            target = merge_map[target]
        
        # Skip self-loops
        if source == target:
            continue
        
        # Only keep edges between kept nodes
        if source in kept_node_ids and target in kept_node_ids:
            # Update edge with merged nodes
            edge_copy = edge.copy()
            edge_copy['source'] = source
            edge_copy['target'] = target
            
            # Filter out generic predicates
            predicate = edge_copy.get('predicate', 'related_to').lower()
            if predicate in ['related to', 'connected to', 'associated with']:
                # Only keep these if confidence is high
                if edge_copy.get('confidence', 0.9) < 0.8:
                    continue
            
            filtered_edges.append(edge_copy)
    
    # Create filtered graph
    filtered_kg = {
        'nodes': filtered_nodes,
        'edges': filtered_edges,
        'node_count': len(filtered_nodes),
        'edge_count': len(filtered_edges),
        'filtered_stats': {
            'original_nodes': len(kg_data.get('nodes', [])),
            'original_edges': len(kg_data.get('edges', [])),
            'nodes_removed': len(kg_data.get('nodes', [])) - len(filtered_nodes),
            'edges_removed': len(kg_data.get('edges', [])) - len(filtered_edges),
            'merge_count': len(merge_map)
        }
    }
    
    return filtered_kg

def main():
    parser = argparse.ArgumentParser(description="Filter and clean knowledge graphs")
    parser.add_argument("input", help="Input knowledge_graph.json file")
    parser.add_argument("-o", "--output", help="Output file (default: knowledge_graph_filtered.json)")
    parser.add_argument("-m", "--min-connections", type=int, default=0, 
                       help="Minimum number of connections for a node (default: 0)")
    parser.add_argument("-c", "--confidence", type=float, default=0.6,
                       help="Minimum confidence threshold (default: 0.6)")
    parser.add_argument("--aggressive", action="store_true",
                       help="Use aggressive filtering (min 2 connections, 0.7 confidence)")
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Error: {args.input} not found")
        sys.exit(1)
    
    # Load the graph
    with open(args.input, 'r') as f:
        kg_data = json.load(f)
    
    # Apply aggressive settings if requested
    if args.aggressive:
        args.min_connections = max(args.min_connections, 2)
        args.confidence = max(args.confidence, 0.7)
    
    # Filter the graph
    filtered_kg = filter_knowledge_graph(
        kg_data, 
        min_connections=args.min_connections,
        confidence_threshold=args.confidence
    )
    
    # Save filtered graph
    if not args.output:
        input_path = Path(args.input)
        args.output = input_path.parent / "knowledge_graph_filtered.json"
    
    with open(args.output, 'w') as f:
        json.dump(filtered_kg, f, indent=2)
    
    # Print statistics
    stats = filtered_kg['filtered_stats']
    print(f"✨ Filtered knowledge graph saved to: {args.output}")
    print(f"\n📊 Filtering Statistics:")
    print(f"  Original: {stats['original_nodes']} nodes, {stats['original_edges']} edges")
    print(f"  Filtered: {filtered_kg['node_count']} nodes, {filtered_kg['edge_count']} edges")
    print(f"  Removed: {stats['nodes_removed']} nodes, {stats['edges_removed']} edges")
    print(f"  Merged: {stats['merge_count']} duplicate nodes")
    print(f"\n🎯 Applied filters:")
    print(f"  - Min connections: {args.min_connections}")
    print(f"  - Min confidence: {args.confidence}")
    print(f"  - Removed generic terms and predicates")
    print(f"  - Merged similar entities")

if __name__ == "__main__":
    main() 