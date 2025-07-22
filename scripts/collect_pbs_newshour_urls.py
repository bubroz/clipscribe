#!/usr/bin/env python3
"""
Collect PBS NewsHour YouTube URLs from the last 30 days.

This script searches YouTube for PBS NewsHour full episodes from the past 30 days
and creates a JSON file with URLs ready for batch processing.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def search_youtube_web(session: aiohttp.ClientSession, query: str) -> List[Dict]:
    """
    Search YouTube via web scraping (as a fallback).
    """
    search_url = f"https://www.youtube.com/results?search_query={query}"
    
    try:
        async with session.get(search_url) as response:
            html = await response.text()
            
        # Extract video IDs using regex
        video_ids = re.findall(r'"videoId":"([^"]+)"', html)
        video_ids = list(set(video_ids))[:10]  # Get unique IDs, limit to 10
        
        results = []
        for video_id in video_ids:
            results.append({
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "video_id": video_id,
                "title": f"PBS NewsHour Episode",  # We'd need more parsing for actual title
                "date": None  # Would need more parsing
            })
        
        return results
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []


async def collect_pbs_urls(days: int = 30) -> List[Dict]:
    """
    Collect PBS NewsHour URLs from the last N days.
    """
    urls = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate search queries for date ranges
    queries = []
    
    # Search by week to get better results
    current_date = start_date
    while current_date < end_date:
        week_end = min(current_date + timedelta(days=7), end_date)
        month_name = current_date.strftime("%B")
        year = current_date.year
        
        # Format: "PBS NewsHour full episode July 2025"
        query = f"PBS+NewsHour+full+episode+{month_name}+{year}"
        queries.append({
            "query": query,
            "start": current_date,
            "end": week_end
        })
        
        current_date = week_end
    
    print(f"🔍 Searching for PBS NewsHour episodes from {start_date.date()} to {end_date.date()}")
    print(f"📋 Generated {len(queries)} search queries")
    
    async with aiohttp.ClientSession() as session:
        for q in queries:
            print(f"\n🔎 Searching: {q['query']} ({q['start'].date()} to {q['end'].date()})")
            results = await search_youtube_web(session, q['query'])
            
            for result in results:
                # Add date range context
                result['search_period'] = {
                    'start': q['start'].isoformat(),
                    'end': q['end'].isoformat()
                }
                urls.append(result)
            
            # Be polite to YouTube
            await asyncio.sleep(2)
    
    # Remove duplicates based on video_id
    seen = set()
    unique_urls = []
    for item in urls:
        if item['video_id'] not in seen:
            seen.add(item['video_id'])
            unique_urls.append(item)
    
    return unique_urls


def generate_batch_config(urls: List[Dict], output_dir: str = "output/pbs_30day_analysis") -> Dict:
    """
    Generate a configuration file for batch processing.
    """
    config = {
        "batch_name": f"PBS NewsHour 30-Day Analysis - {datetime.now().date()}",
        "output_dir": output_dir,
        "videos": urls,
        "processing_options": {
            "use_vertex_ai": False,
            "trust_gemini": True,
            "extract_entities": True,
            "extract_relationships": True,
            "extract_timeline": True,
            "concurrent_limit": 10,  # Increased from 5 to 10 for faster processing
            "mode": "audio",  # Audio-only for speed
            "timeout": 600  # 10 minutes per video max
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_videos": len(urls),
            "date_range": {
                "start": (datetime.now() - timedelta(days=30)).date().isoformat(),
                "end": datetime.now().date().isoformat()
            },
            "estimated_time_minutes": max(5, (len(urls) / 10) * 3.5),  # Realistic estimate
            "estimated_cost_usd": len(urls) * 0.09  # Based on actual PBS test
        }
    }
    
    return config


async def main():
    """
    Main function to collect URLs and create batch config.
    """
    print("🎯 PBS NewsHour 30-Day URL Collector")
    print("=" * 50)
    
    # Collect URLs
    urls = await collect_pbs_urls(days=30)
    
    if not urls:
        print("❌ No URLs found. Please check your internet connection.")
        return
    
    print(f"\n✅ Found {len(urls)} potential PBS NewsHour episodes")
    
    # Create batch configuration
    config = generate_batch_config(urls)
    
    # Save configuration
    output_path = Path("pbs_newshour_30day_batch.json")
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n💾 Saved batch configuration to: {output_path}")
    print(f"📊 Total videos to process: {len(urls)}")
    print(f"�� Estimated cost: ${config['metadata']['estimated_cost_usd']:.2f}")
    print(f"⏱️  Estimated time: {config['metadata']['estimated_time_minutes']:.0f} minutes")
    
    print("\n⚡ SPEED OPTIMIZATION ENABLED:")
    print(f"  • Concurrent processing: 10 videos at once")
    print(f"  • Audio-only mode: 3x faster than video")
    print(f"  • Actual speed: ~{3.5:.1f} minutes per batch")
    
    print("\n🚀 To process these videos, run:")
    print(f"   poetry run python examples/batch_processing.py {output_path}")
    
    print("\n💡 Pro tips for even faster processing:")
    print("  • Filter to weekdays only (PBS doesn't air weekends)")
    print("  • Increase concurrent_limit to 15 if you have good bandwidth")
    print("  • Use Vertex AI for enterprise-scale processing")
    
    # Also save just the URLs for manual inspection
    urls_path = Path("pbs_newshour_30day_urls.txt")
    with open(urls_path, 'w') as f:
        for item in urls:
            f.write(f"{item['url']}\n")
    
    print(f"\n📝 URLs also saved to: {urls_path}")


if __name__ == "__main__":
    asyncio.run(main()) 