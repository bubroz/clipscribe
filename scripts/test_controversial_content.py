#!/usr/bin/env python3
"""
Test controversial content with Voxtral → Grok-4 pipeline.
This validates uncensored extraction on content that would be blocked by other models.
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables
os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"
os.environ["USE_VOXTRAL"] = "true"

from src.clipscribe.utils.logging import setup_logging
from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from src.clipscribe.processors.hybrid_processor import HybridProcessor
from src.clipscribe.models import VideoIntelligence
import logging

setup_logging(level="INFO")
logger = logging.getLogger(__name__)


class ControversialContentTester:
    """Test controversial content extraction."""
    
    def __init__(self):
        self.video_client = EnhancedUniversalVideoClient()
        self.processor = HybridProcessor(
            voxtral_model="voxtral-mini-2507",
            grok_model="grok-4-0709"
        )
        self.results = {}
    
    async def process_video(self, url: str, test_name: str) -> Dict[str, Any]:
        """Process a single controversial video."""
        
        print(f"\n{'='*80}")
        print(f"PROCESSING: {test_name}")
        print(f"URL: {url}")
        print("="*80)
        
        start_time = time.time()
        
        try:
            # Step 1: Download audio
            print("\n📥 Downloading audio...")
            audio_path, metadata = await self.video_client.download_audio(url)
            
            print(f"   ✅ Downloaded: {Path(audio_path).name}")
            print(f"   • Title: {metadata.title}")
            print(f"   • Duration: {metadata.duration}s ({metadata.duration/60:.1f} min)")
            print(f"   • Channel: {metadata.channel}")
            
            # Step 2: Process with Voxtral → Grok-4
            print("\n🔄 Processing with Voxtral → Grok-4 pipeline...")
            
            # Convert metadata to dict for processor
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
            
            # Process video
            result = await self.processor.process_video(
                audio_path,
                metadata_dict,
                force_reprocess=True
            )
            
            processing_time = time.time() - start_time
            
            # Extract metrics
            entity_count = len(result.entities)
            relationship_count = len(result.relationships)
            topic_count = len(result.topics)
            
            print(f"\n✅ PROCESSING COMPLETE!")
            print(f"   • Entities: {entity_count}")
            print(f"   • Relationships: {relationship_count}")
            print(f"   • Topics: {topic_count}")
            print(f"   • Processing time: {processing_time:.1f}s")
            print(f"   • Cost: ${result.processing_cost:.4f}")
            
            # Check for controversial entities
            controversial_terms = [
                "immigration", "border", "CCP", "China", "infiltration",
                "trans", "gender", "medical", "Kaiser",
                "Robinson", "Islam", "Muslim", "extremism",
                "Fuentes", "spiritual", "battle", "Ireland", "Israel",
                "race", "black", "white", "suppression", "mate"
            ]
            
            # Check entities for controversial content
            entity_text = " ".join([e.name.lower() for e in result.entities])
            found_controversial = [term for term in controversial_terms if term.lower() in entity_text]
            
            print(f"\n🔍 CONTROVERSIAL CONTENT DETECTION:")
            print(f"   • Found {len(found_controversial)} controversial terms")
            if found_controversial:
                print(f"   • Terms: {', '.join(found_controversial[:10])}")
            
            # Save outputs
            output_dir = self._create_output_dir(url, metadata.video_id)
            await self._save_outputs(result, output_dir, metadata_dict, processing_time)
            
            print(f"\n💾 OUTPUTS SAVED TO: {output_dir}")
            
            return {
                "success": True,
                "entities": entity_count,
                "relationships": relationship_count,
                "topics": topic_count,
                "controversial_terms": len(found_controversial),
                "cost": result.processing_cost,
                "time": processing_time,
                "output_dir": str(output_dir)
            }
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            import traceback
            print(f"\n❌ ERROR: {e}")
            print(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "time": time.time() - start_time
            }
    
    def _create_output_dir(self, url: str, video_id: str) -> Path:
        """Create output directory for this test."""
        
        # Determine platform
        if "youtube.com" in url or "youtu.be" in url:
            platform = "youtube"
        elif "rumble.com" in url:
            platform = "rumble"
        else:
            platform = "unknown"
        
        # Create directory
        date_str = datetime.now().strftime("%Y%m%d")
        output_dir = Path(f"output/sensitive_content_tests/{date_str}_{platform}_{video_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    async def _save_outputs(
        self, 
        result: VideoIntelligence, 
        output_dir: Path,
        metadata: Dict[str, Any],
        processing_time: float
    ):
        """Save all output files for auditing."""
        
        # 1. Save transcript
        transcript_data = {
            "text": result.transcript.full_text,
            "segments": result.transcript.segments,
            "language": result.transcript.language
        }
        with open(output_dir / "transcript.json", "w") as f:
            json.dump(transcript_data, f, indent=2, default=str)
        
        # 2. Save entities
        entities_data = [
            {
                "name": e.name,
                "type": e.type,
                "extraction_sources": e.extraction_sources,
                "mention_count": e.mention_count,
                "properties": e.properties
            }
            for e in result.entities
        ]
        with open(output_dir / "entities.json", "w") as f:
            json.dump(entities_data, f, indent=2, default=str)
        
        # 3. Save relationships
        relationships_data = [
            {
                "subject": r.subject,
                "predicate": r.predicate,
                "object": r.object,
                "properties": r.properties
            }
            for r in result.relationships
        ]
        with open(output_dir / "relationships.json", "w") as f:
            json.dump(relationships_data, f, indent=2, default=str)
        
        # 4. Save summary
        summary = f"""# Video Intelligence Summary

## Metadata
- **Title**: {metadata['title']}
- **Channel**: {metadata['channel']}
- **Duration**: {metadata['duration']}s ({metadata['duration']/60:.1f} min)
- **URL**: {metadata['url']}
- **Processed**: {datetime.now().isoformat()}

## Extraction Results
- **Entities**: {len(result.entities)}
- **Relationships**: {len(result.relationships)}
- **Topics**: {len(result.topics)}

## Processing Metrics
- **Time**: {processing_time:.1f}s
- **Cost**: ${result.processing_cost:.4f}
- **Pipeline**: Voxtral → Grok-4

## Key Entities
{chr(10).join([f"- {e.name} ({e.type})" for e in result.entities[:20]])}

## Key Relationships
{chr(10).join([f"- {r.subject} → {r.predicate} → {r.object}" for r in result.relationships[:20]])}

## Topics
{chr(10).join([f"- {t.name}" for t in result.topics[:10]])}
"""
        with open(output_dir / "summary.md", "w") as f:
            f.write(summary)
        
        # 5. Save processing metrics
        metrics = {
            "processing_time": processing_time,
            "processing_cost": result.processing_cost,
            "entity_count": len(result.entities),
            "relationship_count": len(result.relationships),
            "topic_count": len(result.topics),
            "transcript_length": len(result.transcript.full_text),
            "pipeline": "voxtral_grok4",
            "timestamp": datetime.now().isoformat()
        }
        with open(output_dir / "processing_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"   ✅ Saved 5 output files")


async def main():
    """Run controversial content tests."""
    
    print("="*80)
    print("CONTROVERSIAL CONTENT TESTING")
    print("Testing Voxtral → Grok-4 Pipeline on Censored Topics")
    print("="*80)
    
    tester = ControversialContentTester()
    
    # Test videos (starting with most controversial)
    test_videos = [
        # Most controversial first
        ("https://www.youtube.com/watch?v=3p2NaXyZy4U", "Trans Healthcare Controversy"),
        ("https://www.youtube.com/watch?v=mNZDKI46UZo", "CCP Border Infiltration"),
        ("https://www.youtube.com/watch?v=Y77AEt-YWr8", "Mate Suppression Theory"),
    ]
    
    results = []
    
    for url, name in test_videos:
        result = await tester.process_video(url, name)
        results.append(result)
        
        if not result["success"]:
            print(f"\n⚠️ Failed to process {name}")
            continue
    
    # Final summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        total_cost = sum(r["cost"] for r in successful)
        total_time = sum(r["time"] for r in successful)
        total_entities = sum(r["entities"] for r in successful)
        total_controversial = sum(r["controversial_terms"] for r in successful)
        
        print(f"\n📊 AGGREGATE METRICS:")
        print(f"   • Total cost: ${total_cost:.4f}")
        print(f"   • Total time: {total_time:.1f}s")
        print(f"   • Total entities: {total_entities}")
        print(f"   • Controversial terms found: {total_controversial}")
        print(f"   • Avg cost/video: ${total_cost/len(successful):.4f}")
        
        print(f"\n📁 OUTPUT LOCATIONS:")
        for r in successful:
            print(f"   • {r['output_dir']}")
    
    print("\n" + "="*80)
    print("✨ TESTING COMPLETE!")
    print("Check output/sensitive_content_tests/ for all files")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
