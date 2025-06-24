#!/usr/bin/env python3
"""Video Intelligence Demo - Process videos from any platform."""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clipscribe.retrievers import VideoIntelligenceRetriever
from src.clipscribe.models import VideoIntelligence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_video_search(query: str = "OpenAI GPT-5 announcement"):
    """Demo searching and processing YouTube videos."""
    print(f"\n🔍 Searching for videos about: '{query}'")
    print("-" * 60)
    
    try:
        # Create retriever
        retriever = VideoIntelligenceRetriever()
        
        # Search and process videos
        results = await retriever.search(query, max_results=2)
        
        if not results:
            print("❌ No videos found!")
            return
        
        print(f"✅ Found and processed {len(results)} videos\n")
        
        # Display results
        for i, video in enumerate(results, 1):
            print(f"\n📹 Video {i}: {video.metadata.title}")
            print(f"🔗 URL: {video.metadata.url}")
            
            # Video details
            print(f"📺 Channel: {video.metadata.channel}")
            print(f"⏱️  Duration: {video.metadata.duration} seconds")
            
            # Summary
            print(f"\n📝 Summary:")
            print(video.summary)
            
            # Key points
            if video.key_points:
                print(f"\n🔑 Key Points:")
                for kp in video.key_points[:5]:  # Show first 5
                    timestamp = kp.timestamp
                    mins = timestamp // 60
                    secs = timestamp % 60
                    print(f"  • [{mins:02d}:{secs:02d}] {kp.text}")
            
            # Entities
            if video.entities:
                print(f"\n🏷️  Entities Found:")
                # Group by type
                by_type = {}
                for entity in video.entities:
                    if entity.type not in by_type:
                        by_type[entity.type] = []
                    by_type[entity.type].append(entity.name)
                
                for entity_type, names in by_type.items():
                    print(f"  • {entity_type}: {', '.join(set(names[:5]))}")
            
            print(f"\n💰 Processing Cost: ${video.processing_cost:.4f}")
            print("\n" + "=" * 60)
        
        # Show stats
        stats = retriever.get_stats()
        print(f"\n📊 Total Processing Stats:")
        print(f"  • Videos processed: {stats['videos_processed']}")
        print(f"  • Total cost: ${stats['total_cost']:.4f}")
        print(f"  • Average cost: ${stats['average_cost']:.4f}")
    
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


async def demo_specific_video(video_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"):
    """Demo processing a specific video URL."""
    print(f"\n🎬 Processing specific video: {video_url}")
    print("-" * 60)
    
    try:
        retriever = VideoIntelligenceRetriever()
        
        # Check if URL is supported
        if not retriever.video_client.is_supported_url(video_url):
            print(f"❌ URL not supported: {video_url}")
            return
            
        result = await retriever.process_url(video_url)
        
        if result:
            print(f"✅ Video processed successfully!")
            print(f"\n📹 Title: {result.metadata.title}")
            print(f"📝 Summary: {result.summary[:200]}...")
            print(f"💰 Processing Cost: ${result.processing_cost:.4f}")
        else:
            print("❌ Failed to process video")
        
    except Exception as e:
        logger.error(f"Failed to process video: {e}")


async def demo_multi_platform():
    """Demo processing videos from different platforms."""
    print("\n🌐 Multi-Platform Video Processing Demo")
    print("-" * 60)
    
    # Example URLs from different platforms
    test_urls = [
        ("YouTube", "https://www.youtube.com/watch?v=EqInoO9L3Ow"),
        ("Twitter/X", "https://twitter.com/OpenAI/status/1234567890"),
        ("TikTok", "https://www.tiktok.com/@tech/video/1234567890"),
        ("Vimeo", "https://vimeo.com/123456789"),
    ]
    
    retriever = VideoIntelligenceRetriever()
    
    for platform, url in test_urls:
        print(f"\n🎯 Testing {platform}...")
        
        # Check if supported
        if retriever.video_client.is_supported_url(url):
            print(f"✅ {platform} is supported!")
        else:
            print(f"❌ {platform} URL not recognized: {url}")
    
    print(f"\n📊 Total supported platforms: 1800+ via yt-dlp")


async def demo_cost_analysis():
    """Demo cost analysis for different video lengths."""
    print("\n💰 Video Processing Cost Analysis")
    print("-" * 60)
    
    from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
    
    transcriber = GeminiFlashTranscriber()
    
    video_lengths = [
        (60, "1 minute"),
        (300, "5 minutes"),
        (600, "10 minutes"),
        (1800, "30 minutes"),
        (3600, "1 hour"),
        (7200, "2 hours")
    ]
    
    print("\nEstimated costs for different video lengths:")
    print("Duration        | Audio Cost | Token Cost | Total Cost")
    print("----------------|------------|------------|------------")
    
    for seconds, label in video_lengths:
        cost = transcriber._calculate_cost(seconds)
        audio_cost = (seconds / 60) * transcriber.audio_cost_per_minute
        token_cost = cost - audio_cost
        
        print(f"{label:15} | ${audio_cost:10.4f} | ${token_cost:10.4f} | ${cost:10.4f}")
    
    print("\n📊 Cost Breakdown:")
    print(f"  • Audio: ${transcriber.audio_cost_per_minute:.3f}/minute")
    print(f"  • Tokens: ${transcriber.token_costs['output']:.2f}/M output tokens")


async def main():
    """Run all demos."""
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found in environment!")
        print("Please set it in your .env file")
        return
    
    print("🚀 ClipScribe Video Intelligence Demo")
    print("=" * 60)
    
    # Run demos
    demos = [
        ("1", "Search YouTube videos", lambda: demo_video_search("Gemini 2.5 Flash announcement")),
        ("2", "Process specific video", lambda: demo_specific_video("https://www.youtube.com/watch?v=EqInoO9L3Ow")),
        ("3", "Multi-platform test", demo_multi_platform),
        ("4", "Cost analysis", demo_cost_analysis),
        ("5", "Run all demos", None)
    ]
    
    print("\nSelect a demo:")
    for num, desc, _ in demos[:-1]:
        print(f"  {num}. {desc}")
    print(f"  {demos[-1][0]}. {demos[-1][1]}")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "5":
        # Run all demos
        for num, desc, func in demos[:-1]:
            await func()
            await asyncio.sleep(1)
    elif choice in ["1", "2", "3", "4"]:
        # Run selected demo
        await demos[int(choice) - 1][2]()
    else:
        print("❌ Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main()) 