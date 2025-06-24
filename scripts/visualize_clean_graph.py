#!/usr/bin/env python3
"""
One-step clean visualization: filter noise and create beautiful graphs.

Because who wants to look at spaghetti? :-)
"""

import json
import sys
from pathlib import Path
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(
        description="Filter and visualize knowledge graphs in one step",
        epilog="Examples:\n"
               "  Basic:      python visualize_clean_graph.py output/VIDEO/knowledge_graph.json\n"
               "  Aggressive: python visualize_clean_graph.py output/VIDEO/knowledge_graph.json --aggressive\n"
               "  3D:         python visualize_clean_graph.py output/VIDEO/knowledge_graph.json --3d\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("input", help="Input knowledge_graph.json file")
    parser.add_argument("--aggressive", action="store_true",
                       help="Use aggressive filtering (recommended for news videos)")
    parser.add_argument("--moderate", action="store_true",
                       help="Use moderate filtering (min 1 connection, 0.65 confidence)")
    parser.add_argument("--3d", dest="three_d", action="store_true",
                       help="Create 3D visualization instead of 2D")
    parser.add_argument("--both", action="store_true",
                       help="Create both 2D and 3D visualizations")
    parser.add_argument("-m", "--min-connections", type=int,
                       help="Override minimum connections threshold")
    parser.add_argument("-c", "--confidence", type=float,
                       help="Override confidence threshold")
    parser.add_argument("--no-filter", action="store_true",
                       help="Skip filtering, just visualize")
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"❌ Error: {args.input} not found")
        sys.exit(1)
    
    input_path = Path(args.input)
    
    # Determine filtering settings
    if args.no_filter:
        filtered_path = input_path
        print("🎯 Skipping filtering, visualizing original graph")
    else:
        # Build filter command
        filter_cmd = [
            sys.executable, 
            str(Path(__file__).parent / "filter_knowledge_graph.py"),
            str(input_path)
        ]
        
        if args.aggressive:
            filter_cmd.append("--aggressive")
            print("🧹 Using aggressive filtering (recommended for news)")
        elif args.moderate:
            if not args.min_connections:
                args.min_connections = 1
            if not args.confidence:
                args.confidence = 0.65
            print("🧹 Using moderate filtering")
        
        if args.min_connections is not None:
            filter_cmd.extend(["-m", str(args.min_connections)])
        if args.confidence is not None:
            filter_cmd.extend(["-c", str(args.confidence)])
        
        # Run filtering
        print(f"📊 Filtering {input_path.name}...")
        result = subprocess.run(filter_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Filtering failed: {result.stderr}")
            sys.exit(1)
        
        print(result.stdout)
        filtered_path = input_path.parent / "knowledge_graph_filtered.json"
    
    # Create visualizations
    viz_scripts = []
    if args.three_d and not args.both:
        viz_scripts.append(("visualize_knowledge_graph_plotly.py", "3D"))
    elif args.both:
        viz_scripts.append(("visualize_knowledge_graph.py", "2D"))
        viz_scripts.append(("visualize_knowledge_graph_plotly.py", "3D"))
    else:
        viz_scripts.append(("visualize_knowledge_graph.py", "2D"))
    
    outputs = []
    for script, viz_type in viz_scripts:
        print(f"\n🎨 Creating {viz_type} visualization...")
        viz_cmd = [
            sys.executable,
            str(Path(__file__).parent / script),
            str(filtered_path)
        ]
        
        result = subprocess.run(viz_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Visualization failed: {result.stderr}")
        else:
            print(result.stdout)
            # Extract output path from stdout
            for line in result.stdout.split('\n'):
                if 'saved to:' in line:
                    output_file = line.split('saved to:')[1].strip()
                    outputs.append(output_file)
    
    # Open the visualizations
    if outputs:
        print(f"\n🚀 Opening visualization{'s' if len(outputs) > 1 else ''}...")
        for output in outputs:
            subprocess.run(["open", output])
    
    # Quick stats
    if not args.no_filter:
        with open(filtered_path, 'r') as f:
            filtered_data = json.load(f)
        
        if 'filtered_stats' in filtered_data:
            stats = filtered_data['filtered_stats']
            removal_rate = stats['nodes_removed'] / stats['original_nodes'] * 100
            print(f"\n📈 Summary: Removed {removal_rate:.0f}% of noise")
            print(f"   Clean graph has {filtered_data['node_count']} meaningful entities")

if __name__ == "__main__":
    main() 