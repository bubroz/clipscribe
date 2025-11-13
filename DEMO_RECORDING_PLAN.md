# Demo Recording Plan
**ClipScribe v3.0.0**  
**Date:** November 13, 2025  
**Purpose:** Demo videos for marketing, documentation, and collaborator onboarding

---

## Demo Strategy

**Goal:** Show off v3.0.0 features (multi-format exports, series analysis) to:
- Potential users (marketing)
- Collaborators (onboarding)
- Designer/stakeholders (context)
- Hacker News / Reddit audience

**Approach:** Multiple short, focused demos (3-7 min each) rather than one long comprehensive demo

**Why Short Demos:**
- Easier to produce (less editing)
- More shareable (specific links for specific features)
- Better retention (people watch short videos)
- Reusable (embed different demos in different contexts)

---

## Demo 1: Quickstart (5 minutes)

**Purpose:** Show how easy it is to get started

**Content:**
1. Prerequisites check (30 sec)
   - Python 3.12+ installed
   - Poetry installed
   - API keys ready

2. Installation (1 min)
   - `git clone` repo
   - `poetry install`
   - Configure .env

3. Process first video (2 min)
   - `clipscribe process audio.mp3`
   - Show processing progress
   - Wait for completion

4. View outputs (1.5 min)
   - Open JSON in VS Code
   - Show entities, relationships, topics
   - Quick data tour

**Test Video:** Use short 5-10 min video from test_videos/ folder

**Recording Tool:** QuickTime (Mac native, simple)

**Script:** Write before recording

**Hosting:** YouTube (unlisted) + embed in README

---

## Demo 2: Multi-Format Exports (5 minutes)

**Purpose:** Showcase the 5 export formats

**Content:**
1. Process with all formats (1 min)
   - `clipscribe process video.mp3 --formats all`
   - Show flag usage

2. Tour each format (3 min)
   - JSON: Open in VS Code, show structure
   - DOCX: Open in Google Docs, show report
   - CSV: Open entities.csv in Excel, show data
   - PPTX: Open in Google Slides, flip through slides
   - Markdown: Show in VS Code preview

3. Use case explanation (1 min)
   - When to use each format
   - Multi-format flexibility value prop

**Test Video:** Use one of the sample outputs (already processed)

**Recording Tool:** QuickTime + screen recording

**Hosting:** YouTube + link from web_presence docs

---

## Demo 3: Series Analysis (7 minutes)

**Purpose:** Show cross-video intelligence (premium feature)

**Content:**
1. Setup file list (1 min)
   - Create videos.txt
   - Add 3 video paths

2. Run process-series (2 min)
   - `clipscribe process-series videos.txt --series-name "Demo-Series"`
   - Show processing multiple videos

3. Review series analysis (3 min)
   - Open series_report.json
   - Show entity frequency (appeared in 2 of 3 videos)
   - Show relationship patterns
   - Show topic evolution

4. Series outputs (1 min)
   - Series PPTX presentation
   - Aggregate CSV data

**Test Videos:** 3 related short videos (5-10 min each)

**Recording Tool:** QuickTime

**Hosting:** YouTube + sales/marketing use

---

## Demo 4: Provider Comparison (5 minutes) - OPTIONAL

**Purpose:** Show cost/quality trade-offs

**Content:**
1. Same video, 3 providers (3 min)
   - Process with Voxtral (cheap, no speakers)
   - Process with WhisperX Local (FREE, speakers)
   - Process with WhisperX Modal (cloud, high quality)

2. Compare outputs (1 min)
   - Speaker attribution differences
   - Cost differences
   - Quality comparison

3. When to use each (1 min)

**Test Video:** Interview with 2 clear speakers

**Recording Tool:** QuickTime

**Hosting:** YouTube (optional demo)

---

## Recording Specifications

### Technical Setup

**Screen Recording:**
- Tool: QuickTime (Mac native, simple)
- Resolution: 1920x1080 (standard HD)
- Frame rate: 30fps
- Format: MOV (convert to MP4 for YouTube)

**Audio:**
- Microphone: Built-in Mac mic or external
- Quiet environment
- Clear, conversational tone
- No background music

**Terminal:**
- Font size: 16-18pt (readable)
- Color scheme: Light (better for recording)
- Full screen terminal or clear window

### Post-Production

**Editing:**
- Minimal (or none if one-take)
- Cut dead air/mistakes
- Add title cards (optional)
- No fancy effects

**Software:**
- QuickTime (for basic cuts)
- iMovie (if more editing needed)
- Or just upload raw

### Upload

**YouTube Setup:**
- Create ClipScribe channel (or use personal)
- Upload as Unlisted (not Public initially)
- Good titles and descriptions
- Timestamps in description

**Alternative:** Loom (easier, but less permanent)

---

## Distribution Plan

### Embed in Documentation

**Root README.md:**
- Add "Video Demos" section after Quick Start
- Embed Demo 1 (Quickstart)
- Link to others

**docs/web_presence/:**
- Reference demos in content strategy
- Provide links for designer to see product

### Share with Collaborators

**Send demos to:**
- UI/UX designer (context)
- Engineer collaborators (onboarding)
- Any beta testers

### Marketing (After Website Launch)

**Hacker News:**
- Post "Show HN: ClipScribe v3.0 - Open source video intelligence extraction"
- Link to GitHub + Demo 1

**Reddit:**
- r/OSINT - Demo 2 (formats useful for OSINT)
- r/datascience - Demo 2 (data formats)
- r/Python - Demo 1 (CLI tool)

**Twitter/X:**
- Tweet Demo 1 with sample outputs
- Thread showing all 5 formats
- "Built in open, free to use"

---

## Demo Production Timeline

**Recommended Order:**

**Week 1 (This Week):**
- [ ] Write scripts for Demo 1 and 2
- [ ] Record Demo 1 (Quickstart) - 1 hour
- [ ] Record Demo 2 (Multi-format) - 1 hour
- [ ] Upload to YouTube (unlisted)
- [ ] Embed in README

**Week 2 (Next Week):**
- [ ] Record Demo 3 (Series analysis) - 1.5 hours
- [ ] Upload and link from docs
- [ ] Share with designer and collaborators

**Week 3 (After Website Design Starts):**
- [ ] Review feedback
- [ ] Re-record if needed
- [ ] Make public when website launches

---

## Alternative: Written Tutorials

**If video recording is too time-consuming:**

Create detailed markdown tutorials with screenshots:
- `docs/tutorials/quickstart.md`
- `docs/tutorials/multi_format_exports.md`
- `docs/tutorials/series_analysis.md`

**Pros:**
- Easier to maintain
- Faster to create
- More accessible (text is searchable)
- Works in all contexts

**Cons:**
- Less engaging than video
- Harder to show UX flow
- No audio/narration

**Hybrid Approach:**
- Screenshots + text for most features
- Video only for key demos (Quickstart)

---

## Test Video Recommendations

**For Demos:** Use short, appropriate videos

**Good Options:**
1. **From samples:** Use existing samples (already processed)
   - business_interview_30min
   - technical_single_speaker_16min
   
2. **New short video:** Find 5-10 min video with:
   - Clear audio
   - Interesting content (tech/business/news)
   - Good entity extraction
   - Not controversial

**Avoid:**
- Long videos (>15 min) for demos
- Controversial/sensitive content
- Poor audio quality
- Music videos or entertainment (weak intelligence)

---

## Next Steps

**Immediate:**
1. Decide: Video demos or written tutorials?
2. If video: Write scripts for Demo 1 & 2
3. If written: Create tutorial structure

**This Week:**
- Produce Demo 1 (Quickstart)
- Embed in README
- Share with collaborators

**After Designer Starts:**
- Produce remaining demos
- Use for marketing when site launches

---

**Status:** Plan complete, awaiting production decision  
**Time to Produce:** 3-4 hours total for all demos  
**Value:** High (marketing + onboarding + documentation)

