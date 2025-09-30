"""
Rate limiter for ToS compliance across video platforms.

Simple, conservative approach:
- 1 request every 10 seconds per platform
- 100 videos per day per platform
- No tiers, no complexity - just safe defaults
"""

import asyncio
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Conservative rate limiter to prevent ToS violations.
    
    Prevents:
    - YouTube bot detection (SABR)
    - Vimeo mass scraping flags
    - IP/account bans
    
    Defaults:
    - 1 request every 10 seconds
    - 100 videos per day per platform
    
    Environment overrides:
    - CLIPSCRIBE_REQUEST_DELAY (seconds between requests)
    - CLIPSCRIBE_DAILY_CAP (videos per day)
    """
    
    def __init__(self):
        # Conservative defaults (can override via environment)
        self.REQUEST_DELAY = int(os.getenv("CLIPSCRIBE_REQUEST_DELAY", "10"))  # seconds
        self.DAILY_CAP = int(os.getenv("CLIPSCRIBE_DAILY_CAP", "100"))  # videos/day
        
        # Track request timestamps per platform
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)
        
        # Track last request time per platform (for delay)
        self.last_request_time: Dict[str, datetime] = {}
        
        # Track consecutive failures (for ban detection)
        self.consecutive_failures: Dict[str, int] = defaultdict(int)
        
        logger.info(
            f"RateLimiter initialized: {self.REQUEST_DELAY}s delay, "
            f"{self.DAILY_CAP} videos/day cap"
        )
    
    async def wait_if_needed(self, platform: str):
        """
        Wait to comply with rate limit before proceeding.
        
        Args:
            platform: Platform name (youtube, vimeo, etc.)
        """
        if platform in self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time[platform]).total_seconds()
            
            if elapsed < self.REQUEST_DELAY:
                wait_time = self.REQUEST_DELAY - elapsed
                logger.info(
                    f"Rate limiting {platform}: waiting {wait_time:.1f}s "
                    f"(1 req/{self.REQUEST_DELAY}s)"
                )
                await asyncio.sleep(wait_time)
        
        self.last_request_time[platform] = datetime.now()
    
    def check_daily_cap(self, platform: str) -> bool:
        """
        Check if under daily limit for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            True if under cap, False if cap reached
        """
        if platform not in self.request_history:
            return True
        
        # Count requests in last 24 hours
        cutoff = datetime.now() - timedelta(days=1)
        recent_requests = [ts for ts in self.request_history[platform] if ts > cutoff]
        
        if len(recent_requests) >= self.DAILY_CAP:
            logger.warning(
                f"Daily cap reached for {platform}: "
                f"{len(recent_requests)}/{self.DAILY_CAP} videos"
            )
            return False
        
        return True
    
    def record_request(self, platform: str, success: bool = True):
        """
        Record request for tracking and ban detection.
        
        Args:
            platform: Platform name
            success: Whether request succeeded
        """
        # Record timestamp
        self.request_history[platform].append(datetime.now())
        
        # Track failures for ban detection
        if not success:
            self.consecutive_failures[platform] += 1
            
            if self.consecutive_failures[platform] >= 3:
                logger.error(
                    f"⚠️  Ban detection: {self.consecutive_failures[platform]} "
                    f"consecutive failures on {platform}. May be IP banned."
                )
        else:
            # Reset on success
            self.consecutive_failures[platform] = 0
        
        # Cleanup old history (keep 7 days for debugging)
        cutoff = datetime.now() - timedelta(days=7)
        self.request_history[platform] = [
            ts for ts in self.request_history[platform] if ts > cutoff
        ]
    
    def get_stats(self, platform: str) -> dict:
        """
        Get current statistics for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Dictionary with request counts and status
        """
        if platform not in self.request_history:
            return {
                "platform": platform,
                "requests_today": 0,
                "requests_this_week": 0,
                "daily_cap": self.DAILY_CAP,
                "remaining_today": self.DAILY_CAP
            }
        
        now = datetime.now()
        day_cutoff = now - timedelta(days=1)
        week_cutoff = now - timedelta(days=7)
        
        requests_today = len([ts for ts in self.request_history[platform] if ts > day_cutoff])
        requests_this_week = len([ts for ts in self.request_history[platform] if ts > week_cutoff])
        
        return {
            "platform": platform,
            "requests_today": requests_today,
            "requests_this_week": requests_this_week,
            "daily_cap": self.DAILY_CAP,
            "remaining_today": max(0, self.DAILY_CAP - requests_today),
            "consecutive_failures": self.consecutive_failures[platform]
        }
    
    def get_all_stats(self) -> dict:
        """
        Get statistics for all platforms.
        
        Returns:
            Dictionary with stats for each platform
        """
        all_platforms = set(self.request_history.keys()) | set(self.last_request_time.keys())
        
        return {
            platform: self.get_stats(platform)
            for platform in all_platforms
        }


class DailyCapExceeded(Exception):
    """Raised when daily request cap is exceeded."""
    
    def __init__(self, platform: str, cap: int):
        self.platform = platform
        self.cap = cap
        super().__init__(
            f"Daily cap exceeded for {platform}: {cap} videos/day. "
            f"Try again tomorrow or set CLIPSCRIBE_DAILY_CAP higher."
        )


class PossibleBanDetected(Exception):
    """Raised when consecutive failures suggest IP/account ban."""
    
    def __init__(self, platform: str, failures: int):
        self.platform = platform
        self.failures = failures
        super().__init__(
            f"Possible ban detected on {platform}: {failures} consecutive failures. "
            f"Your IP may be temporarily blocked. Wait 1-24 hours before retrying."
        )

