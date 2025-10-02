# ClipScribe Implementation Timeline - Option B (Bulletproof)

**Date**: September 30, 2025  
**Decision**: Option B - Build fallback for alpha (bulletproof approach)  
**Timeline**: 3 weeks to alpha-ready  
**Target**: Alpha testing starts Week 4 (Oct 22-28)

---

## Overview

**Goal**: 99%+ success rate before alpha testing begins

**Approach**:
1. **Week 1**: Rate limiting + ToS compliance (simplified, no tiers)
2. **Week 2**: Playwright fallback for reliability
3. **Week 3**: Integration, testing, monitoring
4. **Week 4**: Alpha testing (5-10 users)

**Key Decisions**:
- ✅ No tier system yet (single safe default: 100/day, 1 req/10s)
- ✅ Conservative defaults always
- ✅ Playwright fallback before alpha (not after)
- ✅ 99%+ success rate before user testing

---

## Week 1 (Oct 1-7): Rate Limiting Foundation

### **Day 1-2 (Tue-Wed, Oct 1-2): Simple Rate Limiter**

**Goal**: Core rate limiting without complexity

**Tasks**:
```python
# Create: src/clipscribe/utils/rate_limiter.py

class RateLimiter:
    """
    Simple, conservative rate limiter.
    No tiers, no complexity - just safe defaults.
    """
    
    # Class-level defaults (can override via env)
    REQUEST_DELAY = int(os.getenv("CLIPSCRIBE_REQUEST_DELAY", 10))  # seconds
    DAILY_CAP = int(os.getenv("CLIPSCRIBE_DAILY_CAP", 100))  # videos/day
    
    def __init__(self):
        self.request_history = {}  # platform -> list of timestamps
        self.last_request_time = {}  # platform -> datetime
    
    async def wait_if_needed(self, platform: str):
        """Wait to comply with rate limit."""
        if platform in self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time[platform]).total_seconds()
            if elapsed < self.REQUEST_DELAY:
                wait_time = self.REQUEST_DELAY - elapsed
                logger.info(f"Rate limiting: waiting {wait_time:.1f}s for {platform}")
                await asyncio.sleep(wait_time)
        
        self.last_request_time[platform] = datetime.now()
    
    def check_daily_cap(self, platform: str) -> bool:
        """Check if under daily limit."""
        if platform not in self.request_history:
            return True
        
        # Count requests in last 24 hours
        cutoff = datetime.now() - timedelta(days=1)
        recent = [ts for ts in self.request_history[platform] if ts > cutoff]
        
        if len(recent) >= self.DAILY_CAP:
            logger.warning(f"Daily cap reached for {platform}: {len(recent)}/{self.DAILY_CAP}")
            return False
        
        return True
    
    def record_request(self, platform: str):
        """Record request for tracking."""
        if platform not in self.request_history:
            self.request_history[platform] = []
        
        self.request_history[platform].append(datetime.now())
        
        # Cleanup old entries (keep 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        self.request_history[platform] = [
            ts for ts in self.request_history[platform] if ts > cutoff
        ]
```

**Testing**:
- [ ] Unit test: `test_rate_limiter.py`
- [ ] Test wait logic with mock sleep
- [ ] Test daily cap enforcement
- [ ] Test platform isolation

**Deliverable**: Simple, working rate limiter (150 lines)

---

### **Day 3 (Thu, Oct 3): Integration with UniversalVideoClient**

**Goal**: Add rate limiting to downloads

**Tasks**:
```python
# Modify: src/clipscribe/retrievers/universal_video_client.py

class UniversalVideoClient:
    def __init__(self, use_impersonation: bool = True, impersonate_target: str = "Chrome-131:Macos-14"):
        # ... existing init ...
        self.rate_limiter = RateLimiter()
    
    async def download_audio(self, video_url: str, output_dir: Optional[str] = None):
        # Detect platform
        platform = self._detect_platform(video_url)
        
        # Check daily cap BEFORE waiting
        if not self.rate_limiter.check_daily_cap(platform):
            raise DailyCapExceeded(
                f"Daily limit reached for {platform} ({self.rate_limiter.DAILY_CAP} videos/day). "
                f"Try again tomorrow or set CLIPSCRIBE_DAILY_CAP higher."
            )
        
        # Wait for rate limit
        await self.rate_limiter.wait_if_needed(platform)
        
        try:
            # ... existing download logic ...
            audio_path, metadata = await self._do_download(video_url, output_dir)
            
            # Record successful request
            self.rate_limiter.record_request(platform)
            return audio_path, metadata
            
        except Exception as e:
            # Still record request (counts toward limit)
            self.rate_limiter.record_request(platform)
            raise
    
    def _detect_platform(self, url: str) -> str:
        """Extract platform from URL."""
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        elif "vimeo.com" in url:
            return "vimeo"
        elif "tiktok.com" in url:
            return "tiktok"
        return "other"


class DailyCapExceeded(Exception):
    """Raised when daily cap is reached."""
    pass
```

**Testing**:
- [ ] Integration test with real URLs (mocked download)
- [ ] Test rate limiting in action
- [ ] Test cap enforcement
- [ ] Test platform detection

**Deliverable**: Rate-limited downloads working

---

### **Day 4 (Fri, Oct 4): CLI ToS Warnings**

**Goal**: User education and consent

**Tasks**:
```python
# Modify: src/clipscribe/commands/cli.py

@click.command()
@click.argument("url")
@click.option("--accept-tos", is_flag=True, help="Accept ToS (skip warning)")
@click.option("--quiet", is_flag=True, help="Suppress ToS warning")
def process_video(url: str, accept_tos: bool, quiet: bool):
    """Process a video URL."""
    
    # Show ToS warning on first use (unless --accept-tos)
    if not accept_tos and not quiet:
        show_tos_warning()
        
        if not click.confirm("\nDo you accept these terms?", default=True):
            click.echo("Processing cancelled.")
            return
    
    # ... rest of processing ...


def show_tos_warning():
    """Display ToS compliance notice."""
    click.echo(click.style("\n⚠️  TERMS OF SERVICE NOTICE ⚠️\n", fg="yellow", bold=True))
    click.echo("ClipScribe respects platform Terms of Service with conservative rate limits:")
    click.echo("")
    click.echo(f"  • Rate limit: 1 request every {RateLimiter.REQUEST_DELAY} seconds")
    click.echo(f"  • Daily limit: {RateLimiter.DAILY_CAP} videos per platform")
    click.echo("  • Automatic bot detection bypass (curl-cffi)")
    click.echo("  • Fallback browser automation if needed (~$0.10 extra)")
    click.echo("")
    click.echo("These limits prevent IP bans and account suspensions.")
    click.echo("You can adjust via environment variables:")
    click.echo("  export CLIPSCRIBE_DAILY_CAP=200")
    click.echo("")
```

**Testing**:
- [ ] CLI flow with warning
- [ ] Test --accept-tos flag
- [ ] Test --quiet flag
- [ ] Verify message clarity

**Deliverable**: Clear ToS warnings in place

---

### **Day 5 (Sat-Sun, Oct 5-6): Testing & Documentation**

**Weekend Tasks**:
- [ ] End-to-end testing with real videos
- [ ] Test rate limiting over time
- [ ] Document rate limiter in `docs/TOS_COMPLIANCE.md`
- [ ] Update `docs/GETTING_STARTED.md`
- [ ] Update `README.md` with ToS notice

**Deliverable**: Week 1 complete, ready for Week 2

---

## Week 2 (Oct 8-14): Playwright Fallback

### **Day 1-2 (Mon-Tue, Oct 8-9): Playwright Setup & Core**

**Goal**: Working browser automation

**Tasks**:
```bash
# Install Playwright
poetry add playwright
poetry run playwright install chromium  # ~100MB download
```

```python
# Create: src/clipscribe/retrievers/browser_downloader.py

class PlaywrightDownloader:
    """Browser automation fallback for curl-cffi failures."""
    
    async def __aenter__(self):
        """Start browser."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def download_with_browser(self, video_url: str, output_path: str) -> str:
        """Download video using full browser automation."""
        page = await self.browser.new_page()
        
        try:
            # Navigate to video
            await page.goto(video_url, wait_until="networkidle")
            
            # Wait for video player
            await page.wait_for_selector("video", timeout=10000)
            
            # Extract media URL from network requests
            # ... implementation details ...
            
            # Download with yt-dlp using browser cookies
            # ... implementation details ...
            
            return audio_path
            
        finally:
            await page.close()
```

**Testing**:
- [ ] Test browser launches
- [ ] Test YouTube page load
- [ ] Test Vimeo page load
- [ ] Test media URL capture

**Deliverable**: Working Playwright downloader

---

### **Day 3-4 (Wed-Thu, Oct 10-11): Hybrid Downloader**

**Goal**: Intelligent fallback logic

**Tasks**:
```python
# Create: src/clipscribe/retrievers/hybrid_downloader.py

class HybridDownloader:
    """
    Try curl-cffi first, fallback to Playwright on bot detection.
    
    Success rate: 99%+
    Cost: $0.027 (90% curl-cffi) + $0.127 (10% Playwright) = ~$0.034 avg
    """
    
    def __init__(self, allow_expensive_fallback: bool = True):
        self.curl_cffi_client = UniversalVideoClient()
        self.allow_expensive_fallback = allow_expensive_fallback
        self.fallback_count = 0
        self.total_downloads = 0
    
    async def download_audio(self, video_url: str, output_dir: str):
        self.total_downloads += 1
        
        # Try curl-cffi first
        try:
            audio, meta = await self.curl_cffi_client.download_audio(video_url, output_dir)
            logger.info("✓ curl-cffi download successful")
            return audio, meta
            
        except Exception as e:
            logger.warning(f"curl-cffi failed: {e}")
            
            # Should we fallback?
            if not self._should_fallback(e):
                raise
            
            if not self.allow_expensive_fallback:
                raise DownloadError("Fallback disabled") from e
            
            # Warn user
            logger.warning("⚠️  Falling back to Playwright (~$0.10 extra)")
            
            # Try Playwright
            self.fallback_count += 1
            
            async with PlaywrightDownloader() as browser:
                audio = await browser.download_with_browser(video_url, f"{output_dir}/audio.mp3")
            
            logger.info("✓ Playwright fallback successful")
            return audio, {"source": "playwright_fallback"}
    
    def _should_fallback(self, error: Exception) -> bool:
        """Detect bot detection errors."""
        error_str = str(error).lower()
        
        # Fallback triggers
        if any(kw in error_str for kw in ["bot", "403", "429", "captcha", "verify"]):
            return True
        
        # Don't fallback for these
        if any(kw in error_str for kw in ["404", "not found", "geo"]):
            return False
        
        return False
```

**Testing**:
- [ ] Test curl-cffi success (no fallback)
- [ ] Test forced fallback (mock 403 error)
- [ ] Test fallback disabled
- [ ] Test cost tracking

**Deliverable**: Intelligent hybrid downloader

---

### **Day 5 (Fri, Oct 12): Integration & Testing**

**Goal**: Replace UniversalVideoClient with HybridDownloader

**Tasks**:
```python
# Modify: src/clipscribe/retrievers/video_retriever_v2.py

class VideoIntelligenceRetrieverV2:
    def __init__(self, allow_expensive_fallback: bool = True):
        # Replace: self.downloader = UniversalVideoClient()
        self.downloader = HybridDownloader(allow_expensive_fallback=allow_expensive_fallback)
        # ... rest of init ...
```

**Testing**:
- [ ] End-to-end with YouTube
- [ ] End-to-end with Vimeo
- [ ] Test both curl-cffi and Playwright paths
- [ ] Performance benchmarking
- [ ] Cost tracking

**Deliverable**: Hybrid downloader integrated

---

## Week 3 (Oct 15-21): Polish & Monitoring

### **Day 1-2 (Mon-Tue, Oct 15-16): Edge Cases**

**Goal**: Handle all failure scenarios

**Tasks**:
- [ ] Test geo-restricted videos (clear error)
- [ ] Test private/deleted videos (404)
- [ ] Test age-restricted (needs cookies)
- [ ] Test various platforms (TikTok, Instagram)
- [ ] Refine fallback triggers
- [ ] Add platform-specific handling

**Deliverable**: Robust error handling

---

### **Day 3-4 (Wed-Thu, Oct 17-18): Monitoring & Metrics**

**Goal**: Visibility into fallback usage

**Tasks**:
```python
# Create: src/clipscribe/utils/metrics.py

class DownloadMetrics:
    """Track download statistics."""
    
    def __init__(self):
        self.stats = {
            "curl_cffi_success": 0,
            "curl_cffi_failure": 0,
            "playwright_success": 0,
            "playwright_failure": 0,
            "total_cost": 0.0
        }
    
    def record_curl_cffi_success(self):
        self.stats["curl_cffi_success"] += 1
    
    def record_playwright_fallback(self, success: bool):
        if success:
            self.stats["playwright_success"] += 1
            self.stats["total_cost"] += 0.10
        else:
            self.stats["playwright_failure"] += 1
    
    def get_summary(self) -> dict:
        total = sum([
            self.stats["curl_cffi_success"],
            self.stats["playwright_success"],
            self.stats["playwright_failure"]
        ])
        
        fallback_rate = (
            self.stats["playwright_success"] / total * 100 
            if total > 0 else 0
        )
        
        return {
            "total_downloads": total,
            "success_rate": f"{(self.stats['curl_cffi_success'] + self.stats['playwright_success']) / total * 100:.1f}%",
            "fallback_rate": f"{fallback_rate:.1f}%",
            "total_fallback_cost": f"${self.stats['total_cost']:.2f}"
        }
```

**Tasks**:
- [ ] Add metrics collection
- [ ] CLI command to show stats: `clipscribe stats`
- [ ] Dashboard in logs
- [ ] Alert on high fallback rates (>20%)

**Deliverable**: Monitoring in place

---

### **Day 5 (Fri, Oct 19): Documentation & Prep**

**Goal**: Ready for alpha testing

**Tasks**:
- [ ] Complete user documentation
- [ ] Alpha tester guide
- [ ] Troubleshooting guide
- [ ] Feedback forms
- [ ] Final testing checklist

**Documentation Updates**:
- [ ] `docs/TOS_COMPLIANCE.md` - Complete ToS guide
- [ ] `docs/TROUBLESHOOTING.md` - Fallback scenarios
- [ ] `docs/GETTING_STARTED.md` - Updated with warnings
- [ ] `README.md` - Fallback feature
- [ ] `CHANGELOG.md` - v2.51.2 with rate limiting + fallback

**Deliverable**: Alpha-ready codebase

---

## Week 4 (Oct 22-28): Alpha Testing

### **Alpha Testing Goals**

**Participants**: 5-10 diverse users
- 2-3 students/educators
- 2-3 professionals/analysts
- 1-2 journalists/creators

**Objectives**:
- Validate 99%+ success rate
- Test rate limiting UX
- Measure fallback frequency
- Gather cost feedback
- Identify edge cases

**Success Criteria**:
- Zero IP bans reported
- 95%+ user satisfaction
- <15% fallback rate
- Clear understanding of costs
- No critical bugs

---

## Technical Deliverables Summary

### **Week 1 Deliverables**
- ✅ `src/clipscribe/utils/rate_limiter.py` (150 lines)
- ✅ Rate limiting integrated in `UniversalVideoClient`
- ✅ CLI ToS warnings
- ✅ Documentation: `docs/TOS_COMPLIANCE.md`
- ✅ Tests: `tests/unit/test_rate_limiter.py`

### **Week 2 Deliverables**
- ✅ `src/clipscribe/retrievers/browser_downloader.py` (300 lines)
- ✅ `src/clipscribe/retrievers/hybrid_downloader.py` (200 lines)
- ✅ Playwright integration
- ✅ Fallback logic
- ✅ Tests: `tests/unit/test_hybrid_downloader.py`

### **Week 3 Deliverables**
- ✅ `src/clipscribe/utils/metrics.py` (100 lines)
- ✅ Edge case handling
- ✅ Monitoring dashboard
- ✅ Complete documentation
- ✅ Alpha testing materials

---

## Cost Analysis

### **Development Time**
- **Week 1**: 3 days (rate limiting)
- **Week 2**: 5 days (Playwright fallback)
- **Week 3**: 4 days (polish + monitoring)
- **Total**: ~12 days (2.5 weeks full-time)

### **Operational Costs**

**Infrastructure** (per month):
- Cloud Run: $50-100
- Compute Engine: $100-300 (with Spot VMs)
- Redis: $30-50
- Monitoring: $20-40
- **Total**: $200-490/month

**Per-Video Costs**:
- curl-cffi success (90%): $0.027/video
- Playwright fallback (10%): $0.127/video
- **Average**: $0.0343/video (~27% increase over v2.51.1)

**For 1000 videos/month**:
- curl-cffi only: $27.00
- With 10% fallback: **$37.00** (+$10/month for 99% reliability)

**ROI**: $10/month to go from 90% → 99% success = **excellent value**

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Week 1 delay | Medium | Low | Simple design, no tiers |
| Playwright complexity | Medium | Medium | Well-documented library |
| Fallback rate >20% | Low | Medium | Conservative curl-cffi triggers |
| Alpha user confusion | Medium | Low | Clear documentation + warnings |
| Cost overruns | Low | Low | Transparent cost tracking |

---

## Success Metrics

### **Week 1 Success**
- ✅ Rate limiter functional
- ✅ ToS warnings clear
- ✅ No code complexity
- ✅ Tests passing

### **Week 2 Success**
- ✅ Playwright working
- ✅ Fallback logic solid
- ✅ 99%+ success rate
- ✅ Cost tracking accurate

### **Week 3 Success**
- ✅ Edge cases handled
- ✅ Monitoring operational
- ✅ Documentation complete
- ✅ Ready for alpha

### **Week 4 Success**
- ✅ 5-10 alpha testers onboarded
- ✅ 99%+ success rate confirmed
- ✅ <15% fallback rate
- ✅ Zero IP bans
- ✅ Positive feedback

---

## Next Steps (Tomorrow Morning)

**Tuesday, Oct 1 - 9am:**
1. ☕ Review this timeline
2. 💻 Create `src/clipscribe/utils/rate_limiter.py`
3. ✅ Write first test: `test_rate_limiter.py`
4. 🚀 Begin implementation

**By EOD Tuesday:**
- [ ] Core `RateLimiter` class complete
- [ ] Unit tests passing
- [ ] Platform detection logic

**Ready to start?** 🚀

---

**Status**: Approved for implementation  
**Timeline**: 3 weeks to alpha  
**Confidence**: HIGH (simplified approach, proven technologies)

