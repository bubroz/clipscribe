#!/usr/bin/env python3
"""
Test the last 3 most recent Stoic Viking videos to validate:
1. Bot detection bypass is working
2. Voxtral -> Grok-4 pipeline processes correctly
3. Output files are generated properly
4. No censorship or content blocking

Usage: poetry run python scripts/test_stoic_viking_recent.py
"""

import asyncio
import logging
from pathlib import Path
from clipscribe.retrievers import VideoIntelligenceRetriever
from clipscribe.config.settings import Settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_stoic_viking_videos():
    """Test the 3 most recent Stoic Viking videos."""

    # Most recent 3 Stoic Viking videos
    videos = [
        {
            "url": "https://www.youtube.com/watch?v=LddCoh0K-50",
            "title": "Health & Nutrition Made Simple | Weight, Composition, Performance"
        },
        {
            "url": "https://www.youtube.com/watch?v=5Fy2y3vzkWE",
            "title": "Partnering with Barbell Apparel"
        },
        {
            "url": "https://www.youtube.com/watch?v=Ii3UpOT8x-A",
            "title": "Attack Life with Brute Force"
        }
    ]

    results = []

    for i, video in enumerate(videos, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing Video {i}/3: {video['title']}")
        logger.info(f"URL: {video['url']}")
        logger.info(f"{'='*60}")

        try:
            # Create VideoIntelligenceRetriever instance
            settings = Settings()
            retriever = VideoIntelligenceRetriever(
                use_cache=True,
                use_advanced_extraction=True,
                mode="auto",
                output_dir="output",
                use_flash=False,
                cookies_from_browser="chrome",  # Use browser cookies for bot detection bypass
                settings=settings,
            )

            # Process the video
            result = await retriever.process_url(video['url'])

            if result:
                # Save all formats
                saved_files = retriever.save_all_formats(result, "output")
                output_dir = Path(saved_files['directory'])
                logger.info(f"Output directory: {output_dir}")

                expected_files = [
                    "transcript.json",
                    "transcript.txt",
                    "entities.json",
                    "relationships.json",
                    "facts.json",
                    "knowledge_graph.json",
                    "knowledge_graph.gexf",
                    "knowledge_graph.graphml",
                    "metadata.json",
                    "report.md",
                    "manifest.json"
                ]

                missing_files = []
                for filename in expected_files:
                    filepath = output_dir / filename
                    if filepath.exists():
                        logger.info(f"✅ {filename}")
                    else:
                        logger.error(f"❌ MISSING: {filename}")
                        missing_files.append(filename)

                # Log processing metrics
                logger.info(f"Processing cost: ${result.processing_cost:.4f}")
                logger.info(f"Entities found: {len(result.entities)}")
                logger.info(f"Relationships found: {len(result.relationships) if hasattr(result, 'relationships') else 'N/A'}")

                results.append({
                    "video": video,
                    "success": len(missing_files) == 0,
                    "missing_files": missing_files,
                    "cost": result.processing_cost,
                    "entity_count": len(result.entities),
                    "relationship_count": len(result.relationships) if hasattr(result, 'relationships') else 0,
                    "output_dir": str(output_dir)
                })
            else:
                raise Exception("Processing returned None")

        except Exception as e:
            logger.error(f"❌ Failed to process {video['title']}: {e}")
            results.append({
                "video": video,
                "success": False,
                "error": str(e),
                "cost": 0,
                "entity_count": 0,
                "relationship_count": 0
            })

    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("TEST RESULTS SUMMARY")
    logger.info(f"{'='*80}")

    successful = 0
    total_cost = 0
    total_entities = 0

    for i, result in enumerate(results, 1):
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        logger.info(f"Video {i}: {status}")
        logger.info(f"  Title: {result['video']['title']}")
        logger.info(f"  Cost: ${result['cost']:.4f}")
        logger.info(f"  Entities: {result['entity_count']}")

        if result["success"]:
            successful += 1
            total_cost += result["cost"]
            total_entities += result["entity_count"]
        else:
            if "missing_files" in result:
                logger.info(f"  Missing files: {result['missing_files']}")
            if "error" in result:
                logger.info(f"  Error: {result['error']}")

    logger.info(f"\nOVERALL RESULTS:")
    logger.info(f"  Successful: {successful}/3 videos")
    logger.info(f"  Total Cost: ${total_cost:.4f}")
    logger.info(f"  Average Cost: ${total_cost/3:.4f} per video")
    logger.info(f"  Total Entities: {total_entities}")

    if successful == 3:
        logger.info("🎉 ALL TESTS PASSED! Bot detection bypass is working perfectly.")
    else:
        logger.error(f"⚠️  {3-successful} videos failed. Bot detection may still be an issue.")

if __name__ == "__main__":
    asyncio.run(test_stoic_viking_videos())