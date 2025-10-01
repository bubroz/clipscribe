# PRD: X (Twitter) Content Generator from Video Drops

**Date**: September 30, 2025  
**Status**: APPROVED - Primary focus for Week 2  
**Priority**: P1 (High value, consultant validated)  
**Timeline**: 7 days

---

## Problem Statement

**User Need**: Automatically generate engaging X (Twitter) posts when monitored YouTube channels upload new videos.

**Current State**: 
- ClipScribe extracts intelligence (entities, relationships)
- Output is JSON/MD files (not X-ready)
- Manual process to create posts

**Desired State**:
- Monitor channels via RSS (feedparser)
- Auto-detect new videos
- Generate "sticky" summaries (<280 chars)
- Auto-grab thumbnails
- Create draft tweets (text + image)
- User reviews and posts manually

---

## Success Criteria

1. **Drop Detection**: RSS monitoring detects new videos within 15 minutes
2. **Summary Quality**: "Sticky" summaries that are:
   - Objective and informative
   - Engaging hook (fact or question)
   - 3-5 key entities mentioned
   - <280 characters
   - No hashtags (per consultant)
3. **Thumbnail Retrieval**: 100% success rate grabbing video thumbnails
4. **Output Format**: `tweet.txt` + `thumbnail.jpg` ready for manual posting
5. **Processing Time**: <2 minutes from detection to draft

---

## Implementation Plan

### Day 1: Drop Monitoring (RSS)

**Goal**: Detect new video uploads automatically

**Tasks**:
```bash
# Install feedparser
poetry add feedparser

# Create monitor class
# src/clipscribe/monitors/channel_monitor.py
class ChannelMonitor:
    """Monitor YouTube channels for new video drops via RSS."""
    
    def __init__(self, channel_ids: list):
        self.channel_ids = channel_ids
        self.seen_videos = set()  # Track processed videos
    
    def get_rss_url(self, channel_id: str) -> str:
        """Convert channel ID to RSS feed URL."""
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    async def check_for_new_videos(self) -> list:
        """Check all monitored channels for new videos."""
        import feedparser
        
        new_videos = []
        for channel_id in self.channel_ids:
            feed_url = self.get_rss_url(channel_id)
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                video_id = entry.yt_videoid
                if video_id not in self.seen_videos:
                    new_videos.append({
                        'video_id': video_id,
                        'url': entry.link,
                        'title': entry.title,
                        'published': entry.published,
                        'channel': feed.feed.title
                    })
                    self.seen_videos.add(video_id)
        
        return new_videos

# CLI command
clipscribe monitor --channels UCg5EWI7X2cyS98C8hQwDCcw --interval 600  # 10 minutes
```

**Tests**:
- Feed parsing
- New video detection
- Duplicate prevention

**Deliverable**: Working RSS monitoring

---

### Day 2: X Draft Exporter

**Goal**: Generate "sticky" X-ready summaries

**Tasks**:
```python
# src/clipscribe/exporters/x_exporter.py

class XContentGenerator:
    """Generate X (Twitter) ready content from video intelligence."""
    
    async def generate_sticky_summary(
        self, 
        result: VideoIntelligence,
        max_length: int = 280
    ) -> str:
        """
        Generate 'sticky' summary using Grok-4.
        
        Sticky = objective + informative + engaging hook
        
        Template:
        [Hook: Interesting fact or question]
        [Key entities: 3-5 names/orgs]
        [Key relationship: 1-2 connections]
        [Closing: Implication or question]
        [URL]
        
        Example:
        "Stoic Viking partners Barbell Apparel after 10+ years. 
        Joins ranks: Valhalla VFT, Chad Wright. 
        Revolutionizes athletic gear—lifetime guarantee. 
        What's next for fitness collabs? [URL]"
        """
        
        # Build prompt for Grok
        entities_list = [e.name for e in result.entities[:5]]
        relationships_list = [
            f"{r.subject} {r.predicate} {r.object}" 
            for r in result.relationships[:3]
        ]
        
        prompt = f"""
        Create a sticky X (Twitter) post from this video intelligence:
        
        Title: {result.metadata.title}
        Entities: {', '.join(entities_list)}
        Key Relationships: {'; '.join(relationships_list)}
        
        Requirements:
        - Objective and informative (no hype)
        - Engaging hook (interesting fact or question)
        - Mention 3-5 key entities
        - Include 1-2 key relationships
        - End with implication or question
        - EXACTLY under {max_length} characters
        - NO hashtags
        - Neutral tone
        
        Return ONLY the tweet text, nothing else.
        """
        
        # Call Grok for summary
        summary = await self._generate_with_grok(prompt)
        
        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length-4] + "..."
        
        return summary
    
    def save_x_draft(
        self,
        summary: str,
        thumbnail_path: str,
        video_url: str,
        output_dir: Path
    ):
        """Save X draft as tweet.txt + thumbnail.jpg."""
        
        draft_dir = output_dir / "x_draft"
        draft_dir.mkdir(parents=True, exist_ok=True)
        
        # Save tweet text
        tweet_file = draft_dir / "tweet.txt"
        tweet_content = f"{summary}\n\n{video_url}"
        tweet_file.write_text(tweet_content)
        
        # Copy thumbnail
        if thumbnail_path and Path(thumbnail_path).exists():
            import shutil
            shutil.copy(thumbnail_path, draft_dir / "thumbnail.jpg")
        
        return {
            'tweet_file': str(tweet_file),
            'thumbnail': str(draft_dir / "thumbnail.jpg")
        }
```

**CLI**:
```bash
# Generate X draft from video
clipscribe x-draft "https://youtube.com/watch?v=abc" --output-dir output/x_drafts

# Output:
#   output/x_drafts/x_draft/tweet.txt
#   output/x_drafts/x_draft/thumbnail.jpg
```

**Tests**:
- Summary generation
- Character limit enforcement
- File creation

**Deliverable**: X draft generator working

---

### Day 3: Obsidian + Export Formats

**Goal**: Basic Obsidian export + CSV/PDF

**Tasks**:
```python
# Obsidian exporter (from earlier design)
class ObsidianExporter:
    def export_video_note(self, result, vault_path):
        # Create markdown with wikilinks
        # Entity notes in entities/
        # Video note in videos/
        pass

# CSV export
def export_csv(result, output_path):
    # entities.csv, relationships.csv
    pass

# PDF export  
def export_pdf(result, output_path):
    # Use markdown -> PDF (pandoc or reportlab)
    pass
```

**CLI**:
```bash
clipscribe export obsidian output/my_video ~/Documents/Vault
clipscribe export csv output/my_video entities.csv
clipscribe export pdf output/my_video report.pdf
```

**Deliverable**: Multi-format exports

---

### Day 4: Simple Summary (Grok Integration)

**Goal**: Add overview summary to all outputs

**Tasks**:
```python
# Update HybridProcessor to generate summary
async def generate_summary(self, transcript, entities, relationships):
    """Generate 100-200 word objective summary."""
    
    prompt = f"""
    Create an objective 100-200 word summary:
    
    Transcript: {transcript[:2000]}
    Entities: {[e.name for e in entities[:10]]}
    Relationships: {[f"{r.subject} {r.predicate} {r.object}" for r in relationships[:5]]}
    
    Format:
    - Overview (what happened)
    - Key entities and their roles
    - Main relationships/connections  
    - Implications or significance
    
    Tone: Informative, objective, professional
    """
    
    return await self._call_grok(prompt)

# Add to core.json and report.md
```

**Deliverable**: All outputs include executive summary

---

### Day 5: Topic Timeline Test

**Goal**: Test if accurate topic timelines are viable

**Tasks**:
```python
# Test timeline extraction
def test_topic_timeline_accuracy():
    """
    Test if Voxtral segments + Grok can produce accurate timelines.
    
    Example expected output:
    - Intro [0-30s]: Hook about not wearing shirts
    - Announcement [30-90s]: Partnership with Barbell Apparel
    - Background [90-150s]: 10-year history with brand
    - Call-to-action [150-180s]: Check out their products
    """
    
    # Use Voxtral segments (timed)
    # Prompt Grok to categorize segments into topics
    # Manually verify accuracy
    
    # If >80% accurate: Keep
    # If <80%: Scrap, use simple summary instead
```

**Decision point**: Keep or scrap based on accuracy

---

### Day 6-7: Full CLI Flow + Polish

**Goal**: Complete end-to-end workflow

**CLI Commands**:
```bash
# Monitor channels for drops
clipscribe monitor --channels stoicviking,otherchannel --interval 600

# Process single video with X draft
clipscribe process video URL --with-x-draft

# Generate X draft from existing output
clipscribe x-draft output/20250930_youtube_abc/

# Export to Obsidian
clipscribe export obsidian output/my_videos/ ~/Documents/Vault

# Export to CSV/PDF
clipscribe export csv output/my_video/
clipscribe export pdf output/my_video/
```

**Polish**:
- Progress indicators
- Better error messages
- Success confirmations
- Example outputs in CLI help

**Deliverable**: Production-ready CLI for personal use

---

## Technical Implementation Details

### Thumbnail Extraction
```python
# Already in yt-dlp options
self.ydl_opts = {
    'writethumbnail': True,  # Download thumbnail
    'skip_download': False,   # Still download video
}

# After download, thumbnail will be:
# output_dir/VideoTitle-videoid.jpg
```

### X API Integration (Optional Auto-Post)
```python
# If user wants auto-posting
import tweepy

client = tweepy.Client(
    bearer_token=os.getenv('X_BEARER_TOKEN')
)

# Upload media
media = api.media_upload('thumbnail.jpg')

# Post tweet
client.create_tweet(
    text=tweet_text,
    media_ids=[media.media_id]
)
```

**Note**: Start with manual posting (just generate drafts), add auto-post later if requested.

---

## Example Output

### Input:
```
Video: "Partnering with Barbell Apparel"
URL: https://youtube.com/watch?v=5Fy2y3vzkWE
```

### Generated X Draft (`tweet.txt`):
```
Stoic Viking partners Barbell Apparel after 10+ years as customer. Joins athlete roster: Valhalla VFT, Tom Haviland, Chad Wright. Lifetime guarantee backing—what partnerships follow in athletic gear space?

https://youtube.com/watch?v=5Fy2y3vzkWE
```

**Character count**: 251 (under 280 limit)

**Image**: `thumbnail.jpg` (YouTube auto-thumbnail)

---

## Success Metrics

### Week 2 Success:
- [ ] Monitor 3-5 channels successfully
- [ ] Generate 10 X drafts (test various video types)
- [ ] >80% of summaries are "sticky" (engaging)
- [ ] 100% thumbnail retrieval success
- [ ] Obsidian export works (creates proper vault structure)

### Quality Checks:
- Summaries are objective (no hype)
- Summaries are informative (real intel)
- Summaries are sticky (want to click/engage)
- Character limits respected
- No hashtag spam

---

## Dependencies

```bash
# New dependencies needed
poetry add feedparser  # RSS monitoring
poetry add tweepy      # X API (optional)
poetry add pandas      # CSV export
poetry add reportlab   # PDF generation (or use pandoc)
```

---

**Status**: Ready to implement  
**Timeline**: 7 days (Week 2)  
**Next**: Start with Day 1 - Drop monitoring

