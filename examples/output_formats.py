#!/usr/bin/env python3
"""Output Formats Example - Export transcripts in various formats."""

import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from clipscribe.retrievers import UniversalVideoClient
from clipscribe.models import VideoIntelligence


async def demonstrate_output_formats():
    """Show all available output formats."""
    
    client = UniversalVideoClient()
    
    # Sample video
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("📹 Processing video for format demonstration...")
    
    # Process with all formats
    result = await client.transcribe_video(
        video_url,
        save_outputs=True,
        output_formats=['txt', 'json']  # Core formats for intelligence extraction
    )
    
    print("\n✅ Video processed! Demonstrating output formats:\n")
    
    # 1. Plain Text (.txt)
    print("1️⃣ Plain Text (.txt)")
    print("-" * 40)
    print("Simple text transcript, perfect for:")
    print("  • Reading and analysis")
    print("  • Copy/paste into documents")
    print("  • Full-text search")
    print("\nExample:")
    print(result.transcript.full_text[:200] + "...\n")
    
    # 2. JSON (.json)
    print("2️⃣ JSON (.json)")
    print("-" * 40)
    print("Structured data format with full metadata:")
    print("  • API integration")
    print("  • Database import")
    print("  • Custom processing")
    print("  • Knowledge graph generation")
    print("\nExample structure:")
    example_json = {
        "metadata": {
            "title": result.metadata.title,
            "duration": result.metadata.duration,
            "url": result.metadata.url
        },
        "transcript": {
            "full_text": "...",
            "segments": [
                {"start": 0.0, "end": 3.0, "text": "..."}
            ]
        },
        "entities": [
            {"name": "Person Name", "type": "PERSON", "confidence": 0.95}
        ],
        "relationships": [
            {"subject": "Person", "predicate": "works_at", "object": "Company"}
        ],
        "processing": {
            "cost": result.processing_cost,
            "time": result.processing_time
        }
    }
    print(json.dumps(example_json, indent=2)[:400] + "...\n")
    
    # 3. Knowledge Graph Files
    print("3️⃣ Knowledge Graph Formats")
    print("-" * 40)
    print("Extracted intelligence in graph format:")
    print("  • knowledge_graph.json - Raw graph data")
    print("  • knowledge_graph.gexf - Gephi visualization")
    print("  • relationships.json - Entity relationships")
    print("  • entities.json - Extracted entities")
    print("  • facts.txt - Key facts from video")
    
    return result


async def intelligence_format_examples(result: VideoIntelligence):
    """Show intelligence extraction output formats."""
    
    print("\n\n🧠 Intelligence Extraction Formats")
    print("=" * 50)
    
    # 1. Entities format
    print("\n1️⃣ Entities JSON Format:")
    print("-" * 40)
    entities_example = {
        "video_url": result.metadata.url,
        "entities": [
            {"name": "John Smith", "type": "PERSON", "confidence": 0.95},
            {"name": "Apple Inc.", "type": "ORGANIZATION", "confidence": 0.98},
            {"name": "San Francisco", "type": "LOCATION", "confidence": 0.92}
        ],
        "topics": ["technology", "business", "innovation"]
    }
    print(json.dumps(entities_example, indent=2))
    
    # 2. Relationships format
    print("\n2️⃣ Relationships JSON Format:")
    print("-" * 40)
    relationships_example = {
        "relationships": [
            {
                "subject": "John Smith",
                "predicate": "CEO_of",
                "object": "Apple Inc.",
                "confidence": 0.89
            },
            {
                "subject": "Apple Inc.",
                "predicate": "headquartered_in",
                "object": "San Francisco",
                "confidence": 0.95
            }
        ]
    }
    print(json.dumps(relationships_example, indent=2))
    
    # 3. Knowledge Graph GEXF
    print("\n3️⃣ GEXF Format (for Gephi):")
    print("-" * 40)
    print("XML-based graph format that includes:")
    print("  • Node colors by entity type")
    print("  • Node sizes by confidence")
    print("  • Edge weights from relationships")
    print("  • Ready for Gephi import")
    
    # 4. Facts format
    print("\n4️⃣ Facts Text Format:")
    print("-" * 40)
    print("# Key Facts Extracted from Video")
    print("")
    print("1. John Smith is the CEO of Apple Inc. (confidence: 0.89)")
    print("2. Apple Inc. is headquartered in San Francisco (confidence: 0.95)")
    print("3. The company announced a new product launch (confidence: 0.87)")
    print("...")


async def save_intelligence_outputs(result: VideoIntelligence, output_dir: str = "intelligence_output"):
    """Save intelligence extraction outputs."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create structured output directory
    video_dir = output_path / f"{timestamp}_analysis"
    video_dir.mkdir(exist_ok=True)
    
    # Save transcript
    txt_path = video_dir / "transcript.txt"
    with open(txt_path, 'w') as f:
        f.write(result.transcript.full_text)
    
    # Save full JSON
    json_path = video_dir / "transcript.json"
    with open(json_path, 'w') as f:
        json.dump(result.dict(), f, indent=2, default=str)
    
    # Save manifest
    manifest = {
        "version": "2.4",
        "created_at": datetime.now().isoformat(),
        "video": {
            "title": result.metadata.title,
            "url": result.metadata.url
        },
        "files": {
            "transcript.txt": {"format": "plain_text"},
            "transcript.json": {"format": "json"}
        }
    }
    
    manifest_path = video_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n💾 Intelligence outputs saved to {video_dir}/")
    print(f"  • Transcript: transcript.txt")
    print(f"  • Full data: transcript.json")
    print(f"  • Manifest: manifest.json")


async def main():
    """Demonstrate all output format options."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print("📄 ClipScribe Output Formats Demo")
    print("=" * 50)
    
    # Show all standard formats
    result = await demonstrate_output_formats()
    
    # Show intelligence extraction format examples
    await intelligence_format_examples(result)
    
    # Save outputs
    await save_intelligence_outputs(result)
    
    print("\n\n🎯 Format Selection Guide:")
    print("  • TXT: General purpose, human-readable transcript")
    print("  • JSON: Full structured data with entities and relationships")
    print("  • GEXF: Knowledge graph for Gephi visualization")
    print("  • Intelligence files: Entities, relationships, facts for analysis")


if __name__ == "__main__":
    asyncio.run(main())  #  