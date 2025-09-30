# ClipScribe: Bot Detection Problem - External Consultation Brief

**Date:** September 30, 2025  
**For:** Third-party engineering consultation  
**Context:** Video intelligence extraction platform blocked by bot detection

---

## 1. WHO (Stakeholders & System)

### Project: ClipScribe
- **Purpose**: Automated video intelligence extraction (transcription → entity/relationship extraction → knowledge graphs)
- **Target Users**: DoD/IC analysts, researchers, OSINT investigators
- **Current Status**: Private alpha, v2.51.0

### Technology Stack
- **Language**: Python 3.12 with Poetry
- **Download**: yt-dlp v2025.08.27 (Python library for 1800+ video platforms)
- **Transcription**: Voxtral (Mistral's speech-to-text API) - $0.001/min
- **Extraction**: Grok-4 (xAI's LLM) - extracts entities, relationships
- **Audio Processing**: ffmpeg for video → audio conversion

### What's Working vs. Broken
| Component | Status | Evidence |
|-----------|--------|----------|
| Intelligence Pipeline | ✅ 100% FUNCTIONAL | Processed test video successfully |
| Voxtral Transcription | ✅ WORKING | 3368 chars extracted, English detected |
| Grok-4 Extraction | ✅ WORKING | 11 entities, 8 relationships extracted |
| Knowledge Graph | ✅ WORKING | Built 11-node graph successfully |
| ffmpeg Audio Extraction | ✅ WORKING | Successfully converted mp4 → mp3 |
| **Video Downloads** | ❌ **BLOCKED** | **Bot detection on ALL platforms** |

---

## 2. WHAT (The Problem)

### Symptom: Cannot Download Videos from Any Platform

**YouTube Error:**
```
ERROR: [youtube] 5Fy2y3vzkWE: Requested format is not available
Available formats: 0 audio/video, 4 image storyboards only
```

**Vimeo Error:**
```
ERROR: [vimeo] 148751763: This request has been blocked due to its TLS fingerprint.
Install a required impersonation dependency if possible...
```

### Root Cause: Multi-Layered Bot Detection

Modern video platforms detect automation through:

1. **TLS Fingerprinting** (Vimeo, others)
   - Analyzes SSL/TLS client hello signature
   - yt-dlp's fingerprint is known and blocked
   - Detects before any HTTP request

2. **SABR - Server-Side Ad-Brokered Requests** (YouTube)
   - Removes all streamable formats from API response
   - Only returns image storyboards (thumbnails)
   - JavaScript signature (`nsig`) decryption fails

3. **Request Pattern Analysis** (All platforms)
   - Header timing and order detection
   - User-Agent consistency validation
   - Cookie/session validation

### Current Mitigation Attempts (ALL FAILED)
Our code already implements:
```python
# Browser cookie extraction
opts["cookiesfrombrowser"] = ("chrome", chrome_profile_path)

# Mobile web client
opts["extractor_args"]["youtube"].append("player_client=mweb")

# Browser headers
opts["http_headers"] = {
    "User-Agent": "Mozilla/5.0 (Macintosh; ...) Chrome/120.0.0.0",
    "Accept": "text/html,application/xhtml+xml,...",
    # ... full browser header set
}
```

**Result:** Still blocked on YouTube and Vimeo.

---

## 3. WHERE (Scope & Environment)

### Platforms Tested
- **YouTube**: ❌ SABR bot detection (no formats available)
- **Vimeo**: ❌ TLS fingerprinting (request blocked)
- **Others**: Untested, but likely similar

### Environment
- **OS**: macOS 24.6.0
- **Network**: Residential IP (not datacenter)
- **Browser**: Chrome installed with active session
- **Python**: 3.12 in Poetry virtualenv
- **yt-dlp**: v2025.08.27 (latest stable)

### What Works
When we **manually** extract audio from a cached video file using ffmpeg, then process it:
```bash
# Manual extraction works
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3

# Processing works perfectly
Result: ✅ 3368 chars transcribed, 11 entities, 8 relationships, $0.214 cost
```

**Conclusion**: Pipeline is 100% functional, ONLY download is blocked.

---

## 4. WHEN (Timeline & Patterns)

### When Does It Fail?
- **Immediately** on yt-dlp format extraction
- **Before** any download attempt
- **Every time** regardless of video (public, no restrictions)
- **All platforms** using modern bot detection

### Timeline Context
- **v2.51.0 committed**: September 5, 2025 ("pipeline complete")
- **Never validated end-to-end** until today (September 30)
- **Assumed YouTube-specific**: Planned PO token solution
- **Today's discovery**: Problem is platform-wide, not YouTube-specific

### Bot Detection Evolution
- **2024-2025**: YouTube rolled out SABR
- **2025**: Vimeo implemented TLS fingerprinting
- **Trend**: Increasing sophistication across platforms

---

## 5. WHY (Business Impact & Technical Reasons)

### Business Impact
- **CRITICAL**: Cannot process 80%+ of target content (YouTube/Vimeo)
- **Blocking**: Multi-video batch processing feature (Phase 2)
- **User Friction**: Manual download required (not automated)
- **Reputation**: "1800+ platform support" claim is misleading

### Technical Reasons for Detection

#### Why yt-dlp Gets Detected
1. **Known TLS Fingerprint**: Python's SSL library has identifiable signature
2. **Missing Browser Features**: No JavaScript execution, WebGL, Canvas fingerprinting
3. **Request Timing**: Too fast, too consistent
4. **Header Inconsistencies**: Even with browser headers, order/timing differs

#### Why Our Workarounds Failed
| Workaround | Why It Failed |
|------------|---------------|
| Browser cookies | Cookies don't include session tokens YouTube needs |
| Custom headers | Timing and order still detectable |
| mweb client | YouTube now blocks mweb for SABR-protected content |
| Residential IP | TLS fingerprint detected before IP matters |

---

## 6. HOW (Solution Options & Questions)

### Option 1: Impersonation Library (QUICK TEST)
**Approach**: Install `curl-cffi` to mimic browser TLS signature

```bash
poetry add curl-cffi
# yt-dlp auto-detects and uses it
```

**Pros:**
- Lightweight (no browser)
- Fast (native performance)
- Easy to test (1-2 days)

**Cons:**
- May still be detected
- Fingerprint ages as browsers update
- Not guaranteed to work long-term

**Question for Engineer**: Is `curl-cffi` or `python-tls-client` effective against modern TLS fingerprinting, or is this a temporary workaround?

---

### Option 2: Browser Automation (ROBUST)
**Approach**: Use Selenium/Playwright to control real Chrome browser

```python
from playwright.async_api import async_playwright

async def download_with_browser(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        # Trigger download, extract audio
```

**Pros:**
- Real browser = no TLS fingerprinting
- JavaScript execution (passes all checks)
- Works on ALL platforms
- Long-term stable

**Cons:**
- Heavy (100-500MB RAM per browser)
- Slower (real browser overhead)
- Complex management (browser updates, crashes)

**Questions for Engineer**:
1. Is headless Chrome still detectable via navigator.webdriver, Canvas fingerprinting, etc.?
2. Should we use `undetected-chromedriver` or similar anti-detection patches?
3. For production, how do we manage browser instances (pool, cleanup, memory)?

---

### Option 3: Paid Proxies (REJECTED)
**Approach**: Rotate through residential proxy IPs

**Cost Analysis:**
- Residential proxies: $3-15/GB
- Average video: ~50MB download
- Cost per video: $0.15-0.75
- Current target: $0.02-0.04/video

**Verdict**: Breaks cost model by 5-20x. NOT VIABLE.

---

### Option 4: Official APIs (LIMITED)
**Approach**: Use platform APIs instead of scraping

**Reality Check:**
- YouTube Data API: ❌ Doesn't provide download access
- Vimeo API: ❌ Requires paid tier, limited to own videos
- Most platforms: ❌ No download API exists

**Verdict**: NOT VIABLE for download use case.

---

## Key Questions for Third-Party Engineer

### 1. TLS Fingerprinting Solution
**Q**: Is `curl-cffi` effective against Vimeo's TLS fingerprinting in 2025, or will it be detected quickly?

**Context**: Vimeo explicitly says "Install a required impersonation dependency" in error message, suggesting they know about `curl-cffi`.

---

### 2. Browser Automation Viability
**Q**: For production use (100-1000 videos/day), is Playwright/Selenium with anti-detection patches (like `undetected-chromedriver`) a sustainable solution?

**Concerns**:
- Detection via `navigator.webdriver`
- Canvas/WebGL fingerprinting
- Browser memory/CPU overhead at scale

---

### 3. Hybrid Approach Feasibility
**Q**: Should we use a **hybrid strategy**?
- Impersonation library (fast path)
- Browser automation (fallback when detected)
- Exponential backoff on detection

**Trade-offs**: Complexity vs. reliability

---

### 4. Alternative Architectures
**Q**: Are there fundamentally different approaches we're missing?

**Examples**:
- Browser extension that intercepts downloads?
- Desktop app with embedded browser?
- Cloud-based browser pool service?

---

### 5. Long-Term Sustainability
**Q**: In your experience, how often do bot detection systems evolve?

**Planning**: Should we design for 6 months? 2 years? Continuous adaptation?

---

## Current Workaround (Available Today)

**Manual Download Pipeline**:
1. User downloads video from platform (browser)
2. User provides local file to ClipScribe
3. ClipScribe processes (we proved this works)

**Pros**: Works today, zero detection issues  
**Cons**: Not automated, user friction, doesn't scale

---

## Cost Concern (Secondary Issue)

Current cost is **$0.214 for 2.9-minute video** (~$0.074/minute).

**Target**: $0.02-0.04/video  
**Actual**: 5-10x over target

**Breakdown**:
- Voxtral: $0.003 (transcription)
- Grok-4: $0.211 (extraction) ← **98% of cost**

**Question**: Is there a cheaper extraction model we should consider, or are shorter prompts the solution?

---

## Test Results Summary

| Test | Platform | Result | Conclusion |
|------|----------|--------|------------|
| 1 | YouTube | ❌ SABR blocking | No formats available |
| 2 | Local .mp4 | ❌ Wrong format | Test design issue (fixed) |
| 3 | Vimeo | ❌ TLS fingerprint | Platform-wide detection |
| 4 | Extracted audio | ✅ **SUCCESS** | **Pipeline 100% functional** |

---

## Recommendation Sought

**Given**:
- Pipeline is functional
- Bot detection is platform-wide
- Need automated solution for production

**Please advise**:
1. Best immediate solution (impersonation vs browser)
2. Production-ready architecture for scale
3. Expected longevity of each approach
4. Any alternative strategies we haven't considered

---

## Attached Reference Files (if needed)

1. **BASELINE_VALIDATION_RESULTS.md** - Complete test results and analysis
2. **universal_video_client.py (excerpt)** - Current download implementation with workarounds
3. **Test output logs** - Actual error messages from YouTube, Vimeo
4. **Cost breakdown** - Detailed processing costs
5. **Pipeline architecture diagram** - Visual of working components

---

**Contact**: Available for follow-up questions  
**Timeline**: Need solution direction this week to unblock Phase 2 development  
**Budget**: Open to reasonable infrastructure costs, but must maintain cost-per-video economics
