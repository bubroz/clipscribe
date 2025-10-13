# ClipScribe

Video intelligence for government monitoring. Built for tracking political content and generating X posts.

**Version**: 2.54.0 (Oct 2025)  
**Status**: Personal alpha - in active use  
**Stack**: Voxtral transcription + Grok-4 intelligence extraction

---

## What It Does

Extracts intelligence from videos. Transcribes, identifies entities, maps relationships, and generates structured reports.

**Primary output**: Intelligence records (JSON, transcripts, knowledge graphs)  
**Optional feature**: X/Twitter draft generation (one use case among many)

**Real workflow**: Monitor channels → Process new videos → Get intelligence files → Use however you want (X posts, research, archiving, etc.)

Built for real-time intelligence collection.

---

## Quick Start

```bash
# Install
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
poetry install

# Set up API keys in .env
VOXTRAL_API_KEY=your_key
XAI_API_KEY=your_key
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id

# Process one video
poetry run clipscribe process video "https://youtube.com/watch?v=..."

# Monitor a channel (10 workers, checks every 5 min)
poetry run clipscribe monitor-async --channels UCxxx --interval 300 --workers 10
```

---

## What You Get

**Intelligence files** (always):
- `core.json` - All entities, relationships, full summary
- `transcript.txt` - Complete transcript
- `knowledge_graph.json` - Entity/relationship graph
- `report.md` - Formatted intelligence report
- `metadata.json` - Video metadata

**Optional** (with `--with-x-draft`):
- `x_draft/` - 3 tweet styles + thumbnail
- Mobile GCS page for review
- Telegram notification

**The core value is the intelligence extraction.** X drafts are just one way to use it.

**Cost**: $0.03-0.06 per video  
**Time**: 3-5 minutes per video  
**Quality**: 30-87 entities per political video

---

## Current Capabilities (Tested Oct 2025)

**What actually works**:
- YouTube RSS monitoring (auto-detects new uploads)
- Shorts filtering (skips <60 second videos)
- 10-worker async processing (10 videos at once)
- Telegram notifications with retry (100% delivery)
- GCS mobile pages with collapsible summaries
- Complete transcription (no censorship)
- Dense entity extraction (government-focused)
- 3 tweet style generation
- Worker auto-restart (prevents memory corruption after 100 videos)

**What doesn't work**:
- Only YouTube (no direct government site scrapers yet)
- No entity canonicalization (Biden vs Joe Biden = separate)
- Grok API occasionally flaky (~10% chunk failures, retries work)

---

## Tech Stack

- **Transcription**: Voxtral-mini-2507 (Mistral, uncensored)
- **Intelligence**: Grok-4 (xAI, uncensored)
- **Infrastructure**: Python 3.12, asyncio, 10-worker pool
- **Storage**: Google Cloud Storage (72hr retention)
- **Notifications**: Telegram Bot API
- **Downloads**: yt-dlp with browser impersonation

---

## Files

Each video creates:
- `core.json` - Entities, relationships, full summary
- `transcript.txt` - Complete transcript
- `knowledge_graph.json` - Graph data
- `report.md` - Formatted intelligence report  
- `x_draft/` - Tweet options and thumbnail

---

## Use Case

You're monitoring government videos. A new video drops. ClipScribe:
1. Downloads and transcribes it (Voxtral)
2. Extracts entities and relationships (Grok)
3. Generates 3 tweet style options
4. Uploads to GCS with mobile-optimized page
5. Sends you Telegram notification

You tap the notification, see the summary and tweets, pick one, post it. Takes 30 seconds.

That's it. Built for speed and government content.

---

## Installation

Requires:
- Python 3.12
- Poetry
- API keys (Voxtral, xAI, optional Telegram)
- Google Cloud credentials (for GCS uploads)

See `docs/CLI_REFERENCE.md` for command details.

---

## Status

**Currently**: Personal alpha. One user (me). Monitoring government channels for X content.

**Tested**: FoxNews monitoring - 8/8 videos processed successfully, no crashes, all features working.

**Not production** yet. Memory corruption workaround in place (workers restart every 100 videos). Grok API flaky. But it works.

**Future**: Maybe SaaS for political commentators. Maybe not. Depends on if this workflow actually works long-term.

---

## Contact

Zac Forristall  
zforristall@gmail.com  
Amateur

Private repo. Not taking users yet.

---

**Last Updated**: October 12, 2025
