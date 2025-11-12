#!/usr/bin/env python3
"""
Download Story 1 videos using ClipScribe's UniversalVideoClient with Playwright fallback.

This uses our existing infrastructure that handles:
- SABR/bot detection bypass via Playwright
- Cookie extraction
- Automatic fallbacks
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.retrievers.universal_video_client import UniversalVideoClient
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Story 1 videos (30 total: Tesla, OpenAI, Palantir)
STORY1_VIDEOS = [
    # Tesla (10)
    "https://www.youtube.com/watch?v=9tl6mGbObXc",
    "https://www.youtube.com/watch?v=fG2WbHLXUkQ",
    "https://www.youtube.com/watch?v=gveK0yp-O5o",
    "https://www.youtube.com/watch?v=AGnQ2ZAXPgs",
    "https://www.youtube.com/watch?v=JJvXIFaqHqY",
    "https://www.youtube.com/watch?v=_jR5K4XgI7A",
    "https://www.youtube.com/watch?v=wxlV4A6kg64",
    "https://www.youtube.com/watch?v=MFgKzPgm8Lw",
    "https://www.youtube.com/watch?v=L6Etc0ngrTc",
    "https://www.youtube.com/watch?v=lULP_Mfwd-o",
    # OpenAI (10)
    "https://www.youtube.com/watch?v=6uYEPfiBMAE",
    "https://www.youtube.com/watch?v=nTDS5r5fk_k",
    "https://www.youtube.com/watch?v=pO9L1HRqQLQ",
    "https://www.youtube.com/watch?v=aI3M9gUrDdg",
    "https://www.youtube.com/watch?v=b-4AtwuM8Vo",
    "https://www.youtube.com/watch?v=cuSDy0Rmdks",
    "https://www.youtube.com/watch?v=pzJfRzm3bL0",
    "https://www.youtube.com/watch?v=Zcw_epDd1ak",
    "https://www.youtube.com/watch?v=P7Oa9Hh2L0A",
    "https://www.youtube.com/watch?v=nL2ixZuBbr0",
    # Palantir (10)
    "https://www.youtube.com/watch?v=mqa1yEd891o",
    "https://www.youtube.com/watch?v=-_R1dPYPbxU",
    "https://www.youtube.com/watch?v=lcOLKSdsQ9c",
    "https://www.youtube.com/watch?v=o1ZFfK8hL5M",
    "https://www.youtube.com/watch?v=_eSvCpVueFU",
    "https://www.youtube.com/watch?v=HabEH_Yu4wI",
    "https://www.youtube.com/watch?v=5ogGK_G_5Zs",
    "https://www.youtube.com/watch?v=b67wVR3SSPo",
    "https://www.youtube.com/watch?v=wWxWTfjTR5A",
    "https://www.youtube.com/watch?v=dNbbowEggiA",
]


async def download_videos():
    """Download all Story 1 videos with Playwright fallback support."""
    output_dir = Path("test_videos/story1_ai_companies")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create progress file
    progress_file = Path("output/story1_download_progress.txt")
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    
    client = UniversalVideoClient()
    
    msg = f"\n{'='*80}\nDownloading {len(STORY1_VIDEOS)} videos for Story 1: AI Companies\nOutput: {output_dir}\nUsing UniversalVideoClient with Playwright fallback\n{'='*80}\n"
    print(msg)
    
    with open(progress_file, 'w') as f:
        f.write(msg)
    
    successful = 0
    failed = 0
    failed_urls = []
    
    for i, url in enumerate(STORY1_VIDEOS, 1):
        status_msg = f"\n[{i}/{len(STORY1_VIDEOS)}] Downloading: {url}"
        print(status_msg)
        
        with open(progress_file, 'a') as f:
            f.write(status_msg + "\n")
        
        try:
            # This will use Playwright fallback if regular download fails
            audio_path, metadata = await client.download_audio(url, output_dir=str(output_dir))
            
            success_msg = f"  ✅ SUCCESS: {metadata.title}\n     Duration: {metadata.duration}s\n     File: {audio_path}"
            print(success_msg)
            
            with open(progress_file, 'a') as f:
                f.write(success_msg + "\n")
            
            successful += 1
            
        except Exception as e:
            error_msg = f"  ❌ FAILED: {e}"
            print(error_msg)
            
            with open(progress_file, 'a') as f:
                f.write(error_msg + "\n")
            
            failed += 1
            failed_urls.append(url)
        
        # Rate limiting pause
        await asyncio.sleep(2)
    
    summary = f"\n{'='*80}\nDownload Complete!\n  Successful: {successful}/{len(STORY1_VIDEOS)}\n  Failed: {failed}/{len(STORY1_VIDEOS)}\n  Success Rate: {successful/len(STORY1_VIDEOS)*100:.1f}%\n{'='*80}\n"
    print(summary)
    
    with open(progress_file, 'a') as f:
        f.write(summary)
        if failed_urls:
            f.write("\nFailed URLs:\n")
            for url in failed_urls:
                f.write(f"  {url}\n")
    
    print(f"\n✅ Progress saved to: {progress_file}")
    print(f"\nTo monitor progress in real-time, run in another terminal:")
    print(f"  tail -f {progress_file}")


if __name__ == "__main__":
    asyncio.run(download_videos())

