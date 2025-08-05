#!/usr/bin/env python3
"""Cost Optimization Example - Strategies to minimize transcription costs."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from clipscribe.retrievers import UniversalVideoClient, GeminiTranscriber


class CostOptimizer:
    """Helper class for cost optimization strategies."""
    
    def __init__(self):
        self.client = UniversalVideoClient()
        self.cost_per_minute = 0.002  # $0.002 per minute
    
    async def preview_cost(self, video_url: str) -> dict:
        """Preview cost before processing."""
        try:
            # Get video info without downloading
            info = await self.client.extract_video_info(video_url)
            duration_minutes = info.get('duration', 0) / 60
            estimated_cost = duration_minutes * self.cost_per_minute
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration_seconds': info.get('duration', 0),
                'duration_minutes': duration_minutes,
                'estimated_cost': estimated_cost,
                'url': video_url
            }
        except Exception as e:
            return {'error': str(e), 'url': video_url}
    
    async def process_with_budget(self, urls: list[str], max_budget: float):
        """Process videos within a budget constraint."""
        print(f"\n💰 Budget-aware processing (max: ${max_budget:.2f})")
        
        # Preview costs for all videos
        previews = []
        for url in urls:
            preview = await self.preview_cost(url)
            if 'error' not in preview:
                previews.append(preview)
        
        # Sort by cost (cheapest first)
        previews.sort(key=lambda x: x['estimated_cost'])
        
        # Select videos within budget
        selected = []
        total_cost = 0
        
        for preview in previews:
            if total_cost + preview['estimated_cost'] <= max_budget:
                selected.append(preview)
                total_cost += preview['estimated_cost']
        
        print(f"\n📋 Selected {len(selected)} videos within budget:")
        for video in selected:
            print(f"  • {video['title'][:50]}...")
            print(f"    Duration: {video['duration_minutes']:.1f} min")
            print(f"    Cost: ${video['estimated_cost']:.4f}")
        
        print(f"\n💵 Total estimated cost: ${total_cost:.4f}")
        print(f"💰 Remaining budget: ${max_budget - total_cost:.4f}")
        
        return selected
    
    async def chunk_long_video(self, video_url: str, max_chunk_minutes: int = 10):
        """Process long videos in chunks to manage costs."""
        print(f"\n🔪 Chunked processing (max {max_chunk_minutes} min/chunk)")
        
        # Get video info
        info = await self.client.extract_video_info(video_url)
        total_minutes = info.get('duration', 0) / 60
        
        if total_minutes <= max_chunk_minutes:
            print(f"  ℹ️  Video is short enough ({total_minutes:.1f} min)")
            return
        
        # Calculate chunks
        num_chunks = int(total_minutes / max_chunk_minutes) + 1
        chunk_cost = max_chunk_minutes * self.cost_per_minute
        
        print(f"\n📊 Chunking strategy:")
        print(f"  • Total duration: {total_minutes:.1f} minutes")
        print(f"  • Number of chunks: {num_chunks}")
        print(f"  • Cost per chunk: ${chunk_cost:.4f}")
        print(f"  • Total cost: ${num_chunks * chunk_cost:.4f}")
        
        print(f"\n💡 Benefits:")
        print(f"  • Process chunks separately")
        print(f"  • Stop if not relevant")
        print(f"  • Better error recovery")
        print(f"  • Spread costs over time")


async def compare_processing_costs():
    """Compare costs for different video lengths and qualities."""
    print("\n📊 Cost Comparison Table")
    print("=" * 60)
    
    scenarios = [
        ("Short clip", 1),      # 1 minute
        ("Music video", 4),     # 4 minutes
        ("Tutorial", 15),       # 15 minutes
        ("Lecture", 60),        # 1 hour
        ("Documentary", 120),   # 2 hours
        ("Long stream", 240),   # 4 hours
    ]
    
    print(f"{'Video Type':<15} | {'Duration':<10} | {'Cost':<10} | {'Per Hour':<10}")
    print("-" * 60)
    
    for name, minutes in scenarios:
        cost = minutes * 0.002
        per_hour = (cost / minutes) * 60 if minutes > 0 else 0
        
        duration_str = f"{minutes} min" if minutes < 60 else f"{minutes/60:.1f} hrs"
        print(f"{name:<15} | {duration_str:<10} | ${cost:<9.4f} | ${per_hour:<9.2f}")
    
    print("\n💡 Cost-saving tips:")
    print("  • Preview video duration before processing")
    print("  • Process only relevant segments")
    print("  • Use batch processing for better rates")
    print("  • Consider audio quality settings")


async def smart_processing_demo():
    """Demonstrate smart processing strategies."""
    optimizer = CostOptimizer()
    
    print("\n🧠 Smart Processing Strategies")
    print("=" * 50)
    
    # Example videos
    test_urls = [
        "https://www.youtube.com/watch?v=short_video",    # 2 min
        "https://www.youtube.com/watch?v=medium_video",   # 10 min
        "https://www.youtube.com/watch?v=long_video",     # 60 min
        "https://www.youtube.com/watch?v=very_long",      # 120 min
    ]
    
    # 1. Preview costs
    print("\n1️⃣ Cost Preview:")
    total_cost = 0
    for url in test_urls:
        preview = await optimizer.preview_cost(url)
        if 'error' not in preview:
            print(f"  • {preview['duration_minutes']:.1f} min = ${preview['estimated_cost']:.4f}")
            total_cost += preview['estimated_cost']
    
    print(f"\n  Total: ${total_cost:.4f}")
    
    # 2. Budget processing
    await optimizer.process_with_budget(test_urls, max_budget=0.10)
    
    # 3. Chunk processing
    await optimizer.chunk_long_video(test_urls[-1], max_chunk_minutes=15)


async def main():
    """Run cost optimization demos."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print("💰 ClipScribe Cost Optimization Guide")
    print("=" * 50)
    print("\n✨ Gemini 2.5 Flash: $0.002/minute")
    print("   (92% cheaper than traditional transcription!)")
    
    # Run demos
    await compare_processing_costs()
    await smart_processing_demo()
    
    print("\n🎯 Key Takeaways:")
    print("  • Always preview costs before processing")
    print("  • Use chunking for long videos")
    print("  • Batch process for efficiency")
    print("  • Set budget limits for large projects")
    print("  • Consider partial processing for previews")


if __name__ == "__main__":
    asyncio.run(main())  #  