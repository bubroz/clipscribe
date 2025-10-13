# Station10 Architecture - Critical Decisions

**Date**: Oct 12, 2025, 8:45 PM PDT  
**Goal**: Design multi-user intelligence platform for Station10 Media  
**Users**: 3 co-founders  
**Domain**: station10.media (Cloudflare)

---

## DECISION 1: Shared vs Isolated Intelligence

**Option A: Fully Shared** (Recommended)
- One knowledge graph, everyone contributes
- Any user can search any video
- Entities/relationships merge across all processing
- Like: "Shared Google Drive + shared search"

**Option B: User Isolation**
- Each user has their own library
- Explicit sharing required
- More complex, more privacy

**RECOMMENDATION**: Start with Option A
- You're co-founders (trusted)
- Intelligence is more valuable when merged
- Simpler to build
- Can add privacy later if needed

---

## DECISION 2: Telegram Bot Architecture

**Option A: One Bot, User Auth** (Recommended)
```
Bot: @Station10IntelBot
Users authenticate with /start
Bot tracks who's who
Commands work for authenticated users
```

**Option B: Three Separate Bots**
```
Bot 1: @Station10_Zac_Bot
Bot 2: @Station10_Partner1_Bot
Bot 3: @Station10_Partner2_Bot
```

**RECOMMENDATION**: Option A (One bot)
- Cleaner UX
- Easier to maintain
- Shared context
- Standard pattern for team bots

---

## DECISION 3: Storage Architecture

**Current**: Files in `output/`  
**Multi-user**: Need database

**Option A: Hybrid (Files + SQLite Index)** (Recommended)
- Videos still saved as files (preserve current system)
- SQLite tracks: user_id, video_id, entities, relationships
- Fast queries, simple deployment
- Can upgrade to Postgres later

**Option B: Full PostgreSQL**
- All data in database
- More robust, more complex
- Overkill for 3 users

**RECOMMENDATION**: Hybrid (files + SQLite)
- Minimal changes to current code
- Adds user tracking
- Fast enough for 3 people
- Easy migration path

---

## DECISION 4: Cost Tracking

**Simple model**:
```python
costs = {
    'zac': {'videos': 50, 'cost': 2.50},
    'partner1': {'videos': 30, 'cost': 1.80},
    'partner2': {'videos': 20, 'cost': 1.20}
}
```

Stored in SQLite, displayed via `/stats`

**Budget limits**: Per-user monthly cap (e.g., $50/month)

---

## DECISION 5: Deployment

**Current**: Your laptop with caffeinate  
**Multi-user**: Needs 24/7 server

**Options**:
- Google Cloud Run (serverless, scales)
- DigitalOcean droplet ($12/month)
- Your laptop (if it runs 24/7 anyway)

**RECOMMENDATION**: Start on your laptop, migrate to Cloud Run after validation

---

## Build Order (Tonight)

1. **Database schema** (30 min)
2. **User auth in Telegram** (45 min)
3. **Core commands** (/process, /recent, /search) (2 hours)
4. **Cost tracking** (30 min)
5. **Test with all 3 users** (30 min)

**Total: ~4.5 hours**

Ready to start?

