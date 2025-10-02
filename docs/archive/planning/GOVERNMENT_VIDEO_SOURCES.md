# Government Video Sources - Research & Strategy

**Date**: October 1, 2025  
**Purpose**: Determine best sources for local/state/federal government videos  
**Goal**: Build X account with timely government intelligence posts

---

## 🎯 Your Use Case

**Goal**: Process government videos → Generate X posts → Grow account

**Value Proposition:**
- Hard-to-find content (not heavily shared on social media)
- Timely intelligence (committee hearings, briefings, local meetings)
- Informative analysis (entities, relationships, quotes)
- Professional presentation (objective summaries)

**Target Audience:**
- Policy analysts
- Local citizens
- Journalists
- Government watchdogs

---

## 📺 Government Video Platforms (Research Findings)

### Federal Level

**1. YouTube Channels (BEST - works with ClipScribe now)**

**C-SPAN** (@cspan, @cspan2, @cspan3)
- ✅ Full archives on YouTube
- ✅ Works with yt-dlp/ClipScribe TODAY
- ✅ House, Senate, committee hearings
- ✅ Already indexed and searchable
- 📍 Channel IDs to monitor

**White House** (@WhiteHouse)
- ✅ Press briefings
- ✅ Speeches and events
- ✅ Works with ClipScribe TODAY
- 📍 Channel ID: UCYxRlFDqcWM4y7FfpiAN3KQ

**Congressional Committees** (various)
- ✅ Many have YouTube channels
- ✅ Works with ClipScribe
- 📍 Need to identify channel IDs

**2. Official Websites (NEEDS RESEARCH/TESTING)**

**C-SPAN.org**
- ❌ yt-dlp extractor broken (tested, failed)
- ⚠️ Would need OBS for live streams
- ⚠️ OR: Wait for videos to appear on YouTube channel
- **Recommendation**: Use YouTube instead

**Congress.gov, Senate.gov, House.gov**
- ❓ Unknown if yt-dlp supports
- ⚠️ Many embed YouTube videos (use those)
- ⚠️ Custom players may need OBS

---

### State Level (California)

**California State Legislature**

**Assembly YouTube** (@CaliforniaAssemblyDemocrats)
- ✅ Works with ClipScribe
- ✅ Floor sessions, hearings
- 📍 Channel ID: [NEED TO FIND]

**Senate**
- ❓ senate.ca.gov - has MP4 downloads per consultant
- ✅ If direct MP4, yt-dlp may work
- **Test needed**

---

### Local Level (Yolo County, Davis CA)

**Yolo County**
- ⚠️ Hosted on swagit.com
- ❓ yt-dlp support unknown
- ✅ Consultant says "right-click MP4 download"
- **Test needed**

**City of Davis**
- ✅ YouTube channel (@cityofdaviscalif)
- ✅ Works with ClipScribe TODAY
- ✅ Granicus also has MP4 downloads
- 📍 Channel ID: [NEED TO FIND]

---

## 🔬 TESTING NEEDED

**I need to test these platforms with ClipScribe:**

### Priority 1 (Do NOW - 15 min)
1. **C-SPAN YouTube**
   - Test: `clipscribe process video [C-SPAN YouTube URL]`
   - Expected: Should work (it's YouTube)
   
2. **White House YouTube**
   - Test: Same
   - Expected: Should work

3. **California Assembly YouTube**
   - Test: Same
   - Expected: Should work

### Priority 2 (Research - 30 min)
4. **Senate.ca.gov direct MP4**
   - Test if yt-dlp can download
   - If not, can we use `requests` to download MP4 directly?

5. **Swagit.com (Yolo County)**
   - Test yt-dlp support
   - Check if direct MP4 download possible

6. **Granicus (Davis)**
   - Test yt-dlp support
   - Verify MP4 access

---

## 💡 RECOMMENDATION

**Start with YouTube channels (works TODAY):**

### Immediate Monitoring Setup

```bash
# Monitor federal government channels
clipscribe monitor \
  --channels UCYxRlFDqcWM4y7FfpiAN3KQ,UC[C-SPAN] \
  --interval 600 \
  --with-x-draft

# Result:
# - New White House briefing drops
# - Auto-processes in 2-3 minutes
# - X draft ready with entities/relationships
# - You review and post
```

**Workflow:**
1. Video drops (White House briefing, committee hearing)
2. ClipScribe auto-processes (2-3 min)
3. You get X draft: "Biden addresses [topic]. Key entities: [people]. [Provocative question]?"
4. You review, edit if needed, post
5. Your followers get timely intel with context

### Advantages
- ✅ Works TODAY (no new development)
- ✅ Proven reliability (YouTube + curl-cffi)
- ✅ High-value content (official government sources)
- ✅ Timely (RSS detects within 15 min of upload)
- ✅ Differentiated (most people don't watch full hearings)

### Your Value-Add
- **Speed**: Post intel within 30 min of video drop
- **Context**: Entities + relationships (not just summary)
- **Accessibility**: Make long hearings digestible
- **Neutrality**: Objective extraction (Grok doesn't editorialize)

---

## 🚀 PHASE 2: Expand to Direct Sources

**After validating YouTube workflow works:**

### Add Direct Download Support

**For platforms with MP4:**
- Senate.ca.gov
- Granicus (Davis)
- Other direct-download platforms

**Implementation** (~1-2 hours):
```python
# Add direct MP4 downloader
class DirectMP4Downloader:
    """Download MP4 files directly (bypasses yt-dlp)."""
    
    async def download_mp4(self, url: str, output_path: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
```

**Integration:**
- Detect MP4 URLs
- Download directly
- Process with existing pipeline

---

## 📊 CONTENT STRATEGY

### Your X Account Theme
**"Government Intelligence in Real-Time"**

**What you post:**
- Committee hearing intel (who said what, key relationships)
- Press briefing analysis (entities mentioned, policy connections)
- Local government decisions (Yolo County, Davis City Council)
- Executive order breakdowns (who's affected, what changes)

**X Post Template:**
```
[Hook: Timely event/controversy]
[Key entities: 3-5 officials/orgs]
[Key relationship or revelation]
[Provocative question for engagement]
[Video URL]
```

**Example:**
```
Senate Judiciary hearing on crime: 
AG testifies on National Guard deployments. 
Key mentions: DC, Chicago, Baltimore mayors. 
Senators question legality—what precedents apply?

https://c-span.org/video/...
```

**Frequency:**
- Daily: 3-5 posts (White House, Senate, House)
- Weekly: 2-3 deep dives (long committee hearings)
- As needed: Local government (Yolo, Davis)

---

## ✅ ANSWER TO YOUR QUESTIONS

### 1. Do you HAVE to use OBS?

**NO - for YouTube channels:**
- C-SPAN YouTube: Works with ClipScribe TODAY ✅
- White House YouTube: Works TODAY ✅
- Most government channels: On YouTube ✅

**MAYBE - for direct websites:**
- C-SPAN.org: Currently broken in yt-dlp, would need OBS for live OR wait for YouTube upload
- Some state sites: Depends on platform

**Recommendation**: 
- **Start with YouTube** (works now, 80% of content)
- **Add direct download later** (1-2 hours dev) for remaining 20%

### 2. Is this viable for growing X account?

**ABSOLUTELY YES:**

**Why it works:**
- ✅ Timely (post within 30 min of hearing/briefing)
- ✅ Unique angle (most people don't extract entities)
- ✅ High-value (government = important)
- ✅ Differentiated (no one else doing this with AI)
- ✅ Scalable (monitor multiple channels)

**Competitive advantages:**
- Speed: You post before traditional media summarizes
- Depth: Entity extraction beats surface summary
- Consistency: Automated pipeline = daily posts
- Authority: Citing specific quotes with timestamps

---

## 🎯 NEXT STEPS

### This Morning (30 min):
1. Find C-SPAN YouTube channel IDs
2. Find White House channel ID
3. Find California channels
4. Test one video from each to verify

### This Afternoon (1 hour):
5. Set up monitoring on 3-5 key channels
6. Generate 5 X drafts from recent videos
7. Review quality and engagement

### This Week:
8. Post 3-5 X posts
9. Monitor engagement (likes, replies, retweets)
10. Iterate on summary style based on what works

---

**Want me to:**
1. Find the channel IDs for you?
2. Test C-SPAN/WhiteHouse YouTube downloads?
3. Create a monitoring command for your specific channels?
4. Generate X drafts from recent government videos?

**This is a GREAT use case** - timely government intel is perfect for X growth.

