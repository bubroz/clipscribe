# ClipScribe Cleanup Plan

**Date**: October 15, 2025  
**Reason**: Clean up after Telegram bot exploration, align with roadmap  
**Goal**: Clean slate before Phase 1.3 implementation

---

## Cleanup Checklist

### 1. Code Cleanup

#### Remove Telegram Bot
- [ ] Delete `src/clipscribe/bot/station10_bot.py`
- [ ] Delete `src/clipscribe/database/db_manager.py` (will create simpler version)
- [ ] Delete `src/clipscribe/database/schema.sql` (will create single-user version)
- [ ] Remove Telegram dependencies from `pyproject.toml`

#### Simplify Database
- [ ] Create new single-user database schema
- [ ] Keep: videos, entities, costs tables
- [ ] Remove: users table, multi-user foreign keys
- [ ] Update database manager for single-user

#### Keep & Integrate Good Code
- [ ] Keep `src/clipscribe/processors/hybrid_processor.py` (Voxtral+Grok)
- [ ] Extract error handling from bot to core utils
- [ ] Make hybrid processor the default in retriever

---

### 2. File & Directory Cleanup

#### Root Directory
```
Current mess:
  .deployignore
  DEPLOY_TO_VPS.md
  create_deployment.sh
  VPS_ARCHITECTURE.md
  
Action:
  - Delete .deployignore (not needed)
  - Archive DEPLOY_TO_VPS.md
  - Delete create_deployment.sh
  - Delete VPS_ARCHITECTURE.md
```

#### Scripts Directory
```
Review scripts/:
  - configure_r2_lifecycle.py → Delete (not using R2)
  - station10-bot.service → Archive
  - Keep others (they're useful)
```

#### Archive Organization
```
Current:
  archive/
    planning_oct_2025/
    roadmaps/
    telegram_exploration_oct_2025/
    
Better:
  archive/
    2025_october_telegram_exploration/
      - All Telegram/VPS files
      - SALVAGE_PLAN.md
      - Lessons learned
    roadmaps_historical/
      - Old roadmaps for reference
```

---

### 3. Documentation Consolidation

#### Keep (Single Source of Truth)
- [ ] `ROADMAP.md` - Update to remove VPS references
- [ ] `CONTINUATION_PROMPT.md` - Update current state
- [ ] `CHANGELOG.md` - Add v2.54.2 cleanup entry

#### Create New
- [ ] `ARCHITECTURE.md` - Current system architecture
- [ ] `CLOUD_RUN_BATCH.md` - Phase 1.3 architecture (Google native)

#### Archive/Delete
- [ ] Archive `VPS_ARCHITECTURE.md` → `archive/2025_october_telegram_exploration/`
- [ ] Archive all `STATION10_*.md` → Already done
- [ ] Delete redundant architecture docs

---

### 4. Dependencies Cleanup

#### pyproject.toml
```toml
# Remove:
python-telegram-bot = "^20.x"  # Not needed

# Keep:
voxtral (if exists)
httpx (for Grok API)
all existing core dependencies
```

#### poetry.lock
- [ ] Run `poetry lock` after removing dependencies
- [ ] Test that everything still works

---

### 5. Cloud Run Jobs Review

#### Existing Jobs (Need Review)
```
Current state:
  - clipscribe-worker-flash (scheduled every 5 min)
  - clipscribe-worker-pro (scheduled every 10 min)
  - Designed for RSS monitoring
  
Decision needed:
  - Are these active?
  - Should we disable schedulers?
  - Repurpose for batch processing?
```

**Action**: Research current state, document decisions

---

### 6. Git Cleanup

#### Commits to Make
1. **Remove Telegram bot code**
   ```
   git rm src/clipscribe/bot/station10_bot.py
   git rm src/clipscribe/database/db_manager.py
   git rm src/clipscribe/database/schema.sql
   git commit -m "refactor: remove Telegram bot from exploration"
   ```

2. **Clean up root directory**
   ```
   git rm .deployignore create_deployment.sh VPS_ARCHITECTURE.md DEPLOY_TO_VPS.md
   git commit -m "chore: remove VPS deployment files"
   ```

3. **Archive exploration files**
   ```
   git mv archive/telegram_exploration_oct_2025 archive/2025_october_telegram_exploration
   git commit -m "chore: organize Telegram exploration archive"
   ```

4. **Update dependencies**
   ```
   # After removing telegram deps
   git add pyproject.toml poetry.lock
   git commit -m "deps: remove Telegram bot dependencies"
   ```

5. **Create single-user database**
   ```
   # After creating new schema
   git add src/clipscribe/database/
   git commit -m "feat: add single-user entity database"
   ```

6. **Tag clean state**
   ```
   git tag v2.54.2-cleaned
   git push origin main --tags
   ```

---

### 7. Testing After Cleanup

#### Verify Core Functionality
- [ ] Test video processing with hybrid processor
- [ ] Test CLI commands still work
- [ ] Test database operations (if implemented)
- [ ] Run test suite: `poetry run pytest`

#### Verify Clean State
- [ ] `git status` shows clean working tree
- [ ] No untracked files that should be tracked
- [ ] All tests passing
- [ ] Documentation up to date

---

## Success Criteria

### Clean State Achieved When:
- [ ] No Telegram code in src/
- [ ] No VPS deployment files in root
- [ ] Single ROADMAP.md with clear Phase 1.3 plan
- [ ] Archive directory organized
- [ ] All documentation consistent
- [ ] Git history clean and understandable
- [ ] Test suite passing
- [ ] Ready to start Phase 1.3 implementation

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

