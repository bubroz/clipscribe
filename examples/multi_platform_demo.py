#!/usr/bin/env python3
"""Demo script for multi-platform video intelligence using yt-dlp's 1800+ supported sites."""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clipscribe.retrievers import UniversalVideoClient, GeminiFlashTranscriber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_multi_platform_videos():
    """Demo processing videos from various platforms."""
    
    # Example URLs from different platforms
    test_urls = {
        "YouTube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "Twitter/X": "https://twitter.com/i/status/1234567890",  # Example format
        "TikTok": "https://www.tiktok.com/@username/video/1234567890",  # Example format
        "Vimeo": "https://vimeo.com/123456789",  # Example format
        "TED": "https://www.ted.com/talks/example_talk",  # Example format
        "BBC": "https://www.bbc.com/news/av/world-12345678",  # Example format
        "SoundCloud": "https://soundcloud.com/artist/track",  # Example format
        "Reddit": "https://www.reddit.com/r/videos/comments/abc123/",  # Example format
        "Twitch Clips": "https://clips.twitch.tv/ExampleClip",  # Example format
    }
    
    client = UniversalVideoClient()
    transcriber = GeminiFlashTranscriber()
    
    print("\n🌍 Multi-Platform Video Intelligence Demo")
    print("=" * 60)
    print(f"\nyt-dlp supports 1800+ sites! Here are some examples:\n")
    
    # Show some supported sites
    print("📺 Popular platforms supported:")
    platforms = [
        "YouTube, YouTube Shorts, YouTube Music",
        "Twitter/X, TikTok, Instagram, Facebook",
        "Vimeo, Dailymotion, Twitch, Reddit",
        "BBC, CNN, TED, NBC, ABC News",
        "SoundCloud, Bandcamp, Mixcloud",
        "And 1800+ more!"
    ]
    for platform in platforms:
        print(f"  • {platform}")
    
    print("\n" + "=" * 60)
    
    # Test URL support checking
    print("\n🔍 Testing URL Support Detection:")
    
    test_check_urls = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube"),
        ("https://vimeo.com/123456789", "Vimeo"),
        ("https://soundcloud.com/example/track", "SoundCloud"),
        ("https://example.com/not-supported", "Unknown Site"),
    ]
    
    for url, name in test_check_urls:
        try:
            is_supported = client.is_supported_url(url)
            status = "✅ Supported" if is_supported else "❌ Not Supported"
            print(f"  {name}: {status}")
        except Exception as e:
            print(f"  {name}: ⚠️ Check failed - {e}")
    
    print("\n" + "=" * 60)
    
    # Demo processing a non-YouTube video
    print("\n🎬 Demo: Processing a video from any supported platform")
    print("\nEnter a video URL from any supported site")
    print("(or press Enter to use a YouTube example):")
    
    user_url = input().strip()
    
    if not user_url:
        user_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        print(f"Using example: {user_url}")
    
    try:
        print(f"\n🔄 Processing: {user_url}")
        
        # Get video info
        metadata = await client.get_video_info(user_url)
        
        print(f"\n📋 Video Information:")
        print(f"  • Title: {metadata.title}")
        print(f"  • Channel/Uploader: {metadata.channel}")
        print(f"  • Duration: {metadata.duration} seconds")
        print(f"  • Views: {metadata.view_count:,}")
        print(f"  • Published: {metadata.published_at.strftime('%Y-%m-%d')}")
        
        # Ask if user wants to process it
        print("\n❓ Would you like to download and analyze this video? (y/n)")
        if input().lower().strip() == 'y':
            print("\n🔊 Downloading audio...")
            audio_file, _ = await client.download_audio(user_url)
            
            print("🧠 Analyzing with Gemini Flash...")
            analysis = await transcriber.transcribe_audio(audio_file, metadata.duration)
            
            print(f"\n✅ Analysis Complete!")
            print(f"  • Processing Time: {analysis['processing_time']:.1f}s")
            print(f"  • Processing Cost: ${analysis['processing_cost']:.4f}")
            
            # Show summary
            print(f"\n📝 Summary:")
            print(analysis['summary'][:500] + "..." if len(analysis['summary']) > 500 else analysis['summary'])
            
            # Clean up
            try:
                os.remove(audio_file)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Failed to process video: {e}")
        print(f"\n❌ Error: {e}")


async def demo_site_search():
    """Demo searching capabilities (currently YouTube only)."""
    print("\n🔍 Video Search Demo")
    print("=" * 60)
    
    client = UniversalVideoClient()
    
    print("\nNote: Currently, search is only implemented for YouTube.")
    print("Direct URL processing works for ALL 1800+ supported sites!")
    
    query = input("\nEnter search query (or press Enter for default): ").strip()
    if not query:
        query = "OpenAI announcements"
    
    print(f"\n🔄 Searching YouTube for: '{query}'")
    
    results = await client.search_videos(query, max_results=5)
    
    if results:
        print(f"\n✅ Found {len(results)} results:\n")
        for i, video in enumerate(results, 1):
            print(f"{i}. {video.title}")
            print(f"   Channel: {video.channel}")
            print(f"   Duration: {video.duration}s | Views: {video.view_count:,}")
            print(f"   URL: {video.url}")
            print()
    else:
        print("❌ No results found")


async def demo_batch_processing():
    """Demo batch processing from multiple platforms."""
    print("\n🚀 Batch Multi-Platform Processing Demo")
    print("=" * 60)
    
    client = UniversalVideoClient()
    
    # Example: News from different sources
    urls = [
        "https://www.youtube.com/watch?v=example1",  # YouTube news
        "https://www.bbc.com/news/av/example",       # BBC news video
        "https://twitter.com/i/status/example",      # Twitter/X video
        "https://www.ted.com/talks/example",         # TED talk
    ]
    
    print("\n📊 Example: Processing news from multiple sources")
    print("\nThis would process videos from:")
    print("  • YouTube News")
    print("  • BBC News")
    print("  • Twitter/X")
    print("  • TED Talks")
    print("  • And any other supported news site!")
    
    print("\n💡 Use Cases:")
    print("  1. Monitor news across all platforms")
    print("  2. Track trending topics on TikTok + YouTube + Twitter")
    print("  3. Analyze educational content from TED + YouTube + Coursera")
    print("  4. Research podcasts from SoundCloud + YouTube + Spotify")


async def main():
    """Run all demos."""
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found in environment!")
        print("Please set it in your .env file")
        return
    
    print("🚀 ClipScribe 2.0 - Multi-Platform Video Intelligence")
    print("Powered by yt-dlp (1800+ supported sites!)")
    print("=" * 60)
    
    demos = [
        ("1", "Multi-platform video processing", demo_multi_platform_videos),
        ("2", "Search videos (YouTube)", demo_site_search),
        ("3", "Batch processing concept", demo_batch_processing),
        ("4", "Run all demos", None)
    ]
    
    print("\nSelect a demo:")
    for num, desc, _ in demos[:-1]:
        print(f"  {num}. {desc}")
    print(f"  {demos[-1][0]}. {demos[-1][1]}")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "4":
        # Run all demos
        for num, desc, func in demos[:-1]:
            await func()
            await asyncio.sleep(1)
    elif choice in ["1", "2", "3"]:
        # Run selected demo
        await demos[int(choice) - 1][2]()
    else:
        print("❌ Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main()) 