# Station10.media (ClipScribe)

**Video intelligence extraction SaaS - Launching February 2026**

Extract speakers, entities, relationships, and AI-generated clips from any video.  
Built for journalists, researchers, and analysts who need professional-grade accuracy without censorship.

**Status:** v2.58.0 - Comprehensive validation suite planned - Oct 21, 2025  
**Stack:** Dual-mode transcription (Voxtral + WhisperX on Modal GPU), Grok-4 intelligence, serverless infrastructure  
**Validation:** Academic-grade benchmarking in progress (678 hours, 8 datasets, English + Mandarin)

---

## What Station10.media Does

Upload any video or paste a URL, get:

**Transcription:**
- Standard tier: 95% accuracy (Voxtral)
- Premium tier: 97-99% accuracy (WhisperX) - medical/legal grade

**Speaker Intelligence:**
- Automatic speaker diarization (who spoke when)
- AI speaker identification (context-based naming)
- Speaker-entity attribution (who mentioned what)

**Entity Extraction:**
- People, organizations, topics, concepts
- Confidence scores and evidence quotes
- Relationship mapping with timestamps

**Auto-Clip Generation:**
- AI recommendations (newsworthy + viral + info-dense)
- Auto-generate clips as .mp4 files
- Social media captions included

**Search & Analysis:**
- Search entities across all your videos
- Find relationships between topics
- Track mentions over time

---

## Pricing (Planned)

**Pay-per-minute:**
- Standard: $0.10/minute (general content, 95% accurate)
- Premium: $0.20/minute (medical/legal/technical, 99% accurate)

**Subscriptions:**
- Free: 10 minutes trial
- Starter: $39/month (500 minutes)
- Professional: $149/month (2000 minutes + 100 premium)
- Business: $399/month (6000 minutes + 500 premium + API)

**Value:** Replaces Descript ($24/mo) + Opus Clip ($29/mo) + Fireflies ($29/mo) = $82/month of separate tools.

---

## Quality Validation (In Progress)

**Academic-Grade Benchmarking:**
- **678 hours** professional ground truth data
- **8 datasets:** AnnoMI, CHiME-6, AMI, ICSI, AISHELL-4/5, AliMeeting, MAGICDATA
- **Languages:** English, Mandarin, + multilingual support
- **Metrics:** WER, DER, speaker attribution accuracy
- **Timeline:** 9-week comprehensive validation (Oct-Dec 2025)

**Targets:**
- WER (clean): <15% | WER (far-field): <60% | DER: <20%
- Benchmark: Beat CHiME-6 baseline (77.9% → <60%)
- Publication: Interspeech 2026 submission planned

**See:** `VALIDATION_MASTER_PLAN.md` for complete details

---

## Features (In Development)

### Week 1-4: Core Engine (IN PROGRESS)
- [x] Dual-mode transcription (Voxtral + WhisperX)
- [x] Speaker diarization (pyannote.audio) - **VALIDATED Oct 19**
- [x] Modal GPU deployment - **11.6x realtime, 92% margin**
- [ ] Speaker identification (Grok context-based)
- [ ] Entity extraction with speaker attribution
- [x] Multi-speaker validation (1, 3, 7, 10 speakers tested) - **Oct 19-20**
- [ ] Quality improvements (speaker cleanup integration) - **Next session**

### Week 5-8: Intelligence
- [ ] Intelligent clip recommendations (multi-objective)
- [ ] Auto-clip generation (ffmpeg)
- [ ] Entity search database
- [ ] Batch processing

### Week 9-12: Web Interface
- [ ] Next.js frontend
- [ ] Upload interface
- [ ] Live processing status
- [ ] Results viewer (transcript, entities, clips)

### Week 13-14: Production
- [ ] User authentication
- [ ] Stripe billing
- [ ] Email notifications

### Week 15-16: Launch
- [ ] Beta testing (10 users)
- [ ] Public launch
- [ ] Product Hunt

**Target launch:** February 10, 2026

---

## Current Development Status

**What's working:**
- ✅ WhisperX transcription (97-99% accuracy)
- ✅ Speaker diarization (identifies multiple speakers)
- ✅ Voxtral transcription (95% accuracy, fast)
- ✅ Auto-tier selection (medical/legal → premium)
- ✅ Test suite (26 videos, all scenarios covered)

**What's being built:**
- 🔄 Multi-speaker validation (4-5 speaker test in progress)
- ⏳ Speaker identification (Grok-based naming)
- ⏳ Clip recommendation engine
- ⏳ Web interface (starts Week 9)

**Latest:** Week 1 Day 1 complete (Oct 15, 2025)

---

## Tech Stack

**Transcription:**
- Voxtral (Mistral API) - standard tier
- WhisperX (Modal serverless GPU) - premium tier ✅ VALIDATED
- pyannote.audio - speaker diarization

**Intelligence:**
- Grok-4 (xAI) - entity extraction, speaker ID, clip recommendations

**Infrastructure (Planned):**
- Frontend: Next.js (Cloud Run - planned)
- Backend: FastAPI (Cloud Run - planned)
- GPU Workers: Modal Labs (WhisperX transcription) ✅ DEPLOYED
- CPU Workers: Cloud Run Jobs (Voxtral, entity extraction) - planned
- Database: PostgreSQL (Cloud SQL)
- Storage: Google Cloud Storage
- Queue: Cloud Tasks + Pub/Sub

**Development:**
- Python 3.12
- Poetry for dependencies
- Async processing
- Apple Silicon optimized (M3 Max development)

---

## Why Build This?

**Problem:** Processing video content manually takes hours.  
- Watch video, take notes: 1-2 hours
- Find key quotes, identify speakers: 30-60 minutes  
- Create clips for social media: 30-60 minutes
- Total: 2-4 hours per video

**Solution:** Station10.media does it in 5-10 minutes.
- Upload video
- Get transcript with speakers
- Get AI-selected clips ready to share
- Get entity intelligence with relationships

**ROI:** 35:1 time savings ($107 value at $60/hour vs $3 cost)

---

## Differentiation

**vs Competitors:**
- **Descript** ($24/mo): Transcription + editing, NO speaker intelligence, NO auto-clips
- **Opus Clip** ($29/mo): Auto-clips only, NO transcription, NO entities
- **Fireflies** ($29/mo): Basic entities, NO clips, generic speakers

**Station10.media:** All features + speaker-entity attribution + multi-objective clip AI + uncensored

**Pricing:** $149/mo Pro tier vs $82/mo for 3 separate inferior tools

---

## Repository Structure

```
clipscribe/
├── src/clipscribe/          # Core engine (Python)
│   ├── transcribers/        # Voxtral + WhisperX
│   ├── processors/          # Intelligence pipeline
│   ├── database/            # Entity search
│   └── api/                 # FastAPI backend
├── docs/                    # Documentation
│   ├── planning/            # SaaS roadmap, architecture
│   └── advanced/testing/    # Test video suite
├── scripts/                 # Utilities
├── tests/                   # Test suite
└── examples/                # Usage examples
```

---

## Development

**Clone and install:**
```bash
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
poetry install
```

**Set up environment:**
```bash
cp .env.example .env
# Add: MISTRAL_API_KEY, XAI_API_KEY, HUGGINGFACE_TOKEN
```

**Test transcription:**
```bash
poetry run python scripts/test_whisperx.py test_videos/sample.mp3
```

**Full roadmap:** See `ROADMAP.md` and `docs/planning/SAAS_PRODUCT_ROADMAP.md`

---

## Status

**v2.55.0** - Active SaaS development  
**Timeline:** Week 1 of 16 (Oct 15 - Feb 10, 2026)  
**Current:** Building core intelligence features  
**Next:** Speaker identification, clip generation (Week 2-3)  
**Launch:** February 10, 2026 (private beta Week 15, public Week 16)

---

## Contact

Zac Forristall  
zforristall@gmail.com  
[@bubroz](https://github.com/bubroz)

**Product:** station10.media (launching Feb 2026)  
**This repo:** Core engine development (private during development)

---

*Last updated: October 15, 2025 - Week 1 Day 1 complete*
