#!/usr/bin/env python3
"""
Simple Output Validation for ClipScribe

Just process one video and examine the actual output structure and quality.
No complex models, just raw data inspection.

Usage:
    poetry run python scripts/validate_output_simple.py
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import tempfile
from pprint import pprint

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def validate_single_video():
    """Process one video and validate the output."""
    
    # Test with a shorter video for speed
    test_url = "https://www.youtube.com/watch?v=V9VEvGSzzk0"  # 18 min privacy video
    
    logger.info("="*80)
    logger.info("🧪 CLIPSCRIBE OUTPUT VALIDATION TEST")
    logger.info("="*80)
    logger.info(f"Test URL: {test_url}")
    
    try:
        # Import modules
        from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
        from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
        
        # 1. Download
        logger.info("\n📥 STEP 1: Downloading video...")
        client = EnhancedUniversalVideoClient()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path, metadata = await client.download_audio(test_url, output_dir=tmpdir)
            
            duration = int(getattr(metadata, "duration", 0) or 0)
            title = getattr(metadata, "title", "Unknown")
            
            logger.info(f"✅ Downloaded: {title}")
            logger.info(f"   Duration: {duration}s ({duration/60:.1f} minutes)")
            logger.info(f"   File size: {Path(audio_path).stat().st_size / 1024 / 1024:.1f} MB")
            
            # 2. Transcribe with Flash
            logger.info("\n🎙️ STEP 2: Transcribing with Gemini Flash...")
            transcriber = GeminiFlashTranscriber(use_pro=False)
            
            result = await transcriber.transcribe_audio(audio_path, duration)
            
            # 3. Analyze output structure
            logger.info("\n📊 STEP 3: Analyzing Output Structure...")
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Result keys: {list(result.keys())}")
            
            # Save full output for inspection
            output_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / "raw_output.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"\n💾 Full output saved to: {output_file}")
            
            # 4. Validate content
            logger.info("\n✅ VALIDATION RESULTS:")
            
            # Transcript validation
            transcript = result.get("transcript", "")
            if transcript:
                logger.info(f"📝 Transcript:")
                logger.info(f"   Length: {len(transcript)} characters")
                logger.info(f"   Words: {len(transcript.split())} words")
                logger.info(f"   First 200 chars: {transcript[:200]}...")
                
                # Check quality
                has_punctuation = any(c in transcript for c in ['.', '!', '?'])
                has_capitalization = transcript != transcript.lower()
                logger.info(f"   Has punctuation: {'✅' if has_punctuation else '❌'}")
                logger.info(f"   Has capitalization: {'✅' if has_capitalization else '❌'}")
            else:
                logger.error("   ❌ No transcript found!")
            
            # Entity validation
            entities = result.get("entities", [])
            logger.info(f"\n🏷️ Entities:")
            logger.info(f"   Total count: {len(entities)}")
            
            if entities:
                # Sample first 5 entities
                logger.info("   Sample entities:")
                for i, entity in enumerate(entities[:5]):
                    name = entity.get("name", "Unknown")
                    entity_type = entity.get("type", "Unknown")
                    confidence = entity.get("confidence", 0)
                    logger.info(f"     {i+1}. {name} ({entity_type}) - Confidence: {confidence:.2f}")
                
                # Check structure
                sample = entities[0]
                logger.info(f"   Entity structure keys: {list(sample.keys())}")
                
                # Entity quality metrics
                unique_names = len(set(e.get("name", "").lower() for e in entities))
                avg_confidence = sum(e.get("confidence", 0) for e in entities) / len(entities)
                
                logger.info(f"   Unique entities: {unique_names}")
                logger.info(f"   Average confidence: {avg_confidence:.2f}")
                
                # Entity types distribution
                types = {}
                for e in entities:
                    t = e.get("type", "Unknown")
                    types[t] = types.get(t, 0) + 1
                logger.info(f"   Entity types: {types}")
            else:
                logger.error("   ❌ No entities found!")
            
            # Relationship validation
            relationships = result.get("relationships", [])
            logger.info(f"\n🔗 Relationships:")
            logger.info(f"   Total count: {len(relationships)}")
            
            if relationships:
                # Sample first 3 relationships
                logger.info("   Sample relationships:")
                for i, rel in enumerate(relationships[:3]):
                    source = rel.get("source") or rel.get("subject", "Unknown")
                    target = rel.get("target") or rel.get("object", "Unknown")  
                    rel_type = rel.get("type") or rel.get("relationship", "Unknown")
                    logger.info(f"     {i+1}. {source} --[{rel_type}]--> {target}")
                
                # Check structure
                sample = relationships[0]
                logger.info(f"   Relationship structure keys: {list(sample.keys())}")
            else:
                logger.warning("   ⚠️ No relationships found (might be normal for some content)")
            
            # Other extracted data
            key_points = result.get("key_points", [])
            dates = result.get("dates", [])
            
            logger.info(f"\n📌 Additional Extractions:")
            logger.info(f"   Key points: {len(key_points)}")
            if key_points and len(key_points) > 0:
                sample_point = str(key_points[0])
                logger.info(f"     Sample: {sample_point[:100]}..." if len(sample_point) > 100 else f"     Sample: {sample_point}")
            
            logger.info(f"   Dates found: {len(dates)}")
            if dates:
                logger.info(f"     Sample dates: {dates[:3]}")
            
            # Cost analysis
            estimated_cost = duration / 60 * 0.0035  # Flash cost
            logger.info(f"\n💰 Cost Analysis:")
            logger.info(f"   Estimated cost: ${estimated_cost:.4f}")
            logger.info(f"   Entities per dollar: {len(entities) / estimated_cost:.0f}")
            logger.info(f"   Relationships per dollar: {len(relationships) / estimated_cost:.0f}")
            
            # Overall quality score
            logger.info(f"\n📈 QUALITY SUMMARY:")
            quality_checks = {
                "Has transcript": bool(transcript),
                "Has entities": len(entities) > 0,
                "Has relationships": len(relationships) > 0,
                "Good entity density": len(entities) / (duration/60) > 2,
                "Good confidence": avg_confidence > 0.7 if entities else False,
                "Has punctuation": has_punctuation if transcript else False,
                "Has key points": len(key_points) > 0,
                "Has dates": len(dates) > 0
            }
            
            passed = sum(1 for v in quality_checks.values() if v)
            total = len(quality_checks)
            
            for check, result in quality_checks.items():
                logger.info(f"   {'✅' if result else '❌'} {check}")
            
            logger.info(f"\n   Overall: {passed}/{total} checks passed ({passed/total*100:.0f}%)")
            
            if passed >= 6:
                logger.info("\n🎉 OUTPUT QUALITY: GOOD - Ready for use!")
            elif passed >= 4:
                logger.info("\n⚠️ OUTPUT QUALITY: ACCEPTABLE - Some improvements needed")
            else:
                logger.error("\n❌ OUTPUT QUALITY: POOR - Significant issues")
            
            return passed >= 6  # Return success if quality is good
            
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("❌ GOOGLE_API_KEY not set")
        logger.error("Please run: source .env")
        sys.exit(1)
    
    success = await validate_single_video()
    
    logger.info("\n" + "="*80)
    if success:
        logger.info("✅ VALIDATION PASSED - Core functionality working!")
        logger.info("📋 Check test_results folder for detailed output")
    else:
        logger.error("❌ VALIDATION FAILED - Review issues above")
    logger.info("="*80)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
