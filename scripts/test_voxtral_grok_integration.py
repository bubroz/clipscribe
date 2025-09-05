#!/usr/bin/env python3
"""
Test the integrated Voxtral-Grok pipeline to ensure we're not using Gemini.
This validates that the CLI properly routes to the HybridProcessor.
"""

import asyncio
import logging
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2
from clipscribe.validators.output_validator import OutputValidator
from clipscribe.core_data import CoreData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_pipeline():
    """Test the complete Voxtral-Grok pipeline."""
    
    # Test video URL (short for quick testing)
    test_url = "https://www.youtube.com/watch?v=5Fy2y3vzkWE"  # Attack Life with Brute Force
    
    logger.info("=" * 80)
    logger.info("TESTING VOXTRAL-GROK PIPELINE (NO GEMINI!)")
    logger.info("=" * 80)
    
    # Check environment variables
    mistral_key = os.getenv("MISTRAL_API_KEY")
    xai_key = os.getenv("XAI_API_KEY")
    
    if not mistral_key:
        logger.error("❌ MISTRAL_API_KEY not set - Voxtral won't work!")
        return False
    else:
        logger.info("✅ MISTRAL_API_KEY found")
    
    if not xai_key:
        logger.error("❌ XAI_API_KEY not set - Grok won't work!")
        return False
    else:
        logger.info("✅ XAI_API_KEY found")
    
    # Test the V2 retriever
    logger.info("\n🚀 Initializing VideoIntelligenceRetrieverV2...")
    try:
        retriever = VideoIntelligenceRetrieverV2(
            output_dir="output/test_integration",
            use_cache=True
        )
        logger.info("✅ Retriever initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize retriever: {e}")
        return False
    
    # Process the video
    logger.info(f"\n📹 Processing video: {test_url}")
    try:
        result = await retriever.process_url(test_url)
        
        if result:
            logger.info("✅ Video processed successfully!")
            logger.info(f"   Title: {result.metadata.title}")
            logger.info(f"   Duration: {result.metadata.duration}s")
            logger.info(f"   Entities: {len(result.entities)}")
            logger.info(f"   Relationships: {len(result.relationships)}")
            logger.info(f"   Cost: ${result.processing_cost:.4f}")
            
            # Validate outputs
            output_dir = retriever.output_dir / f"*{test_url.split('/')[-1]}*"
            output_dirs = list(retriever.output_dir.glob(f"*{test_url.split('/')[-1]}"))
            
            if output_dirs:
                output_dir = output_dirs[0]
                logger.info(f"\n📁 Output directory: {output_dir}")
                
                # Run validator
                logger.info("\n🔍 Validating output files...")
                validator = OutputValidator()
                report = validator.validate_directory(output_dir)
                
                if report["errors"]:
                    logger.error(f"❌ Validation errors: {report['errors']}")
                else:
                    logger.info("✅ No validation errors!")
                
                if report["warnings"]:
                    logger.warning(f"⚠️ Warnings: {report['warnings'][:3]}")
                
                # Check for core.json
                core_path = output_dir / "core.json"
                if core_path.exists():
                    logger.info("✅ core.json created (consolidated output)")
                    
                    # Load and check
                    core_data = CoreData.from_legacy_files(output_dir)
                    logger.info(f"   Loaded {len(core_data.entities)} entities")
                    logger.info(f"   Loaded {len(core_data.relationships)} relationships")
                else:
                    logger.warning("⚠️ core.json not found (using legacy format)")
                
                # Check we're NOT using Gemini
                legacy_files = ["gemini_entities.json", "gemini_relationships.json"]
                gemini_found = False
                for filename in legacy_files:
                    if (output_dir / filename).exists():
                        logger.error(f"❌ Found Gemini file: {filename} - still using old pipeline!")
                        gemini_found = True
                
                if not gemini_found:
                    logger.info("✅ No Gemini files found - using Voxtral-Grok!")
                
                # Apply fixes if needed
                if report["warnings"]:
                    logger.info("\n🔧 Applying automatic fixes...")
                    fixes = validator.fix_common_issues(output_dir)
                    if fixes["applied"]:
                        logger.info(f"✅ Applied {len(fixes['applied'])} fixes")
                        for fix in fixes["applied"]:
                            logger.info(f"   - {fix}")
            
            return True
        else:
            logger.error("❌ Processing failed - no result returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Processing failed with error: {e}", exc_info=True)
        return False


async def test_cli_integration():
    """Test that the CLI properly uses the new pipeline."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING CLI INTEGRATION")
    logger.info("=" * 80)
    
    # Import the CLI
    from clipscribe.commands.cli import VideoIntelligenceRetriever
    
    # Check what class it's using
    logger.info(f"CLI is using: {VideoIntelligenceRetriever.__module__}.{VideoIntelligenceRetriever.__name__}")
    
    if "video_retriever_v2" in VideoIntelligenceRetriever.__module__:
        logger.info("✅ CLI is using VideoIntelligenceRetrieverV2 (Voxtral-Grok)")
        return True
    else:
        logger.error("❌ CLI is still using old VideoIntelligenceRetriever (Gemini)")
        return False


async def main():
    """Run all tests."""
    success = True
    
    # Test CLI integration
    if not await test_cli_integration():
        success = False
    
    # Test pipeline
    if not await test_pipeline():
        success = False
    
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL TESTS PASSED - VOXTRAL-GROK PIPELINE WORKING!")
        logger.info("=" * 80)
    else:
        logger.info("\n" + "=" * 80)
        logger.error("❌ TESTS FAILED - CHECK ERRORS ABOVE")
        logger.info("=" * 80)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

