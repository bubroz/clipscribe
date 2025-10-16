# ClipScribe

Extract intelligence from videos. Transcribe, identify entities, map relationships.

**v2.55.0** - SaaS development, Week 1 Day 1 complete  
**Stack**: Voxtral + Grok-4 (uncensored)

---

## What This Does

Takes a video, pulls out:
- Complete transcript
- Every entity mentioned (people, organizations, topics)
- Who said what about whom (with direct quotes)
- Executive summary
- Knowledge graph

Saves it all as JSON + readable reports. Optionally generates X post drafts if you want to share it.

Built for monitoring video content. Turns out structured intelligence extraction is useful for more than just social media.

## Quick Start

```bash
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
poetry install

# Add to .env:
VOXTRAL_API_KEY=your_key
XAI_API_KEY=your_key
```

Process a video:
```bash
poetry run clipscribe process video "https://youtube.com/watch?v=..."
```

Monitor a channel:
```bash
poetry run clipscribe monitor-async --channels UCxxx --interval 300 --workers 10
```

That's it. Everything else is in `docs/CLI_REFERENCE.md`.

## Output Files

Each video generates:
- `core.json` - Entities, relationships, complete summary
- `transcript.txt` - Full transcript
- `knowledge_graph.json` - Graph data
- `report.md` - Readable intelligence report
- `metadata.json` - Video info

Run with `--with-x-draft` to also get:
- `x_draft/` folder with 3 tweet styles
- Mobile preview page (GCS)
- Telegram notification

The intelligence files are the valuable part. X stuff is optional.

## Current State

**What works** (tested Oct 2025):
- YouTube monitoring via RSS
- 10 concurrent workers (processes 10 videos at once)
- Shorts automatically filtered
- Dense entity extraction (30-87 per video)
- Telegram notifications (100% delivery with retry)
- Complete summaries (no cutoffs)
- 3 tweet styles that actually sound different

**What doesn't**:
- Only YouTube (no direct scrapers for senate.gov, granicus, etc)
- Entity deduplication is basic (Biden vs Joe Biden = separate entities)
- Grok API flakes out sometimes (~10% of chunks fail, retries fix most)
- Memory leak workaround (workers restart every 100 videos to prevent crash)

**Test results**: FoxNews monitoring ran 8 videos, 8/8 successful, no crashes. It works.

## Tech Details

- **Transcription**: Voxtral-mini-2507 (Mistral API, $0.002/min, uncensored)
- **Extraction**: Grok-4 (xAI, uncensored, good at entities)
- **Architecture**: Python 3.12 asyncio, 10-worker pool
- **Downloads**: yt-dlp with curl-cffi impersonation
- **Storage**: GCS for mobile pages (optional)
- **Notifications**: Telegram (optional)

Cost averages $0.03-0.06 per video depending on length and entity density.

## Status

Personal alpha. One user. Built for video monitoring workflow, using daily.

Validated on news content. Works reliably. Has some rough edges (memory leak workaround, Grok flakiness) but functional.

Not taking other users. Might never be a product. Might stay a personal tool. We'll see.

## Contact

Zac Forristall  
zforristall@gmail.com  
Amateur

---

**Last updated**: October 12, 2025
