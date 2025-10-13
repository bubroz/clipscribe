# Station10 Intelligence Platform - Research & Design

**Date**: October 12, 2025, 8:30 PM PDT  
**Context**: Adapt ClipScribe for 3-person media company use  
**Status**: Research phase - partners don't know yet

---

## Current Situation

**Station10 Media**: Launched media company, 3 co-founders  
**ClipScribe**: Personal tool (you), working well, validated  
**Goal**: Introduce ClipScribe as research tool for Station10

**Your role**: Technical co-founder (not engineering background)  
**Timeline**: No rush - partners unaware, can design properly first

---

## Research Questions to Answer

### 1. Multi-User Architecture

**Question**: How to handle 3 users with different needs?

**Options to research**:
- **Shared bot, shared data**: Everyone sees everything
- **Shared bot, user isolation**: Separate libraries, opt-in sharing
- **Separate bots per user**: Complete isolation
- **Hybrid**: Shared knowledge graph + private processing

**Pros/Cons needed**: Security, costs, complexity, UX

### 2. Cost Allocation & Budgets

**Question**: How to prevent one person from racking up huge bills?

**Current costs**: $0.03-0.06/video
**If one person processes 1000 videos**: $30-60

**Options to research**:
- Per-user API keys (tracks automatically)
- Shared pool with limits
- Cost warnings at thresholds
- Monthly budget caps

**Need to research**: Voxtral/Grok API key management, multi-tenant costs

### 3. Telegram Bot Architecture

**Question**: One bot for all 3, or separate?

**Options**:
A. **One shared bot**:
   - Pros: Simple, shared knowledge, one setup
   - Cons: No privacy, hard to track who did what
   
B. **Three separate bots**:
   - Pros: Complete isolation, clear cost tracking
   - Cons: No sharing, 3x setup work
   
C. **One bot, user auth**:
   - Pros: Shared knowledge + privacy, one bot
   - Cons: More complex, need user management

**Best practice to research**: Multi-user Telegram bots, authentication patterns

### 4. Intelligence Sharing Model

**Your vision**: "Like Google Drive"
- Shared knowledge graph (everyone's contributions)
- Personal libraries (my processed videos)
- Opt-in sharing (share specific videos/collections)

**Questions to research**:
- How to merge knowledge graphs from multiple users?
- Entity deduplication across users?
- Permission model (view vs edit)?
- Search scope (my videos vs all videos)?

### 5. Database vs Files

**Current**: File-based (one folder per video)
**Multi-user**: Probably needs database

**Research needed**:
- SQLite (simple, local)
- PostgreSQL (proper multi-user)
- Supabase (hosted Postgres + auth)
- Or stick with files + metadata DB?

---

## Research Tasks for Next Session

1. **Telegram Bot API 8.0 deep dive**: Mini Apps, inline keyboards, user auth
2. **Multi-tenant cost tracking**: How other tools handle this
3. **Intelligence sharing patterns**: How research tools enable collaboration
4. **Database options**: What's appropriate for 3 users, 100-1000 videos
5. **Authentication**: Telegram-based auth vs separate
6. **Deployment**: Where to host (your laptop won't cut it for 3 people)

---

## Before We Build Anything

**Critical decision**:
- Do you tell partners about ClipScribe before building multi-user features?
- Or build it, validate it works for Station10 use case, THEN share?

**My take**: You're at 977K tokens. We should:
1. End this session with research doc created
2. Let 24hr test finish
3. Next session: Deep research on multi-user architecture
4. Then build properly from the start

**This is too important to rush at the end of a long session.**

Should we wrap here and tackle this fresh tomorrow?

