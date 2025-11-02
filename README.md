# Station10.media (ClipScribe)

**Video intelligence extraction platform - Production-ready core engine**

Extract speakers, entities, relationships, and intelligence from any video.  
Built for journalists, researchers, and analysts who need professional-grade accuracy without censorship.

**Current Status:** v2.61.0 - Complete intelligence with Grok-4 Fast Reasoning - October 29, 2025  
**Production Stack:** WhisperX transcription (Modal GPU), Grok-4 Fast Reasoning, complete intelligence extraction  
**Validation Results:** 625 entities, 0.90 confidence, 17/18 entity types, 0.5% duplicates across 3 diverse videos (195min)

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

### Quality Metrics (Validated Oct 28, 2025)
- **Average confidence:** 0.90 (excellent)
- **Entity type coverage:** 17/18 types (94%)
- **Duplicate rate:** 0.5% (3 in 625 entities) - industry-leading
- **High-value entity ratio:** 74.8% (PERSON/ORG/GPE/EVENT focus)
- **Deduplication effectiveness:** 22.7% reduction via fuzzy matching
- **Processing cost:** $0.20-0.42 per video (88min avg)

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

## Validation Results (October 28, 2025)

**Test Videos:**
- All-In Podcast (88min, 4 speakers): 325 entities, 210 relationships, 15 types, 0.91 confidence
- The View (36min, 5 speakers): 86 entities, 12 relationships, 12 types, 0.89 confidence
- MTG Interview (71min, 2 speakers): 214 entities, 140 relationships, 17 types, 0.91 confidence

**Quality Metrics:**
- Total entities: 625 with 0.90 average confidence
- Total relationships: 362 (0.58 per entity average)
- Entity type coverage: 17/18 spaCy standard types
- Duplicate names: 3 across all videos (0.5% rate)
- Deduplication: 22.7% reduction from raw extraction

**Technical Details:** See `FINAL_VALIDATION_ASSESSMENT.md`

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

**Version:** v2.60.0  
**Current Phase:** Core engine complete, intelligence features ready to build  
**Last Major Milestone:** Entity extraction validation complete (Oct 28, 2025)  
**Next Milestone:** Auto-clip generation (Week 5-8)

**Recent Achievements:**
- Grok-4 entity extraction with 18 spaCy types
- Advanced fuzzy deduplication (99.5% unique)
- Transcript chunking for long videos (>45k chars)
- Production validation (625 entities, 0.90 confidence)
- Repository cleanup (archived 86 unused files)

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

**Last Updated:** October 28, 2025 - v2.60.0 production-ready release
