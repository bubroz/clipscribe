"""
PO Token Manager for YouTube Access.

Automates extraction and rotation of YouTube Proof of Origin (PO) tokens
to bypass bot detection and ensure reliable video downloads.
"""

import asyncio
import json
import logging
import os
import random
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


@dataclass
class POToken:
    """Represents a YouTube PO token with metadata."""
    po_token: str
    visitor_data: str
    extracted_at: datetime
    ttl_seconds: int = 21600  # 6 hours default
    profile_id: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        age = datetime.now() - self.extracted_at
        return age.total_seconds() > self.ttl_seconds
    
    @property
    def should_rotate(self) -> bool:
        """Check if token should be rotated (50% of TTL)."""
        age = datetime.now() - self.extracted_at
        return age.total_seconds() > (self.ttl_seconds * 0.5)
    
    def to_yt_dlp_args(self) -> str:
        """Format token for yt-dlp extractor args."""
        return f"youtube:po_token=web.gvs+{self.po_token};visitor_data={self.visitor_data}"


class POTokenManager:
    """
    Manages YouTube PO tokens with automatic extraction and rotation.
    
    Features:
    - Headless Chrome extraction via Selenium
    - Proactive token rotation
    - Multiple profile support
    - Thread-safe token management
    - Stealth mode to avoid detection
    """
    
    def __init__(
        self,
        max_profiles: int = 3,
        ttl_seconds: int = 21600,  # 6 hours
        rotation_interval: int = 10800,  # 3 hours
        cache_dir: Optional[Path] = None,
        enable_stealth: bool = True
    ):
        """
        Initialize PO Token Manager.
        
        Args:
            max_profiles: Maximum number of Chrome profiles
            ttl_seconds: Token time-to-live in seconds
            rotation_interval: How often to rotate tokens
            cache_dir: Directory for caching tokens
            enable_stealth: Use selenium-stealth to avoid detection
        """
        self.max_profiles = max_profiles
        self.ttl_seconds = ttl_seconds
        self.rotation_interval = rotation_interval
        self.cache_dir = cache_dir or Path.home() / ".clipscribe" / "po_tokens"
        self.enable_stealth = enable_stealth
        
        # Token storage
        self.tokens: List[POToken] = []
        self.lock = threading.Lock()
        
        # Background rotation
        self.rotation_thread: Optional[threading.Thread] = None
        self.stop_rotation = threading.Event()
        
        # Setup
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_cached_tokens()
        
        # Try to import selenium-stealth if enabled
        if self.enable_stealth:
            try:
                from selenium_stealth import stealth
                self.stealth = stealth
            except ImportError:
                logger.warning("selenium-stealth not installed, running without stealth mode")
                self.enable_stealth = False
                self.stealth = None
    
    def start(self):
        """Start background token rotation."""
        if not self.rotation_thread or not self.rotation_thread.is_alive():
            self.stop_rotation.clear()
            self.rotation_thread = threading.Thread(target=self._rotation_worker, daemon=True)
            self.rotation_thread.start()
            logger.info("PO Token rotation started")
    
    def stop(self):
        """Stop background token rotation."""
        if self.rotation_thread and self.rotation_thread.is_alive():
            self.stop_rotation.set()
            self.rotation_thread.join(timeout=5)
            logger.info("PO Token rotation stopped")
    
    def get_token(self) -> Optional[POToken]:
        """
        Get a valid PO token.
        
        Returns:
            Valid POToken or None if unavailable
        """
        with self.lock:
            # Find first non-expired token
            for token in self.tokens:
                if not token.is_expired:
                    logger.debug(f"Using token from profile {token.profile_id}")
                    return token
        
        # No valid token, try to extract one
        logger.info("No valid token available, extracting new one")
        new_token = self._extract_token(profile_id=0)
        if new_token:
            with self.lock:
                self.tokens.append(new_token)
                self._save_cached_tokens()
        return new_token
    
    def _rotation_worker(self):
        """Background worker for token rotation."""
        while not self.stop_rotation.is_set():
            try:
                self._rotate_tokens()
            except Exception as e:
                logger.error(f"Token rotation error: {e}")
            
            # Sleep for rotation interval
            self.stop_rotation.wait(self.rotation_interval)
    
    def _rotate_tokens(self):
        """Rotate tokens that need refreshing."""
        tokens_to_rotate = []
        
        with self.lock:
            for i, token in enumerate(self.tokens):
                if token.should_rotate:
                    tokens_to_rotate.append((i, token.profile_id))
        
        # Rotate tokens outside lock
        for idx, profile_id in tokens_to_rotate:
            logger.info(f"Rotating token for profile {profile_id}")
            new_token = self._extract_token(profile_id)
            
            if new_token:
                with self.lock:
                    if idx < len(self.tokens):
                        self.tokens[idx] = new_token
                    self._save_cached_tokens()
                logger.info(f"Token rotated for profile {profile_id}")
            else:
                logger.error(f"Failed to rotate token for profile {profile_id}")
    
    def _extract_token(self, profile_id: int = 0) -> Optional[POToken]:
        """
        Extract PO token from YouTube.
        
        Args:
            profile_id: Chrome profile ID to use
            
        Returns:
            Extracted POToken or None on failure
        """
        driver = None
        try:
            # Setup Chrome options
            options = self._get_chrome_options(profile_id)
            driver = webdriver.Chrome(options=options)
            
            # Apply stealth if available
            if self.enable_stealth and self.stealth:
                self.stealth(
                    driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )
            
            # Navigate to YouTube embed page (less suspicious than main site)
            embed_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"  # Rick Roll for testing
            driver.get(embed_url)
            
            # Wait for page load
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Extract tokens from page context
            po_token, visitor_data = self._extract_from_page(driver)
            
            if po_token and visitor_data:
                token = POToken(
                    po_token=po_token,
                    visitor_data=visitor_data,
                    extracted_at=datetime.now(),
                    ttl_seconds=self.ttl_seconds,
                    profile_id=profile_id
                )
                logger.info(f"Successfully extracted PO token for profile {profile_id}")
                return token
            else:
                logger.error(f"Failed to extract tokens from page for profile {profile_id}")
                return None
                
        except Exception as e:
            logger.error(f"Token extraction failed for profile {profile_id}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def _extract_from_page(self, driver) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract PO token and visitor data from page.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            Tuple of (po_token, visitor_data) or (None, None)
        """
        try:
            # Method 1: Check localStorage
            po_token = driver.execute_script("return localStorage.getItem('po_token');")
            visitor_data = driver.execute_script("return localStorage.getItem('visitor_data');")
            
            if po_token and visitor_data:
                return po_token, visitor_data
            
            # Method 2: Parse from page scripts
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                content = script.get_attribute("innerHTML")
                if not content:
                    continue
                
                # Look for PO token pattern
                po_match = re.search(r'"poToken":"([^"]+)"', content)
                visitor_match = re.search(r'"visitorData":"([^"]+)"', content)
                
                if po_match and visitor_match:
                    return po_match.group(1), visitor_match.group(1)
            
            # Method 3: Check cookies
            cookies = driver.get_cookies()
            po_token = None
            visitor_data = None
            
            for cookie in cookies:
                if cookie['name'] == '__Secure-YEC':
                    # Extract from YEC cookie
                    value = unquote(cookie['value'])
                    po_match = re.search(r'po_token=([^&]+)', value)
                    if po_match:
                        po_token = po_match.group(1)
                elif cookie['name'] == 'VISITOR_INFO1_LIVE':
                    visitor_data = cookie['value']
            
            if po_token and visitor_data:
                return po_token, visitor_data
            
            logger.warning("Could not extract tokens from any source")
            return None, None
            
        except Exception as e:
            logger.error(f"Token extraction from page failed: {e}")
            return None, None
    
    def _get_chrome_options(self, profile_id: int) -> Options:
        """
        Get Chrome options for headless extraction.
        
        Args:
            profile_id: Profile ID for isolation
            
        Returns:
            Configured Chrome options
        """
        options = Options()
        
        # Headless mode
        options.add_argument("--headless=new")  # New headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Window size
        options.add_argument("--window-size=1920,1080")
        
        # User agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # Profile isolation
        profile_dir = self.cache_dir / f"profile_{profile_id}"
        profile_dir.mkdir(exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Additional stealth options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        return options
    
    def _load_cached_tokens(self):
        """Load cached tokens from disk."""
        cache_file = self.cache_dir / "tokens.json"
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            for token_data in data:
                token = POToken(
                    po_token=token_data['po_token'],
                    visitor_data=token_data['visitor_data'],
                    extracted_at=datetime.fromisoformat(token_data['extracted_at']),
                    ttl_seconds=token_data.get('ttl_seconds', self.ttl_seconds),
                    profile_id=token_data.get('profile_id', 0)
                )
                if not token.is_expired:
                    self.tokens.append(token)
            
            logger.info(f"Loaded {len(self.tokens)} cached tokens")
        except Exception as e:
            logger.error(f"Failed to load cached tokens: {e}")
    
    def _save_cached_tokens(self):
        """Save tokens to disk cache."""
        cache_file = self.cache_dir / "tokens.json"
        
        try:
            data = []
            for token in self.tokens:
                if not token.is_expired:
                    data.append({
                        'po_token': token.po_token,
                        'visitor_data': token.visitor_data,
                        'extracted_at': token.extracted_at.isoformat(),
                        'ttl_seconds': token.ttl_seconds,
                        'profile_id': token.profile_id
                    })
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(data)} tokens to cache")
        except Exception as e:
            logger.error(f"Failed to save cached tokens: {e}")


# Global instance for easy access
_manager: Optional[POTokenManager] = None


def get_manager() -> POTokenManager:
    """Get or create the global PO Token Manager."""
    global _manager
    if _manager is None:
        # Load from environment
        max_profiles = int(os.getenv("PO_TOKEN_MAX_PROFILES", "3"))
        ttl_seconds = int(os.getenv("PO_TOKEN_TTL", "21600"))  # 6 hours
        rotation_interval = int(os.getenv("PO_TOKEN_ROTATION", "10800"))  # 3 hours
        
        _manager = POTokenManager(
            max_profiles=max_profiles,
            ttl_seconds=ttl_seconds,
            rotation_interval=rotation_interval
        )
        _manager.start()
    
    return _manager
