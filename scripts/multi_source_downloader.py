#!/usr/bin/env python3
"""
Multi-Source Video Downloader

Downloads content from various sources identified by Grok:
- Direct MP3/MP4 links (wget/httpx)
- RSS podcast feeds (feedparser)
- Vimeo (yt-dlp)
- Page scraping (BeautifulSoup for CNBC, WIRED, Bloomberg, think tanks)
- C-SPAN archives (custom or yt-dlp)
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
import feedparser
from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MultiSourceDownloader:
    """
    Downloads videos/audio from multiple source types.
    
    Handles:
    - Direct MP3/MP4 URLs
    - RSS podcast feeds
    - Vimeo videos
    - News site videos (CNBC, Bloomberg, Yahoo Finance)
    - Think tank presentations
    - C-SPAN archives
    """
    
    def __init__(self, output_base_dir: str = "test_videos"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = httpx.AsyncClient(
            timeout=300.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        
        self.stats = {
            'downloaded': 0,
            'failed': 0,
            'by_method': {}
        }
    
    async def download_video(self, video_info: Dict, story_dir: str) -> Optional[str]:
        """
        Download video based on download_method specified.
        
        Args:
            video_info: Video metadata from Grok JSON
            story_dir: Story subdirectory name
            
        Returns:
            Path to downloaded file or None if failed
        """
        method = video_info.get('download_method', 'unknown')
        url = video_info['url']
        title = video_info['title']
        
        output_dir = self.output_base_dir / story_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading [{method}]: {title[:60]}...")
        
        try:
            if method == 'direct_mp3':
                file_path = await self._download_direct(url, output_dir, '.mp3', title)
            elif method == 'direct_mp4':
                file_path = await self._download_direct(url, output_dir, '.mp4', title)
            elif method == 'rss_feed':
                file_path = await self._download_from_rss(url, output_dir, title)
            elif method == 'vimeo':
                file_path = await self._download_vimeo(url, output_dir, title)
            elif method == 'page_scrape':
                file_path = await self._scrape_and_download(url, output_dir, title)
            elif method == 'c-span_archive':
                file_path = await self._download_cspan(url, output_dir, title)
            elif method == 'archive':
                file_path = await self._download_archive(url, output_dir, title)
            else:
                logger.warning(f"Unknown method: {method}, trying direct download")
                file_path = await self._download_direct(url, output_dir, '.mp3', title)
            
            if file_path:
                self.stats['downloaded'] += 1
                self.stats['by_method'][method] = self.stats['by_method'].get(method, 0) + 1
                logger.info(f"  ✅ SUCCESS: {file_path}")
                return file_path
            else:
                self.stats['failed'] += 1
                logger.error(f"  ❌ FAILED: No file returned")
                return None
                
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"  ❌ FAILED: {e}")
            return None
    
    async def _download_direct(self, url: str, output_dir: Path, ext: str, title: str) -> Optional[str]:
        """Download direct MP3/MP4 link with httpx."""
        try:
            # Sanitize filename
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
            safe_title = safe_title[:100]  # Limit length
            
            filename = f"{safe_title}{ext}"
            filepath = output_dir / filename
            
            # Skip if already exists
            if filepath.exists():
                logger.info(f"  File already exists: {filename}")
                return str(filepath)
            
            # Download
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Save
            filepath.write_bytes(response.content)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Direct download failed: {e}")
            return None
    
    async def _download_from_rss(self, rss_url: str, output_dir: Path, title: str) -> Optional[str]:
        """Parse RSS feed and download latest episode."""
        try:
            # Fetch RSS feed
            response = await self.client.get(rss_url)
            response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.text)
            
            if not feed.entries:
                logger.error("No entries in RSS feed")
                return None
            
            # Get first entry (latest episode)
            entry = feed.entries[0]
            
            # Find enclosure (audio file)
            enclosure_url = None
            for enclosure in entry.get('enclosures', []):
                if 'audio' in enclosure.get('type', ''):
                    enclosure_url = enclosure.get('url') or enclosure.get('href')
                    break
            
            if not enclosure_url and entry.get('links'):
                for link in entry.links:
                    if link.get('type', '').startswith('audio'):
                        enclosure_url = link.get('href')
                        break
            
            if not enclosure_url:
                logger.error("No audio enclosure found in RSS feed")
                return None
            
            # Download the enclosure
            return await self._download_direct(enclosure_url, output_dir, '.mp3', title)
            
        except Exception as e:
            logger.error(f"RSS download failed: {e}")
            return None
    
    async def _download_vimeo(self, url: str, output_dir: Path, title: str) -> Optional[str]:
        """Download from Vimeo using yt-dlp."""
        try:
            import yt_dlp
            
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)[:100]
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(output_dir / f"{safe_title}.%(ext)s"),
                'quiet': False,
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find downloaded file
            for ext in ['.mp3', '.m4a', '.webm']:
                filepath = output_dir / f"{safe_title}{ext}"
                if filepath.exists():
                    return str(filepath)
            
            return None
            
        except Exception as e:
            logger.error(f"Vimeo download failed: {e}")
            return None
    
    async def _scrape_and_download(self, url: str, output_dir: Path, title: str) -> Optional[str]:
        """
        Scrape page and extract video/audio URL, then download.
        
        Handles:
        - CNBC
        - WIRED  
        - Bloomberg
        - Yahoo Finance
        - Think tanks
        """
        try:
            # Fetch page
            response = await self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find video/audio sources
            media_url = None
            
            # Method 1: Look for <video> or <audio> tags
            for tag in ['video', 'audio']:
                element = soup.find(tag)
                if element and element.get('src'):
                    media_url = element['src']
                    break
            
            # Method 2: Look for source tags within video/audio
            if not media_url:
                for tag in ['video', 'audio']:
                    parent = soup.find(tag)
                    if parent:
                        source = parent.find('source')
                        if source and source.get('src'):
                            media_url = source['src']
                            break
            
            # Method 3: Try yt-dlp generic extractor
            if not media_url:
                logger.info("No direct media found, trying yt-dlp generic extractor...")
                return await self._download_with_ytdlp(url, output_dir, title)
            
            # Download the media URL
            if media_url.startswith('//'):
                media_url = 'https:' + media_url
            elif media_url.startswith('/'):
                parsed = urlparse(url)
                media_url = f"{parsed.scheme}://{parsed.netloc}{media_url}"
            
            ext = '.mp4' if 'video' in media_url or '.mp4' in media_url else '.mp3'
            return await self._download_direct(media_url, output_dir, ext, title)
            
        except Exception as e:
            logger.error(f"Page scrape failed: {e}")
            return None
    
    async def _download_with_ytdlp(self, url: str, output_dir: Path, title: str) -> Optional[str]:
        """Fallback: use yt-dlp generic extractor."""
        try:
            import yt_dlp
            
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)[:100]
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(output_dir / f"{safe_title}.%(ext)s"),
                'quiet': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find downloaded file
            for ext in ['.mp3', '.m4a', '.webm', '.mp4']:
                filepath = output_dir / f"{safe_title}{ext}"
                if filepath.exists():
                    return str(filepath)
            
            return None
            
        except Exception as e:
            logger.error(f"yt-dlp generic extractor failed: {e}")
            return None
    
    async def _download_cspan(self, url: str, output_dir: Path, title: str) -> Optional[str]:
        """Download from C-SPAN using yt-dlp (it has C-SPAN support)."""
        return await self._download_with_ytdlp(url, output_dir, title)
    
    async def _download_archive(self, url: str, output_dir: Path, title: str) -> Optional[str]:
        """Download from government archives (try yt-dlp first)."""
        return await self._download_with_ytdlp(url, output_dir, title)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def get_stats(self) -> Dict:
        """Get download statistics."""
        return self.stats.copy()


async def download_all_stories():
    """Download videos from all 4 Grok research JSONs."""
    downloader = MultiSourceDownloader()
    
    # Load all JSON files
    story_files = [
        ('research/grok_story1_ai_companies.json', 'story1_ai_companies'),
        ('research/grok_story2_defense_tech.json', 'story2_defense_tech'),
        ('research/grok_story3_supply_chain.json', 'story3_supply_chain'),
        ('research/grok_story4_cartel_ops.json', 'story4_cartel_ops'),
    ]
    
    # Progress tracking
    progress_file = Path('output/grok_downloads_progress.txt')
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(progress_file, 'w') as f:
        f.write("=== GROK MULTI-SOURCE DOWNLOADS ===\n\n")
    
    total_videos = 0
    total_downloaded = 0
    
    for json_file, story_dir in story_files:
        if not Path(json_file).exists():
            logger.warning(f"Skipping {json_file} - file not found")
            continue
        
        with open(json_file, 'r') as f:
            story_data = json.load(f)
        
        story_name = story_data.get('story', story_dir)
        videos = story_data.get('videos', [])
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Story: {story_name}")
        logger.info(f"Videos: {len(videos)}")
        logger.info(f"{'='*80}\n")
        
        with open(progress_file, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Story: {story_name}\n")
            f.write(f"Videos: {len(videos)}\n")
            f.write(f"{'='*80}\n\n")
        
        for i, video in enumerate(videos, 1):
            total_videos += 1
            
            msg = f"[{i}/{len(videos)}] {video['title'][:60]}..."
            logger.info(msg)
            
            with open(progress_file, 'a') as f:
                f.write(f"{msg}\n")
            
            file_path = await downloader.download_video(video, story_dir)
            
            if file_path:
                total_downloaded += 1
                with open(progress_file, 'a') as f:
                    f.write(f"  ✅ Downloaded: {file_path}\n")
            else:
                with open(progress_file, 'a') as f:
                    f.write(f"  ❌ Failed: {video['url']}\n")
            
            # Rate limiting
            await asyncio.sleep(1)
    
    # Final stats
    stats = downloader.get_stats()
    
    summary = f"\n{'='*80}\n"
    summary += f"DOWNLOAD COMPLETE\n"
    summary += f"  Total videos: {total_videos}\n"
    summary += f"  Downloaded: {total_downloaded}\n"
    summary += f"  Failed: {total_videos - total_downloaded}\n"
    summary += f"  Success rate: {total_downloaded/total_videos*100:.1f}%\n\n"
    summary += f"By method:\n"
    for method, count in stats['by_method'].items():
        summary += f"  {method}: {count}\n"
    summary += f"{'='*80}\n"
    
    logger.info(summary)
    
    with open(progress_file, 'a') as f:
        f.write(summary)
    
    await downloader.close()
    
    logger.info(f"\n✅ Progress saved to: {progress_file}")
    logger.info(f"\nTo monitor: tail -f {progress_file}")


if __name__ == "__main__":
    asyncio.run(download_all_stories())

