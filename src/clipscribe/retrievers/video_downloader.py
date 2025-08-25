"""Video Downloader Module - Handles video downloading and metadata extraction."""

import asyncio
import logging
from typing import Optional, Tuple, Any, Dict
from pathlib import Path

from ..models import VideoMetadata
from .universal_video_client import UniversalVideoClient
from .video_retention_manager import VideoRetentionManager
from ..config.settings import VideoRetentionPolicy

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Handles video downloading and initial metadata extraction."""

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cookies_from_browser: Optional[str] = None,
    ):
        """Initialize the video downloader."""
        self.cache_dir = Path(cache_dir or "cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cookies_from_browser = cookies_from_browser

        self.video_client = UniversalVideoClient()

    def is_supported_url(self, video_url: str) -> bool:
        """Check if a video URL is supported."""
        return self.video_client.is_supported_url(video_url)

    async def download_video(
        self,
        video_url: str,
        cookies_from_browser: Optional[str] = None
    ) -> Tuple[str, VideoMetadata]:
        """
        Download video and return media file path and metadata.

        Args:
            video_url: URL of the video to download
            cookies_from_browser: Browser to extract cookies from

        Returns:
            Tuple of (media_file_path, metadata)

        Raises:
            Exception: If download fails
        """
        try:
            logger.info(f"Downloading video: {video_url}")

            media_file, metadata = await self.video_client.download_video(
                video_url,
                output_dir=self.cache_dir,
                cookies_from_browser=cookies_from_browser or self.cookies_from_browser,
            )

            logger.info(f"Successfully downloaded: {metadata.title}")
            return media_file, metadata

        except Exception as e:
            logger.error(f"Failed to download video {video_url}: {e}")
            raise

    async def cleanup_temp_file(
        self,
        media_path: Path,
        retention_policy: VideoRetentionPolicy,
        retention_manager: Optional[VideoRetentionManager] = None
    ) -> None:
        """Clean up temporary video files based on retention policy."""
        if retention_policy == VideoRetentionPolicy.DELETE and media_path.exists():
            try:
                media_path.unlink()
                logger.debug(f"Cleaned up temp file: {media_path}")
            except OSError as e:
                logger.warning(f"Could not remove temp file {media_path}: {e}")

    async def search_videos(
        self, query: str, max_results: int = 5, site: str = "youtube"
    ) -> list:
        """Search for videos (delegated to universal client)."""
        return await self.video_client.search_videos(query, max_results, site)
