"""Universal Video Client for 1800+ Sites using yt-dlp."""

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


class UniversalVideoClient:
    """Handle video search and audio extraction from 1800+ sites using yt-dlp."""
    
    def __init__(self):
        """Initialize universal video client with optimized settings."""
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s-%(id)s.%(ext)s',
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
            # Add user agent to avoid blocks
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            # Enable SponsorBlock for YouTube
            'sponsorblock_mark': 'all',
            # Better format selection
            'format_sort': ['quality', 'res', 'fps', 'hdr:12', 'codec:vp9.2', 'size', 'br', 'asr', 'proto', 'ext', 'hasaud', 'source', 'id'],
        }
    
    def get_supported_sites(self) -> List[str]:
        """Get a list of all supported sites (1800+)."""
        try:
            # Get list of all extractors
            from yt_dlp.extractor import list_extractors
            extractors = list_extractors()
            
            # Extract site names from extractors
            sites = []
            for ie in extractors:
                if hasattr(ie, 'IE_NAME') and ie.IE_NAME != 'generic':
                    sites.append(ie.IE_NAME)
            
            return sorted(list(set(sites)))
        except:
            # Fallback to some known popular sites
            return [
                'youtube', 'twitter', 'tiktok', 'vimeo', 'facebook',
                'instagram', 'twitch', 'reddit', 'dailymotion', 'soundcloud',
                'bandcamp', 'bbc', 'cnn', 'ted', 'pornhub', 'xvideos',
                'imgur', 'gfycat', 'streamable', 'mixcloud', 'patreon'
            ]
    
    def is_supported_url(self, url: str) -> bool:
        """
        Check if a URL is supported by yt-dlp.
        
        Supports 1800+ sites including:
        - Video platforms: YouTube, Vimeo, Dailymotion, Twitch
        - Social media: Twitter/X, TikTok, Instagram, Facebook, Reddit
        - News sites: BBC, CNN, NBC, ABC, Fox News, Reuters
        - Educational: TED, Coursera, Khan Academy, MIT OpenCourseWare
        - Entertainment: Netflix trailers, Hulu clips, Crunchyroll
        - Adult content: PornHub, XVideos, etc.
        - Music: SoundCloud, Bandcamp, Mixcloud
        - And 1800+ more!
        """
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            try:
                # Try to extract basic info without downloading
                ydl.extract_info(url, download=False, process=False)
                return True
            except yt_dlp.utils.DownloadError:
                return False
            except Exception:
                # For some sites, we might need to try with process=True
                try:
                    ydl.extract_info(url, download=False)
                    return True
                except:
                    return False
    
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 5,
        site: str = "youtube",
        sort_by: str = "relevance"
    ) -> List[VideoMetadata]:
        """
        Search for videos. Currently supports YouTube search, but can be extended.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            site: Site to search (currently only 'youtube' has search)
            sort_by: Sort order
            
        Returns:
            List of VideoMetadata objects
        """
        if site.lower() == "youtube":
            try:
                logger.info(f"Searching YouTube for: {query}")
                
                # Use youtube-search-python for YouTube
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
                            tags=[]
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
        else:
            # For other sites, we'd need to use yt-dlp's search functionality
            # Some sites support search via yt-dlp (e.g., "ytsearch:query")
            logger.warning(f"Search not implemented for site: {site}")
            return []
    
    async def download_audio(
        self, 
        video_url: str,
        output_dir: Optional[str] = None
    ) -> Tuple[str, VideoMetadata]:
        """
        Download audio from ANY supported video site (1800+ sites).
        
        Supports:
        - YouTube, Vimeo, Dailymotion
        - Twitter/X, TikTok, Instagram
        - Twitch, Reddit, Facebook
        - SoundCloud, Bandcamp
        - BBC, CNN, TED
        - And 1800+ more!
        
        Args:
            video_url: Video URL from any supported site
            output_dir: Directory to save audio file (uses temp if None)
            
        Returns:
            Tuple of (audio_file_path, video_metadata)
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        # Update options with output directory
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = os.path.join(output_dir, '%(title)s-%(id)s.%(ext)s')
        
        try:
            logger.info(f"Downloading audio from: {video_url}")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract video info first
                info = ydl.extract_info(video_url, download=False)
                
                # Log the site being used
                extractor = info.get('extractor', 'unknown')
                logger.info(f"Using extractor: {extractor}")
                
                # Create metadata from full info
                metadata = self._create_metadata_from_info(info)
                
                # Now download the audio
                ydl.download([video_url])
                
                # Find the downloaded file
                # yt-dlp might change the filename, so we need to search
                title = info.get('title', 'Unknown')
                video_id = info.get('id', '')
                
                # Look for the file
                audio_file = None
                for filename in os.listdir(output_dir):
                    if video_id in filename and filename.endswith(('.mp3', '.m4a', '.opus', '.webm')):
                        audio_file = os.path.join(output_dir, filename)
                        break
                
                if not audio_file or not os.path.exists(audio_file):
                    raise FileNotFoundError(f"Audio file not found after download")
                
                logger.info(f"Audio downloaded: {audio_file}")
                return audio_file, metadata
                
        except Exception as e:
            logger.error(f"Audio download failed: {e}")
            raise
    
    async def get_video_info(self, video_url: str) -> VideoMetadata:
        """Get video metadata from ANY supported site without downloading."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Log which site this is from
                extractor = info.get('extractor', 'unknown')
                logger.info(f"Extracting info from {extractor}: {info.get('title', 'Unknown')}")
                
                return self._create_metadata_from_info(info)
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise
    
    def _create_metadata_from_info(self, info: Dict) -> VideoMetadata:
        """Create VideoMetadata from yt-dlp info dict (works for any site)."""
        # Parse upload date - different sites use different formats
        upload_date = info.get('upload_date', '')
        timestamp = info.get('timestamp')
        
        if timestamp:
            published_at = datetime.fromtimestamp(timestamp)
        elif upload_date:
            try:
                published_at = datetime.strptime(upload_date, '%Y%m%d')
            except:
                published_at = datetime.now()
        else:
            published_at = datetime.now()
        
        # Extract site-agnostic metadata
        return VideoMetadata(
            video_id=info.get('id', ''),
            title=info.get('title', 'Unknown'),
            channel=info.get('uploader', info.get('channel', 'Unknown')),
            channel_id=info.get('channel_id', info.get('uploader_id', '')),
            duration=info.get('duration', 0),
            url=info.get('webpage_url', info.get('url', '')),
            published_at=published_at,
            view_count=info.get('view_count', 0),
            description=info.get('description', ''),
            tags=info.get('tags', [])
        )
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        try:
            # Handle different duration formats
            if isinstance(duration_str, (int, float)):
                return int(duration_str)
                
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
            if isinstance(views_str, (int, float)):
                return int(views_str)
                
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
    
    async def download_video(self, video_url: str, output_dir: str = ".") -> tuple[str, VideoMetadata]:
        """
        Download full video file from any supported platform.
        
        Args:
            video_url: URL of the video
            output_dir: Directory to save the video
            
        Returns:
            Tuple of (video_path, metadata)
        """
        if not self.is_supported_url(video_url):
            raise ValueError(f"Unsupported URL: {video_url}")
        
        # Get video info first
        metadata = await self.get_video_metadata(video_url)
        
        # Create safe filename
        safe_title = "".join(c for c in metadata.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:100]  # Limit length
        
        # Video extension depends on platform, but mp4 is most common
        video_filename = f"{safe_title}-{metadata.video_id}.mp4"
        video_path = os.path.join(output_dir, video_filename)
        
        logger.info(f"Downloading video from: {video_url}")
        
        # yt-dlp options for video download
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prefer mp4
            'outtmpl': video_path,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'no_color': True,
            'progress_hooks': [self._progress_hook],
        }
        
        # Add any platform-specific options
        platform = self._detect_platform(video_url)
        logger.info(f"Using extractor: {platform}")
        
        if platform == "twitter":
            ydl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        logger.info(f"Video downloaded: {video_path}")
        
        return video_path, metadata
    
    def _progress_hook(self, d):
        # This method is empty in the original code block
        # It's assumed to exist as it's called in the download_video method
        pass 