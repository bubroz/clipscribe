#!/usr/bin/env python3
"""
Fast Batch Processing for PBS NewsHour - Optimized for speed without sacrificing quality.

This script demonstrates how to process 30 days of PBS NewsHour in ~10 minutes
using aggressive parallelization and optimizations.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv
import tenacity

from clipscribe.retrievers import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence
from clipscribe.extractors.multi_video_processor import MultiVideoProcessor

# Load environment variables
load_dotenv()

async def process_batch_fast(urls: list[str], concurrent_limit: int = 10):
    """
    Process videos with maximum concurrency for speed.
    
    Key optimizations:
    - Process 10+ videos concurrently
    - Audio-only mode (3x faster)
    - Connection pooling via GeminiPool
    - No video retention (delete after processing)
    """
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrent_limit)
    
    # Create shared client, configured for speed and advanced extraction
    retriever = VideoIntelligenceRetriever(
        use_advanced_extraction=True, 
        mode='audio', 
        use_cache=True, 
        output_formats=['json', 'csv', 'gexf']
    )
    
    @tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_exponential(min=2, max=60))
    async def process_one(url: str, index: int):
        async with semaphore:
            try:
                start = datetime.now()
                # Create a unique directory for each video's output
                video_id = url.split("v=")[-1]
                output_dir = f"output/pbs_30day/{index:03d}_{video_id}"
                
                print(f"⚡ [{index}/{len(urls)}] Starting: {url}")
                
                # Process with all optimizations
                result = await retriever.process_url(url)
                if result:
                    retriever.save_all_formats(result, output_dir=output_dir)
                
                duration = (datetime.now() - start).total_seconds()
                entities = len(result.entities) if result else 0
                
                print(f"✅ [{index}/{len(urls)}] Done in {duration:.1f}s: {entities} entities")
                return result
                
            except Exception as e:
                print(f"❌ [{index}/{len(urls)}] Failed processing {url}: {str(e)}")
                # Re-raise the exception to trigger tenacity's retry mechanism
                raise
    
    # Create all tasks
    tasks = []
    for i, url in enumerate(urls):
        tasks.append(asyncio.create_task(process_one(url, i + 1)))
    
    # Process all concurrently
    print(f"\n🚀 Processing {len(urls)} videos with {concurrent_limit}x concurrency...")
    start_time = datetime.now()
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    # Separate successful results from exceptions
    successful = [r for r in results if isinstance(r, VideoIntelligence)]
    failures = [r for r in results if isinstance(r, BaseException)]
    
    if successful:
        total_entities = sum(len(r.entities) for r in successful)
        total_relationships = sum(len(r.relationships) if hasattr(r, 'relationships') and r.relationships else 0 for r in successful)
        total_cost = sum(r.processing_cost for r in successful)
        
        print(f"\n📊 BATCH COMPLETE!")
        print(f"  • Time: {total_time/60:.1f} minutes ({total_time/len(urls):.1f}s per video)")
        print(f"  • Success: {len(successful)}/{len(results)} videos")
        print(f"  • Failures: {len(failures)}")
        print(f"  • Entities: {total_entities:,} total ({total_entities/len(successful):.0f} avg)")
        print(f"  • Relationships: {total_relationships:,} total")
        print(f"  • Cost: ${total_cost:.2f} (${total_cost/len(successful):.3f} per video)")
        print(f"  • Speed: {len(urls)/(total_time/3600):.1f} videos/hour")

        # Multi-video synthesis
        print("\n🔬 Synthesizing multi-video collection intelligence...")
        try:
            processor = MultiVideoProcessor()
            output_dir_collection = "output/pbs_30day_collection"
            collection = await processor.process_videos(successful)
            retriever.save_collection_outputs(collection, output_dir=output_dir_collection)
            print(f"✅ Collection synthesis complete! Check {output_dir_collection}")
        except Exception as e:
            print(f"⚠️ Warning: Multi-video synthesis failed: {e}")
            print("Individual video outputs are still available in output/pbs_30day/")
    else:
        print("\n❌ No videos processed successfully.")

    if failures:
        print("\nDetailed Failures:")
        for f in failures:
            print(f"- {f}")
    
    return successful, failures


async def main():
    """Demo fast batch processing."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print("⚡ PBS NewsHour Fast Batch Processor")
    print("=" * 50)
    
    # Load batch configuration
    config_path = Path("pbs_newshour_30day_batch.json")
    
    try:
        if not config_path.exists():
            print("❌ No batch configuration found!")
            print("Run this first: poetry run python scripts/collect_pbs_newshour_urls.py")
            return
    
        with open(config_path) as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading configuration file '{config_path}': {e}")
        return
    
    urls = [item['url'] for item in config['videos']]
    
    print(f"\n📺 Found {len(urls)} PBS NewsHour episodes")
    print(f"💰 Estimated cost: ${len(urls) * 0.035:.2f}") # Updated cost estimate for 2.5 Flash
    print(f"⏱️  Target time: <15 minutes")
    
    # Options for speed
    print("\n🎯 Speed options:")
    print("  1. Standard (10 concurrent) - ~11 minutes")
    print("  2. Fast (15 concurrent) - ~7 minutes")
    print("  3. Ludicrous (20 concurrent) - ~5 minutes")
    print("  4. Weekdays only (~22 videos) - even faster!")
    
    choice = input("\nSelect speed mode (1-4): ").strip()
    
    concurrent = 10  # Default to safe concurrency
    if choice == "1":
        concurrent = 10
    elif choice == "2":
        concurrent = 15
    elif choice == "3":
        concurrent = 20
        print("\n⚠️  Warning: This may hit rate limits!")
    elif choice == "4":
        # Filter weekdays only (PBS doesn't air weekends)
        print("\n📅 Filtering to weekdays only...")
        urls = urls[:22]  # Approximate weekdays in 30 days
        concurrent = 15
    else:
        print("Invalid choice, using default standard speed.")
        concurrent = 10
    
    print(f"\n🚀 Starting batch with {concurrent}x concurrency...")
    print(f"📊 Processing {len(urls)} videos")
    
    # Process the batch
    await process_batch_fast(urls, concurrent_limit=concurrent)
    
    print("\n✨ Done! Check output/pbs_30day/ for individual results and output/pbs_30day_collection/ for the unified analysis.")
    print("\n💡 Next steps:")
    print("  1. Explore the unified knowledge graph in Gephi.")
    print("  2. Analyze entity frequency and trends from the collection's CSV files.")


if __name__ == "__main__":
    asyncio.run(main()) 