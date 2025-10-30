# Topic Taxonomy - Final Recommendation

**Date:** October 29, 2025  
**Decision:** Hybrid Schema.org + ACLED approach  
**Rationale:** Start simple (Schema.org), add intelligence depth (ACLED) as needed

---

## RECOMMENDATION: SCHEMA.ORG BASE + ACLED MAPPING

### **Phase 1 (Week 2): Schema.org Only**

**Use Schema.org Event types as primary taxonomy:**

```json
{
  "topic": {
    "name": "Israel-Hamas Ceasefire",
    "relevance": 0.95,
    "time_range": "00:00-15:00",
    "schema_type": "Event",
    "schema_subtype": "PoliticalEvent"
  }
}
```

**Schema.org Event Types:**
- Event (root)
  - BusinessEvent
  - EducationEvent
  - PoliticalEvent ← Most relevant for our content
  - SocialEvent
  - SportsEvent
  - etc.

**Why Start Here:**
- ✅ Simple (20-30 types, not 295)
- ✅ Web standard (Google compatibility)
- ✅ Easy to implement (Week 2 realistic)
- ✅ Covers all content types
- ✅ Can add more later

---

### **Phase 2 (Future): Add ACLED Codes**

**For conflict/political content, add ACLED mapping:**

```json
{
  "topic": {
    "name": "Israel-Hamas Ceasefire",
    "schema_type": "PoliticalEvent",
    "acled_category": "STRATEGIC_DEVELOPMENTS",
    "acled_subtype": "Agreement/ceasefire",
    "acled_code": "60"  // ACLED numeric code
  }
}
```

**ACLED's 6 Categories (36 subtypes):**
1. BATTLES (13 subtypes)
2. VIOLENCE_AGAINST_CIVILIANS (6 subtypes)
3. EXPLOSIONS_REMOTE_VIOLENCE (7 subtypes)
4. PROTESTS (3 subtypes)
5. RIOTS (2 subtypes)
6. STRATEGIC_DEVELOPMENTS (5 subtypes)

**When to Add:**
- After Week 2 (once basic search working)
- For government/intelligence customers
- For conflict monitoring use cases

---

## DATABASE SCHEMA (Week 2 Implementation)

```sql
CREATE TABLE topics (
    id UUID PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    relevance FLOAT NOT NULL,  -- 0.0-1.0
    time_range VARCHAR(50),     -- "00:00-15:00"
    
    -- Schema.org (Phase 1)
    schema_type VARCHAR(100),   -- "Event", "NewsArticle", etc.
    schema_subtype VARCHAR(100), -- "PoliticalEvent", "BusinessEvent"
    
    -- ACLED (Phase 2, optional)
    acled_category VARCHAR(100),
    acled_subtype VARCHAR(100),
    acled_code INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for search
    INDEX idx_video_id (video_id),
    INDEX idx_name (name),
    INDEX idx_relevance (relevance),
    INDEX idx_schema_type (schema_type)
);
```

---

## API ENDPOINT DESIGN

```python
# POST /api/topics/search
{
  "query": "ceasefire",           # Text search in topic names
  "min_relevance": 0.8,           # Filter by relevance
  "schema_type": "PoliticalEvent", # Filter by type
  "limit": 50
}

# Response:
{
  "topics": [
    {
      "id": "uuid",
      "video_id": "P-2",
      "video_title": "All-In Podcast",
      "name": "Israel-Hamas Ceasefire",
      "relevance": 0.95,
      "time_range": "00:00-15:00",
      "schema_type": "Event",
      "schema_subtype": "PoliticalEvent"
    }
  ],
  "total": 1,
  "query_time_ms": 15
}
```

---

## IMPLEMENTATION PLAN

**Week 2 (This Week):**
1. Create topics table (Schema.org only)
2. Implement FastAPI search endpoint
3. Load our 13 validated topics into database
4. Test search functionality
5. Add to Textual TUI

**Week 3 (Next):**
6. Add ACLED category mapping (optional field)
7. Create ACLED code reference data
8. Enhance search with ACLED filtering

**Week 4:**
9. GDELT codes (if needed for specific customers)
10. Complete taxonomy documentation

---

**Decision: Start with Schema.org (simple), add ACLED (depth) later.**

**Ready to implement.**

