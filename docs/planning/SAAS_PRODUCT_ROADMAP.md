# Station10.media - 16-Week Execution Plan

**Start Date**: October 15, 2025  
**Target Launch**: February 10, 2026  
**Goal**: Full-featured video intelligence SaaS

---

## Development Strategy

### Parallel Track Approach

```
Track 1: Core Engine (CLI-first, then expose via API)
Track 2: Web Interface (design, then build on Track 1)
Track 3: Infrastructure (billing, auth, deployment)

Weeks 1-8: Heavy on Track 1 (build capabilities)
Weeks 9-14: Heavy on Track 2 (web interface)
Weeks 15-16: Integration + launch prep
```

---

## Week-by-Week Breakdown

### **Week 1** (Oct 15-22): Transcription Foundation

**Track 1: Core Engine**
- [ ] Install and test WhisperX on M3 Max
- [ ] Benchmark: Voxtral vs WhisperX on medical/legal samples
- [ ] Build dual-mode transcriber class
- [ ] Auto-detection logic (content type → mode)
- [ ] CLI: `clipscribe process video "url" --quality auto|fast|accurate`

**Track 2: Web Design**
- [ ] Sketch UI flows (Figma or paper)
- [ ] Landing page design
- [ ] Upload page design
- [ ] Results page design

**Track 3: Infrastructure**
- [ ] Set up PostgreSQL on Cloud SQL ($9/mo)
- [ ] Set up Redis Memorystore ($30/mo)
- [ ] Configure GCS buckets (station10-videos, station10-results)

**Deliverable**: WhisperX working, web designs ready, infra provisioned

**Validation**: Test both modes on user's medical/legal samples

---

### **Week 2** (Oct 22-29): Speaker Diarization

**Track 1: Core Engine**
- [ ] Integrate pyannote.audio
- [ ] Align speaker segments with transcript
- [ ] Format output: Transcript with [SPEAKER_00] timestamps
- [ ] Test on multi-speaker videos (debates, interviews)
- [ ] CLI: Output shows speakers

**Track 2: Web Design**
- [ ] Design speaker visualization
- [ ] Transcript view with speaker highlighting
- [ ] Color-code speakers

**Track 3: Infrastructure**
- [ ] Test concurrent processing on M3 Max (how many videos simultaneously?)
- [ ] Memory profiling (WhisperX + pyannote usage)

**Deliverable**: Accurate speaker diarization, web designs refined

**Validation**: 95%+ accuracy on speaker segments

---

### **Week 3** (Oct 29-Nov 5): Speaker Identification

**Track 1: Core Engine**
- [ ] Grok speaker identification prompt
- [ ] Confidence scoring
- [ ] Manual override system
- [ ] Test accuracy on known speakers
- [ ] CLI: Shows identified speaker names

**Track 2: Web Design**
- [ ] Speaker identification UI
- [ ] Confidence indicators
- [ ] Manual correction interface

**Track 3: Infrastructure**
- [ ] Grok API rate limiting (if needed)
- [ ] Error handling for API failures

**Deliverable**: Speaker names inferred from context (85%+ accuracy when confident)

**Validation**: Test on political videos, medical conferences, legal content

---

### **Week 4** (Nov 5-12): Entity Extraction with Speakers

**Track 1: Core Engine**
- [ ] Grok entity extraction with speaker attribution
- [ ] "Biden mentioned X" vs "Reporter mentioned X"
- [ ] Evidence quotes with speaker labels
- [ ] Relationship extraction with speakers
- [ ] CLI: Full output with speaker-entity linkage

**Track 2: Web Design**
- [ ] Entity list view (grouped by speaker)
- [ ] Filter entities by speaker
- [ ] Relationship graph with speaker colors

**Track 3: Infrastructure**
- [ ] Database schema finalized (speakers + entities + relationships)
- [ ] Migration scripts

**Deliverable**: Complete intelligence with speaker attribution

**Validation**: Entity accuracy comparable to current + speaker context adds value

---

### **Week 5** (Nov 12-19): Clip Recommendations

**Track 1: Core Engine**
- [ ] Grok clip recommendation prompt (3 objectives)
- [ ] Multi-criteria scoring (newsworthy, viral, dense)
- [ ] Custom prompt support
- [ ] Top 5-10 clips per video
- [ ] CLI: Shows recommendations with scores

**Track 2: Web Design**
- [ ] Clip recommendation cards
- [ ] Score visualizations
- [ ] Preview at timestamp (video player integration)

**Track 3: Infrastructure**
- [ ] Video player CDN (GCS signed URLs)
- [ ] Thumbnail generation for clips

**Deliverable**: Intelligent clip recommendations

**Validation**: Would you actually share these clips? Are they good?

---

### **Week 6** (Nov 19-26): Auto-Clip Generation

**Track 1: Core Engine**
- [ ] ffmpeg clip generation
- [ ] Metadata sidecar files
- [ ] Batch clip generation (all recommendations)
- [ ] Interactive approval workflow (CLI)
- [ ] CLI: Generate approved clips

**Track 2: Web Design**
- [ ] Clip approval interface
- [ ] Checkboxes for clip selection
- [ ] Download all / download selected
- [ ] Social media caption display

**Track 3: Infrastructure**
- [ ] Clip storage in GCS
- [ ] Download links (signed URLs)
- [ ] Cleanup policy (auto-delete after 30 days)

**Deliverable**: Clips auto-generated and downloadable

**Validation**: Clip quality good enough to share?

---

### **Week 7** (Nov 26-Dec 3): Entity Search

**Track 1: Core Engine**
- [ ] Implement ClipScribeDatabase (from db_manager.py)
- [ ] Search queries (entity, speaker, relationship)
- [ ] Cross-video search
- [ ] CLI search commands
- [ ] Stats and reporting

**Track 2: Web Design**
- [ ] Search interface
- [ ] Filter UI (by speaker, date, video)
- [ ] Search results display
- [ ] Library view (all your videos)

**Track 3: Infrastructure**
- [ ] Database optimization (indexes)
- [ ] Full-text search (if needed)

**Deliverable**: Search working across all videos

---

### **Week 8** (Dec 3-10): Batch Processing

**Track 1: Core Engine**
- [ ] Batch job submission
- [ ] Job queue management
- [ ] Parallel processing (4-6 videos concurrently on M3)
- [ ] Progress tracking
- [ ] CLI batch commands

**Track 2: Web Design**
- [ ] Batch upload UI (multiple files or URLs)
- [ ] Batch progress dashboard
- [ ] Notifications (email when batch complete)

**Track 3: Infrastructure**
- [ ] Cloud Pub/Sub (job completion)
- [ ] SendGrid or Gmail API (notifications)
- [ ] Google Chat webhook (for you)

**Deliverable**: Can process 25 videos overnight

---

### **Week 9** (Dec 10-17): Frontend Implementation Begins

**Track 1: Maintenance**
- [ ] Bug fixes from Weeks 1-8
- [ ] Performance optimization
- [ ] Cost analysis

**Track 2: Web Development** (Primary focus)
- [ ] Set up Next.js project
- [ ] Build landing page
- [ ] Build upload interface
- [ ] Integrate with backend API

**Track 3: Infrastructure**
- [ ] FastAPI or Django backend
- [ ] REST API endpoints
  - POST /api/upload
  - GET /api/process/:id
  - GET /api/videos
  - POST /api/clips/generate

**Deliverable**: Web UI can upload videos

---

### **Week 10** (Dec 17-24): Processing UI

**Track 2: Web Development** (Primary)
- [ ] Processing status page (WebSocket live updates)
- [ ] Progress visualization
- [ ] Error handling UI
- [ ] Cancel job capability

**Track 1: API**
- [ ] WebSocket endpoint (live progress)
- [ ] Job cancellation
- [ ] Error formatting for UI

**Track 3: Infrastructure**
- [ ] Vercel deployment (frontend)
- [ ] Cloud Run API deployment

**Deliverable**: Live processing updates in web UI

**Holiday Break**: Dec 24-Jan 1 (optional pause)

---

### **Week 11** (Jan 1-7): Results Viewer

**Track 2: Web Development** (Primary)
- [ ] Transcript viewer (interactive, speaker highlighting)
- [ ] Entity cards (expandable, speaker attribution)
- [ ] Relationship graph (interactive, zoomable)
- [ ] Clip recommendations view
  - Score badges
  - Select clips to generate
  - Preview at timestamp

**Track 1: API**
- [ ] Format data for web display
- [ ] Clip generation endpoint
- [ ] Download endpoints (clips, full results)

**Deliverable**: Full results exploration in web

---

### **Week 12** (Jan 7-14): Authentication & Accounts

**Track 2: Web Development**
- [ ] Email signup (magic link auth)
- [ ] User dashboard
- [ ] Video library (grid view of all videos)
- [ ] Account settings

**Track 3: Infrastructure**
- [ ] User database schema
- [ ] Session management
- [ ] Email service (SendGrid)

**Deliverable**: User can create account and see their videos

---

### **Week 13** (Jan 14-21): Billing Integration

**Track 2: Web Development**
- [ ] Stripe Elements integration
- [ ] Add payment method
- [ ] Buy credits ($1/video)
- [ ] Subscribe ($30/month)
- [ ] Usage display (videos remaining)

**Track 3: Infrastructure**
- [ ] Stripe webhooks
- [ ] Credit/quota tracking
- [ ] Billing history

**Deliverable**: Can charge customers

---

### **Week 14** (Jan 21-28): End-to-End Testing

**All Tracks: Testing**
- [ ] Full workflow test (signup → pay → upload → process → download)
- [ ] Load test (10 concurrent users)
- [ ] Payment test (actual Stripe transactions)
- [ ] Error scenarios (bad videos, payment failures)
- [ ] Cost validation (margins positive?)

**Deliverable**: Confident system works under load

---

### **Week 15** (Jan 28-Feb 4): Documentation & Legal

**Track 2: Content**
- [ ] Help documentation
- [ ] Video tutorials (how to use)
- [ ] FAQ page
- [ ] Support email setup

**Track 3: Legal**
- [ ] Terms of Service (lawyer review if possible)
- [ ] Privacy Policy
- [ ] Refund policy (7-day money back?)
- [ ] GDPR compliance (if targeting EU)

**Deliverable**: Legally protected

---

### **Week 16** (Feb 4-11): Launch

**All Tracks: Launch Prep**
- [ ] Beta testing (5-10 people)
- [ ] Bug fixes from beta
- [ ] Demo videos (3 use cases)
- [ ] X launch thread
- [ ] Product Hunt (optional)
- [ ] Press outreach (TechCrunch, etc)

**Deliverable**: PUBLIC LAUNCH

---

## Monthly Milestones

### End of Month 1 (Nov 15)
✓ Core engine working (transcription, speakers, entities)
✓ Clip system functional (recommendations + generation)
✓ CLI fully functional
✓ Tested on medical/legal content
**Risk check**: Is accuracy actually better? Is speaker ID working?

### End of Month 2 (Dec 15)
✓ Batch processing working
✓ Entity search implemented
✓ Web interface 50% complete (upload, process, results pages)
✓ API endpoints built
**Risk check**: Can web UI actually handle the complexity?

### End of Month 3 (Jan 15)
✓ Web interface complete
✓ Authentication working
✓ Stripe integrated
✓ End-to-end tested
**Risk check**: Would you pay for this?

### End of Month 4 (Feb 15)
✓ Beta tested
✓ Launched publicly
✓ First paying customers (goal: 5-10)
**Risk check**: Do customers actually want this?

---

## Risk Mitigation

### High-Risk Items

**1. WhisperX Accuracy Claim**
- **Risk**: May not be significantly better than Voxtral
- **Mitigation**: Test Week 1, validate before building around it
- **Backup**: If not better, use Voxtral for everything

**2. Speaker Identification Accuracy**
- **Risk**: Grok may not identify speakers reliably
- **Mitigation**: Test Week 3, measure accuracy
- **Backup**: Generic labels (SPEAKER_00) with manual override

**3. Clip Recommendations Quality**
- **Risk**: Grok recommendations may not be actually good
- **Mitigation**: Test Week 5 on real content
- **Backup**: Simpler algorithm (keyword matching + info density)

**4. Web UI Complexity**
- **Risk**: Showing all features in web UI may be overwhelming
- **Mitigation**: Progressive disclosure, simple default view
- **Backup**: Start with basic transcription, add features incrementally

**5. Market Validation**
- **Risk**: Nobody wants to pay for this
- **Mitigation**: Beta test with real users Week 15
- **Backup**: Pivot to different features based on feedback

---

## Cost Projections (First 6 Months)

### Pre-Launch (Months 1-3)
```
Infrastructure: $40/mo × 3 = $120
Testing videos: $0.05 × 500 = $25
Total: ~$145
```

### Post-Launch (Months 4-6)
```
Infrastructure: $40/mo × 3 = $120

Scenario A: Low traction (50 videos/mo)
- Processing: 50 × $0.05 = $2.50/mo
- Revenue: 50 × $1.00 = $50/mo
- Profit: $10/mo (break-even plus)

Scenario B: Medium traction (500 videos/mo)
- Processing: 500 × $0.05 = $25/mo
- Revenue: 500 × $0.75 avg = $375/mo
- Profit: $335/mo

Scenario C: High traction (2000 videos/mo)
- Processing: 2000 × $0.05 = $100/mo
- Revenue: 2000 × $0.60 avg = $1200/mo
- Profit: $1060/mo
```

**Break-even: 40 videos/month at $1/video**

---

## Critical Decisions Needed

### 1. **Open Source or Closed?**

**Your question: "Do we have to do that?"**

**My answer: No, you don't.**

**Closed Source (Recommended for SaaS):**
```
Pros:
- Protect your competitive advantage
- Can charge for it
- Control the narrative
- No support burden for self-hosters

Cons:
- Harder to market (no GitHub stars)
- No community contributions
- You build everything yourself
```

**Open Core (Alternative):**
```
ClipScribe CLI: Open source (GitHub)
Station10.media: Closed source (hosted service)

Pros:
- GitHub for credibility + marketing
- Community can contribute to CLI
- You keep SaaS secret sauce private
- Best of both worlds

Cons:
- More complex (two codebases)
```

**My recommendation for ASAP launch: Closed source.** Open source later if helpful for marketing.

---

### 2. **Prioritization for ASAP**

**Given 16-week timeline, you MUST cut something.**

**Option A: Launch without WhisperX high-accuracy**
```
MVP: Voxtral + pyannote + clips
Later: Add WhisperX as premium upgrade

Launch: Week 12 (3 weeks faster)
Missing: 99% accuracy mode
```

**Option B: Launch without batch processing**
```
MVP: Single video at a time
Later: Add batch in v2

Launch: Week 14 (2 weeks faster)
Missing: Batch capability
```

**Option C: Launch without speaker identification**
```
MVP: Generic speaker labels (SPEAKER_00)
Later: Add Grok naming in v2

Launch: Week 14 (2 weeks faster)
Missing: Auto speaker naming
```

**Option D: Full 16 weeks, no cuts**
```
Everything works before launch
Launch: Week 16 (February 10)
```

**Which would you cut to launch faster? Or keep full 16 weeks?**

---

### 3. **Development Mode**

**Are you:**
- [ ] Building this solo? (16-week timeline realistic)
- [ ] Have a developer to hire? (8-10 weeks possible)
- [ ] Building with AI assistance only? (20+ weeks realistic)

### 4. **Launch Type**

**How do you want to launch?**

**Option A: Stealth Beta**
```
- Invite only
- 10 beta users
- Free for feedback
- Refine based on usage
- Public launch 4 weeks later
```

**Option B: Public Launch**
```
- Announce on X
- Open to anyone
- Charge from day 1
- Learn in public
```

**Which approach?**

---

## My Recommended Path

**16-Week Full Build → Private Beta → Public Launch**

```
Weeks 1-14: Build everything
Week 15: Beta testing (10 users, free)
Week 16: Fixes based on beta
Week 17: Public launch on X

Total: 17 weeks (mid-February 2026)
```

**Why this works:**
- All features working
- Beta users validate quality
- Launch with testimonials
- Lower risk

---

## Next Steps

**Answer these to finalize the plan:**

1. **Timeline commitment**: 16 weeks realistic for you? Or need faster?
2. **Feature cuts**: Would you cut anything to launch faster?
3. **Open vs closed**: Keep code private for SaaS?
4. **Beta vs public**: Test with beta users first, or launch immediately?
5. **Solo vs team**: Building alone or hiring dev help?

**Then I'll:**
- Update ROADMAP.md with SaaS focus
- Create detailed tech specs
- Set up project tracker (GitHub Projects or similar)
- Begin Week 1 implementation plan

**What's your call?**
