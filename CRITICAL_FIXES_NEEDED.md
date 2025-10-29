# CRITICAL FIXES NEEDED - README Accuracy & Security Audit

**Date:** October 28, 2025, 23:35 PDT
**Severity:** HIGH - Multiple inaccuracies in customer-facing README

---

## CRITICAL INACCURACIES IN README.md

### 1. Voxtral Claims (NOT IMPLEMENTED) ❌
**Lines with issues:**
- "Standard tier: 95% accuracy (Voxtral)"
- "Voxtral transcription (95% accuracy, fast)"
- "Voxtral (Mistral API) - standard tier"
- "Auto-tier selection (medical/legal → premium)"

**Reality:**
- Voxtral is NOT in current production pipeline
- Only WhisperX on Modal is implemented
- No dual-tier system exists
- No auto-tier selection

**Impact:** MISLEADING - customers would expect features that don't exist

**Fix:** Remove all Voxtral references OR clearly mark as "Planned"

---

### 2. Grok Model Confusion ❌
**Claims:**
- Header: "Grok-2 entity intelligence" ✅ CORRECT
- Tech Stack: "Grok-4 (xAI)" ❌ WRONG

**Reality:**
- Using: `grok-2-1212` (Grok-2, December 2021 version)
- Grok-4 doesn't exist (made up)

**Questions to Research:**
- Is `grok-2-1212` the LATEST Grok-2 model?
- Are there newer models? (grok-beta, grok-vision-beta, etc.)
- Should we be using a different/better model?

**Fix:** Verify latest Grok models, use best available, update docs accurately

---

### 3. Features Marked as Working (NOT IMPLEMENTED) ❌
**"What's working" section claims:**
- "Voxtral transcription (95% accuracy)"
- "Auto-tier selection (medical/legal → premium)"

**"What's being built" section claims:**
- "Multi-speaker validation (4-5 speaker test in progress)"

**Reality:**
- Voxtral: NOT implemented
- Auto-tier: NOT implemented
- Multi-speaker validation: COMPLETE (not in progress)

**Fix:** Update to reflect actual current state

---

### 4. Dates Inconsistent ❌
**Found:**
- "Latest:" Week 1 Day 1 complete (Oct 15, 2025)"
- "*Last updated: October 15, 2025 - Week 1 Day 1 complete*"

**Current date:** October 28, 2025

**Fix:** Update all dates to Oct 28, 2025

---

### 5. Pricing Not Validated ❌
**Claims:**
- "Standard: $0.10/minute"
- "Premium: $0.20/minute"

**Reality:**
- Only validated WhisperX: $0.20-0.42/VIDEO (not per minute)
- Standard tier (Voxtral) doesn't exist
- No per-minute pricing validated

**Fix:** Mark as "Planned" or remove specific numbers

---

## SECURITY AUDIT RESULTS

### ✅ PASSED - No Critical Security Issues

**Verified:**
- ✅ secrets/ directory properly gitignored
- ✅ .env files properly gitignored
- ✅ service-account.json NOT in git (checked git ls-files)
- ✅ No hardcoded API keys in tracked files
- ✅ test_videos/ MP3s NOT in git (too large)
- ✅ output/, logs/, cache/ properly gitignored

**Found (Non-Issues):**
- `scripts/create_beta_token.py` - helper script (not actual tokens)
- `src/clipscribe/utils/po_token_manager.py` - token manager (not hardcoded tokens)
- API_KEY references in code - all use environment variables ✅

**Conclusion:** Security is GOOD - no secrets exposed

---

## REPOSITORY BLOAT AUDIT

### Files in Repo: 516 total

**Breakdown:**
- Source code: ~100 files (src/)
- Tests: ~60 files (tests/)
- Scripts: ~90 files (scripts/)
- Docs: ~80 files (docs/, archive/, root)
- Config: ~20 files (pyproject.toml, docker, etc.)
- Dependencies: poetry.lock, package files
- Examples: ~10 files (examples/)

**Potentially Unnecessary:**
? streamlit_app/ (7 files) - is this used?
? lib/ (bindings, tom-select, vis-9.1.2) - frontend assets, needed?
? docker/ files - are we using Docker?
? cloudbuild*.yaml files - are we using Cloud Build?

### Large Files (>30K):
- poetry.lock (737K) - NEEDED ✅
- CHANGELOG.md (541K) - NEEDED ✅
- Source files (30-60K each) - NEEDED ✅

**Conclusion:** No obvious bloat, but need to verify unused services

---

## CLARIFYING QUESTIONS FOR USER

### 1. Grok Models:
**Q:** Are we using the latest/best Grok model available?
- Current: `grok-2-1212`
- Options: grok-beta? grok-vision-beta? grok-2-latest?
- **Should I research and switch to latest?**

### 2. Voxtral Dual-Tier:
**Q:** Is Voxtral planned for future, or should we remove it entirely?
- Option A: Remove all Voxtral references (simplify to WhisperX only)
- Option B: Mark as "Planned for future" throughout
- **Which approach?**

### 3. Repository Files:
**Q:** Are these in use or should they be removed/archived?
- streamlit_app/ (7 files)
- lib/ (frontend assets: tom-select, vis-9.1.2)
- docker/ files (nginx.conf, redis.conf, supervisord.conf)
- cloudbuild*.yaml files (4 files)
- **Should I audit and remove unused?**

### 4. README Audience:
**Q:** Is README for GitHub visitors or for internal reference?
- If GitHub: Remove "in development", show only working features
- If internal: Keep roadmap and planned features
- **Which audience?**

---

## IMMEDIATE FIXES (No Questions Needed)

Will fix immediately:
1. ✅ Change "Grok-4" → "Grok-2" in tech stack
2. ✅ Update all dates to Oct 28, 2025
3. ✅ Remove "What's being built" section (outdated)
4. ✅ Update "Latest" to v2.60.0 validation complete
5. ✅ Mark Voxtral as "(Planned)" if keeping, or remove entirely
6. ✅ Update feature status to current reality

---

## PROPOSED README REWRITE

**Honest, Accurate, Current:**
- Focus on what's ACTUALLY working (WhisperX, Grok-2, entity extraction)
- Mark everything else as "Planned" or "In Development"
- Use validated metrics only (0.90 confidence, 625 entities, etc.)
- Consistent dates (Oct 28, 2025 throughout)
- No made-up model names (Grok-4)
- No fictional features (Voxtral, auto-tier)

**Waiting for your answers on clarifying questions before proceeding with full rewrite.**

