# TUI + API Approach - Final Decision & Implementation Plan

**Date:** October 29, 2025, 02:35 PDT  
**Decision:** Build TUI + API (not GUI) for intelligence analysts  
**Rationale:** Target market prefers terminal, ships faster, enables integrations

---

## WHY TUI + API

**Target Market:**
- Intelligence analysts (terminal-native, script-driven workflows)
- Investigative journalists (data analysis, automation)
- Researchers (batch processing, custom scripts)

**Key Benefits:**
- Ships 4 weeks faster (Week 5 vs Week 13)
- Better for analysts (keyboard-driven, composable)
- Enables integrations (Chimera, Palantir, custom)
- Fits data provider model (API is the product)
- Same pricing ($29-149/mo for CLI + API)

---

## UPDATED WEEK 2-4 PLAN

**Week 2: TUI + Search APIs**
- Topic search API (FastAPI)
- Entity search API (18 spaCy types)
- Rich TUI with Textual (Intelligence Dashboard)
- Keyboard-driven navigation

**Week 3: Auto-Clip + API**
- Auto-clip generation API
- ffmpeg integration  
- TUI clip recommender
- Intelligence scoring

**Week 4: Batch + Docs**
- Batch processing API
- TUI batch monitor
- OpenAPI/Swagger docs
- E2E validation

**Target:** TUI + API beta Week 5 (December 2025)

---

## DOCUMENTATION UPDATES COMPLETED

- ✅ README.md (TUI + API plan, GUI optional)
- ✅ ROADMAP.md (Week 2-4 TUI, Week 9-12 GUI removed)
- ✅ CONTINUATION_PROMPT.md (TUI roadmap)
- ✅ TODO list (22 items, TUI-focused)

---

**Next:** Repository audit, final cleanup, commit all changes

