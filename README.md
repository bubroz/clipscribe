# ClipScribe

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](CHANGELOG.md)
[![Providers](https://img.shields.io/badge/providers-3%20transcription%20%2B%201%20intelligence-blue.svg)](#how-it-works)

**Intelligence extraction platform for video and audio**

Extract structured, evidence-based intelligence from video content. Get entities, relationships, speaker attribution, and temporal context in machine-readable format.

---

## What You Get

Process a 30-minute video and receive **50-70+ structured data points:**

### Transcript Intelligence
- **Speaker-attributed segments** with timestamps (WhisperX providers)
- **Word-level timing** for precise navigation (WhisperX providers)
- **Language detection** (auto, all providers)
- **Up to 12 speakers** detected and labeled (validated with WhisperX)

### Entity Extraction
- **Named entities** (people, organizations, locations, events)
- **18 entity types** (PERSON, ORG, GPE, EVENT, PRODUCT, MONEY, DATE, TIME, etc.)
- **Evidence quotes** for every entity (100% coverage)
- **Confidence scores** (0-1) for extraction quality

**Example:**
```json
{
  "name": "Alex Karp",
  "type": "PERSON",
  "confidence": 1.0,
  "evidence": "Alex Karp, thanks for having us into the Palantir lair..."
}
```

### Relationship Mapping
- **Connections between entities** (who-said-what-about-whom)
- **Action predicates** (announced, criticized, invested_in, etc.)
- **Evidence quotes** supporting each relationship
- **Subject-predicate-object structure** (graph-ready format)

**Example:**
```json
{
  "subject": "Trump",
  "predicate": "announced",
  "object": "Gaza ceasefire deal",
  "evidence": "President Trump scores an international win with the Gaza ceasefire deal",
  "confidence": 1.0
}
```

### Topic Analysis
- **Main themes** with relevance scores
- **Time ranges** (when each topic discussed)
- **Temporal context** (MM:SS format)

**Example:**
```json
{
  "name": "Government Shutdown and ACA Subsidies",
  "relevance": 1.0,
  "time_range": "00:00-15:00"
}
```

### Key Moments
- **Significant points** with exact timestamps
- **Significance scoring** (0-1)
- **Supporting quotes** for each moment

**Example:**
```json
{
  "timestamp": "00:30",
  "description": "Trump's Gaza ceasefire achievement contrasting with domestic shutdown",
  "significance": 0.9,
  "quote": "President Trump scores an international win with the Gaza ceasefire deal, but the battle at the Capitol rages on"
}
```

### Sentiment Analysis
- **Overall sentiment** (positive, negative, neutral, mixed)
- **Per-topic sentiment** (nuanced analysis)
- **Confidence scores**

**Example:**
```json
{
  "overall": "mixed",
  "confidence": 0.9,
  "per_topic": {
    "Government Shutdown": "negative",
    "Gaza Ceasefire": "positive",
    "Jennifer Aniston Interview": "neutral"
  }
}
```

### Output Formats

**Five export formats for every workflow:**

**JSON** (default) - Complete structured data:
- Machine-readable (Pandas, SQL, any analysis tool)
- Evidence-based (verifiable, citable)
- Structured (consistent schema)
- Cost-tracked (know exactly what you spent)

**DOCX** - Professional reports:
- Google Docs, Microsoft Word, Apple Pages compatible
- Executive summary, entities table, relationships with evidence
- Share with non-technical stakeholders

**CSV** - Data analysis (5 files):
- entities.csv, relationships.csv, topics.csv, key_moments.csv, segments.csv
- Excel, Google Sheets, Numbers compatible
- Import to databases, Pandas, R

**PPTX** - Executive presentations:
- 7-slide deck for stakeholder briefings
- Google Slides, PowerPoint, Keynote compatible
- Ready to present

**Markdown** - Searchable documentation:
- GitHub-flavored markdown
- VS Code, Obsidian compatible
- Version control friendly

**Choose formats with `--formats` flag:**
```bash
clipscribe process video.mp3 --formats json docx csv
clipscribe process video.mp3 --formats all  # All 5 formats
```

**Complete schema reference:** [docs/OUTPUT_FORMAT.md](docs/OUTPUT_FORMAT.md)

---

## How It Works

### Three Processing Options

Choose optimal provider for your use case:

| Provider | Cost (30min) | Speakers | Speed | Best For |
|----------|--------------|----------|-------|----------|
| **Voxtral** | $0.03 | ❌ | API (seconds) | Single-speaker, budget |
| **WhisperX Local** | **FREE** | ✅ | 1-2x realtime | Privacy, multi-speaker, zero cost |
| **WhisperX Modal** | $0.06 | ✅ | 10x realtime | Professional quality, scalability |

*Plus intelligence extraction: ~$0.005 per video*

### Quick Start

```bash
# Install
poetry install

# Set API keys (choose your providers)
export XAI_API_KEY=your_key                  # Required (Grok intelligence)
export MISTRAL_API_KEY=your_key              # For Voxtral provider
export HUGGINGFACE_TOKEN=your_token          # For local speaker diarization

# Optional: For Modal cloud GPU provider
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export GCS_BUCKET=your-bucket

# Process a file
clipscribe process interview.mp3

# Results saved to: output/timestamp_filename/transcript.json
```

**That's it.** Single command, comprehensive intelligence extracted.

---

## Use Cases

### Research & Analysis
**Problem:** 100 hours of interview footage, need structured data  
**Solution:** Process all 100 hours for $6 (local) or $12 (cloud GPU), get:
- Complete entity database (people, orgs, locations mentioned)
- Relationship network (who said what about whom)
- Topic timeline (when each subject discussed)
- Searchable, citable, evidence-based

**Value:** Structured data for import into research databases, visualization tools, or analysis pipelines.

### Legal & Compliance
**Problem:** Depositions, hearings, recordings need speaker attribution  
**Solution:** Upload files, get:
- Speaker-attributed transcripts
- Evidence-based entity extraction
- Searchable by person, organization, topic
- Export to JSON, DOCX, CSV, PPTX, Markdown - choose formats for your workflow

**Value:** Faster discovery, verifiable citations, speaker accountability, professional reports.

### Financial Intelligence
**Problem:** Earnings calls, investor presentations need competitive intelligence  
**Solution:** Process corpus of calls, extract:
- Company mentions with context
- Executive statements (attributed to speaker)
- Competitive relationships
- Temporal trends

**Value:** Structured data for financial analysis tools, competitive intelligence databases.

### Content Production
**Problem:** Podcast/video archives need metadata, show notes  
**Solution:** Automated extraction of:
- Speaker segments (who spoke when)
- Key moments with timestamps
- Topic timeline
- Entity mentions (people, companies referenced)

**Value:** Automated show notes, searchable archives, content discoverability.

---

## Why ClipScribe

**vs Traditional Transcription** (Rev.ai, AssemblyAI):
- ✅ We extract intelligence, not just words
- ✅ Structured entities + relationships
- ✅ Evidence-based (every claim citable)
- ✅ Often cheaper ($0.003-0.06 vs $0.60-1.20 per 30min)

**vs Manual Analysis:**
- ✅ Process 1000 hours in 12-24 hours (10 GPUs)
- ✅ Consistent extraction (no human variance)
- ✅ Machine-readable output (direct to analysis tools)
- ✅ ~$100-200 vs $50k+ manual transcription + analysis

**Unique Advantages:**
- Speaker attribution (who said what)
- Evidence for every extraction (verifiable)
- Relationship mapping (connections between entities)
- Temporal context (when topics discussed)
- Flexible deployment (local FREE to cloud GPU)

---

## Technical Specs

**Validated Performance:**
- **Processing:** 1-10x realtime (CPU to GPU)
- **Multi-speaker:** Up to 12 speakers detected (validated)
- **Accuracy:** 97-99% transcription (WhisperX large-v3)
- **Entity Coverage:** 18 spaCy entity types
- **Output Size:** ~1MB JSON per 30min video (rich data!)

**Data Per Video (Typical 30min):**
- 17-45 entities with evidence
- 5-11 relationships with quotes
- 5-6 topics with time ranges
- 4-6 key moments with timestamps
- Complete sentiment analysis
- Speaker-attributed transcript

**Deployment Options:**
- Local (Apple Silicon/CPU): FREE, privacy-focused
- Cloud GPU (Modal): Scalable, 10x realtime
- API-first (GCS upload): Enterprise-ready

---

## Installation

```bash
git clone https://github.com/bubroz/clipscribe
cd clipscribe
poetry install

# Configure (see docs/CLI.md for details)
cp .env.example .env
# Add your API keys

# Process your first file
clipscribe process audio.mp3

# Output: output/timestamp_filename/transcript.json
```

**Complete documentation:** [docs/](docs/)

---

## Documentation

- **[CLI Reference](docs/CLI.md)** - Complete command guide
- **[Provider Selection](docs/PROVIDERS.md)** - Choose optimal provider
- **[API Reference](docs/API.md)** - GCS upload flow
- **[Local Processing](docs/LOCAL_PROCESSING.md)** - FREE Apple Silicon guide
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Performance](docs/PERFORMANCE_BENCHMARKS.md)** - Validated metrics

---

## What's New in v3.0.0

**Multi-Format Export System:**
- 5 output formats: JSON, DOCX, CSV, PPTX, Markdown
- Universal compatibility (Google Workspace, Microsoft Office, Apple iWork)
- `--formats` flag for format selection
- Professional reports, executive decks, data tables

**Series Analysis Command:**
- `process-series` for cross-video intelligence
- Entity frequency tracking across videos
- Relationship pattern detection
- Topic evolution analysis
- Aggregate insights and statistics

**Provider Architecture:**
- Swappable transcription providers (Voxtral, Local, Cloud GPU)
- Cost flexibility (FREE to $0.06 per 30min)
- Provider selection via CLI flags

**File-First Design:**
- Process local files (no URL dependencies)
- More reliable (no download complexity)
- Privacy-focused option (local processing)

**Comprehensive Intelligence:**
- Evidence-based extraction (100% coverage)
- Speaker attribution (up to 12 speakers)
- Temporal context (time ranges, timestamps)
- Machine-readable and human-readable formats

**Validated:**
- Multi-speaker (12 speakers detected)
- File formats (MP3, MP4)
- All 3 providers working
- All 5 export formats tested

---

## Example Output

**From 30min interview:**

**Entities:** 17-45 with evidence  
**Relationships:** 5-11 with quotes  
**Topics:** 5-6 with time ranges  
**Speakers:** 2-12 detected  
**Cost:** $0.003-0.06  
**Processing:** 3-60 minutes  

**Output Format:** Comprehensive JSON (import into Pandas, SQL, visualization tools, research databases)

---

## Project Status

**Version:** v3.0.0  
**Released:** November 13, 2025  
**Status:** Production-ready with multi-format exports and series analysis  
**Providers:** 3 transcription, 1 intelligence (all validated)

**Features:** Multi-format exports (JSON, DOCX, CSV, PPTX, Markdown) + Series analysis

---

## Contact

**Developer:** Zac Forristall  
**Email:** zforristall@gmail.com  
**GitHub:** [@bubroz](https://github.com/bubroz)

**License:** MIT  
**Repository:** https://github.com/bubroz/clipscribe
