# PRD: Playwright Fallback for Bulletproof Download Reliability

**Date:** September 30, 2025  
**Status:** APPROVED - Required for Alpha Launch  
**Priority:** P0 (Blocker with Rate Limiting)  
**Target:** Week 3-4 (October 2025)

## Problem Statement

curl-cffi provides 100% success rate currently, but consultant warns of **10-20% failure risk** as platforms evolve detection methods. Without a fallback, ClipScribe is vulnerable to:

- **YouTube algorithm updates** → Overnight 10-20% failure rate
- **Vimeo detection changes** → Sudden TLS fingerprint blocks
- **Platform-specific issues** → Single point of failure
- **User frustration** → Unreliable service = churn

**Consultant Recommendation:**
> "No fallback risks 10-20% failures. Hybrid: curl-cffi primary (zero config), Playwright fallback for failures. 90-100% success rate target."

## Success Criteria

1. **Automatic Failover**: curl-cffi fails → Playwright triggers automatically
2. **90-100% Success Rate**: Combined success rate across all scenarios
3. **Cost Awareness**: Users warned of $0.10+ cost for Playwright fallback
4. **Performance**: Fallback decision in <1 second
5. **User Control**: Option to disable expensive fallback

## Architecture Design

### High-Level Flow

```
User Request → UniversalVideoClient
    ↓
Try curl-cffi (fast, free)
    ↓
Success? → Return audio file ✓
    ↓
Failure? → Check error type
    ↓
    ├─ Retryable (network)? → Retry curl-cffi (3x)
    ├─ Bot detection (403/429)? → Fallback to Playwright
    └─ Not found (404)? → Fail immediately
    ↓
Playwright download (slow, $0.10+)
    ↓
Success? → Return audio file ✓
    ↓
Failure? → Exhausted all options, fail with clear error
```

### Decision Tree

```python
def should_fallback_to_playwright(error: Exception) -> bool:
    """
    Determine if error warrants expensive Playwright fallback.
    
    Fallback triggers:
    - HTTP 403/429 (bot detection)
    - "bot" in error message
    - "captcha" in error message
    - "verify" in error message
    - Consecutive curl-cffi failures (3+)
    
    Do NOT fallback for:
    - HTTP 404 (video not found)
    - Network timeouts (retry curl-cffi)
    - Invalid URL (fail fast)
    - Geo-restricted (can't help)
    """
    error_str = str(error).lower()
    
    # Bot detection indicators
    if any(keyword in error_str for keyword in ["bot", "captcha", "verify", "403", "429"]):
        return True
    
    # Pattern: "requested format is not available"
    if "requested format" in error_str or "not available" in error_str:
        return True
    
    # Don't fallback for these
    if any(keyword in error_str for keyword in ["404", "not found", "timeout", "geo"]):
        return False
    
    return False
```

## Technical Implementation

### 1. Playwright Downloader Class

```python
# src/clipscribe/retrievers/browser_downloader.py

import asyncio
from playwright.async_api import async_playwright, Browser, Page
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PlaywrightDownloader:
    """
    Browser automation fallback for when curl-cffi fails.
    
    Cost: ~$0.10+ per video (slower, more resource intensive)
    Use: Only when curl-cffi fails with bot detection errors
    
    Features:
    - Full browser rendering (JavaScript, cookies, etc.)
    - Passes all bot detection (looks like real user)
    - Handles video player interactions
    - Extracts media URLs from page
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self._playwright = None
        
    async def __aenter__(self):
        """Context manager entry - start browser."""
        self._playwright = await async_playwright().start()
        
        # Launch Chromium with realistic settings
        self.browser = await self._playwright.chromium.launch(
            headless=True,  # Run without visible window
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--no-sandbox',  # Cloud Run compatibility
                '--disable-dev-shm-usage',  # Docker compatibility
            ]
        )
        logger.info("Playwright browser launched for fallback download")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close browser."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Playwright browser closed")
    
    async def download_with_browser(
        self, 
        video_url: str, 
        output_path: str,
        timeout: int = 60000  # 60 seconds
    ) -> str:
        """
        Download video using full browser automation.
        
        Strategy:
        1. Open page in browser
        2. Wait for video player to load
        3. Extract media URL from network requests
        4. Download media directly
        5. Extract audio with ffmpeg
        
        Returns:
            Path to downloaded audio file
        
        Raises:
            PlaywrightDownloadError: If download fails
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use 'async with' context.")
        
        page = await self.browser.new_page()
        
        try:
            logger.info(f"Playwright: Loading {video_url}")
            
            # Intercept network requests to find media URLs
            media_urls = []
            
            async def capture_media_request(request):
                url = request.url
                # Look for video/audio formats
                if any(ext in url for ext in ['.mp4', '.webm', '.m4a', '.mp3']):
                    media_urls.append(url)
                    logger.debug(f"Captured media URL: {url}")
            
            page.on("request", capture_media_request)
            
            # Navigate to video page
            await page.goto(video_url, timeout=timeout, wait_until="networkidle")
            
            # Wait for video player (platform-specific selectors)
            if "youtube.com" in video_url or "youtu.be" in video_url:
                await page.wait_for_selector("video", timeout=10000)
            elif "vimeo.com" in video_url:
                await page.wait_for_selector(".vp-video", timeout=10000)
            
            # Give network time to capture media URLs
            await asyncio.sleep(2)
            
            if not media_urls:
                raise PlaywrightDownloadError("No media URLs captured from page")
            
            logger.info(f"Playwright: Found {len(media_urls)} media URLs")
            
            # Use yt-dlp with captured cookies/headers from browser
            cookies = await page.context.cookies()
            
            # Download best quality media
            best_media_url = self._select_best_media_url(media_urls)
            
            # Use yt-dlp with browser cookies for authenticated download
            audio_path = await self._download_media_with_cookies(
                best_media_url, 
                output_path, 
                cookies
            )
            
            logger.info(f"Playwright: Successfully downloaded to {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Playwright download failed: {e}")
            raise PlaywrightDownloadError(f"Browser download failed: {e}") from e
        
        finally:
            await page.close()
    
    def _select_best_media_url(self, urls: list) -> str:
        """Select highest quality media URL from captured list."""
        # Prefer audio-only formats
        audio_urls = [u for u in urls if any(ext in u for ext in ['.m4a', '.mp3', '.opus'])]
        if audio_urls:
            return audio_urls[0]
        
        # Fall back to video (will extract audio)
        return urls[0]
    
    async def _download_media_with_cookies(
        self, 
        media_url: str, 
        output_path: str, 
        cookies: list
    ) -> str:
        """Download media using yt-dlp with browser cookies."""
        # Convert Playwright cookies to yt-dlp format
        cookie_file = self._create_cookie_file(cookies)
        
        import yt_dlp
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'cookiefile': cookie_file,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([media_url])
        
        return output_path
    
    def _create_cookie_file(self, cookies: list) -> str:
        """Create Netscape cookie file from Playwright cookies."""
        import tempfile
        
        cookie_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        
        # Netscape cookie format
        cookie_file.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies:
            cookie_file.write(
                f"{cookie['domain']}\tTRUE\t{cookie['path']}\t"
                f"{'TRUE' if cookie.get('secure') else 'FALSE'}\t"
                f"{cookie.get('expires', 0)}\t{cookie['name']}\t{cookie['value']}\n"
            )
        
        cookie_file.close()
        return cookie_file.name


class PlaywrightDownloadError(Exception):
    """Raised when Playwright download fails."""
    pass
```

### 2. Hybrid Downloader with Fallback

```python
# src/clipscribe/retrievers/hybrid_downloader.py

from .universal_video_client import UniversalVideoClient
from .browser_downloader import PlaywrightDownloader, PlaywrightDownloadError
from ..utils.rate_limiter import RateLimiter
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class HybridDownloader:
    """
    Intelligent downloader with automatic fallback.
    
    Strategy:
    1. Try curl-cffi (fast, free, 90% success)
    2. On bot detection → Playwright fallback (slow, $0.10+, 100% success)
    3. Combined: 90-100% success rate
    
    Cost optimization:
    - curl-cffi: $0 extra (just bandwidth)
    - Playwright: ~$0.10/video (warn user)
    """
    
    def __init__(
        self, 
        allow_expensive_fallback: bool = True,
        warn_on_fallback: bool = True
    ):
        self.curl_cffi_client = UniversalVideoClient()
        self.allow_expensive_fallback = allow_expensive_fallback
        self.warn_on_fallback = warn_on_fallback
        self.rate_limiter = RateLimiter()
        
        # Track fallback usage for monitoring
        self.fallback_count = 0
        self.total_downloads = 0
    
    async def download_audio(
        self, 
        video_url: str, 
        output_dir: str
    ) -> Tuple[str, dict]:
        """
        Download audio with automatic fallback.
        
        Returns:
            (audio_path, metadata) tuple
        
        Raises:
            DownloadError: If both methods fail
        """
        self.total_downloads += 1
        
        # Rate limiting
        platform = self._detect_platform(video_url)
        await self.rate_limiter.wait_if_needed(platform)
        
        # Attempt 1: curl-cffi (fast, free)
        logger.info(f"Attempting download with curl-cffi: {video_url}")
        
        try:
            audio_path, metadata = await self.curl_cffi_client.download_audio(
                video_url, output_dir
            )
            
            logger.info(f"✓ curl-cffi download successful: {audio_path}")
            self.rate_limiter.record_request(platform, success=True)
            return audio_path, metadata
            
        except Exception as curl_error:
            logger.warning(f"curl-cffi download failed: {curl_error}")
            self.rate_limiter.record_request(platform, success=False)
            
            # Decide if we should fallback
            if not self._should_fallback(curl_error):
                logger.error(f"Not a fallback scenario, failing: {curl_error}")
                raise
            
            if not self.allow_expensive_fallback:
                logger.error("Fallback disabled by user, failing")
                raise DownloadError(
                    "curl-cffi failed and Playwright fallback is disabled. "
                    "Enable fallback with allow_expensive_fallback=True"
                ) from curl_error
            
            # Warn user about cost
            if self.warn_on_fallback:
                logger.warning(
                    "⚠️  curl-cffi failed - falling back to Playwright browser automation. "
                    "This may cost ~$0.10 extra for this video."
                )
            
            # Attempt 2: Playwright (slow, expensive, reliable)
            logger.info(f"Attempting Playwright fallback: {video_url}")
            self.fallback_count += 1
            
            try:
                async with PlaywrightDownloader() as browser:
                    audio_path = await browser.download_with_browser(
                        video_url, 
                        f"{output_dir}/audio.mp3"
                    )
                
                logger.info(f"✓ Playwright fallback successful: {audio_path}")
                
                # Create minimal metadata
                metadata = {
                    "title": "Unknown (Playwright download)",
                    "source": "playwright_fallback",
                    "url": video_url,
                    "cost_warning": "Expensive fallback used (~$0.10)"
                }
                
                return audio_path, metadata
                
            except PlaywrightDownloadError as playwright_error:
                logger.error(f"Playwright fallback also failed: {playwright_error}")
                raise DownloadError(
                    "Both curl-cffi and Playwright fallback failed. "
                    "Video may be geo-restricted, deleted, or platform issue."
                ) from playwright_error
    
    def _should_fallback(self, error: Exception) -> bool:
        """Determine if error warrants Playwright fallback."""
        error_str = str(error).lower()
        
        # Bot detection indicators
        bot_keywords = ["bot", "captcha", "verify", "403", "429", "requested format", "not available"]
        if any(keyword in error_str for keyword in bot_keywords):
            return True
        
        # Don't fallback for these
        no_fallback_keywords = ["404", "not found", "geo", "private", "deleted"]
        if any(keyword in error_str for keyword in no_fallback_keywords):
            return False
        
        return False
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        elif "vimeo.com" in url:
            return "vimeo"
        elif "tiktok.com" in url:
            return "tiktok"
        return "default"
    
    def get_fallback_stats(self) -> dict:
        """Get fallback usage statistics."""
        fallback_rate = (self.fallback_count / self.total_downloads * 100) if self.total_downloads > 0 else 0
        
        return {
            "total_downloads": self.total_downloads,
            "fallback_count": self.fallback_count,
            "fallback_rate": f"{fallback_rate:.1f}%",
            "curl_cffi_success_rate": f"{100 - fallback_rate:.1f}%"
        }


class DownloadError(Exception):
    """Raised when all download methods fail."""
    pass
```

### 3. Integration with Video Retriever

```python
# Update src/clipscribe/retrievers/video_retriever_v2.py

from .hybrid_downloader import HybridDownloader

class VideoIntelligenceRetrieverV2:
    def __init__(self, allow_expensive_fallback: bool = True):
        # Replace UniversalVideoClient with HybridDownloader
        self.downloader = HybridDownloader(allow_expensive_fallback=allow_expensive_fallback)
        # ... rest of init ...
```

## Implementation Plan

### **Week 2 (Oct 8-14): Playwright Integration**

**Monday-Tuesday (Oct 8-9): Core Playwright Class**
- [ ] Install playwright: `poetry add playwright`
- [ ] Run: `poetry run playwright install chromium`
- [ ] Create `PlaywrightDownloader` class
- [ ] Test basic browser automation
- [ ] Test media URL capture

**Wednesday-Thursday (Oct 10-11): Hybrid Downloader**
- [ ] Create `HybridDownloader` class
- [ ] Implement fallback decision logic
- [ ] Add cost warnings
- [ ] Test with intentional curl-cffi failures

**Friday (Oct 12): Integration & Testing**
- [ ] Replace `UniversalVideoClient` with `HybridDownloader`
- [ ] End-to-end testing
- [ ] Performance benchmarking
- [ ] Cost tracking

### **Week 3 (Oct 15-21): Refinement & Alpha**

**Monday-Tuesday (Oct 15-16): Edge Cases**
- [ ] Test geo-restricted videos
- [ ] Test private/deleted videos
- [ ] Test various platforms (YouTube, Vimeo, TikTok)
- [ ] Refine fallback triggers

**Wednesday-Thursday (Oct 17-18): Monitoring**
- [ ] Add fallback rate metrics
- [ ] Dashboard for fallback usage
- [ ] Cost tracking per user
- [ ] Alert on high fallback rates

**Friday (Oct 19): Alpha Testing Prep**
- [ ] Documentation
- [ ] User guides
- [ ] Feedback forms
- [ ] Final testing

## Testing Strategy

### **Unit Tests**

```python
# tests/unit/test_hybrid_downloader.py

@pytest.mark.asyncio
async def test_curl_cffi_success():
    """Test primary path succeeds."""
    downloader = HybridDownloader()
    
    with patch.object(downloader.curl_cffi_client, 'download_audio') as mock_curl:
        mock_curl.return_value = ("/path/audio.mp3", {"title": "Test"})
        
        audio, meta = await downloader.download_audio("https://youtube.com/watch?v=test", "/tmp")
        
        assert audio == "/path/audio.mp3"
        assert downloader.fallback_count == 0  # No fallback used

@pytest.mark.asyncio
async def test_playwright_fallback_on_bot_detection():
    """Test fallback triggers on 403 error."""
    downloader = HybridDownloader()
    
    with patch.object(downloader.curl_cffi_client, 'download_audio') as mock_curl, \
         patch('clipscribe.retrievers.hybrid_downloader.PlaywrightDownloader') as mock_pw:
        
        # Simulate bot detection error
        mock_curl.side_effect = Exception("HTTP Error 403: Bot detected")
        
        # Mock Playwright success
        mock_pw.return_value.__aenter__.return_value.download_with_browser.return_value = "/path/audio.mp3"
        
        audio, meta = await downloader.download_audio("https://youtube.com/watch?v=test", "/tmp")
        
        assert audio == "/path/audio.mp3"
        assert downloader.fallback_count == 1  # Fallback used
```

### **Integration Tests**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_youtube_download_with_fallback():
    """Test real download with fallback capability."""
    downloader = HybridDownloader()
    
    # Use a known-good test video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    audio, meta = await downloader.download_audio(test_url, "/tmp")
    
    assert os.path.exists(audio)
    assert audio.endswith(".mp3")
    
    # Should succeed with curl-cffi (no fallback)
    assert downloader.fallback_count == 0
```

## Cost Analysis

### **Scenario 1: curl-cffi Only (Current)**
- Cost: $0.027/video (Voxtral + Grok-4)
- Success rate: 90-100% (until detection changes)
- Processing time: 79s

### **Scenario 2: curl-cffi + Playwright Fallback (Proposed)**
- curl-cffi success (90%): $0.027/video
- Playwright fallback (10%): $0.127/video ($0.027 + $0.10 browser cost)
- **Average cost: $0.0343/video** (27% increase)
- Success rate: 99%+
- Processing time: 79s (curl-cffi) or 120s (Playwright)

**Cost breakdown for 1000 videos/month:**
- **Without fallback**: 900 success @ $0.027 = $24.30
- **With fallback**: 900 @ $0.027 + 100 @ $0.127 = $24.30 + $12.70 = **$37.00**
- **Extra cost**: $12.70/month (35% increase) for 10% higher reliability

**Value proposition**: $12.70/month to go from 90% → 99% success rate is excellent ROI.

## User Experience

### **CLI with Fallback**

```bash
$ clipscribe process video https://youtube.com/watch?v=test

⚠️  TERMS OF SERVICE NOTICE ⚠️
ClipScribe uses:
  • Primary: curl-cffi (fast, included in cost)
  • Fallback: Playwright browser (~$0.10 extra if primary fails)
  
Continue? [Y/n] y

Processing: https://youtube.com/watch?v=test
→ Downloading audio...
  ✓ Download successful (curl-cffi)
→ Transcribing with Voxtral...
  ✓ Transcript: 2,290 characters
→ Extracting intelligence with Grok-4...
  ✓ Entities: 11 | Relationships: 10
→ Generating outputs...
  ✓ 5 files created in output/20251001_youtube_test/

Cost: $0.027 | Time: 79s
```

### **With Fallback Triggered**

```bash
$ clipscribe process video https://youtube.com/watch?v=test

Processing: https://youtube.com/watch?v=test
→ Downloading audio...
  ✗ Primary method failed (bot detection)
  ⚠️  Falling back to Playwright browser automation...
  ⚠️  This will cost ~$0.10 extra for this video.
  ✓ Download successful (Playwright fallback)
→ Transcribing with Voxtral...
  ✓ Transcript: 2,290 characters
→ Extracting intelligence with Grok-4...
  ✓ Entities: 11 | Relationships: 10
→ Generating outputs...
  ✓ 5 files created in output/20251001_youtube_test/

Cost: $0.127 (includes $0.10 fallback) | Time: 120s
```

## Success Metrics

- **Success Rate**: 99%+ (combined curl-cffi + Playwright)
- **Fallback Rate**: <20% (ideally <10%)
- **User Satisfaction**: Clear understanding of fallback and costs
- **Cost Control**: Average <$0.04/video including fallbacks
- **Performance**: Fallback adds <45s to processing time

## Dependencies

```toml
# pyproject.toml

[tool.poetry.dependencies]
playwright = "^1.40.0"

[tool.poetry.group.dev.dependencies]
pytest-playwright = "^0.4.3"
```

## Risks & Mitigation

**Risk**: Playwright adds 500MB+ to deployment  
**Mitigation**: Multi-stage Docker builds, lazy install

**Risk**: Playwright may also fail on some platforms  
**Mitigation**: Clear error messages, suggest alternatives

**Risk**: Users surprised by fallback costs  
**Mitigation**: Clear warnings, opt-in for expensive fallback

---

**Status**: Ready for implementation  
**Timeline**: Week 2-3 (Oct 8-19)  
**Owner**: Development team

