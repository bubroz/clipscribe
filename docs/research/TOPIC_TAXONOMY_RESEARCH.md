# Topic Taxonomy Research - Week 1

**Research Lead:** AI Assistant  
**Started:** October 29, 2025  
**Goal:** Determine optimal topic classification system for intelligence applications

---

## RESEARCH OVERVIEW

**We need to decide:** How to categorize the topics extracted by Grok-4?

**Current State:**
- Grok-4 extracts topics like "Israel-Hamas Ceasefire", "AI GPU Deals", "Healthcare Affordability"
- Topics are free-form strings (no standardized categories)
- Need to map to taxonomy for:
  - Cross-video topic tracking
  - Standard intelligence reporting
  - API compatibility
  - Search/filtering

**Options:**
1. **ACLED** - Conflict & political events (36 types)
2. **GDELT** - Global events (295 CAMEO codes)
3. **Schema.org** - Web standard (800+ types)
4. **Custom** - Build our own for video intelligence

---

## OPTION 1: ACLED (Armed Conflict Location & Event Data)

**Overview:**
- Designed for: Conflict monitoring, political violence tracking
- Granularity: 36 specific event types across 6 categories
- Used by: Researchers, NGOs, government agencies
- Open source: Yes (codebook freely available)

**6 Main Categories:**
1. **BATTLES** (13 subtypes)
   - Armed clash
   - Government regains territory
   - Non-state actor overtakes territory
   - Chemical weapon use
   - Air/drone strike
   - Suicide bomb
   - Shelling/artillery/missile attack
   - Remote explosive/landmine/IED
   - Grenade
   - Sexual violence
   - Attack
   - Abduction/forced disappearance
   - Looting/property destruction

2. **VIOLENCE AGAINST CIVILIANS** (6 subtypes)
   - Attack on civilians
   - Mob violence
   - Sexual violence against civilians
   - Abduction/forced disappearance of civilians
   - Looting/property destruction against civilians
   - Recruitment of child soldiers

3. **EXPLOSIONS/REMOTE VIOLENCE** (7 subtypes)
   - Shelling/artillery/missile attack
   - Air/drone strike
   - Suicide bomb
   - Remote explosive/landmine/IED
   - Grenade
   - Chemical weapon
   - Biological weapon

4. **PROTESTS** (3 subtypes)
   - Peaceful protest
   - Protest with intervention
   - Excessive force against protesters

5. **RIOTS** (2 subtypes)
   - Violent demonstration
   - Mob violence

6. **STRATEGIC DEVELOPMENTS** (5 subtypes)
   - Agreement/ceasefire
   - Arrests
   - Change to group/activity
   - Disrupted weapons use
   - Headquarters or base established
   - Looting/property destruction
   - Non-violent transfer of territory
   - Other

**Pros for Our Use:**
- ✅ Highly specific (great for conflict/political content)
- ✅ Intelligence community standard
- ✅ Open codebook (easy to implement)
- ✅ Good for news/politics (our target market)

**Cons:**
- ❌ Limited to conflict events (no tech, business, culture)
- ❌ 36 types may be too narrow for all content
- ❌ Not designed for all video types

**Example Mapping:**
- Grok topic: "Israel-Hamas Ceasefire"
- ACLED code: `STRATEGIC_DEVELOPMENTS > Agreement/ceasefire`
- Use case: Track ceasefire mentions across 100 news videos

---

## OPTION 2: GDELT (Global Database of Events, Language, Tone)

**Overview:**
- Designed for: Global event monitoring (news, diplomacy, conflict, economics)
- Granularity: 295 CAMEO (Conflict and Mediation Event Observations) codes
- Used by: Researchers, intelligence analysts, media monitoring
- Open source: Yes (full documentation available)

**CAMEO Code Structure (5 levels):**
```
Level 1: 20 root categories (01-20)
Level 2: ~60 categories (2 digits: 01, 02, etc.)
Level 3: ~180 categories (3 digits: 010, 011, etc.)
Level 4: ~260 categories (4 digits: 0101, 0102, etc.)
Level 5: 295 specific codes (5 digits: 01011, 01012, etc.)
```

**20 Root Event Types:**
01. MAKE PUBLIC STATEMENT
02. APPEAL
03. EXPRESS INTENT TO COOPERATE
04. CONSULT
05. ENGAGE IN DIPLOMATIC COOPERATION
06. ENGAGE IN MATERIAL COOPERATION
07. PROVIDE AID
08. YIELD
09. INVESTIGATE
10. DEMAND
11. DISAPPROVE
12. REJECT
13. THREATEN
14. PROTEST
15. EXHIBIT FORCE POSTURE
16. REDUCE RELATIONS
17. COERCE
18. ASSAULT
19. FIGHT
20. USE UNCONVENTIONAL MASS VIOLENCE

**Example 5-Digit Code:**
- `04311` = "Consult on economic policy"
  - `04` = CONSULT (root)
  - `043` = "Consult on policy"
  - `0431` = "Consult on economic policy"
  - `04311` = "Consult on economic policy with specific country"

**Pros for Our Use:**
- ✅ Extremely comprehensive (295 codes cover almost everything)
- ✅ Hierarchical (can be broad or specific)
- ✅ Intelligence standard (GDELT used worldwide)
- ✅ Handles diplomacy, economics, conflict, cooperation

**Cons:**
- ❌ Complex (295 codes overwhelming)
- ❌ Designed for news events (not all video content)
- ❌ May be overkill for MVP

**Example Mapping:**
- Grok topic: "Trump announces Gaza ceasefire"
- GDELT code: `050` = "ENGAGE IN DIPLOMATIC COOPERATION"
- Or: `0501` = "Express accord"

---

## OPTION 3: Schema.org (Web Standard)

**Overview:**
- Designed for: Structured data on the web (Google, Bing, etc.)
- Granularity: 800+ types across all domains
- Used by: Google Search, Knowledge Graph, SEO
- Open source: Yes (w3.org standard)

**Event Types (Subset Relevant to Us):**
- **Event** (root type)
  - BusinessEvent
  - ChildrensEvent
  - ComedyEvent
  - DanceEvent
  - EducationEvent
  - ExhibitionEvent
  - Festival
  - FoodEvent
  - LiteraryEvent
  - MusicEvent
  - **PublicationEvent**
  - SaleEvent
  - ScreeningEvent
  - SocialEvent
  - SportsEvent
  - TheaterEvent
  - VisualArtsEvent
  - **PoliticalEvent** (proposed, not official)

**Additional Relevant Types:**
- **NewsArticle** (for news content)
- **VideoObject** (our core type)
- **Person, Organization, Place** (entities)
- **CreativeWork** (podcasts, shows)

**Pros for Our Use:**
- ✅ Web standard (Google compatibility)
- ✅ Broad coverage (all content types)
- ✅ SEO benefits (structured data)
- ✅ Simple hierarchy (easier than GDELT)

**Cons:**
- ❌ Less granular than ACLED/GDELT for intelligence
- ❌ Not designed for analysis (designed for search)
- ❌ Missing some intelligence categories

**Example Mapping:**
- Grok topic: "Israel-Hamas Ceasefire"
- Schema.org type: `Event > PoliticalEvent`
- Properties: name, startDate, location, organizer

---

## RECOMMENDATION: HYBRID APPROACH

**Use Schema.org as BASE + ACLED/GDELT for DEPTH:**

```json
{
  "topic": {
    "name": "Israel-Hamas Ceasefire",
    "grok_relevance": 0.95,
    "time_range": "00:00-15:00",
    
    // Schema.org (broad compatibility)
    "schema_type": "Event/PoliticalEvent",
    
    // ACLED (intelligence depth)
    "acled_category": "STRATEGIC_DEVELOPMENTS",
    "acled_subtype": "Agreement/ceasefire",
    
    // GDELT (global events)
    "gdelt_code": "050",  // Diplomatic cooperation
    "gdelt_description": "Engage in diplomatic cooperation",
    
    // Our custom
    "station10_category": "Conflict Resolution",
    "entities_involved": ["Israel", "Hamas", "Gaza", "Donald Trump"]
  }
}
```

**Why Hybrid:**
- ✅ Schema.org for web compatibility (SEO, Google)
- ✅ ACLED for conflict content (news, politics)
- ✅ GDELT for comprehensive events (diplomacy, economics)
- ✅ Custom for video-specific categories

**Implementation Strategy:**
1. **Phase 1 (Week 2):** Schema.org only (simple, gets us started)
2. **Phase 2 (Week 4):** Add ACLED mapping (for news/politics)
3. **Phase 3 (Future):** Add GDELT codes (for comprehensive intelligence)

---

## NEXT STEPS

**My Research (This Week):**
1. Download ACLED codebook PDF (analyze full structure)
2. Download GDELT documentation (understand CAMEO codes)
3. Map example topics to all 3 taxonomies
4. Create conversion functions (Grok topic → taxonomy codes)
5. Propose hybrid taxonomy for Station10

**Your Input Needed:**
- Which taxonomy fits your intelligence analyst use case best?
- Do you need GDELT's 295 codes or is ACLED's 36 sufficient?
- Should we start simple (Schema.org) or go deep (GDELT)?

**Deliverable:**
- `TOPIC_TAXONOMY_FINAL_RECOMMENDATION.md`
- Implementation guide for Week 2
- Mapping tables (topic → codes)

---

**Status:** RESEARCH STARTED  
**Next:** Download ACLED/GDELT docs, create detailed comparison

