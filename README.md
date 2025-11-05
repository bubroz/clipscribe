# Station10.media (ClipScribe)

**Video intelligence extraction platform - Production-ready core engine**

Extract speakers, entities, relationships, and intelligence from any video.  
Built for journalists, researchers, and analysts who need professional-grade accuracy without censorship.

**Current Status:** v2.61.0 - API-first with Grok-4 Structured Outputs - November 4, 2025  
**Production Stack:** WhisperX transcription (Modal GPU), Grok-4 Fast Reasoning, search APIs validated  
**Latest Validation:** Structured Outputs (Nov 1), API tests 14/14 passing (Nov 4), ready for Chimera

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

## Planned Features (In Development)

### Week 2-4: API-First Development
- **Topic Search API:** Find videos by topic with relevance filtering ✅ COMPLETE
- **Entity Search API:** Track people/orgs across videos (18 spaCy types) ✅ COMPLETE
- **Auto-Clip API:** Generate clips from key_moments with intelligence scoring
- **Batch Processing:** Multi-video intelligence with progress tracking
- **Chimera Integration:** API-to-API for SAT analysis of video corpus
- **OpenAPI Documentation:** Complete API spec for integrations

### Week 5-8: Production & Integration
- Beta testing with intelligence analysts
- API rate limiting and authentication
- Chimera integration (SAT analysis of video corpus)
- Data provider API (intelligence-as-a-service for government/enterprise)

### Future (Optional)
- Simple web interface (if customers demand visual interface)
- Chimera UI integration (SAT analysis results viewer)

**Target Launch:** December 2025 (API beta + Chimera integration)

---

## Tech Stack

**Current Production:**
- **Transcription:** WhisperX on Modal Labs (A10G GPU, 11.6x realtime)
- **Speaker Diarization:** pyannote.audio with adaptive thresholds
- **Intelligence:** Grok-4 (xAI) for entity extraction, relationships, topics, key moments
- **Deduplication:** Advanced fuzzy matching (ported from EntityNormalizer)
- **Storage:** Google Cloud Storage (transcripts, results, artifacts)
- **Development:** Python 3.12, Poetry, async processing

**Planned (Future):**
- **Air-gapped Option:** Voxtral transcription for systems without internet access
- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Backend API:** FastAPI, PostgreSQL, Cloud Run
- **Auth:** Clerk or similar
- **Billing:** Stripe

---

## Validation Results (Grok-4 Fast Reasoning, Oct 29, 2025)

**Test Videos:**
- All-In Podcast (88min, 4 speakers): 107 entities, 6 relationships, 5 topics
- The View (36min, 5 speakers): 56 entities, 8 relationships, 3 topics  
- MTG Interview (71min, 2 speakers): 124 entities, 7 relationships, 5 topics

**Grok-4 Quality Improvement:**
- Total entities: 287 (vs 625 with Grok-2) - more selective, higher quality
- Entity evidence: 100% coverage (vs 0% with Grok-2)
- Topics: 13 extracted with relevance + time ranges (NEW!)
- Key moments: 13 with timestamps + significance (NEW!)
- Sentiment: All 3 videos analyzed (NEW!)

**API Validation (Nov 1, 2025):**
- Search APIs: 14/14 tests passing
- Query performance: <100ms average
- Database: 13 topics, 287 entities indexed

**Latest Results:** See `STRUCTURED_OUTPUTS_RESULTS.md` (Nov 1, 2025)

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

**Product:** Station10.media (ClipScribe)  
**Repository:** Private during development  
**License:** Proprietary

---

**Last Updated:** November 4, 2025 - v2.61.0 Structured Outputs implemented, APIs validated, ready for Chimera
