#!/usr/bin/env python3
"""
Convert existing ClipScribe output to Chimera format.

This script reads the existing output files from a ClipScribe run and
generates the chimera_format.json file that's compatible with Chimera Researcher.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None


def convert_to_chimera_format(output_dir: Path) -> Dict[str, Any]:
    """
    Convert ClipScribe output directory to Chimera format.
    
    Args:
        output_dir: Path to ClipScribe output directory
        
    Returns:
        Dictionary in Chimera format
    """
    # Load all necessary files
    metadata = load_json_file(output_dir / "metadata.json")
    transcript_json = load_json_file(output_dir / "transcript.json")
    entities = load_json_file(output_dir / "entities.json")
    
    if not all([metadata, transcript_json]):
        raise ValueError("Missing required files (metadata.json, transcript.json)")
    
    # Extract video metadata
    video_meta = metadata.get("video", {})
    
    # Build Chimera format
    chimera_data = {
        "type": "video",
        "source": "video_intelligence",
        "url": video_meta.get("url", ""),
        "title": video_meta.get("title", ""),
        "content": transcript_json.get("transcript", {}).get("full_text", ""),
        "summary": transcript_json.get("analysis", {}).get("summary", ""),
        "metadata": {
            "channel": video_meta.get("channel"),
            "duration": video_meta.get("duration"),
            "published_at": video_meta.get("published_at"),
            "view_count": video_meta.get("view_count"),
            "key_points": transcript_json.get("analysis", {}).get("key_points", []),
            "entities": entities.get("entities", []) if entities else [],
            "topics": entities.get("topics", []) if entities else [],
            "sentiment": transcript_json.get("analysis", {}).get("sentiment"),
            "processing_cost": transcript_json.get("processing", {}).get("cost", 0)
        }
    }
    
    # Add relationships if available
    relationships = load_json_file(output_dir / "relationships.json")
    if relationships:
        chimera_data["metadata"]["relationships"] = relationships.get("relationships", [])
    
    # Add knowledge graph if available
    knowledge_graph = load_json_file(output_dir / "knowledge_graph.json")
    if knowledge_graph:
        chimera_data["metadata"]["knowledge_graph"] = knowledge_graph
    
    return chimera_data


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python convert_to_chimera.py <output_directory>")
        print("Example: python convert_to_chimera.py output/20250624_youtube_HSODoOfhnks")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    
    if not output_dir.exists():
        print(f"Error: Directory {output_dir} does not exist")
        sys.exit(1)
    
    if not output_dir.is_dir():
        print(f"Error: {output_dir} is not a directory")
        sys.exit(1)
    
    try:
        # Convert to Chimera format
        print(f"Converting {output_dir} to Chimera format...")
        chimera_data = convert_to_chimera_format(output_dir)
        
        # Save to file
        chimera_path = output_dir / "chimera_format.json"
        with open(chimera_path, 'w', encoding='utf-8') as f:
            json.dump(chimera_data, f, indent=2)
        
        print(f"✅ Successfully created {chimera_path}")
        print(f"   - Title: {chimera_data['title']}")
        print(f"   - URL: {chimera_data['url']}")
        print(f"   - Content length: {len(chimera_data['content'])} chars")
        print(f"   - Entities: {len(chimera_data['metadata']['entities'])}")
        
        if "relationships" in chimera_data["metadata"]:
            print(f"   - Relationships: {len(chimera_data['metadata']['relationships'])}")
        
        if "knowledge_graph" in chimera_data["metadata"]:
            kg = chimera_data["metadata"]["knowledge_graph"]
            print(f"   - Knowledge graph: {kg.get('node_count', 0)} nodes, {kg.get('edge_count', 0)} edges")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 