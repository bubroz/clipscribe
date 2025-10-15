# ClipScribe Cleanup Plan

**Date**: October 15, 2025  
**Reason**: Clean up after Telegram bot exploration, align with roadmap  
**Goal**: Clean slate before Phase 1 implementation  
**Status**: ✅ COMPLETE

---

## Cleanup Checklist (ALL COMPLETE ✅)

### 1. Code Cleanup ✅

#### Remove Telegram Bot ✅
- [x] Delete `src/clipscribe/bot/station10_bot.py`
- [x] Delete `src/clipscribe/database/db_manager.py` (created simpler version)
- [x] Delete `src/clipscribe/database/schema.sql` (created single-user version)
- [x] Remove Telegram dependencies from `pyproject.toml`

#### Simplify Database ✅
- [x] Create new single-user database schema
- [x] Keep: videos, entities tables + ADD relationships table
- [x] Remove: users table, multi-user foreign keys
- [x] Update database manager for single-user

#### Keep & Integrate Good Code ✅
- [x] Keep `src/clipscribe/processors/hybrid_processor.py` (Voxtral+Grok)
- [x] Extract error handling from bot to core utils (`utils/error_handler.py`)
- [ ] Make hybrid processor the default in retriever (TODO: Phase 1)

---

### 2. File & Directory Cleanup ✅

#### Root Directory ✅
- [x] Deleted .deployignore
- [x] Deleted DEPLOY_TO_VPS.md
- [x] Deleted create_deployment.sh
- [x] Deleted VPS_ARCHITECTURE.md
- [x] Archived STATUS.md (Oct 12 RSS monitoring notes)
- [x] Deleted Dockerfile.station10
- [x] Deleted NEXT_SESSION_STATION10.md

#### Scripts Directory ✅
- [x] Deleted configure_r2_lifecycle.py (not using R2)
- [x] Deleted station10-bot.service
- [x] Kept other useful scripts

#### Archive Organization ✅
- [x] Organized: archive/telegram_exploration_oct_2025/ (all Station10 docs)
- [x] Organized: archive/roadmaps/ (historical roadmaps)
- [x] Kept: archive/planning_oct_2025/ (other planning docs)

---

### 3. Documentation Consolidation ✅

#### Keep (Single Source of Truth) ✅
- [x] `ROADMAP.md` - Single canonical roadmap
- [x] `CONTINUATION_PROMPT.md` - Updated current state
- [x] `CHANGELOG.md` - Added v2.54.2 cleanup entry

#### Create New
- [ ] `ARCHITECTURE.md` - TODO: Create for Phase 1 (current system)
- [ ] `CLOUD_RUN_BATCH.md` - TODO: Create for Phase 1.3 (detailed architecture)

#### Archive/Delete ✅
- [x] Deleted VPS_ARCHITECTURE.md
- [x] Archived all STATION10_*.md
- [x] Archived old roadmaps (3 files)
- [x] Archived STATUS.md

---

### 4. Dependencies Cleanup ✅

#### pyproject.toml ✅
- [x] Removed python-telegram-bot
- [x] Removed boto3 (unused)

#### poetry.lock ✅
- [x] Ran `poetry lock` to regenerate
- [x] Clean dependencies

---

### 5. Cloud Run Jobs Review

#### Existing Jobs (Needs Research Next Session)
```
Current state:
  - clipscribe-worker-flash (scheduled every 5 min)
  - clipscribe-worker-pro (scheduled every 10 min)
  - Designed for RSS monitoring
  
Decision:
  - Disable schedulers
  - Repurpose for on-demand batch processing
  - Add Pub/Sub trigger support
```

**Action**: TODO for Phase 1.3 implementation

---

### 6. Git Cleanup ✅

#### Commits Made ✅
1. [x] Removed Telegram bot code
2. [x] Removed VPS deployment files  
3. [x] Archived exploration files
4. [x] Updated dependencies
5. [x] Created single-user database
6. [x] Organized all archives
7. [x] Updated all documentation
8. [x] Pushed to origin/main

#### Tag Created
- [ ] TODO: Tag v2.54.2 after final verification

---

### 7. Testing After Cleanup

#### Verify Core Functionality
- [x] Git working tree clean
- [ ] TODO: Fix integration test imports (low priority)
- [x] Database schema validated
- [x] Error handler created

#### Verify Clean State ✅
- [x] `git status` shows clean working tree
- [x] No untracked VPS/Telegram files
- [x] All documentation updated
- [x] Ready for Phase 1 implementation

---

## Success Criteria ✅

### Clean State Achieved ✅
- [x] No Telegram code in src/
- [x] No VPS deployment files in root
- [x] Single ROADMAP.md with clear Phase 1 plan
- [x] Archive directory organized
- [x] All documentation consistent
- [x] Git history clean and understandable
- [x] Core code functional (hybrid processor, database)
- [x] Ready to start Phase 1 implementation

### Remaining for Next Session
- [ ] Tag v2.54.2
- [ ] Fix integration test imports (update to video_retriever_v2)
- [ ] Research Cloud Run Jobs current state
- [ ] Begin Phase 1.1 implementation (batch processing)

---

## Post-Cleanup: Next Steps

**After cleanup is complete:**

1. Review ROADMAP.md one final time
2. Create detailed Phase 1.3 implementation plan
3. Verify Cloud Run Jobs setup
4. Start building batch CLI commands

**Not before cleanup is done.**

---

## Estimated Time

- Code cleanup: 1 hour
- File/directory cleanup: 30 minutes
- Documentation consolidation: 1 hour
- Git cleanup & commits: 30 minutes
- Testing: 30 minutes
- **Total: 3-4 hours**

Better to spend 4 hours cleaning up properly than build on a messy foundation.

---

*This cleanup must be completed before any Phase 1.3 implementation begins.*

