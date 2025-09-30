# Reference Files for External Consultant

These files provide technical context without requiring codebase access.

---

## 1. Test Output: YouTube SABR Detection

```bash
$ yt-dlp --list-formats "https://www.youtube.com/watch?v=5Fy2y3vzkWE"

[youtube] Extracting URL: https://www.youtube.com/watch?v=5Fy2y3vzkWE
[youtube] 5Fy2y3vzkWE: Downloading webpage
[youtube] 5Fy2y3vzkWE: Downloading tv simply player API JSON
[youtube] 5Fy2y3vzkWE: Downloading tv client config
[youtube] 5Fy2y3vzkWE: Downloading tv player API JSON

WARNING: [youtube] 5Fy2y3vzkWE: nsig extraction failed: Some formats may be missing
WARNING: [youtube] 5Fy2y3vzkWE: nsig extraction failed: Some formats may be missing  
WARNING: [youtube] 5Fy2y3vzkWE: Some tv client https formats have been skipped as 
         they are missing a url. YouTube may have enabled the SABR-only or 
         Server-Side Ad Placement experiment for the current session.
WARNING: [youtube] 5Fy2y3vzkWE: Some web client https formats have been skipped as 
         they are missing a url. YouTube is forcing SABR streaming for this client.
WARNING: Only images are available for download.

[info] Available formats for 5Fy2y3vzkWE:
ID  EXT   RESOLUTION FPS | PROTO | VCODEC MORE INFO
----------------------------------------------------
sb3 mhtml 48x27        1 | mhtml | images storyboard
sb2 mhtml 80x45        1 | mhtml | images storyboard
sb1 mhtml 160x90       1 | mhtml | images storyboard
sb0 mhtml 320x180      1 | mhtml | images storyboard
```

**Analysis**: 
- Zero audio/video formats returned
- Only thumbnail storyboards available
- `nsig` (signature) extraction fails
- YouTube explicitly mentions SABR

---

## 2. Test Output: Vimeo TLS Fingerprinting

```bash
$ yt-dlp "https://vimeo.com/148751763"

[vimeo] 148751763: Downloading webpage
ERROR: [vimeo] 148751763: This request has been blocked due to its TLS fingerprint. 
       Install a required impersonation dependency if possible, or else if you are 
       okay with compromising your security/cookies, try replacing "https:" with 
       "http:" in the input URL. If you are using a data center IP or VPN/proxy, 
       your IP may be blocked.
```

**Analysis**:
- Blocked before any data exchange
- TLS client hello signature detected
- yt-dlp suggests "impersonation dependency" (`curl-cffi`)
- HTTP fallback suggestion (not viable for security)

---

## 3. Current Download Implementation (Simplified)

```python
# src/clipscribe/retrievers/universal_video_client.py (excerpt)

class UniversalVideoClient:
    def __init__(self):
        self.ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "%(title)s-%(id)s.%(ext)s",
            "quiet": True,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/128.0.0.0 Safari/537.36",
            "http_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                # ... full browser header set
            },
        }

    async def download_audio(self, video_url: str, output_dir: str):
        """Download and extract audio from video."""
        
        opts = self.ydl_opts.copy()
        opts["outtmpl"] = os.path.join(output_dir, "%(title)s-%(id)s.%(ext)s")
        
        # YouTube-specific workarounds
        if "youtube.com" in video_url or "youtu.be" in video_url:
            # Strategy 1: Browser cookies + mweb client
            opts_with_cookies = opts.copy()
            chrome_profile_path = os.path.expanduser(
                "~/Library/Application Support/Google/Chrome"
            )
            opts_with_cookies["cookiesfrombrowser"] = ("chrome", chrome_profile_path)
            
            if "extractor_args" not in opts_with_cookies:
                opts_with_cookies["extractor_args"] = {}
            if "youtube" not in opts_with_cookies["extractor_args"]:
                opts_with_cookies["extractor_args"]["youtube"] = []
            opts_with_cookies["extractor_args"]["youtube"].append("player_client=mweb")
            
            opts = opts_with_cookies
        
        # Attempt download
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            ydl.download([video_url])
            # ... find and return audio file
```

**Key Points**:
- Already using browser headers
- Already extracting cookies from Chrome
- Already using mweb client for YouTube
- **Still gets blocked**

---

## 4. Successful Pipeline Test Output

```bash
$ poetry run python test_pipeline_with_audio.py

================================================================================
VOXTRAL-GROK PIPELINE TEST WITH EXTRACTED AUDIO
================================================================================

✅ Audio file found: 3.93 MB

1️⃣  Initializing HybridProcessor...
   INFO: Initialized Voxtral transcriber with model: voxtral-mini-2507
   INFO: HybridProcessor initialized: voxtral-mini-2507 + grok-4-0709
   ✅ HybridProcessor initialized

2️⃣  Processing with Voxtral-Grok pipeline...
   INFO: Direct Voxtral transcription for 172s video
   INFO: Transcribing 171.8 seconds (2.9 min) with Voxtral voxtral-mini-2507
   INFO: Extracting intelligence with grok-4-0709 from Voxtral transcript
   INFO: HTTP Request: POST https://api.x.ai/v1/chat/completions "HTTP/1.1 200 OK"
   INFO: Built knowledge graph with 11 nodes and 8 edges
   INFO: Hybrid processing complete: 11 entities, 8 relationships, $0.2136 cost, 65.1s

3️⃣  Processing complete!
   ✅ Transcript: 3368 chars
   ✅ Language: en
   ✅ Entities: 11
   ✅ Relationships: 8
   ✅ Processing Cost: $0.214
   ✅ Processing Time: 65.2s

Sample Entities:
   1. Attack Life
   2. Brute Force
   3. Barbell Apparel
   4. Mental Resilience
   5. Physical Training
   ... (6 more)

Sample Relationships:
   1. Attack Life → PARTNERS_WITH → Barbell Apparel
   2. Mental Resilience → REQUIRES → Physical Training
   3. Brute Force → METHOD_FOR → Attack Life
   ... (5 more)

================================================================================
✅ PIPELINE VALIDATION PASSED
================================================================================
```

**Proof**: When given proper audio input, the entire pipeline works perfectly.

---

## 5. Architecture Diagram

```
Current Architecture (Blocked at Step 1):
┌─────────────────────────────────────────────────────────────┐
│                      VIDEO PLATFORMS                         │
│  (YouTube, Vimeo, TikTok, Twitter, etc.)                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ yt-dlp download attempt
                           │
                    ❌ BOT DETECTION
                    (TLS fingerprint,
                     SABR, patterns)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLIPSCRIBE PIPELINE                      │
│                                                              │
│  1. [BLOCKED] yt-dlp → Video Download                       │
│  2. [BLOCKED] ffmpeg → Audio Extraction                     │
│  3. ✅ Voxtral API → Transcription ($0.003)                 │
│  4. ✅ Grok-4 API → Entity/Relationship Extraction ($0.211) │
│  5. ✅ Knowledge Graph Builder → Graph Structure            │
│  6. ✅ Output Formatter → JSON/CSV/GEXF/MD files            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT FILES                              │
│  - transcript.txt                                            │
│  - entities.json (11 entities)                              │
│  - relationships.json (8 relationships)                      │
│  - knowledge_graph.gexf (Gephi-compatible)                  │
│  - summary.md                                                │
└─────────────────────────────────────────────────────────────┘


Working Workaround (Manual):
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                            │
│  (Manual download via Chrome/Firefox)                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Manual download
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   LOCAL VIDEO FILE                           │
│  (video.mp4)                                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ ffmpeg extraction
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  EXTRACTED AUDIO FILE                        │
│  (audio.mp3) ✅ Accepted by Voxtral                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              CLIPSCRIBE PIPELINE (100% WORKS)                │
│  Steps 3-6 execute perfectly                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Cost Breakdown

```
Test Video: "Attack Life with Brute Force"
Duration: 2.9 minutes (172 seconds)
Total Cost: $0.214

Detailed Breakdown:
┌─────────────────────────┬──────────┬─────────────┬──────────┐
│ Component               │ Duration │ Rate        │ Cost     │
├─────────────────────────┼──────────┼─────────────┼──────────┤
│ Voxtral Transcription   │ 2.9 min  │ $0.001/min  │ $0.003   │
│ Grok-4 Extraction       │ ~45s API │ Token-based │ $0.211   │
│ Knowledge Graph Build   │ Local    │ Free        │ $0.000   │
│ Output Generation       │ Local    │ Free        │ $0.000   │
├─────────────────────────┼──────────┼─────────────┼──────────┤
│ TOTAL                   │ 65.2s    │             │ $0.214   │
└─────────────────────────┴──────────┴─────────────┴──────────┘

Target: $0.02-0.04 per video
Actual: $0.214 per video (5-10x over)

Problem: Grok-4 extraction is 98% of cost
Solution Needed: Optimize prompts or switch to cheaper model
```

---

## 7. Platform Detection Methods Summary

```
┌──────────────┬─────────────────────────────────────────────────────┐
│ Platform     │ Detection Method                                     │
├──────────────┼─────────────────────────────────────────────────────┤
│ YouTube      │ SABR (Server-Side Ad-Brokered Request)              │
│              │ - Removes streamable formats from API response       │
│              │ - nsig signature validation failure                  │
│              │ - Returns only image storyboards                     │
├──────────────┼─────────────────────────────────────────────────────┤
│ Vimeo        │ TLS Fingerprinting                                   │
│              │ - Analyzes SSL client hello signature                │
│              │ - Blocks before HTTP request                         │
│              │ - Explicit error about TLS fingerprint               │
├──────────────┼─────────────────────────────────────────────────────┤
│ Others       │ Likely Similar (untested)                            │
│ (1800+ sites)│ - Modern platforms adopting bot detection            │
│              │ - Mix of TLS, SABR, and pattern analysis             │
└──────────────┴─────────────────────────────────────────────────────┘
```

---

## 8. Questions Requiring Expertise

### Immediate Decision (This Week)
**Q1**: Should we invest time in `curl-cffi` impersonation, or go straight to browser automation?
- **Context**: curl-cffi might be temporary, browser automation is heavier but robust
- **Timeline**: Need decision to unblock Phase 2 development

### Architecture Decision (Next 2 Weeks)
**Q2**: For production scale (100-1000 videos/day), what's the right architecture?
- **Option A**: Pool of headless Chrome instances (memory-heavy)
- **Option B**: Impersonation library with browser fallback (complex)
- **Option C**: Something else entirely

### Detection Longevity
**Q3**: Based on current bot detection trends, how future-proof is each solution?
- **curl-cffi**: How long until platforms detect this fingerprint?
- **Browser automation**: Can navigator.webdriver be detected reliably?
- **Hybrid approach**: Worth the complexity?

---

These reference files provide the consultant with concrete evidence of:
1. What's broken (YouTube SABR, Vimeo TLS)
2. What's working (complete pipeline with audio)
3. Current implementation (headers, cookies, workarounds)
4. Cost structure (where money is being spent)
5. Architecture (where the blockage occurs)
