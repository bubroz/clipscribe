# ClipScribe → Station10.media SaaS Product Roadmap

**Last Updated**: October 15, 2025  
**Current Version**: v2.54.2  
**Product**: Hosted video intelligence SaaS  
**Target Launch**: February 10, 2026 (16 weeks)

---

## Vision Statement

**Station10.media: Turn any video into structured intelligence in minutes.**

Extract speakers, entities, relationships, and auto-generated clips from any video. Built for journalists, researchers, and intelligence analysts who need professional-grade accuracy without censorship.

**Differentiation:**
- Auto-clip generation with AI recommendations
- Speaker identification (who said what)
- Uncensored processing (medical, legal, controversial)
- Multi-tier accuracy (standard vs premium)
- $0.50-1.50/video (vs competitors at $2-5/video)

---

## Core Product Strategy

### Dual-Mode Architecture (SaaS Economics)

#### Standard Tier ($0.75/video)
```
Cost: $0.05/video
Margin: $0.70 (93%)

Pipeline:
- Voxtral transcription (95% accurate, fast, cheap)
- pyannote speaker diarization (identifies speakers)
- Grok speaker identification (context-based naming)
- Grok entity extraction (with speaker attribution)
- Grok clip recommendations (3 objectives)
- ffmpeg auto-clip generation

Processing time: 4-5 minutes
Use case: News, interviews, general content
```

#### Premium Tier ($1.50/video)
```
Cost: $0.30/video (WhisperX on Cloud Run GPU)
Margin: $1.20 (80%)

Pipeline:
- WhisperX transcription (97-99% accurate, built-in diarization)
- Grok speaker identification
- Grok entity extraction
- Grok clip recommendations
- ffmpeg auto-clip generation

Processing time: 5-6 minutes
Use case: Medical, legal, technical, intelligence
```

---

## 16-Week Development Plan

### **Weeks 1-4: Core Intelligence Engine**

**Deliverable**: Voxtral + WhisperX + speakers + entities working in CLI

#### Week 1: Transcription Foundation
- Install WhisperX, test on medical/legal samples
- Benchmark: Voxtral vs WhisperX accuracy
- Build dual-mode transcriber class
- Auto-detection logic (content type → mode selection)
- **Validation**: Confirm WhisperX actually better for technical content

#### Week 2: Speaker Diarization
- Integrate pyannote.audio
- Align speaker segments with transcript
- Format output with speaker timestamps
- Test on multi-speaker content (debates, panels)
- **Validation**: 95%+ speaker segment accuracy

#### Week 3: Speaker Identification
- Grok speaker identification from context
- Confidence scoring (only ID when confident)
- Manual override system
- Test accuracy on known speakers
- **Validation**: 85%+ accuracy when Grok attempts ID

#### Week 4: Entity Extraction with Speakers
- Grok entity extraction with speaker attribution
- Evidence quotes with speaker labels
- Relationship extraction
- **Validation**: Speaker-entity linkage adds value

**CLI at Week 4:**
```bash
clipscribe process video "url" --quality auto
# Output: Transcript with speakers, entities by speaker, relationships
```

---

### **Weeks 5-8: Clip Intelligence & Batch**

**Deliverable**: Clip recommendations, auto-generation, batch processing

#### Week 5: Intelligent Clip Recommendations
- Grok multi-objective optimization (newsworthy + viral + dense)
- Custom prompt support
- Score each clip (3 dimensions)
- Metadata for social media captions
- **Validation**: Would you share these clips?

#### Week 6: Auto-Clip Generation
- ffmpeg frame-accurate clipping
- Metadata sidecar files (.json)
- Interactive approval workflow (CLI)
- Batch clip generation
- **Validation**: Clip quality acceptable for production use

#### Week 7: Entity Search Database
- Database integration (videos, entities, speakers, relationships)
- Search queries (cross-video)
- Speaker-attributed search
- Cost tracking and stats
- **Validation**: Search finds what you expect

#### Week 8: Batch Processing Backend
- Job queue (Cloud Tasks + Pub/Sub)
- Parallel processing (Cloud Run Jobs)
- Progress tracking (Redis)
- Cost estimation before processing
- **Validation**: Can process 25 videos reliably

**CLI at Week 8:**
```bash
clipscribe batch submit urls.txt --auto-clip --quality auto
clipscribe batch status abc123
clipscribe search "Raytheon" --speaker "Biden"
```

---

### **Weeks 9-12: Web Interface (MVP)**

**Deliverable**: Working web app customers can use

#### Week 9: Frontend Foundation
- Next.js + TailwindCSS setup
- Landing page (demo video, pricing)
- Upload interface (file drag-drop, URL paste)
- FastAPI backend (API for frontend)
- **Deliverable**: Can upload videos via web

#### Week 10: Processing UI
- Processing status page (WebSocket live updates)
- Progress visualization
- Speaker detection status
- Error handling UI
- **Deliverable**: Live progress in web

#### Week 11: Results Viewer
- Transcript viewer (speaker highlighting, interactive)
- Entity cards (filterable by speaker)
- Relationship graph (interactive vis)
- Clip recommendations (with scores)
- Select clips → generate → download
- **Deliverable**: Full results exploration

#### Week 12: Account System
- Email magic link signup (no passwords yet)
- User dashboard
- Video library (grid view)
- Usage tracking (videos processed)
- **Deliverable**: Users can create accounts

---

### **Weeks 13-14: Billing & Production**

**Deliverable**: Can charge customers

#### Week 13: Stripe Integration
- Payment methods
- Pay-per-video ($0.75 standard, $1.50 premium)
- Subscription tiers ($30/mo for 50 videos)
- Credits system
- Billing history
- **Deliverable**: Revenue-generating

#### Week 14: Production Polish
- Error handling (user-friendly messages)
- Email notifications (SendGrid)
- Results sharing (public links)
- Help documentation
- Support email setup
- **Deliverable**: Production-ready

---

### **Weeks 15-16: Beta & Launch**

**Deliverable**: Publicly launched

#### Week 15: Private Beta
- 10 beta testers
- Free processing (feedback only)
- Bug fixes
- UX refinements
- Collect testimonials
- **Deliverable**: Product validated

#### Week 16: Public Launch
- Legal docs (ToS, Privacy Policy)
- Demo videos (3 use cases)
- X launch thread
- Product Hunt launch
- Press outreach
- **Deliverable**: PUBLIC

---

## Technical Architecture (SaaS-Optimized)

### Local Development (You, M3 Max)
```
Use: WhisperX for everything
Why: Free GPU, best quality, test all features
Code: Full-featured with all advanced capabilities
```

### Production (Customers, Cloud Run)
```
Standard Tier (95% of customers):
  - Voxtral API transcription
  - pyannote CPU diarization
  - Grok speaker ID + entities + clips
  - Cost: $0.05, Price: $0.75, Margin: $0.70

Premium Tier (5% of customers):
  - WhisperX on Cloud Run GPU
  - Built-in diarization
  - Grok speaker ID + entities + clips
  - Cost: $0.30, Price: $1.50, Margin: $1.20
```

### Database (Multi-User from Day 1)
```sql
-- PostgreSQL on Cloud SQL
users (id, email, credits, subscription_tier)
videos (id, user_id, video_id, status, cost, quality_tier)
entities (video_id, name, type, speaker, confidence)
relationships (video_id, source, target, speaker)
clips (video_id, clip_id, start, end, scores, gcs_path)
```

---

## Cost Projections

### Pre-Launch (16 weeks)
```
Infrastructure: $40/mo × 4 = $160
Testing videos: $0.05 × 500 = $25
Development time: Your time (no cost calculated)
───────────────────────────────────────
Total: ~$185
```

### Post-Launch (Months 1-6)

**Conservative (50 videos/month):**
```
Revenue: 50 × $0.75 = $37.50/mo
Costs:
  - Infrastructure: $40/mo
  - Processing: 50 × $0.05 = $2.50/mo
  - Total: $42.50/mo
Loss: -$5/mo (acceptable, early stage)
```

**Target (200 videos/month):**
```
Revenue: 200 × $0.75 = $150/mo
Costs:
  - Infrastructure: $40/mo
  - Processing: 200 × $0.05 = $10/mo
  - Total: $50/mo
Profit: $100/mo (break-even achieved)
```

**Growth (1000 videos/month):**
```
Revenue: 1000 × $0.75 = $750/mo
Costs:
  - Infrastructure: $40/mo (scales minimally)
  - Processing: 1000 × $0.05 = $50/mo
  - Total: $90/mo
Profit: $660/mo (sustainable)
```

**Break-even: ~150 videos/month**

---

## Pricing Strategy

### Launch Pricing (Competitive)
```
Free Tier:
  - 3 videos free (no credit card)
  - Full features enabled
  - Hook: Let them see the power

Standard:
  - $0.75/video (pay-as-go)
  - OR $25/month (50 videos = $0.50 each)
  - Voxtral + pyannote + all features

Premium:
  - $1.50/video (pay-as-go)
  - OR $50/month (50 videos = $1.00 each)
  - WhisperX + all features
  - "Medical/Legal Grade Accuracy"

Enterprise:
  - Custom pricing
  - API access
  - Dedicated support
  - White-label options
```

### Competitor Comparison
```
Rev.ai: $0.25/minute = $1.25 per 5-min video
  You: $0.75 (40% cheaper)

AssemblyAI: $0.37 per 5-min video
  You: $0.75 (2x more, but with clips + speaker ID)

Descript: $12/mo for 10 hours
  You: $25/mo for 50 videos (~4 hours)
  
Your edge: Auto-clips + speaker ID (they don't have this)
```

---

## MVP Feature Set (What Must Work for Launch)

### Core Features (Must Have)
1. ✅ Upload video (file or URL)
2. ✅ Transcription (Voxtral standard, WhisperX premium)
3. ✅ Speaker diarization (pyannote)
4. ✅ Speaker identification (Grok, 85%+ when confident)
5. ✅ Entity extraction (with speaker attribution)
6. ✅ Clip recommendations (Grok multi-objective)
7. ✅ Auto-generate clips (ffmpeg)
8. ✅ Download clips + full results
9. ✅ User signup + billing (Stripe)
10. ✅ Video library (see all your videos)

### Can Wait for v2 (Nice to Have)
- ⏳ Batch processing (upload 25 videos at once)
- ⏳ Search across videos (entity search)
- ⏳ Timeline visualization
- ⏳ Interactive graph explorer
- ⏳ Team collaboration
- ⏳ API access

---

## Development Workflow (Week 1 Starts Now)

### Your Setup
```bash
# Local development on M3 Max
poetry install
poetry add whisperx pyannote.audio

# Use WhisperX for all local testing
clipscribe process video "medical-video" --quality accurate
# Tests full pipeline locally, validates features

# When features proven, adapt for Cloud Run with Voxtral
```

### Repository Structure
```
clipscribe/                      # Private repo
├── src/clipscribe/              # Core engine
│   ├── transcribers/
│   │   ├── voxtral_transcriber.py    # For SaaS standard tier
│   │   └── whisperx_transcriber.py   # For local dev + premium
│   ├── processors/
│   │   └── saas_processor.py         # Unified processor (uses both)
│   ├── intelligence/
│   │   ├── speaker_identifier.py     # Grok speaker ID
│   │   ├── clip_recommender.py       # Grok clip recs
│   │   └── entity_extractor.py       # Grok entities
│   └── database/                     # Multi-user DB
│
├── web/                         # Next.js frontend
│   ├── pages/
│   ├── components/
│   └── public/
│
├── api/                         # FastAPI backend
│   ├── app.py
│   ├── auth.py
│   ├── billing.py
│   └── worker.py
│
└── deploy/                      # Cloud Run configs
    ├── Dockerfile.api
    ├── Dockerfile.worker
    └── cloudbuild.yaml
```

---

## Next Immediate Actions

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">git add SAAS_PRODUCT_ROADMAP.md ROADMAP.md PHASE_1_DETAILED_PLAN.md