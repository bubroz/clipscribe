#!/usr/bin/env python3
"""
Test full output generation for controversial content.
Validates ALL output formats are generated correctly.
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"
os.environ["USE_VOXTRAL"] = "true"

from src.clipscribe.utils.logging import setup_logging
from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from src.clipscribe.processors.hybrid_processor import HybridProcessor
from src.clipscribe.retrievers.output_formatter import OutputFormatter
from src.clipscribe.models import VideoIntelligence
import logging

setup_logging(level="INFO")
logger = logging.getLogger(__name__)


async def validate_output_files(output_dir: Path):
    """Validate all output files are present and correct."""
    
    print("\n" + "="*80)
    print("📁 OUTPUT FILE VALIDATION")
    print("="*80)
    
    expected_files = [
        "transcript.txt",
        "transcript.json", 
        "metadata.json",
        "entities.json",
        "entities.csv",
        "relationships.json",
        "relationships.csv",
        "knowledge_graph.json",
        "knowledge_graph.gexf",
        "knowledge_graph.graphml",
        "facts.json",
        "report.md",
        "manifest.json"
    ]
    
    issues = []
    
    for file_name in expected_files:
        file_path = output_dir / file_name
        if not file_path.exists():
            print(f"   ❌ MISSING: {file_name}")
            issues.append(f"Missing {file_name}")
        else:
            file_size = file_path.stat().st_size
            if file_size == 0:
                print(f"   ⚠️ EMPTY: {file_name}")
                issues.append(f"Empty {file_name}")
            else:
                print(f"   ✅ {file_name} ({file_size:,} bytes)")
                
                # Validate JSON files
                if file_name.endswith('.json'):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            
                        # Check specific content
                        if file_name == "entities.json":
                            entity_count = len(data.get("entities", []))
                            print(f"      → {entity_count} entities")
                            if entity_count == 0:
                                issues.append("No entities in entities.json")
                                
                        elif file_name == "relationships.json":
                            rel_count = len(data.get("relationships", []))
                            print(f"      → {rel_count} relationships")
                            
                        elif file_name == "transcript.json":
                            text_len = len(data.get("transcript", {}).get("full_text", ""))
                            print(f"      → {text_len:,} characters")
                            if text_len == 0:
                                issues.append("No transcript text")
                                
                    except json.JSONDecodeError as e:
                        print(f"      ❌ Invalid JSON: {e}")
                        issues.append(f"Invalid JSON in {file_name}")
                
                # Check CSV files
                elif file_name.endswith('.csv'):
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        print(f"      → {len(lines)-1} rows (excluding header)")
                        
                # Check Markdown
                elif file_name == "report.md":
                    with open(file_path, 'r') as f:
                        content = f.read()
                        print(f"      → {len(content):,} characters")
    
    print("\n📊 VALIDATION SUMMARY:")
    if issues:
        print(f"   ⚠️ Found {len(issues)} issues:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ All files present and valid!")
    
    return len(issues) == 0


async def process_and_validate(url: str):
    """Process a video and validate all outputs."""
    
    print(f"\n📹 Processing: {url}")
    print("="*80)
    
    start_time = time.time()
    
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
        print(f"   Channel: {metadata.channel}")
        
        # Prepare metadata
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
        
        # Process with pipeline
        print("\n🔄 Processing with Voxtral → Grok-4 pipeline...")
        result = await processor.process_video(
            audio_path,
            metadata_dict,
            force_reprocess=True
        )
        
        processing_time = time.time() - start_time
        
        if result and result.entities:
            print(f"\n✅ EXTRACTION COMPLETE!")
            print(f"   • Entities: {len(result.entities)}")
            print(f"   • Relationships: {len(result.relationships)}")
            print(f"   • Topics: {len(result.topics)}")
            print(f"   • Processing time: {processing_time:.1f}s ({processing_time/60:.1f} min)")
            print(f"   • Cost: ${result.processing_cost:.4f}")
            
            # Save ALL output formats
            print("\n💾 Saving all output formats...")
            output_paths = formatter.save_all_formats(
                result,
                output_dir="output/full_validation_test",
                include_chimera_format=True
            )
            
            output_dir = output_paths["directory"]
            print(f"   Output directory: {output_dir}")
            
            # Validate all files
            success = await validate_output_files(output_dir)
            
            # Sample content check
            print("\n📋 SAMPLE CONTENT CHECK:")
            
            # Check entities for controversial content
            controversial_terms = [
                "mate", "suppression", "WEF", "Klaus", "Schwab", 
                "Mouse Utopia", "Biden", "Trump", "Zelensky",
                "trans", "gender", "CCP", "border", "immigration"
            ]
            
            entity_names = [e.name.lower() for e in result.entities]
            entity_text = " ".join(entity_names)
            
            found_controversial = []
            for term in controversial_terms:
                if term.lower() in entity_text:
                    found_controversial.append(term)
            
            print(f"   Controversial terms found: {len(found_controversial)}")
            if found_controversial:
                print(f"   Examples: {', '.join(found_controversial[:10])}")
            
            # Check relationships
            if result.relationships:
                print(f"\n   Sample relationships:")
                for r in result.relationships[:5]:
                    print(f"   - {r.subject} → {r.predicate} → {r.object}")
            
            # Check topics
            if result.topics:
                print(f"\n   Topics identified:")
                for t in result.topics[:5]:
                    if t.name:  # Skip empty topics
                        print(f"   - {t.name}")
            
            return success
            
        else:
            print(f"\n⚠️ No entities extracted")
            return False
            
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())
        return False


async def main():
    """Run comprehensive output validation test."""
    
    print("="*80)
    print("COMPREHENSIVE OUTPUT VALIDATION TEST")
    print("="*80)
    
    # Use the Whatifalthist video we already processed
    url = "https://www.youtube.com/watch?v=Y77AEt-YWr8"
    
    success = await process_and_validate(url)
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL OUTPUT FILES VALIDATED SUCCESSFULLY!")
    else:
        print("⚠️ VALIDATION ISSUES FOUND - SEE ABOVE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
