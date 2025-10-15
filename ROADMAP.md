# ClipScribe Roadmap - Canonical Version

**Last Updated**: October 15, 2025  
**Current Version**: v2.54.1  
**Status**: Private alpha, actively used

---

## Vision Statement

**ClipScribe extracts objective intelligence from video content through transcription, entity identification, and relationship mapping.**

Built for journalists, researchers, and intelligence analysts who need to process video content at scale with zero censorship and professional-grade accuracy.

---

## Core Principles

1. **Uncensored Intelligence**: No content filtering or safety blocks
2. **Cost-First Design**: Optimize for $0.03-0.05 per video
3. **Batch-Ready**: Process 10-100 videos efficiently
4. **Export Flexibility**: Multiple formats for different workflows
5. **Professional Quality**: 95%+ accuracy on transcription

---

## Current State (v2.54.1)

### ✅ What Works
- **Voxtral + Grok-4 Pipeline**: Uncensored transcription and extraction
- **1800+ Platform Support**: YouTube, Twitter, TikTok, Vimeo, etc.
- **Entity Extraction**: Dense extraction with confidence scores and evidence quotes
- **Knowledge Graphs**: Relationship mapping with timestamps
- **Multiple Output Formats**: JSON, CSV, Markdown, GEXF
- **Cost Efficiency**: $0.03/video average

### 🔧 Recent Additions
- SQLite database for searchable entity archive
- Enhanced error handling and categorization
- Database reprocessing support
- Hybrid processor as default pipeline

### ⚠️ Known Limitations
- YouTube URLs blocked from datacenter IPs (VPS)
- No web interface yet (CLI only)
- No batch processing (one video at a time)
- Manual workflow for multiple videos

---

## Phase 1: Production Readiness (NOW - Nov 2025)

**Goal**: Make ClipScribe production-ready for daily journalism use

### 1.1 Batch Processing (Priority #1)
**Timeline**: 2 weeks  
**Impact**: Process 10-50 videos in one command

**Features**:
```bash
# Batch from file
clipscribe batch urls.txt --output-dir results/

# Batch from clipboard
clipscribe batch --clipboard

# Monitor progress
clipscribe batch status --job-id abc123
```

**Implementation**:
- Async processing with worker pool
- Progress tracking and resumable jobs
- Error recovery and retry logic
- Cost estimation before processing

### 1.2 Entity Search Database (Priority #2)
**Timeline**: 1 week  
**Impact**: Search across all processed videos

**Features**:
```bash
# Search entities
clipscribe search "Raytheon" --output csv

# Find relationships
clipscribe search-relations "Trump" "Ukraine"

# List all videos
clipscribe library --recent 20

# Stats
clipscribe stats --period 30days
```

**Implementation**:
- Integrate existing SQLite schema
- CLI commands for search and browse
- Export search results
- Cost tracking and reporting

### 1.3 VPS Worker Architecture (Priority #3)
**Timeline**: 1 week  
**Impact**: 24/7 background processing

**Architecture**:
```
Local CLI          VPS Worker
   ↓                  ↓
Download videos → Upload to R2 → VPS processes
   ↓                              ↓
                               Store results
   ↓                              ↓
Fetch results  ← R2 storage  ← Complete
```

**Features**:
- Submit jobs to VPS from local CLI
- VPS runs 24/7 processing queue
- R2 storage for videos and results
- Email/webhook notifications when complete

**Benefits**:
- Your laptop doesn't need to stay on
- Residential IP for downloads (local)
- VPS for compute (datacenter is fine)
- Process overnight batches

---

## Phase 2: Intelligence Enhancement (Dec 2025 - Jan 2026)

**Goal**: 50% improvement in extraction quality and usefulness

### 2.1 Timeline Intelligence
**Features**:
- Extract dates and temporal markers from transcript
- Build chronological event sequences
- TimelineJS export for visual timelines
- "When was X mentioned?" queries

### 2.2 Advanced Entity Normalization
**Features**:
- Cross-video entity deduplication
- "Joe Biden" = "Biden" = "President Biden"
- Entity linking across videos
- Authority scores based on mention frequency

### 2.3 Enhanced Outputs
**Formats**:
- TimelineJS3 (chronological visualization)
- Sigma.js (interactive graphs)
- PowerBI templates (business intelligence)
- Obsidian markdown (knowledge management)

---

## Phase 3: Web Interface (Feb 2026 - Mar 2026)

**Goal**: Modern web UI for browsing and analysis

### 3.1 Core Web Dashboard
**Features**:
- Upload videos (drag & drop, unlimited size)
- Browse processed videos (grid/list view)
- Advanced search with filters
- Video playback with entity overlays
- Export reports (PDF, CSV)

### 3.2 Interactive Visualization
**Features**:
- Graph explorer (nodes = entities, edges = relationships)
- Timeline view (chronological events)
- Entity detail pages (all mentions across videos)
- Relationship explorer (how entities connect)

### 3.3 API Layer
**Endpoints**:
```
POST /api/process       # Submit video
GET  /api/status/:id    # Check progress
GET  /api/video/:id     # Get results
GET  /api/search        # Search entities
GET  /api/stats         # Usage stats
```

---

## Phase 4: Collaboration Features (Apr 2026 - Jun 2026)

**Goal**: Team-based intelligence sharing (for Station10 Media)

### 4.1 Multi-User Support
**Features**:
- User authentication (email/password)
- Per-user budgets and tracking
- Shared knowledge graph (opt-in)
- Private video libraries

### 4.2 Collections & Sharing
**Features**:
- Create collections (group videos by topic)
- Share collections with team members
- Collaborative annotations
- Export collection reports

### 4.3 Advanced Search
**Features**:
- Full-text search across transcripts
- Filter by date, user, cost, entity count
- Saved searches
- Search alerts ("notify me when X is mentioned")

---

## Phase 5: Enterprise Features (Jul 2026+)

**Goal**: Scale to large organizations

### 5.1 Plugin Architecture
- Custom extractors
- Output format plugins
- Integration hooks (Slack, Teams, etc.)

### 5.2 Advanced Analytics
- Trend analysis across video corpus
- Entity co-occurrence patterns
- Sentiment tracking over time
- Influence mapping

---

## Non-Goals (What We Won't Build)

❌ **Social media posting** - ClipScribe is intelligence extraction, not distribution  
❌ **Video editing** - Extract data, don't create videos  
❌ **Real-time streaming** - Batch processing focus  
❌ **AI chat interface** - Structured data extraction, not conversation  
❌ **Mobile apps** - Web interface is sufficient  

---

## Success Metrics

### Phase 1 (Production Readiness)
- Process 50+ videos in single batch
- <5% failure rate
- Search 1000+ videos in <1 second
- VPS processes videos 24/7 unattended

### Phase 2 (Intelligence)
- 95%+ entity extraction accuracy
- Timeline extraction from 80% of videos
- Cross-video entity linking working

### Phase 3 (Web Interface)
- Upload videos >10GB
- Interactive graph exploration
- <2 second page load times

### Phase 4 (Collaboration)
- 3-10 users actively collaborating
- Shared knowledge graph across team
- Per-user cost tracking accurate

---

## Technology Stack

### Core Pipeline
- **Transcription**: Voxtral (Mistral, uncensored)
- **Intelligence**: Grok-4 (xAI, uncensored)
- **Video Download**: yt-dlp + curl-cffi
- **Processing**: Python 3.12 + Poetry

### Infrastructure (Current)
- **Local Development**: macOS
- **VPS**: Linux (for batch workers)
- **Storage**: Local files + future R2/S3
- **Database**: SQLite (local), future PostgreSQL (multi-user)

### Infrastructure (Future)
- **Web Framework**: FastAPI or Django
- **Frontend**: React or Vue.js
- **Deployment**: Docker + Cloud Run
- **Storage**: Cloudflare R2

---

## Decision Log

### October 2025: Telegram Bot Exploration
**Decision**: Explored Telegram bot for Station10 Media  
**Result**: Valuable learnings (hybrid processor, database schema, VPS setup)  
**Action**: Salvaged core components, returned to CLI-first roadmap  
**Rationale**: Web interface + batch processing better serves journalism workflow  

### September 2025: Voxtral + Grok-4 Integration
**Decision**: Replace Gemini with Voxtral + Grok-4  
**Result**: 70% cost reduction, zero censorship, 1.8% WER  
**Action**: Made hybrid processor the default  
**Rationale**: Professional intelligence work requires uncensored pipeline  

---

## Current Focus (October 2025)

**Next 2 Weeks**:
1. Implement batch processing CLI
2. Integrate entity search database
3. Design VPS worker architecture

**Next Month**:
1. Deploy VPS batch worker
2. Test with 50-video batch
3. Begin timeline intelligence extraction

**Next Quarter**:
1. Timeline intelligence (Phase 2.1)
2. Advanced entity normalization (Phase 2.2)
3. Plan web interface architecture (Phase 3)

---

**This is the single source of truth for ClipScribe development.**

All other roadmap documents are archived in `archive/` for historical reference.

