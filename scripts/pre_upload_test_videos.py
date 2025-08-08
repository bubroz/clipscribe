#!/usr/bin/env python3
"""Pre-upload all test videos from MASTER_TEST_VIDEO_TABLE.md to GCS for faster testing."""

import os
import sys
import asyncio
import json
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from clipscribe.retrievers.vertex_ai_transcriber import VertexAITranscriber
from clipscribe.utils.logging import setup_logging

# Set up logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# Define all test videos from MASTER_TEST_VIDEO_TABLE.md
TEST_VIDEOS = [
    # PBS NewsHour
    "https://youtu.be/gxUrKV33yys",  # Full 7/15/24 episode
    "https://youtu.be/2jlsVEeZmVo",  # 7/16/24 episode
    "https://youtu.be/o6wtzHtfjyo",  # 7/17/24 segment
    "https://youtu.be/0ESDiJdCfxY",  # 7/18/24 segment
    
    # FRONTLINE PBS
    "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Pegasus Part 1
    "https://www.youtube.com/watch?v=xYMWTXIkANM",  # Pegasus Part 2
    
    # DW Documentary
    "https://www.youtube.com/watch?v=VHcgnRl2xPM",  # Russia media control
    "https://www.youtube.com/watch?v=PvKoniTXWsQ",  # Plastics crisis
    "https://www.youtube.com/watch?v=PcuxnqQLuAQ",  # Global news wars
    
    # Podcast/Speech/Talk
    "https://www.youtube.com/watch?v=JUthXIGUsq8",  # Lex Fridman - Yann LeCun
    "https://www.youtube.com/watch?v=y_8IKKcTntQ",  # Deep Questions - Cal Newport
    "https://www.youtube.com/watch?v=bdk6o7CUlXY",  # Stanford CS25
    
    # Financial/Business
    "https://www.youtube.com/watch?v=QnClqEBJQmU",  # Bloomberg tech news
    "https://www.youtube.com/watch?v=-1riCe0dOpM",  # CNBC earnings report
    "https://www.youtube.com/watch?v=7sWj6D2i4eU",  # Yahoo Finance
    
    # Specific Test Scenarios
    "https://www.youtube.com/watch?v=0jeZPnNPp9M",  # Science communication
    "https://www.youtube.com/watch?v=f0C_znvD7E8",  # Educational animation
    "https://www.youtube.com/watch?v=pR_bIwOS4Ec",  # Conference talk
    "https://www.youtube.com/watch?v=m5WR6nVISEc",  # Investigative short
    "https://www.youtube.com/watch?v=hj9rK35ucCc",  # Multiple narratives
]

async def main():
    """Pre-upload all test videos to GCS."""
    # Initialize clients
    video_client = EnhancedUniversalVideoClient()
    transcriber = VertexAITranscriber()
    
    # Create output directory for tracking
    output_dir = Path("output/pre_uploaded_videos")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track results
    results = {
        "successful_uploads": [],
        "failed_uploads": [],
        "skipped": []
    }
    
    for url in TEST_VIDEOS:
        try:
            logger.info(f"Processing {url}")
            
            # Check if already uploaded
            # Extract video ID properly from both youtu.be and youtube.com URLs
            if 'youtu.be/' in url:
                video_id = url.split('/')[-1].split('?')[0]
            elif 'youtube.com/watch' in url:
                # Extract from ?v= parameter
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                video_id = params.get('v', [None])[0]
                if not video_id:
                    logger.error(f"Could not extract video ID from {url}")
                    continue
            else:
                video_id = url.split('/')[-1].split('?')[0]  # Fallback
                
            tracking_file = output_dir / f"{video_id}_gcs_info.json"
            if tracking_file.exists():
                with open(tracking_file, 'r') as f:
                    info = json.load(f)
                logger.info(f"Already uploaded: {info['gcs_uri']}")
                results["skipped"].append({
                    "url": url,
                    "gcs_uri": info['gcs_uri']
                })
                continue
            
            # Download video
            logger.info(f"Downloading {url}...")
            cache_dir = Path("output/video_cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            video_path, metadata = await video_client.download_video(url, str(cache_dir))
            if not video_path:
                logger.error(f"Failed to download {url}")
                results["failed_uploads"].append({
                    "url": url,
                    "error": "Download failed"
                })
                continue
            
            # Upload to GCS
            logger.info(f"Uploading to GCS: {video_path}")
            try:
                gcs_uri = await transcriber.upload_to_gcs(Path(video_path))
                logger.info(f"Successfully uploaded: {gcs_uri}")
                
                # Save tracking info
                tracking_info = {
                    "url": url,
                    "gcs_uri": gcs_uri,
                    "local_path": str(video_path),
                    "uploaded_at": datetime.now().isoformat(),
                    "file_size_mb": Path(video_path).stat().st_size / (1024 * 1024)
                }
                
                with open(tracking_file, 'w') as f:
                    json.dump(tracking_info, f, indent=2)
                
                results["successful_uploads"].append(tracking_info)
                
            except Exception as e:
                logger.error(f"Failed to upload {url}: {e}")
                results["failed_uploads"].append({
                    "url": url,
                    "error": str(e)
                })
                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            results["failed_uploads"].append({
                "url": url,
                "error": str(e)
            })
    
    # Save results summary
    summary_file = output_dir / "upload_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("Pre-upload Summary:")
    logger.info(f" Successful uploads: {len(results['successful_uploads'])}")
    logger.info(f"⏭  Skipped (already uploaded): {len(results['skipped'])}")
    logger.info(f" Failed uploads: {len(results['failed_uploads'])}")
    
    if results['failed_uploads']:
        logger.info("\nFailed uploads:")
        for failed in results['failed_uploads']:
            logger.info(f"  - {failed['url']}: {failed['error']}")
    
    logger.info(f"\nResults saved to: {summary_file}")

if __name__ == "__main__":
    asyncio.run(main()) 