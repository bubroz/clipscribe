#!/usr/bin/env python3
"""Quick download of remaining videos needed using UniversalVideoClient."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.retrievers.universal_video_client import UniversalVideoClient
import logging

logging.basicConfig(level=logging.INFO)

# Story 2 (Defense Tech) - need 9 more
STORY2_URLS = [
    "https://www.youtube.com/watch?v=WEFsBV2k_q8",  # China defense tech (78K views, Nov 5)
    # Will search for 8 more using ytsearch
]

# Story 3 (Supply Chain) - need 4 more  
STORY3_URLS = [
    # Will search for 4 using ytsearch
]

async def download_from_search(client, search_query, output_dir, count=5):
    """Download videos from YouTube search."""
    results = []
    
    try:
        # Use yt-dlp search
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch{count}:{search_query}", download=False)
            
            for entry in search_results.get('entries', [])[:count]:
                video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                try:
                    audio_path, metadata = await client.download_audio(video_url, output_dir=output_dir)
                    results.append(audio_path)
                    print(f"  ✅ {metadata.title}")
                except Exception as e:
                    print(f"  ❌ Failed: {e}")
                
                await asyncio.sleep(2)
    
    except Exception as e:
        print(f"Search failed: {e}")
    
    return results

async def main():
    client = UniversalVideoClient()
    
    print("Downloading remaining videos...")
    print("Story 2 (Defense Tech): Need 9 more")
    print("Story 3 (Supply Chain): Need 4 more")
    print("")
    
    # Story 2: Defense Tech
    print("=== STORY 2: DEFENSE TECHNOLOGY ===")
    story2_dir = "test_videos/story2_defense_tech"
    Path(story2_dir).mkdir(parents=True, exist_ok=True)
    
    # Download known URL
    if STORY2_URLS:
        for url in STORY2_URLS:
            try:
                audio, meta = await client.download_audio(url, output_dir=story2_dir)
                print(f"✅ {meta.title}")
            except Exception as e:
                print(f"❌ {e}")
    
    # Search for more
    await download_from_search(client, "defense technology AI weapons Palmer Luckey", story2_dir, 5)
    await download_from_search(client, "autonomous weapons drones military", story2_dir, 3)
    
    # Story 3: Supply Chain
    print("\n=== STORY 3: SUPPLY CHAIN ===")
    story3_dir = "test_videos/story3_supply_chain"
    
    await download_from_search(client, "CHIPS Act semiconductor Intel TSMC", story3_dir, 2)
    await download_from_search(client, "supply chain China trade policy", story3_dir, 2)
    
    print("\n✅ DONE!")
    
    # Count final files
    for story in ['story1_ai_companies', 'story2_defense_tech', 'story3_supply_chain', 'story4_cartel_ops']:
        path = Path(f"test_videos/{story}")
        if path.exists():
            count = len(list(path.glob("*.mp3"))) + len(list(path.glob("*.mp4")))
            print(f"{story}: {count} files")

if __name__ == "__main__":
    asyncio.run(main())

