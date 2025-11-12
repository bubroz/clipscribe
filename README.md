# ClipScribe

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-24%2F24%20passing-success.svg)](tests/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Version](https://img.shields.io/badge/version-2.62.0-blue.svg)](CHANGELOG.md)
[![GPU](https://img.shields.io/badge/GPU-A10G%2024GB-green.svg)](deploy/station10_modal.py)
[![Cost](https://img.shields.io/badge/cost-$0.073%2Fvideo-orange.svg)](#validation-results-nov-12-2025---v2620)

**AI-powered video intelligence extraction**

Extract speakers, entities, relationships, and intelligence from any video.  
Built for anyone who needs professional-grade accuracy without censorship.

**Current Status:** v2.62.0 - xAI November 2025 Features + Enhanced Modal Pipeline - November 12, 2025  
**Production Stack:** WhisperX (Modal GPU, 10-11x realtime), Grok-beta (xAI), Prompt Caching (50% savings)  
**Latest Validation:** 20 videos processed (754min total), $0.073/video avg, 556 entities extracted, 100% test pass rate

---

## Current Capabilities (Validated & Working)

### Transcription & Speaker Intelligence
- **WhisperX transcription** - 97-99% accuracy, medical/legal grade quality
- **Speaker diarization** - Automatic speaker detection and segmentation (pyannote.audio)
- **Multi-speaker handling** - Tested up to 5 speakers with adaptive thresholds
- **Processing speed** - 11.6x realtime on A10G GPU (16min video → 1.4min processing)

### Entity Extraction (Production-Validated)
- **18 entity types** (spaCy standard): PERSON, ORG, GPE, LOC, EVENT, PRODUCT, MONEY, DATE, TIME, FAC, NORP, LANGUAGE, LAW, WORK_OF_ART, CARDINAL, ORDINAL, QUANTITY, PERCENT
- **Relationship mapping** - Connections between entities with confidence scores
- **Topics extraction** - Main themes with relevance scores
- **Key moments** - Important points with timestamps and significance scores
- **Sentiment analysis** - Overall and per-topic sentiment
- **Advanced deduplication** - Fuzzy matching (0.80 threshold), title removal, 99.5% unique entities

### Quality Metrics (Grok-4 Fast Reasoning, Oct 29, 2025)
- **Entity quality:** Selective, named entities only (no noise like "98%", "thursdays")
- **Evidence coverage:** 100% (all entities have supporting transcript quotes)
- **Entity type coverage:** 17/18 spaCy types (PERSON, ORG, GPE, EVENT, etc.)
- **Topics extracted:** 3-5 per video with relevance scores and time ranges
- **Key moments:** 4-5 per video with timestamps and significance
- **Processing cost:** $0.34 per video (WhisperX $0.33 + Grok-4 $0.01)

---

## 🚀 New in v2.62.0: xAI November 2025 Features

### Prompt Caching (50% Cost Reduction)
- **Automatic caching** for prompts >1024 tokens - 50% discount on cached content
- **Smart cache management** - Reuses context across related videos
- **Savings tracking** - Real-time monitoring of cache hit rates and cost savings
- **Zero configuration** - Works automatically, no code changes needed

### Intelligence & Fact-Checking
- **Grok fact-checking** - Verify entities against real-time knowledge (web_search, x_search)
- **Entity enrichment** - Add current context to extracted entities
- **Server-side tools** - Web search, X/Twitter search integrated
- **Confidence scoring** - Track reliability of fact-checked information

### Knowledge Base Management
- **Video collections** - Organize videos into semantic collections
- **Cross-video search** - Find entities and topics across entire knowledge base
- **Entity tracking** - Monitor people/organizations across multiple videos
- **Relationship discovery** - Find co-occurrences and connections

### Enhanced Modal Pipeline
- **Robust language detection** - Multi-sample validation (start/middle/end of audio)
- **GPU OOM protection** - Cascading batch size retry (16→8→4→2→1) handles any video
- **Language validation** - Prevents false positives, never forces English
- **Enhanced cost tracking** - Detailed GPU + Grok breakdowns with cache savings

### Production-Validated Metrics (Nov 12, 2025)
- **Videos processed:** 20 (754 minutes total, 12.6 hours of content)
- **Entities extracted:** 556 (avg 27.8/video, 12 types)
- **Relationships mapped:** 161 (avg 8.1/video)
- **Topics identified:** 97 (avg 4.8/video)
- **Processing cost:** $0.073/video avg ($0.001935/minute)
- **GPU realtime factor:** 10-11x (71min video → 7min processing)
- **Test coverage:** 100% pass rate (24/24 passing, 0 failures)

---

## Planned Features (In Development)

### In Development
- **Topic Search API:** Find videos by topic ✅ COMPLETE
- **Entity Search API:** Track people/orgs across videos ✅ COMPLETE
- Auto-clip generation from key moments
- Batch processing for multiple videos
- Additional entity extraction features

---

## Tech Stack

**Current Production:**
- **Transcription:** WhisperX on Modal Labs (A10G GPU, 10-11x realtime)
- **Speaker Diarization:** pyannote.audio with adaptive thresholds
- **Intelligence:** Grok-beta (xAI) with structured outputs, prompt caching, server-side tools
- **Fact-Checking:** Web search, X/Twitter search integration for entity verification
- **Knowledge Base:** Collections API for cross-video entity tracking and relationship discovery
- **Deduplication:** Advanced fuzzy matching with evidence-based validation
- **Storage:** Google Cloud Storage (transcripts, results, artifacts)
- **Development:** Python 3.12, Poetry, async processing, 100% test coverage

**Planned (Future):**
- **Air-gapped Option:** Voxtral transcription for systems without internet access
- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Backend API:** FastAPI, PostgreSQL, Cloud Run
- **Auth:** Clerk or similar
- **Billing:** Stripe

---

## Validation Results (Nov 12, 2025 - v2.62.0)

**Production Validation (20 Videos, 754 Minutes):**
- **Total segments:** 9,565 transcript segments processed
- **Entities extracted:** 556 entities (avg 27.8/video)
  - Top types: ORG (41.0%), PERSON (20.9%), GPE (13.8%), PRODUCT (11.0%)
  - 12 distinct entity types with full evidence coverage
- **Relationships mapped:** 161 relationships (avg 8.1/video)
- **Topics identified:** 97 topics (avg 4.8/video)
- **Key moments:** 100 key moments extracted (avg 5.0/video)

**Cost Analysis:**
- **Total cost:** $1.46 for 20 videos (12.6 hours of content)
- **Average per video:** $0.073
- **Average per minute:** $0.001935
- **GPU transcription:** $1.41 (96.3% of cost)
- **Grok extraction:** $0.05 (3.7% of cost)

**Performance Metrics:**
- **Processing speed:** 10-11x realtime on A10G GPU
- **Success rate:** 100% (20/20 videos completed)
- **Quality:** Entity confidence 0.9-1.0 avg, 100% evidence coverage
- **Test coverage:** 24/24 tests passing (100% pass rate)

**Latest Results:** See `output/VALIDATION_REPORT_NOV11.md` for complete analysis

---

## Development

**Clone and install:**
```bash
git clone https://github.com/bubroz/clipscribe.git
cd clipscribe
poetry install
```

**Environment setup:**
```bash
cp .env.example .env
# Required: XAI_API_KEY, HUGGINGFACE_TOKEN, GOOGLE_APPLICATION_CREDENTIALS
```

**Test Modal pipeline:**
```bash
poetry run modal deploy deploy/station10_modal.py
```

**Full roadmap:** See `ROADMAP.md`

---

## Repository Structure

```
clipscribe/
├── src/clipscribe/          # Core Python package
│   ├── processors/          # Video processing pipeline
│   ├── extractors/          # Entity extraction (local)
│   ├── retrievers/          # Video download & transcription
│   ├── exporters/           # Output formatters
│   ├── commands/            # CLI commands
│   └── utils/               # Utilities
├── deploy/                  # Modal GPU deployment
│   └── station10_modal.py   # Production transcription service
├── scripts/                 # Utility scripts
│   └── validation/          # Validation test scripts
├── tests/                   # Test suite
├── examples/                # Usage examples
├── docs/                    # Documentation
│   ├── advanced/testing/    # Test video catalog
│   └── archive/             # Historical docs
└── archive/                 # Archived code (Cloud Run, Streamlit, VPS)
```

---

## Project Status

**Version:** v2.61.0  
**Current Phase:** API-first development, Chimera integration focus  
**Last Major Milestone:** Search APIs validated (Nov 1, 2025) - 14/14 tests passing  
**Next Milestone:** Chimera integration design (Week 3)

**Recent Achievements (Oct 29-Nov 1):**
- Grok-4 Fast Reasoning upgrade (complete intelligence extraction)
- Topic search API (13 topics indexed and searchable)
- Entity search API (287 entities with 100% evidence)
- TUI development and removal (pivoted to API-first)
- Comprehensive validation (14 E2E tests, all passing)

**See:** `STATUS.md` for detailed current state

---

## Contact

**Developer:** Zac Forristall  
**Email:** zforristall@gmail.com  
**GitHub:** [@bubroz](https://github.com/bubroz)

**Product:** ClipScribe  
**Repository:** Private during development  
**License:** Proprietary

---

**Last Updated:** November 4, 2025 - v2.61.0 Structured Outputs implemented, APIs validated, ready for Chimera
