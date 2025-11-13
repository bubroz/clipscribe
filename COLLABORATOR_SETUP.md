# Collaborator Setup Guide
**ClipScribe v3.0.0**  
**Date:** November 13, 2025  
**For:** Engineer-level collaborators who want to demo ClipScribe

---

## Quick Start (10 minutes)

Get ClipScribe running on your machine in 10 minutes.

### 1. Clone Repository

```bash
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
```

### 2. Install Dependencies

**Requirements:**
- Python 3.12+ (check: `python3 --version`)
- Poetry (install: `curl -sSL https://install.python-poetry.org | python3 -`)

**Install:**
```bash
poetry install
```

This installs all dependencies including:
- WhisperX (transcription engine)
- python-docx, python-pptx (export formats)
- Click (CLI framework)
- All other requirements

**Time:** ~3-5 minutes

### 3. Configure API Keys

**Copy environment template:**
```bash
cp env.example env.production
```

**Edit `env.production` and add these keys:**

#### Required: Grok API Key

**What:** Intelligence extraction (entities, relationships, topics)  
**Where to get:** https://x.ai (x.ai/api)  
**Cost:** $20/month (pay-as-you-go)  
**Usage:** ~$0.002-0.005 per video

**Get your key:**
1. Go to https://x.ai
2. Sign up / log in
3. Go to API section
4. Create API key
5. Copy key

**Add to env.production:**
```bash
XAI_API_KEY=xai-your-key-here
```

#### Optional: HuggingFace Token

**What:** Speaker diarization models (if using WhisperX)  
**Where:** https://huggingface.co/settings/tokens  
**Cost:** FREE  
**Usage:** Required for multi-speaker videos

**Get your token:**
1. Create free HuggingFace account
2. Go to Settings → Access Tokens
3. Create new token (read access)
4. Copy token

**Add to env.production:**
```bash
HUGGINGFACE_TOKEN=hf_your_token_here
```

#### Optional: Mistral API Key (for Voxtral provider)

**What:** Voxtral transcription provider (alternative to local)  
**Where:** https://mistral.ai  
**Cost:** ~$0.03 per 30min video  
**Usage:** Single-speaker, fast API transcription

**Add to env.production:**
```bash
MISTRAL_API_KEY=your_mistral_key
```

**Note:** You can skip this and just use WhisperX Local (FREE)

### 4. Test Installation

**Quick test:**
```bash
# Check ClipScribe is installed
poetry run clipscribe --version
# Output: ClipScribe v3.0.0

# Check authentication
poetry run clipscribe utils check-auth
# Should show: XAI_API_KEY detected
```

**If errors:** See Troubleshooting section below

### 5. Process Test Video

**Use one of the included test videos:**
```bash
cd test_videos

# List available test videos
ls -lh *.mp3 *.mp4

# Process a short one (FREE with local provider)
poetry run clipscribe process medical_lxFd5xAN4cg.mp3 -t whisperx-local --formats all

# Wait 3-5 minutes for processing...
# Output will be in: output/timestamp_medical/
```

**Check outputs:**
```bash
cd output/20251113_*_medical*/
ls -la

# Should see:
# - transcript.json
# - intelligence_report.docx
# - executive_summary.pptx
# - report.md
# - csv/ (5 files)
```

### 6. You're Ready!

**Demo commands:**
```bash
# Single video with all formats
clipscribe process video.mp3 --formats all

# Single video, specific formats
clipscribe process video.mp3 --formats json docx pptx

# Series analysis (3+ videos)
echo "video1.mp3" > series.txt
echo "video2.mp3" >> series.txt
echo "video3.mp3" >> series.txt
clipscribe process-series series.txt --series-name "My-Series"

# Different providers
clipscribe process video.mp3 -t voxtral --no-diarize  # Cheap, no speakers
clipscribe process video.mp3 -t whisperx-local         # FREE, with speakers
clipscribe process video.mp3 -t whisperx-modal         # Cloud GPU, fast
```

---

## API Keys Sharing (from Zac)

**Option 1: Get Your Own Keys (Recommended)**

**Pros:**
- Full control
- No sharing concerns
- Learn the setup process
- Can demo independently

**Cons:**
- $20/month for Grok (only cost)
- Have to set up accounts

**Total Cost:** $20/month for Grok + FREE for HuggingFace

---

**Option 2: Use Shared Keys (via 1Password)**

**If Zac shares keys via 1Password:**
1. Get invited to shared vault
2. Copy XAI_API_KEY from vault
3. Copy HUGGINGFACE_TOKEN from vault
4. Add to your env.production
5. Don't share these keys further!

**Pros:**
- No cost to you
- Immediate access
- No account setup

**Cons:**
- Shared usage (be considerate)
- Zac pays the bills
- Less independence

---

## Test Videos Available

**In `test_videos/` folder:**

**Good for Demos:**
- `medical_lxFd5xAN4cg.mp3` (16min, 1 speaker, medical content)
- `test_earnings.mp4` (short, business content)
- `legal_7iHl71nt49o.mp3` (legal/political content)

**For Multi-Speaker Testing:**
- `U3w93r5QRb8_The View Full Broadcast.mp3` (36min, 12 speakers)
- `wlONOh_iUXY_Marjorie Taylor Greene.mp3` (multi-speaker political)

**Processing Cost:**
- With WhisperX Local: FREE (just Grok ~$0.002-0.005)
- With Voxtral: ~$0.03-0.05
- With WhisperX Modal: ~$0.06

**Recommendation:** Use WhisperX Local for demos (FREE!)

---

## What You Can Demo

### Basic Features

**Single Video Processing:**
- Show CLI usage
- Explain provider options
- Display output files
- Walk through JSON structure

**Multi-Format Exports:**
- Generate all 5 formats
- Show DOCX in Google Docs
- Show CSV in Excel
- Show PPTX in Slides
- Explain use cases

**Speaker Diarization:**
- Process multi-speaker video
- Show speaker attribution in transcript
- Explain up to 12 speakers
- Show segments.csv with speaker column

### Advanced Features

**Series Analysis:**
- Process 3+ videos
- Show cross-video entity tracking
- Show relationship patterns
- Show topic evolution
- Display series report

**Provider Comparison:**
- Same video, different providers
- Cost/quality trade-offs
- When to use each

**Export Customization:**
- Select specific formats
- Explain format purposes
- Show compatibility (Google/Microsoft/Apple)

---

## Demo Best Practices

**Do:**
- Use short test videos (5-15 min)
- Start with WhisperX Local (FREE)
- Show actual output files (don't just describe)
- Explain the value (not just features)
- Be honest about costs and limitations
- Show sample outputs from examples/

**Don't:**
- Use long videos (>30 min) for demos
- Promise features that don't exist
- Oversell accuracy (AI can make mistakes)
- Use Rick Astley videos (banned in test rules!)
- Process copyrighted content you don't own

---

## Common Issues & Solutions

### "No module named 'pydantic'"

**Problem:** Dependencies not installed properly

**Solution:**
```bash
cd clipscribe
poetry install
poetry run clipscribe --version
```

### "XAI_API_KEY not configured"

**Problem:** API key not in environment

**Solution:**
```bash
# Check env.production file exists
cat env.production | grep XAI

# If missing, add:
echo "XAI_API_KEY=xai-your-key" >> env.production

# Verify
poetry run clipscribe utils check-auth
```

### "HuggingFace token required for diarization"

**Problem:** No HuggingFace token for speaker detection

**Solution Option 1 - Get token:**
```bash
# Get free token from https://huggingface.co/settings/tokens
# Add to env.production:
echo "HUGGINGFACE_TOKEN=hf_your_token" >> env.production
```

**Solution Option 2 - Skip diarization:**
```bash
# Process without speaker attribution
clipscribe process video.mp3 --no-diarize
```

### Processing is slow

**Problem:** Local processing takes time

**Explanation:**
- WhisperX Local runs on your CPU/GPU
- Expected: 1-2x realtime (30min video = 30-60min processing)
- This is normal for local processing

**Faster options:**
- Use shorter videos for demos
- Use WhisperX Modal (cloud GPU, 10x realtime)
- Use Voxtral (API, very fast but no speakers)

### "Modal app not found"

**Problem:** Trying to use whisperx-modal without Modal setup

**Solution:** Use WhisperX Local instead (FREE and doesn't need Modal)
```bash
clipscribe process video.mp3 -t whisperx-local
```

**Note:** Modal provider is for cloud GPU (advanced setup required)

---

## What You're Responsible For

**As a collaborator:**

1. **Keep API keys secure**
   - Don't share with others
   - Don't commit to Git
   - Store in env.production (git-ignored)

2. **Be considerate with shared keys**
   - If using Zac's keys, don't process 100 videos
   - Stick to test videos for demos
   - Ask before high-volume processing

3. **Report issues**
   - If you find bugs, open GitHub issue
   - If docs are wrong, let Zac know
   - If something doesn't work, troubleshoot

4. **Provide feedback**
   - What's confusing?
   - What's missing?
   - What could be better?

---

## Getting Help

**Questions about:**

**Setup/Installation:**
- Check docs/TROUBLESHOOTING.md first
- Check docs/DEVELOPMENT.md for dev setup
- GitHub Issues for bugs

**Demo/Usage:**
- This guide (COLLABORATOR_SETUP.md)
- docs/CLI.md for command reference
- examples/ folder for examples

**Features/Capabilities:**
- docs/OUTPUT_FORMAT.md for format details
- docs/PROVIDERS.md for provider info
- examples/sample_outputs/ for real examples

**Stuck?**
- Email: zforristall@gmail.com
- Response time: 24-48 hours
- GitHub Issues for bugs

---

## Useful Commands Reference

```bash
# Check version
clipscribe --version

# Check authentication
clipscribe utils check-auth

# Process with local (FREE)
clipscribe process video.mp3 -t whisperx-local

# Process with all formats
clipscribe process video.mp3 --formats all

# Process series
clipscribe process-series files.txt --series-name "Series-Name"

# Different providers
clipscribe process video.mp3 -t voxtral            # Cheap, no speakers
clipscribe process video.mp3 -t whisperx-local     # FREE, with speakers
clipscribe process video.mp3 -t whisperx-modal     # Cloud, fast

# Disable diarization (faster)
clipscribe process video.mp3 --no-diarize

# Custom output location
clipscribe process video.mp3 -o my_results/
```

---

## What ClipScribe Does (Elevator Pitch)

**For when people ask "What is this?"**

"ClipScribe extracts structured intelligence from videos. Upload a video, get entities, relationships, topics, and insights in 5 formats (JSON, DOCX, CSV, PPTX, Markdown). It's open source (MIT licensed) - run it yourself for free or use the paid managed service. Built with WhisperX for transcription and Grok for intelligence extraction."

**Key Points:**
- Open source, MIT licensed
- Extracts intelligence (not just transcription)
- 5 output formats for different workflows
- FREE to run yourself, $25-500 for managed service
- Multi-speaker support (up to 12 speakers)
- Series analysis (cross-video patterns)

---

## Next Steps After Setup

**Once you're running:**

1. **Try all 3 providers** - See cost/quality differences
2. **Generate all 5 formats** - Understand use cases
3. **Process a series** - See cross-video intelligence
4. **Open outputs in apps** - DOCX in Docs, CSV in Sheets, PPTX in Slides
5. **Provide feedback** - What works, what doesn't
6. **Help demo** - Show others how it works

---

**Status:** Ready for Collaborators  
**Contact:** zforristall@gmail.com  
**GitHub:** https://github.com/bubroz/clipscribe  
**License:** MIT - Use freely!

