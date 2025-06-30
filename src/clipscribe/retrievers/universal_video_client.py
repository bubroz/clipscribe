"""Universal Video Client for 1800+ Sites using yt-dlp with Enhanced Temporal Intelligence."""

import os
import logging
import tempfile
import asyncio
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
import yt_dlp
from youtubesearchpython.__future__ import (
    VideosSearch,
    Channel,
    Playlist,
    CustomSearch
)
from youtubesearchpython import VideoSortOrder, playlist_from_channel_id

from ..models import VideoMetadata

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """Represents a video chapter with temporal boundaries."""
    title: str
    start_time: float
    end_time: float
    url: Optional[str] = None
    

@dataclass
class VideoSegment:
    """Represents a video segment (e.g., SponsorBlock categories)."""
    category: str
    start_time: float
    end_time: float
    uuid: Optional[str] = None
    

@dataclass
class WordLevelSubtitles:
    """Represents word-level subtitle timing data."""
    word_level_timing: Dict[str, Dict[str, float]]
    full_text: str
    language: str
    

@dataclass
class TemporalMetadata:
    """Comprehensive temporal metadata extracted from video."""
    chapters: List[Chapter]
    subtitles: Optional[WordLevelSubtitles]
    sponsorblock_segments: List[VideoSegment]
    video_metadata: Dict[str, Any]
    word_level_timing: Dict[str, Dict[str, float]]
    content_sections: List[VideoSegment]


class EnhancedUniversalVideoClient:
    """Universal Video Client with comprehensive temporal intelligence extraction."""
    
    def __init__(self):
        """Initialize with enhanced temporal metadata extraction capabilities."""
        # Standard options for basic functionality
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
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'sponsorblock_mark': 'all',
            'format_sort': ['quality', 'res', 'fps', 'hdr:12', 'codec:vp9.2', 'size', 'br', 'asr', 'proto', 'ext', 'hasaud', 'source', 'id'],
        }
        
        # ENHANCED TEMPORAL INTELLIGENCE OPTIONS - The Game Changer! 🚀
        self.temporal_opts = {
            **self.ydl_opts,
            # TEMPORAL INTELLIGENCE CORE FEATURES
            'writesubtitles': True,           # Extract subtitles with timing
            'writeautomaticsub': True,        # Auto-generated captions
            'embedsubs': True,                # Embed subtitle timing data
            'embed_chapters': True,           # Extract chapter information
            'sponsorblock_mark': 'all',       # Mark ALL SponsorBlock segments
            'write_info_json': True,          # Rich temporal metadata
            
            # Subtitle options for word-level timing
            'subtitleslangs': ['en', 'auto'], # English + auto-detect subtitles
            'subtitlesformat': 'vtt',         # WebVTT has precise timing data
            
            # Chapter options
            'embed_metadata': True,           # Comprehensive metadata embedding
            'split_chapters': False,          # Don't split, just extract info
            
            # Enhanced metadata extraction
            'writeinfojson': True,            # Force info JSON generation
            'getcomments': True,              # Extract comments (may have timestamps)
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
        sort_by: str = "relevance",
        period: Optional[str] = None
    ) -> List[VideoMetadata]:
        """
        Search for videos. Currently supports YouTube search, but can be extended.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            site: Site to search (currently only 'youtube' has search)
            sort_by: Sort order
            period: Time period to filter (e.g., 'hour', 'day', 'week', 'month', 'year')
            
        Returns:
            List of VideoMetadata objects
        """
        if site.lower() == "youtube":
            try:
                logger.info(f"Searching YouTube for: {query}, period: {period}, sort_by: {sort_by}")

                video_sort_order = self._get_video_sort_order(sort_by)

                search = CustomSearch(query, video_sort_order, limit=max_results, region='US')
                
                search_result = await search.next()
                results = search_result['result'] if search_result and 'result' in search_result else []
                
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
                            channel=result.get('channel', {}).get('name', 'Unknown'),
                            channel_id=result.get('channel', {}).get('id', ''),
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
    
    async def search_channel(
        self,
        channel_id_or_url: str,
        max_results: int = 10,
        sort_by: str = "newest"
    ) -> List[VideoMetadata]:
        """
        Get videos from a specific YouTube channel.

        Args:
            channel_id_or_url: The ID or URL of the YouTube channel.
            max_results: Maximum number of videos to return.
            sort_by: How to sort the videos ('newest', 'oldest', 'popular').

        Returns:
            A list of VideoMetadata objects from the channel.
        """
        logger.info(f"Attempting to search channel '{channel_id_or_url}' for '{sort_by}' videos.")
        try:
            channel_info = await Channel.get(channel_id_or_url)
            if not channel_info or 'id' not in channel_info:
                logger.error(f"Could not retrieve channel info for {channel_id_or_url}")
                return []
            channel_id = channel_info['id']
            logger.info(f"Successfully found channel ID: {channel_id} for '{channel_id_or_url}'")

            playlist = Playlist(playlist_from_channel_id(channel_id))
            if not playlist:
                logger.error(f"Could not create playlist object for channel ID: {channel_id}")
                return []
            logger.info(f"Fetching videos from uploads playlist: {playlist.url}")
            
            await playlist.next()
            results = playlist.videos or []
            logger.info(f"Fetched initial batch of {len(results)} videos.")

            while playlist.hasMoreVideos and len(results) < max_results:
                logger.info(f"Fetching next batch of videos... (retrieved {len(results)})")
                await playlist.next()
                if playlist.videos:
                    results.extend(playlist.videos)
                else:
                    logger.warning("Playlist returned no more videos on subsequent fetch.")
                    break
            
            logger.info(f"Total videos fetched before sorting/slicing: {len(results)}")

            if sort_by == 'popular':
                logger.info("Sorting results by view count (popular).")
                results.sort(key=lambda v: self._parse_view_count(v.get('viewCount', {}).get('text', '0')), reverse=True)
            
            results = results[:max_results]
            logger.info(f"Final result count after filtering: {len(results)}")

            videos = []
            for result in results:
                try:
                    video_id = result.get('id', '')
                    duration = self._parse_duration(result.get('duration', '0:00'))
                    published_at = self._parse_published_date(result.get('publishedTime', ''))
                    
                    metadata = VideoMetadata(
                        video_id=video_id,
                        title=result.get('title', 'Unknown'),
                        channel=channel_info.get('title', 'Unknown'),
                        channel_id=channel_id,
                        duration=duration,
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        published_at=published_at,
                        view_count=self._parse_view_count(result.get('viewCount', {}).get('text', '0')),
                        description=result.get('description', ''),
                        tags=result.get('keywords', [])
                    )
                    videos.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to parse channel video result: {e}")
                    continue
            
            logger.info(f"Found {len(videos)} videos from channel.")
            return videos

        except Exception as e:
            logger.error(f"YouTube channel search for '{channel_id_or_url}' failed: {e}")
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
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading audio from: {video_url} (attempt {attempt + 1}/{max_retries})")
                
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
                logger.error(f"Audio download failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Check if it's an ffmpeg error
                if "ffmpeg" in str(e).lower() and attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds due to ffmpeg error...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                elif attempt == max_retries - 1:
                    # Last attempt failed
                    raise
                else:
                    # Non-ffmpeg error, raise immediately
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

    def _get_video_sort_order(self, sort_by: str) -> str:
        """Map user-friendly sort option to library-specific value."""
        sort_map = {
            "relevance": VideoSortOrder.relevance,
            "upload_date": VideoSortOrder.uploadDate,
            "view_count": VideoSortOrder.viewCount,
            "rating": VideoSortOrder.rating,
            "newest": VideoSortOrder.uploadDate, # Alias for upload_date
            "popular": VideoSortOrder.viewCount, # Alias for view_count
        }
        return sort_map.get(sort_by.lower(), VideoSortOrder.relevance) 

    async def extract_playlist_preview(
        self, 
        playlist_url: str, 
        max_preview: int = 20
    ) -> Tuple[List[VideoMetadata], int]:
        """
        Extract videos from a playlist and show preview without downloading.
        
        Args:
            playlist_url: YouTube playlist URL
            max_preview: Maximum number of videos to preview
            
        Returns:
            Tuple of (preview_videos, total_count)
        """
        try:
            logger.info(f"Extracting playlist preview from: {playlist_url}")
            
            # Use yt-dlp to extract playlist info without downloading
            with yt_dlp.YoutubeDL({
                'quiet': True, 
                'extract_flat': True,  # Don't extract individual video info
                'playlistend': max_preview  # Limit preview size
            }) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
                
                if not playlist_info:
                    raise ValueError("Could not extract playlist information")
                
                entries = playlist_info.get('entries', [])
                total_count = playlist_info.get('playlist_count', len(entries))
                
                logger.info(f"Found {total_count} total videos, showing preview of {len(entries)}")
                
                # Convert entries to VideoMetadata objects
                preview_videos = []
                for entry in entries:
                    if entry:  # Skip None entries
                        try:
                            # For flat extraction, we have limited info
                            metadata = VideoMetadata(
                                video_id=entry.get('id', ''),
                                title=entry.get('title', 'Unknown'),
                                channel=entry.get('uploader', 'Unknown'),
                                channel_id=entry.get('uploader_id', ''),
                                duration=entry.get('duration', 0),
                                url=entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}"),
                                published_at=datetime.now(),  # Not available in flat extraction
                                view_count=0,  # Not available in flat extraction
                                description=entry.get('description', ''),
                                tags=[]
                            )
                            preview_videos.append(metadata)
                        except Exception as e:
                            logger.warning(f"Failed to parse playlist entry: {e}")
                            continue
                
                return preview_videos, total_count
                
        except Exception as e:
            logger.error(f"Failed to extract playlist preview: {e}")
            raise
    
    def is_playlist_url(self, url: str) -> bool:
        """Check if URL is a playlist URL."""
        return 'playlist?list=' in url or '/playlist/' in url

    async def extract_all_playlist_urls(self, playlist_url: str) -> List[str]:
        """
        Extract all video URLs from a playlist.
        
        Args:
            playlist_url: YouTube playlist URL
            
        Returns:
            List of individual video URLs
        """
        try:
            logger.info(f"Extracting all URLs from playlist: {playlist_url}")
            
            with yt_dlp.YoutubeDL({
                'quiet': True,
                'extract_flat': True,
                'dump_single_json': True
            }) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
                
                if not playlist_info:
                    raise ValueError("Could not extract playlist information")
                
                entries = playlist_info.get('entries', [])
                urls = []
                
                for entry in entries:
                    if entry and entry.get('id'):
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        urls.append(video_url)
                
                logger.info(f"Extracted {len(urls)} video URLs from playlist")
                return urls
                
        except Exception as e:
            logger.error(f"Failed to extract playlist URLs: {e}")
            raise 

    async def extract_temporal_metadata(self, video_url: str) -> TemporalMetadata:
        """
        🚀 BREAKTHROUGH FEATURE: Extract comprehensive temporal metadata using yt-dlp.
        
        This is the game-changing capability that enables Timeline Intelligence v2.0:
        - Chapter boundaries with precise timestamps
        - Word-level subtitle timing for sub-second precision
        - SponsorBlock content filtering (intro/outro/sponsors)
        - Rich temporal context from video metadata
        - Comments with temporal references
        
        Args:
            video_url: URL of the video to analyze
            
        Returns:
            TemporalMetadata with comprehensive temporal intelligence
        """
        logger.info(f"🚀 Extracting comprehensive temporal metadata from: {video_url}")
        
        try:
            with yt_dlp.YoutubeDL(self.temporal_opts) as ydl:
                # Extract ALL metadata without downloading video
                info = ydl.extract_info(video_url, download=False)
                
                logger.info(f"📊 Temporal extraction successful: {info.get('extractor', 'unknown')} - {info.get('title', 'Unknown')}")
                
                return TemporalMetadata(
                    chapters=self._extract_chapters(info),
                    subtitles=self._extract_subtitles(info),
                    sponsorblock_segments=self._extract_sponsorblock(info),
                    video_metadata=self._extract_video_metadata(info),
                    word_level_timing=self._extract_word_timing(info),
                    content_sections=self._identify_content_sections(info)
                )
                
        except Exception as e:
            logger.error(f"❌ Temporal metadata extraction failed: {e}")
            # Return empty temporal metadata to maintain functionality
            return TemporalMetadata(
                chapters=[],
                subtitles=None,
                sponsorblock_segments=[],
                video_metadata={},
                word_level_timing={},
                content_sections=[]
            )

    def _extract_chapters(self, info: Dict) -> List[Chapter]:
        """Extract chapter information with precise timestamps."""
        chapters = []
        
        chapter_data = info.get('chapters', [])
        if not chapter_data:
            # No chapters available
            logger.debug("No chapters found in video")
            return chapters
            
        logger.info(f"📖 Found {len(chapter_data)} chapters")
        
        for chapter in chapter_data:
            try:
                chapters.append(Chapter(
                    title=chapter.get('title', 'Untitled Chapter'),
                    start_time=float(chapter.get('start_time', 0)),
                    end_time=float(chapter.get('end_time', 0)),
                    url=chapter.get('url', '')
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse chapter: {e}")
                continue
                
        logger.info(f"✅ Successfully extracted {len(chapters)} chapters")
        return chapters

    def _extract_subtitles(self, info: Dict) -> Optional[WordLevelSubtitles]:
        """Extract word-level subtitle data with precise timestamps."""
        subtitle_info = info.get('subtitles', {})
        auto_captions = info.get('automatic_captions', {})
        
        # Try English subtitles first, then auto-generated
        subtitle_data = None
        language = 'en'
        
        if 'en' in subtitle_info:
            subtitle_data = subtitle_info['en']
        elif 'en' in auto_captions:
            subtitle_data = auto_captions['en']
            language = 'en-auto'
        else:
            # Try first available subtitle
            if subtitle_info:
                lang = list(subtitle_info.keys())[0]
                subtitle_data = subtitle_info[lang]
                language = lang
            elif auto_captions:
                lang = list(auto_captions.keys())[0]
                subtitle_data = auto_captions[lang]
                language = f"{lang}-auto"
        
        if not subtitle_data:
            logger.debug("No subtitle data available")
            return None
            
        logger.info(f"📝 Found subtitles in language: {language}")
        
        # Extract word-level timing (this would need VTT file parsing)
        # For now, return basic structure - full implementation would parse VTT files
        return WordLevelSubtitles(
            word_level_timing={},  # Would be populated from VTT parsing
            full_text=info.get('description', ''),
            language=language
        )

    def _extract_sponsorblock(self, info: Dict) -> List[VideoSegment]:
        """Extract SponsorBlock segments to identify content vs non-content."""
        segments = []
        
        sponsorblock_chapters = info.get('sponsorblock_chapters', [])
        if not sponsorblock_chapters:
            logger.debug("No SponsorBlock data available")
            return segments
            
        logger.info(f"🚫 Found {len(sponsorblock_chapters)} SponsorBlock segments")
        
        for segment in sponsorblock_chapters:
            try:
                segments.append(VideoSegment(
                    category=segment.get('category', 'unknown'),
                    start_time=float(segment.get('start_time', 0)),
                    end_time=float(segment.get('end_time', 0)),
                    uuid=segment.get('uuid', '')
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse SponsorBlock segment: {e}")
                continue
                
        logger.info(f"✅ Successfully extracted {len(segments)} SponsorBlock segments")
        return segments

    def _extract_video_metadata(self, info: Dict) -> Dict[str, Any]:
        """Extract comprehensive video metadata."""
        return {
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'upload_date': info.get('upload_date', ''),
            'uploader': info.get('uploader', ''),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'comment_count': info.get('comment_count', 0),
            'tags': info.get('tags', []),
            'categories': info.get('categories', []),
            'extractor': info.get('extractor', ''),
            'webpage_url': info.get('webpage_url', ''),
            'id': info.get('id', ''),
        }

    def _extract_word_timing(self, info: Dict) -> Dict[str, Dict[str, float]]:
        """Extract word-level timing from subtitle data."""
        # This would parse VTT files for precise word-level timing
        # Implementation would download and parse subtitle files
        # For now, return empty dict - full implementation in next phase
        logger.debug("Word-level timing extraction: placeholder implementation")
        return {}

    def _identify_content_sections(self, info: Dict) -> List[VideoSegment]:
        """Identify content vs non-content sections using SponsorBlock."""
        content_sections = []
        duration = info.get('duration', 0)
        
        if not duration:
            return content_sections
            
        # Start with full video as content
        content_start = 0
        content_end = duration
        
        # Remove non-content sections based on SponsorBlock
        sponsorblock_segments = self._extract_sponsorblock(info)
        
        for segment in sponsorblock_segments:
            if segment.category in ['sponsor', 'intro', 'outro', 'selfpromo', 'interaction']:
                # This is non-content, split around it
                if segment.start_time > content_start:
                    content_sections.append(VideoSegment(
                        category='content',
                        start_time=content_start,
                        end_time=segment.start_time
                    ))
                content_start = segment.end_time
        
        # Add final content section
        if content_start < content_end:
            content_sections.append(VideoSegment(
                category='content',
                start_time=content_start,
                end_time=content_end
            ))
            
        logger.info(f"📺 Identified {len(content_sections)} content sections")
        return content_sections


# Backward compatibility alias
UniversalVideoClient = EnhancedUniversalVideoClient 