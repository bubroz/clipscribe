"""
Monitor YouTube channels for new video drops via RSS.

Uses RSS feeds (no API key needed) to detect new uploads.
Lightweight, fast, and reliable.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import feedparser

logger = logging.getLogger(__name__)


class ChannelMonitor:
    """
    Monitor YouTube channels for new video uploads.

    Uses RSS feeds (free, no auth required):
    https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID

    Features:
    - Detects new videos within 15 minutes
    - Tracks seen videos to avoid duplicates
    - Persists state across restarts
    - Zero API costs
    """

    def __init__(self, channel_ids: List[str], state_file: Optional[Path] = None):
        """
        Initialize channel monitor.

        Args:
            channel_ids: List of YouTube channel IDs to monitor
            state_file: Path to store seen videos (default: .clipscribe_monitor_state.json)
        """
        self.channel_ids = channel_ids
        self.state_file = state_file or Path.home() / ".clipscribe_monitor_state.json"

        # Load previously seen videos
        self.seen_videos: Set[str] = self._load_state()

        logger.info(
            f"ChannelMonitor initialized: {len(channel_ids)} channels, {len(self.seen_videos)} videos seen"
        )

    def _load_state(self) -> Set[str]:
        """Load seen videos from state file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    return set(data.get("seen_videos", []))
            except Exception as e:
                logger.warning(f"Failed to load monitor state: {e}")

        return set()

    def _save_state(self):
        """Save seen videos to state file."""
        try:
            data = {
                "seen_videos": list(self.seen_videos),
                "last_updated": datetime.now().isoformat(),
                "channels": self.channel_ids,
            }

            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save monitor state: {e}")

    def get_rss_url(self, channel_id: str) -> str:
        """
        Convert channel ID to RSS feed URL.

        Args:
            channel_id: YouTube channel ID (starts with UC...)

        Returns:
            RSS feed URL
        """
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    async def check_for_new_videos(self) -> List[Dict]:
        """
        Check all monitored channels for new videos.

        Returns:
            List of new video dicts with: video_id, url, title, published, channel
        """
        new_videos = []

        for channel_id in self.channel_ids:
            try:
                channel_new = await self._check_channel(channel_id)
                new_videos.extend(channel_new)
            except Exception as e:
                logger.error(f"Failed to check channel {channel_id}: {e}")

        # Save state after checking all channels
        if new_videos:
            self._save_state()
            logger.info(
                f"Found {len(new_videos)} new videos across {len(self.channel_ids)} channels"
            )

        return new_videos

    async def _check_channel(self, channel_id: str) -> List[Dict]:
        """Check single channel for new videos."""
        feed_url = self.get_rss_url(channel_id)

        logger.debug(f"Checking RSS feed: {feed_url}")

        # Parse RSS feed (blocking, but fast ~100ms)
        feed = await asyncio.to_thread(feedparser.parse, feed_url)

        if not feed.entries:
            logger.warning(f"No entries in feed for channel {channel_id}")
            return []

        new_videos = []
        shorts_count = 0

        for entry in feed.entries:
            # Extract video ID from entry
            video_id = entry.get("yt_videoid", "")

            if not video_id:
                # Fallback: parse from link
                link = entry.get("link", "")
                if "watch?v=" in link:
                    video_id = link.split("watch?v=")[1].split("&")[0]

            # Skip if already seen
            if not video_id or video_id in self.seen_videos:
                continue

            # Filter out YouTube Shorts (multiple criteria)
            title = entry.get("title", "")
            description = entry.get("summary", "")
            link = entry.get("link", "")

            is_short = False

            # Check 1: URL pattern (most reliable)
            if "/shorts/" in link:
                logger.debug(f"Skipping Short (URL pattern): {title}")
                is_short = True

            # Check 2: Title contains #shorts or #short
            elif "#shorts" in title.lower() or "#short" in title.lower():
                logger.debug(f"Skipping Short (hashtag in title): {title}")
                is_short = True

            # Check 3: Description contains #shorts
            elif "#shorts" in description.lower():
                logger.debug(f"Skipping Short (hashtag in description): {title}")
                is_short = True

            if not is_short:
                new_videos.append(
                    {
                        "video_id": video_id,
                        "url": entry.get("link", f"https://youtube.com/watch?v={video_id}"),
                        "title": title,
                        "published": entry.get("published", ""),
                        "channel": feed.feed.get("title", "Unknown Channel"),
                        "channel_id": channel_id,
                        "detected_at": datetime.now().isoformat(),
                    }
                )

                # Mark as seen
                self.seen_videos.add(video_id)
            else:
                # Still mark shorts as seen so we don't keep checking them
                self.seen_videos.add(video_id)
                shorts_count += 1

        if new_videos:
            logger.info(
                f"Found {len(new_videos)} new videos on {feed.feed.get('title', channel_id)}"
            )

        if shorts_count > 0:
            logger.info(f"Filtered out {shorts_count} Shorts (only processing full videos)")

        return new_videos

    async def monitor_loop(
        self, interval: int = 600, on_new_video: Optional[callable] = None  # 10 minutes
    ):
        """
        Continuously monitor channels in a loop.

        Args:
            interval: Seconds between checks (default: 600 = 10 minutes)
            on_new_video: Callback function called for each new video
        """
        logger.info(f"Starting monitor loop: checking every {interval}s")

        while True:
            try:
                new_videos = await self.check_for_new_videos()

                # Call callback for each new video
                if new_videos and on_new_video:
                    for video in new_videos:
                        try:
                            await on_new_video(video)
                        except Exception as e:
                            logger.error(f"Callback failed for {video['url']}: {e}")

                # Wait before next check
                logger.debug(f"Waiting {interval}s until next check...")
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Monitor loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    def get_channel_id_from_url(self, channel_url: str) -> Optional[str]:
        """
        Extract channel ID from channel URL.

        Supports:
        - https://youtube.com/@username
        - https://youtube.com/channel/UC...
        - https://youtube.com/c/customname

        For @username URLs, this requires an API call or web scraping.
        For now, we require UC... channel IDs directly.
        """
        if "channel/" in channel_url:
            return channel_url.split("channel/")[1].split("/")[0].split("?")[0]

        if channel_url.startswith("UC") and len(channel_url) == 24:
            return channel_url

        logger.warning(f"Could not extract channel ID from: {channel_url}")
        return None


async def test_monitor():
    """Test the monitor with The Stoic Viking channel."""
    # The Stoic Viking channel ID
    channel_id = "UCg5EWI7X2cyS98C8hQwDCcw"

    monitor = ChannelMonitor([channel_id])

    # Check for new videos
    new_videos = await monitor.check_for_new_videos()

    print(f"Found {len(new_videos)} new videos")
    for video in new_videos:
        print(f"  - {video['title']}")
        print(f"    URL: {video['url']}")
        print(f"    Published: {video['published']}")


if __name__ == "__main__":
    asyncio.run(test_monitor())
