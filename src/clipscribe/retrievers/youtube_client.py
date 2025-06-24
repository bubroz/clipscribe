"""YouTube Client for Video Search and Audio Extraction."""

import os
import logging
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import yt_dlp
from youtubesearchpython import VideosSearch
import json

from ..models import VideoMetadata

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Handle YouTube search and audio extraction using yt-dlp."""
    
    def __init__(self):
        """Initialize YouTube client with optimized settings."""
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'retries': 3,
            'fragment_retries': 3,
            'ignoreerrors': False,
            'logtostderr': False,
            'socket_timeout': 30,
        }
    
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 5,
        sort_by: str = "relevance"
    ) -> List[VideoMetadata]:
        """
        Search YouTube for videos matching the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sort_by: Sort order (relevance, upload_date, view_count, rating)
            
        Returns:
            List of VideoMetadata objects
        """
        try:
            logger.info(f"Searching YouTube for: {query}")
            
            # Use youtube-search-python for better results
            videos_search = VideosSearch(query, limit=max_results)
            results = videos_search.result()['result']
            
            videos = []
            for result in results:
                try:
                    # Extract video metadata
                    video_id = result.get('id', '')
                    duration_str = result.get('duration', '0:00')
                    
                    # Parse duration to seconds
                    duration = self._parse_duration(duration_str)
                    
                    # Parse published date
                    published_str = result.get('publish_time', '')
                    published_at = self._parse_published_date(published_str)
                    
                    # Create metadata object
                    metadata = VideoMetadata(
                        video_id=video_id,
                        title=result.get('title', 'Unknown'),
                        channel=result.get('channel', 'Unknown'),
                        channel_id=result.get('channel_id', ''),
                        duration=duration,
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        published_at=published_at,
                        view_count=self._parse_view_count(result.get('views', '0')),
                        description=result.get('long_desc', ''),
                        tags=[]  # YouTube search doesn't provide tags
                    )
                    
                    videos.append(metadata)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse video result: {e}")
                    continue
            
            logger.info(f"Found {len(videos)} videos")
            return videos
            
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return []
    
    async def download_audio(
        self, 
        video_url: str,
        output_dir: Optional[str] = None
    ) -> Tuple[str, VideoMetadata]:
        """
        Download audio from YouTube video.
        
        Args:
            video_url: YouTube video URL
            output_dir: Directory to save audio file (uses temp if None)
            
        Returns:
            Tuple of (audio_file_path, video_metadata)
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        # Update options with output directory
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = os.path.join(output_dir, '%(id)s.%(ext)s')
        
        try:
            logger.info(f"Downloading audio from: {video_url}")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract video info first
                info = ydl.extract_info(video_url, download=False)
                
                # Create metadata from full info
                metadata = self._create_metadata_from_info(info)
                
                # Now download the audio
                ydl.download([video_url])
                
                # Find the downloaded file
                video_id = info['id']
                audio_file = os.path.join(output_dir, f"{video_id}.mp3")
                
                if not os.path.exists(audio_file):
                    # Check for other audio formats
                    for ext in ['m4a', 'opus', 'webm']:
                        alt_file = os.path.join(output_dir, f"{video_id}.{ext}")
                        if os.path.exists(alt_file):
                            audio_file = alt_file
                            break
                
                if not os.path.exists(audio_file):
                    raise FileNotFoundError(f"Audio file not found after download")
                
                logger.info(f"Audio downloaded: {audio_file}")
                return audio_file, metadata
                
        except Exception as e:
            logger.error(f"Audio download failed: {e}")
            raise
    
    async def get_video_info(self, video_url: str) -> VideoMetadata:
        """Get video metadata without downloading."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return self._create_metadata_from_info(info)
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise
    
    def _create_metadata_from_info(self, info: Dict) -> VideoMetadata:
        """Create VideoMetadata from yt-dlp info dict."""
        # Parse upload date
        upload_date = info.get('upload_date', '')
        if upload_date:
            published_at = datetime.strptime(upload_date, '%Y%m%d')
        else:
            published_at = datetime.now()
        
        return VideoMetadata(
            video_id=info.get('id', ''),
            title=info.get('title', 'Unknown'),
            channel=info.get('uploader', 'Unknown'),
            channel_id=info.get('channel_id', ''),
            duration=info.get('duration', 0),
            url=info.get('webpage_url', ''),
            published_at=published_at,
            view_count=info.get('view_count', 0),
            description=info.get('description', ''),
            tags=info.get('tags', [])
        )
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        try:
            parts = duration_str.split(':')
            if len(parts) == 1:
                return int(parts[0])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                return 0
        except:
            return 0
    
    def _parse_published_date(self, date_str: str) -> datetime:
        """Parse published date string."""
        try:
            # Handle relative dates like "2 days ago"
            if 'ago' in date_str:
                # Simple parsing for common cases
                if 'hour' in date_str:
                    hours = int(date_str.split()[0])
                    return datetime.now() - timedelta(hours=hours)
                elif 'day' in date_str:
                    days = int(date_str.split()[0])
                    return datetime.now() - timedelta(days=days)
                elif 'week' in date_str:
                    weeks = int(date_str.split()[0])
                    return datetime.now() - timedelta(weeks=weeks)
                elif 'month' in date_str:
                    months = int(date_str.split()[0])
                    return datetime.now() - timedelta(days=months*30)
                elif 'year' in date_str:
                    years = int(date_str.split()[0])
                    return datetime.now() - timedelta(days=years*365)
            
            # Try parsing absolute date
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return datetime.now()
    
    def _parse_view_count(self, views_str: str) -> int:
        """Parse view count string to integer."""
        try:
            # Remove commas and "views" text
            clean = views_str.replace(',', '').replace('views', '').strip()
            
            # Handle K, M, B suffixes
            if 'K' in clean:
                return int(float(clean.replace('K', '')) * 1000)
            elif 'M' in clean:
                return int(float(clean.replace('M', '')) * 1_000_000)
            elif 'B' in clean:
                return int(float(clean.replace('B', '')) * 1_000_000_000)
            else:
                return int(clean)
        except:
            return 0 