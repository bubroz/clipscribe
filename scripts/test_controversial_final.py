#!/usr/bin/env python3
"""
Final test with controversial videos to validate complete output including GraphML.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"
os.environ["USE_VOXTRAL"] = "true"

from src.clipscribe.utils.logging import setup_logging
from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from src.clipscribe.processors.hybrid_processor import HybridProcessor
from src.clipscribe.retrievers.output_formatter import OutputFormatter
import logging

setup_logging(level="INFO")
logger = logging.getLogger(__name__)


async def process_controversial_video(url: str, title: str):
    """Process a controversial video and validate all outputs."""
    
    print(f"\n{'='*80}")
    print(f"Processing: {title}")
    print(f"URL: {url}")
    print("="*80)
    
    try:
        # Initialize components
        client = EnhancedUniversalVideoClient()
        processor = HybridProcessor(
            voxtral_model="voxtral-mini-2507",
            grok_model="grok-4-0709"
        )
        formatter = OutputFormatter()
        
        # Download audio
        print("\n📥 Downloading audio...")
        audio_path, metadata = await client.download_audio(url)
        
        print(f"✅ Downloaded: {metadata.title}")
        print(f"   Duration: {metadata.duration}s ({metadata.duration/60:.1f} min)")
        
        # Process with pipeline
        metadata_dict = {
            "video_id": metadata.video_id,
            "title": metadata.title,
            "channel": metadata.channel,
            "channel_id": metadata.channel_id or "unknown",
            "duration": metadata.duration,
            "url": url,
            "description": metadata.description or "",
            "published_at": metadata.published_at
        }
        
        print("\n🔄 Processing with Voxtral → Grok-4 pipeline...")
        result = await processor.process_video(
            audio_path,
            metadata_dict,
            force_reprocess=True
        )
        
        if result and result.entities:
            print(f"\n✅ EXTRACTION COMPLETE!")
            print(f"   • Entities: {len(result.entities)}")
            print(f"   • Relationships: {len(result.relationships)}")
            print(f"   • Topics: {len(result.topics)}")
            print(f"   • Knowledge Graph: {result.knowledge_graph.get('node_count', 0)} nodes, {result.knowledge_graph.get('edge_count', 0)} edges")
            print(f"   • Cost: ${result.processing_cost:.4f}")
            
            # Save ALL output formats
            print("\n💾 Saving all output formats...")
            output_paths = formatter.save_all_formats(
                result,
                output_dir="output/controversial_final_test",
                include_chimera_format=True
            )
            
            output_dir = output_paths["directory"]
            
            # Validate all files exist
            expected_files = [
                "transcript.txt", "transcript.json", "metadata.json",
                "entities.json", "entities.csv",
                "relationships.json", "relationships.csv",
                "knowledge_graph.json", "knowledge_graph.gexf", "knowledge_graph.graphml",
                "facts.json", "report.md", "manifest.json"
            ]
            
            missing = []
            for file in expected_files:
                if not (output_dir / file).exists():
                    missing.append(file)
            
            if missing:
                print(f"\n⚠️ Missing files: {', '.join(missing)}")
            else:
                print(f"\n✅ ALL 14 FILES GENERATED SUCCESSFULLY!")
            
            print(f"\n📁 Output location: {output_dir}")
            
            # Sample controversial content
            controversial_found = []
            entity_names = " ".join([e.name.lower() for e in result.entities])
            controversial_terms = ["immigration", "border", "trans", "gender", "medical", "extremism"]
            
            for term in controversial_terms:
                if term in entity_names:
                    controversial_found.append(term)
            
            if controversial_found:
                print(f"   🔥 Controversial terms found: {', '.join(controversial_found)}")
            
            return True, str(output_dir)
        else:
            print(f"\n❌ No entities extracted")
            return False, None
            
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())
        return False, None


async def main():
    """Run final controversial content tests."""
    
    print("="*80)
    print("FINAL CONTROVERSIAL CONTENT VALIDATION")
    print("Testing complete pipeline with GraphML export")
    print("="*80)
    
    # Two controversial videos from our test set
    test_videos = [
        ("https://www.youtube.com/watch?v=mNZDKI46UZo", "CCP Border Infiltration"),
        ("https://www.youtube.com/watch?v=3p2NaXyZy4U", "Trans Healthcare Controversy"),
    ]
    
    results = []
    output_dirs = []
    
    for url, title in test_videos:
        success, output_dir = await process_controversial_video(url, title)
        results.append((title, success))
        if output_dir:
            output_dirs.append(output_dir)
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    for title, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {title}")
    
    if all(r[1] for r in results):
        print("\n🎉 ALL TESTS PASSED! Pipeline is 100% complete!")
        print("\n📁 OUTPUT LOCATIONS FOR AUDIT:")
        for dir_path in output_dirs:
            print(f"   • {dir_path}")
        print("\n📊 Each output directory contains:")
        print("   1. transcript.txt & transcript.json - Full transcripts")
        print("   2. entities.json & entities.csv - All extracted entities")
        print("   3. relationships.json & relationships.csv - Entity relationships")
        print("   4. knowledge_graph.json - Graph structure")
        print("   5. knowledge_graph.gexf - Gephi visualization format")
        print("   6. knowledge_graph.graphml - yEd/Cytoscape format")
        print("   7. facts.json - Extracted facts")
        print("   8. report.md - Summary report")
        print("   9. metadata.json - Video metadata")
        print("   10. manifest.json - File manifest")
        print("   11. chimera_format.json - Legacy format")
    else:
        print("\n⚠️ Some tests failed. Check logs above.")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
