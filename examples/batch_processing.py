#!/usr/bin/env python3
"""Batch Processing Example - Process multiple videos efficiently."""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from clipscribe.retrievers import UniversalVideoClient
from clipscribe.models import VideoIntelligence


async def process_video_batch(urls: list[str], output_dir: str = "batch_output"):
    """Process multiple videos in parallel."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create client
    client = UniversalVideoClient()
    
    # Create tasks for parallel processing
    tasks = []
    for i, url in enumerate(urls):
        task = asyncio.create_task(
            process_single_video(client, url, output_path / f"video_{i+1}")
        )
        tasks.append(task)
    
    # Process all videos in parallel
    print(f"⚡ Processing {len(urls)} videos in parallel...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Summary
    successful = [r for r in results if isinstance(r, VideoIntelligence)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    return successful, failed


async def process_single_video(client: UniversalVideoClient, url: str, output_dir: Path):
    """Process a single video with error handling."""
    try:
        output_dir.mkdir(exist_ok=True)
        
        print(f"  📹 Starting: {url}")
        result = await client.transcribe_video(
            url,
            output_dir=str(output_dir),
            save_outputs=True,
            output_formats=['txt', 'json']
        )
        print(f"  ✅ Completed: {result.metadata.title}")
        return result
        
    except Exception as e:
        print(f"  ❌ Failed: {url} - {str(e)}")
        return e


async def main():
    """Batch processing demonstration."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print("🚀 ClipScribe Batch Processing Example")
    print("=" * 50)
    
    # Example: Process multiple educational videos
    video_urls = [
        # Add your video URLs here
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://vimeo.com/123456789",  # Example
        "https://www.ted.com/talks/example",  # Example
    ]
    
    print(f"\n📋 Videos to process: {len(video_urls)}")
    
    # Start timer
    start_time = datetime.now()
    
    # Process videos
    successful, failed = await process_video_batch(video_urls)
    
    # Calculate time taken
    duration = (datetime.now() - start_time).total_seconds()
    
    # Display results
    print(f"\n📊 Batch Processing Complete!")
    print(f"  • Success: {len(successful)} videos")
    print(f"  • Failed: {len(failed)} videos")
    print(f"  • Time: {duration:.1f} seconds")
    print(f"  • Average: {duration/len(video_urls):.1f}s per video")
    
    # Cost summary
    if successful:
        total_cost = sum(v.processing_cost for v in successful)
        total_duration = sum(v.metadata.duration for v in successful)
        
        print(f"\n💰 Cost Summary:")
        print(f"  • Total cost: ${total_cost:.4f}")
        print(f"  • Total video duration: {total_duration}s")
        print(f"  • Average cost: ${total_cost/len(successful):.4f} per video")
        
        print(f"\n📁 Output saved to: batch_output/")
        print(f"  • Each video has its own subdirectory")
        print(f"  • Formats: TXT, JSON")
    
    # Show failed videos
    if failed:
        print(f"\n⚠️  Failed videos:")
        for i, err in enumerate(failed):
            print(f"  {i+1}. {video_urls[i]} - {str(err)}")


# Additional helper functions for different batch scenarios

async def process_playlist(playlist_url: str):
    """Process all videos from a YouTube playlist."""
    print(f"\n📺 Processing playlist: {playlist_url}")
    # Note: Implement playlist extraction using yt-dlp
    pass


async def process_channel_recent(channel_url: str, max_videos: int = 10):
    """Process recent videos from a channel."""
    print(f"\n📡 Processing {max_videos} recent videos from channel")
    # Note: Implement channel video extraction
    pass


async def monitor_and_process(urls: list[str], interval_hours: int = 24):
    """Monitor URLs and process new videos periodically."""
    print(f"\n👀 Monitoring {len(urls)} sources every {interval_hours} hours")
    # Note: Implement monitoring logic
    pass


if __name__ == "__main__":
    asyncio.run(main())  # :-) 