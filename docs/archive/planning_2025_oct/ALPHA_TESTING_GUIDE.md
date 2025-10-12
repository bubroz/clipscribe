# ClipScribe Alpha Testing Guide

**Version**: v2.53.0  
**Date**: October 1, 2025  
**For**: Alpha testers (first 5-10 users)

---

## Welcome Alpha Tester! 👋

Thank you for helping test ClipScribe! This guide will help you:
- Install and set up ClipScribe
- Understand what to test
- Report issues effectively
- Get the most value from your testing

**Estimated time**: 30 minutes setup, ongoing testing

---

## What is ClipScribe?

ClipScribe extracts structured intelligence from videos:
- **Entities**: People, organizations, concepts mentioned
- **Relationships**: How entities connect to each other
- **Knowledge Graphs**: Visual network of all connections
- **X Drafts**: Ready-to-post Twitter summaries
- **Exports**: Obsidian, CSV, PDF formats

**Example**: From a 12-minute training video, ClipScribe extracted:
- 35 entities (military units, roles, processes)
- 41 relationships (connections between entities)
- Professional report + knowledge graph
- Engaging X post draft (<280 chars)

---

## Installation

### Prerequisites
- macOS or Linux
- Python 3.12+
- 5GB free disk space

### Step-by-Step

```bash
# 1. Clone repository
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe

# 2. Install with Poetry
curl -sSL https://install.python-poetry.org | python3 -
poetry install

# 3. Set up API keys
cp env.example .env
# Edit .env and add your keys:
#   MISTRAL_API_KEY=your_mistral_key
#   XAI_API_KEY=your_xai_key

# 4. Test installation
poetry run clipscribe --version
# Should show: ClipScribe, version 2.53.0
```

**Get API keys:**
- Mistral: https://console.mistral.ai/
- xAI (Grok): https://console.x.ai/

---

## Quick Start

### Process Your First Video

```bash
# Process a 2-minute video
poetry run clipscribe process video \
  "https://www.youtube.com/watch?v=5Fy2y3vzkWE" \
  --output-dir output/my_first_video

# Expected time: ~90 seconds
# Expected cost: ~$0.027
```

**What you'll get:**
```
output/my_first_video/20251001_youtube_watch/
  ├── core.json (all data)
  ├── knowledge_graph.json (graph structure)
  ├── report.md (human-readable)
  ├── transcript.txt (full transcript)
  └── metadata.json (video info)
```

### Generate X (Twitter) Draft

```bash
# Same video, but with X draft
poetry run clipscribe process video \
  "https://www.youtube.com/watch?v=5Fy2y3vzkWE" \
  --output-dir output/with_x_draft \
  --with-x-draft
```

**You'll also get:**
```
x_draft/
  ├── tweet.txt (ready-to-post text)
  ├── thumbnail.jpg (video thumbnail)
  └── metadata.json (generation details)
```

### Monitor a Channel

```bash
# Auto-process new videos from a channel
poetry run clipscribe monitor \
  --channels UCg5EWI7X2cyS98C8hQwDCcw \
  --interval 600 \
  --with-x-draft

# Press Ctrl+C to stop
```

---

## What to Test

### Core Functionality (Priority 1)

**Test 1: Short Videos (2-5 minutes)**
- [ ] Process 3 different short videos
- [ ] Verify entities are relevant
- [ ] Check relationships make sense
- [ ] Review report quality

**Test 2: Long Videos (10-15 minutes)**
- [ ] Process 2 longer videos
- [ ] Verify chunking works (look for "Processing chunk" messages)
- [ ] Check entity count is reasonable
- [ ] Validate no timeouts

**Test 3: Different Content Types**
- [ ] Educational/training video
- [ ] News/interview video
- [ ] Product review/demo
- [ ] Check quality varies appropriately

### X Content Generation (Priority 2)

**Test 4: X Drafts**
- [ ] Generate 5 X drafts
- [ ] Check character counts (<280)
- [ ] Verify summaries are engaging
- [ ] Confirm thumbnails are included
- [ ] Test readability and "stickiness"

### Integration Features (Priority 3)

**Test 5: Obsidian Export**
- [ ] Export 2-3 videos to Obsidian vault
- [ ] Check wikilinks work
- [ ] View graph view
- [ ] Test entity notes

**Test 6: CSV/PDF Exports**
- [ ] Generate CSV files
- [ ] Generate PDF report
- [ ] Open in Excel/Numbers
- [ ] Check formatting

### Advanced (Optional)

**Test 7: Monitoring**
- [ ] Monitor 1-2 channels for 24 hours
- [ ] Verify new videos are detected
- [ ] Check auto-processing works
- [ ] Validate no duplicates

**Test 8: Deduplication**
- [ ] Process same video twice
- [ ] Verify second run skips
- [ ] Check stats command
- [ ] Test --force flag

---

## Expected Behavior

### Normal Operation
- **Download**: 5-15 seconds
- **Transcription**: 20-30 seconds per 2min
- **Extraction**: 40-80 seconds
- **Total**: 1-2 minutes for short video, 2-4 for long

### Rate Limiting
- 10 second delay between videos (by design)
- 100 videos per day cap per platform
- You'll see: "Rate limiting youtube: waiting 10.0s"

### Error Recovery
- Network errors: Automatic retry (3 attempts)
- Grok timeouts: Automatic retry with chunking
- Download failures: Tries curl-cffi, then Playwright

---

## Known Issues (Not Bugs)

1. **10s delays**: Intentional (ToS compliance)
2. **German transcripts**: Some videos detected as German (Voxtral auto-detect)
3. **Temp cleanup**: Temp files cleaned automatically
4. **First run slow**: Downloads browser (one-time, 130MB)

---

## How to Report Issues

### What We Need

**Good bug report:**
```
Video URL: https://youtube.com/watch?v=abc123
Command: clipscribe process video URL --with-x-draft
Expected: 10-20 entities
Actual: 0 entities
Error message: [paste error]
Logs: [paste relevant logs]
```

**Great bug report:**
```
[Same as above, PLUS:]
- Video duration: 12 minutes
- Content type: Educational/training
- When it failed: During Grok extraction
- What you tried: Ran 3 times, same result
- System: macOS 14.5, Python 3.12
```

### Where to Report

**Option 1: GitHub Issues** (preferred)
- https://github.com/bubroz/clipscribe/issues
- Use "Alpha Feedback" label
- Include command + error + logs

**Option 2: Direct Email**
- zforristall@gmail.com
- Subject: "ClipScribe Alpha Feedback"
- Include same info as GitHub

**Option 3: Quick Feedback**
- Google Form: [link TBD]
- For quick observations

---

## Success Metrics

**What we're measuring:**
- Download success rate (target: 95%+)
- Entity extraction quality (subjective)
- X draft engagement (do they make you want to click?)
- User experience (confusing? clear?)
- Error frequency (how often do things break?)

**What we need from you:**
- Honest feedback (good and bad!)
- Specific examples (URLs, commands, outputs)
- Suggestions (what would make it better?)

---

## FAQ

**Q: Why does it wait 10 seconds between videos?**
A: ToS compliance. YouTube/Vimeo ban IPs for rapid automated access. 10s keeps you safe.

**Q: Can I process videos faster?**
A: Yes! Set `export CLIPSCRIBE_REQUEST_DELAY=5` for 5s delays (riskier).

**Q: What if Grok times out?**
A: Automatic retry with chunking. If it fails 3x, report it.

**Q: Why are some transcripts in German?**
A: Voxtral auto-detects language. Sometimes it's wrong. This is a known issue.

**Q: Can I process private/age-restricted videos?**
A: Use `--cookies-from-browser chrome` flag.

**Q: How do I stop monitoring?**
A: Press Ctrl+C

**Q: Where are my outputs?**
A: `output/` directory, organized by date and video ID.

---

## Tips for Great Testing

1. **Test diverse content**: News, education, entertainment, technical
2. **Test different lengths**: 2min, 10min, 30min+
3. **Try edge cases**: Private videos, playlists, live streams
4. **Use real workflows**: How would YOU actually use this?
5. **Document surprises**: Anything unexpected is valuable feedback

---

## What Happens Next

**Week 1-2**: You test, we fix critical bugs
**Week 3**: We refine based on feedback
**Week 4**: Prepare for beta (20-50 users)
**Month 3-4**: Public launch

**Your feedback shapes the product!**

---

## Contact

**Questions?** zforristall@gmail.com  
**Bugs?** GitHub Issues  
**Ideas?** We want to hear them!

**Thank you for being an alpha tester.** Your feedback is invaluable.

---

**Last Updated**: October 1, 2025  
**Version**: v2.53.0

