# Week 1 Research Plan - Week 5-8 Feature Foundation

**Week:** October 29 - November 5, 2025  
**Goal:** Research and design before building  
**Approach:** Parallel research (you + me), then sync on findings

---

## RESEARCH ASSIGNMENTS

### **Research #1: Auto-Clip Algorithms** (Priority: HIGH)

**Questions to Answer:**
1. How does Opus Clip select clips? (virality scoring methodology)
2. What makes a clip "viral"? (hook, retention, engagement metrics)
3. What makes a clip "newsworthy"? (journalism standards, importance)
4. What makes a clip "info-dense"? (entities per second, complexity)
5. Optimal clip lengths? (TikTok 15-60s, YouTube Shorts 60s, variable?)

**Research Sources:**
- Opus Clip website/blog (how they describe their algorithm)
- TikTok algorithm research (virality factors)
- YouTube Shorts best practices
- Journalism clip selection (news packages, b-roll selection)
- Academic: Video summarization research papers

**Deliverable:**
- `docs/research/AUTO_CLIP_ALGORITHM_RESEARCH.md`
- Scoring formula design
- Clip selection criteria
- Implementation recommendations

**Owner:** YOU (research Opus Clip, virality)  
**Support:** ME (academic research, algorithm design)

---

### **Research #2: Topic Taxonomies** (Priority: HIGH)

**Questions to Answer:**
1. ACLED taxonomy structure (36 event types, how are they organized?)
2. GDELT CAMEO codes (295 codes, what's the hierarchy?)
3. Schema.org Event types (how does Google use them?)
4. Which taxonomy fits intelligence use cases best?
5. Can we map Grok-4 topics to standard taxonomies?

**Research Sources:**
- ACLED codebook (https://acleddata.com/acleddatanew/wp-content/uploads/dlm_uploads/2019/01/ACLED_Codebook_2019FINAL.pdf)
- GDELT documentation (https://www.gdeltproject.org/data.html#documentation)
- Schema.org Event types (https://schema.org/Event)
- Palantir Ontology (public info only)
- Intelligence community standards (MITRE ATT&CK, STIX/TAXII)

**Deliverable:**
- `docs/research/TOPIC_TAXONOMY_RESEARCH.md`
- Comparison matrix (ACLED vs GDELT vs Schema.org)
- Recommended taxonomy for Station10
- Mapping strategy (Grok topics → standard codes)

**Owner:** ME (deep research, technical analysis)  
**Support:** YOU (review findings, decide granularity preference)

---

### **Research #3: SaaS Pricing Models** (Priority: CRITICAL)

**Questions to Answer:**
1. Per-video vs subscription - which converts better?
2. Competitor pricing: Descript ($24), Opus ($29), Fireflies ($29)
3. Our costs: $0.34/video (WhisperX $0.33 + Grok-4 $0.01)
4. Target margin: 60%? 75%? 90%?
5. Pricing tiers: How many? What limits?

**Research Sources:**
- Competitor pricing pages (feature comparison)
- SaaS pricing best practices (Patrick McKenzie, ProfitWell)
- Customer willingness to pay surveys
- Cost structure analysis (variable vs fixed costs)
- Pricing psychology (anchoring, value perception)

**Deliverable:**
- `docs/research/PRICING_MODEL_RESEARCH.md`
- Competitor analysis matrix
- Cost structure breakdown
- Proposed pricing tiers
- Revenue projections

**Owner:** YOU (competitor research, pricing psychology)  
**Support:** ME (cost analysis, margin calculations)

---

### **Research #4: Data Provider Business Model** (Priority: MEDIUM)

**Questions to Answer:**
1. Who buys intelligence data? (gov agencies, media orgs, financial firms)
2. How much do they pay? (contract sizes, pricing models)
3. What compliance needed? (FedRAMP, ITAR, security clearances)
4. Competitors in this space? (Recorded Future, Palantir, etc.)
5. Go-to-market strategy? (direct sales, partnerships, RFPs)

**Research Sources:**
- Government RFP databases (sam.gov)
- Intelligence data provider case studies
- GovCon pricing research
- Compliance requirements (FedRAMP, NIST)
- Partnership opportunities (Chimera, Palantir Foundry)

**Deliverable:**
- `docs/research/DATA_PROVIDER_MODEL_RESEARCH.md`
- Market size analysis
- Competitor landscape
- Compliance roadmap
- Revenue potential (per-customer, total market)

**Owner:** YOU (market research, gov contracts)  
**Support:** ME (technical requirements, integration architecture)

---

## DESIGN ASSIGNMENTS

### **Design #1: Learn Figma** (1-2 hours)

**Tasks:**
1. Create free Figma account (figma.com)
2. Watch beginner tutorial (YouTube: "Figma for Beginners 2024")
3. Explore Community tab (find dashboard/video UI kits)
4. Create "Station10 Design" project

**Deliverable:**
- Figma account set up
- Basic proficiency (components, auto-layout, frames)
- Ready to mock up interfaces

**Owner:** YOU  
**Timeline:** This week

---

### **Design #2: Intelligence Dashboard Mockup**

**What to Mock Up:**
- Video player with timeline
- Topics list (clickable, shows relevance)
- Key moments timeline (significance bars)
- Sentiment indicator
- Entity graph preview
- Clip recommendations panel

**Inspiration:**
- YouTube Analytics dashboard
- Intelligence analysis tools (Palantir, i2 Analyst's Notebook)
- Video editing tools (Descript, Premiere Pro)

**Deliverable:**
- Figma link (view-only)
- Annotations explaining interactions
- Mobile vs desktop views

**Owner:** YOU  
**Timeline:** Mid-week

---

### **Design #3: Clip Recommender UI**

**What to Mock Up:**
- List of recommended clips (sorted by score)
- Each clip showing:
  - Thumbnail preview
  - Timestamp + duration
  - Significance score (visual: stars or bars)
  - Topic tags
  - Sentiment indicator
  - Generate/Download/Share buttons

**Inspiration:**
- Opus Clip results page
- YouTube clip selector
- TikTok creator studio

**Deliverable:**
- Figma link
- Interaction flows
- Score visualization design

**Owner:** YOU  
**Timeline:** End of week

---

## PARALLEL WORK STRUCTURE

**Your Week:**
- Day 1-2: Opus Clip research, pricing research
- Day 3-4: Learn Figma, start Intelligence Dashboard mockup
- Day 5-7: Finish mockups, review my research findings

**My Week:**
- Day 1-2: Topic taxonomy deep dive (ACLED, GDELT, Schema.org)
- Day 3-4: Data provider model research (gov contracts, compliance)
- Day 5-7: Consolidate findings, create implementation plans

**End of Week:**
- Sync meeting: Review all research
- Discuss Figma designs
- Finalize Week 2-4 build plan
- Start building (informed by research)

---

## SUCCESS CRITERIA

**By End of Week 1:**
- [ ] 4 research documents complete
- [ ] 2-3 Figma mockups created
- [ ] Auto-clip scoring algorithm designed
- [ ] Topic taxonomy chosen (ACLED vs GDELT vs Schema.org)
- [ ] Pricing model decided (per-video vs subscription)
- [ ] Week 2-4 build plan finalized

**Then Week 2:**
- Start building with clear requirements
- Implement based on research findings
- UI matches Figma designs
- No guessing, no iteration hell

---

## CURRENT STATUS

**Ready to Start:**
- ✅ Core engine validated (complete intelligence working)
- ✅ Prerequisites met (topics, moments, evidence all extracted)
- ✅ Repository clean (strict standards enforced)
- ✅ Documentation current (all up to date)

**Starting Now:**
- Research #1: Auto-clip algorithms (in progress)
- Next: Topic taxonomies, pricing, data provider
- Parallel: Your Figma design work

**This research week sets us up for efficient, informed building in Weeks 2-4.**

