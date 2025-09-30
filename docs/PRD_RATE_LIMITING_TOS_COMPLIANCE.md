# PRD: Rate Limiting & ToS Compliance System

**Date:** September 30, 2025  
**Status:** URGENT - Required for Alpha Launch  
**Priority:** P0 (Blocker)  
**Target:** Month 1 (October 2025)

## Problem Statement

ClipScribe's curl-cffi bot detection bypass works perfectly (100% success rate), but violates YouTube and Vimeo Terms of Service for automated scraping. Without rate limiting:
- **YouTube**: Automated scraping prohibited (ToS effective March 17, 2025) → IP/account bans at ~200-500 req/day
- **Vimeo**: Mass scraping flagged without consent → Blocks for high-volume access
- **Risk**: User IP bans, account suspensions, platform blocks

**Consultant Recommendation:**
> "Implement caps/alerts to stay aware. Enforce 1 req/5-10s, cap 100-200/day/IP to respect ToS boundaries."

## Success Criteria

1. **Rate Limiting**: 1 req/5-10s delay (configurable)
2. **Daily Caps**: 100-200 videos/day per platform per IP
3. **Ban Detection**: Alert on HTTP 403/429 patterns
4. **User Education**: Clear ToS warnings
5. **Monitoring**: Real-time compliance dashboard

## Technical Design

### 1. Rate Limiter Class

```python
# src/clipscribe/utils/rate_limiter.py

from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from typing import Dict, List, Tuple

class PlatformRateLimiter:
    """
    Rate limiter with per-platform caps and ToS compliance.
    
    Features:
    - Per-platform request delays (1 req/5-10s)
    - Daily request caps (100-200/day)
    - Rolling window tracking
    - Ban detection (consecutive 403/429)
    - User tier support (student/pro/enterprise)
    """
    
    def __init__(self):
        self.request_delay = {
            "youtube": 10,  # Conservative: 1 req/10s
            "vimeo": 8,
            "default": 5
        }
        
        self.daily_caps = {
            "youtube": 150,  # Conservative to avoid bans
            "vimeo": 100,
            "default": 80
        }
        
        # Tier multipliers
        self.tier_multipliers = {
            "student": 0.5,      # 75 YouTube/day
            "professional": 1.0,  # 150 YouTube/day
            "enterprise": 2.0    # 300 YouTube/day
        }
        
        # Tracking
        self.request_history: Dict[str, List[Tuple[datetime, bool]]] = defaultdict(list)
        self.consecutive_failures: Dict[str, int] = defaultdict(int)
        
    async def wait_if_needed(self, platform: str, tier: str = "professional"):
        """Wait for rate limit compliance before proceeding."""
        delay = self.request_delay.get(platform, self.request_delay["default"])
        
        # Check last request time
        if platform in self.request_history and self.request_history[platform]:
            last_request_time, _ = self.request_history[platform][-1]
            time_since_last = (datetime.now() - last_request_time).total_seconds()
            
            if time_since_last < delay:
                wait_time = delay - time_since_last
                logger.info(f"Rate limiting: waiting {wait_time:.1f}s for {platform}")
                await asyncio.sleep(wait_time)
        
    def check_daily_cap(self, platform: str, tier: str = "professional") -> bool:
        """Check if daily cap reached for platform."""
        cap = self.daily_caps.get(platform, self.daily_caps["default"])
        cap *= self.tier_multipliers.get(tier, 1.0)
        
        # Count requests in last 24 hours
        cutoff = datetime.now() - timedelta(days=1)
        recent_requests = [
            req for req in self.request_history[platform]
            if req[0] > cutoff
        ]
        
        if len(recent_requests) >= cap:
            logger.warning(f"Daily cap reached for {platform}: {len(recent_requests)}/{cap}")
            return False
        
        return True
    
    def record_request(self, platform: str, success: bool):
        """Record request outcome for tracking."""
        self.request_history[platform].append((datetime.now(), success))
        
        if not success:
            self.consecutive_failures[platform] += 1
            if self.consecutive_failures[platform] >= 3:
                logger.error(f"Ban detection: 3 consecutive failures on {platform}")
                # Trigger alert
        else:
            self.consecutive_failures[platform] = 0
        
        # Cleanup old history (keep 7 days)
        cutoff = datetime.now() - timedelta(days=7)
        self.request_history[platform] = [
            req for req in self.request_history[platform]
            if req[0] > cutoff
        ]
```

### 2. Integration with UniversalVideoClient

```python
# src/clipscribe/retrievers/universal_video_client.py

from ..utils.rate_limiter import PlatformRateLimiter

class UniversalVideoClient:
    def __init__(self, use_impersonation: bool = True, impersonate_target: str = "Chrome-131:Macos-14", user_tier: str = "professional"):
        # ... existing init ...
        self.rate_limiter = PlatformRateLimiter()
        self.user_tier = user_tier
    
    async def download_audio(
        self, video_url: str, output_dir: Optional[str] = None
    ) -> Tuple[str, VideoMetadata]:
        # Detect platform
        platform = self._detect_platform(video_url)
        
        # Check daily cap
        if not self.rate_limiter.check_daily_cap(platform, self.user_tier):
            raise RateLimitExceeded(
                f"Daily cap reached for {platform}. "
                f"Upgrade to higher tier or try again tomorrow."
            )
        
        # Wait for rate limit
        await self.rate_limiter.wait_if_needed(platform, self.user_tier)
        
        try:
            # ... existing download logic ...
            audio_path, metadata = await self._do_download(video_url, output_dir)
            
            # Record success
            self.rate_limiter.record_request(platform, success=True)
            return audio_path, metadata
            
        except Exception as e:
            # Record failure
            self.rate_limiter.record_request(platform, success=False)
            
            # Check for ban indicators
            if "403" in str(e) or "429" in str(e) or "bot" in str(e).lower():
                logger.error(f"Possible ban detected on {platform}: {e}")
                # Trigger alert
            
            raise
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        elif "vimeo.com" in url:
            return "vimeo"
        elif "tiktok.com" in url:
            return "tiktok"
        else:
            return "default"
```

### 3. User Warnings & Education

```python
# src/clipscribe/commands/cli.py

@click.command()
@click.argument("url")
@click.option("--tier", default="professional", type=click.Choice(["student", "professional", "enterprise"]))
@click.option("--accept-tos", is_flag=True, help="Accept ToS and rate limiting")
def process_video(url: str, tier: str, accept_tos: bool):
    """Process a video URL."""
    
    if not accept_tos:
        click.echo(click.style("\n⚠️  TERMS OF SERVICE WARNING ⚠️\n", fg="yellow", bold=True))
        click.echo("ClipScribe respects platform Terms of Service:")
        click.echo("")
        click.echo("• YouTube: Automated scraping is prohibited (ToS March 17, 2025)")
        click.echo("• Vimeo: Mass scraping requires consent")
        click.echo("")
        click.echo(f"Your tier '{tier}' has the following limits:")
        click.echo(f"  - YouTube: {int(150 * tier_multiplier(tier))} videos/day")
        click.echo(f"  - Vimeo: {int(100 * tier_multiplier(tier))} videos/day")
        click.echo(f"  - Rate: 1 request every 5-10 seconds")
        click.echo("")
        click.echo("Exceeding these limits may result in IP/account bans.")
        click.echo("")
        
        if not click.confirm("Do you accept these terms and limits?"):
            click.echo("Aborted.")
            return
    
    # Proceed with processing
    # ...
```

## Implementation Plan

### Week 1 (Oct 1-7):
- [ ] Create `PlatformRateLimiter` class
- [ ] Integrate with `UniversalVideoClient`
- [ ] Add platform detection logic
- [ ] Implement ToS warnings in CLI

### Week 2 (Oct 8-14):
- [ ] Build monitoring dashboard
- [ ] Add ban detection alerts
- [ ] Create user documentation
- [ ] Test with alpha users

### Week 3 (Oct 15-21):
- [ ] Refine rate limits based on feedback
- [ ] Add tier management system
- [ ] Implement cooldown periods
- [ ] Production deployment

## Testing Strategy

1. **Rate Limit Testing**:
   - Verify 1 req/5-10s delay
   - Test daily cap enforcement
   - Validate tier multipliers

2. **Ban Detection**:
   - Simulate 403/429 responses
   - Test consecutive failure alerts
   - Verify cooldown logic

3. **User Experience**:
   - Test ToS warning flow
   - Validate error messages
   - Check tier limits display

## Success Metrics

- **Compliance**: Zero IP/account bans reported
- **User Satisfaction**: Clear understanding of limits
- **Reliability**: Rate limiter 100% functional
- **Monitoring**: Real-time compliance visibility

## Dependencies

- No new external dependencies
- Uses existing asyncio, datetime, logging

## Risks & Mitigation

**Risk**: Users frustrated by rate limits
**Mitigation**: Clear communication, tier upgrades, respectful defaults

**Risk**: Platform detection errors
**Mitigation**: Fallback to conservative "default" limits

**Risk**: Rate limits too restrictive
**Mitigation**: Tiered approach, user feedback in alpha

---

**Status**: Ready for implementation
**Owner**: Development team
**Timeline**: 3 weeks (Month 1)

