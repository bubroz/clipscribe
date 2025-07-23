# ClipScribe AI Assistant Continuation Prompt

## Current State (2025-07-22 19:42 PDT)

### Core Model Strategy (MANDATORY)
- **Primary Models**: ClipScribe exclusively uses **Gemini 2.5 Flash** (for speed/cost) and **Gemini 2.5 Pro** (for complex reasoning). [[memory:4071092]]
- **No Legacy Models**: Older generations (e.g., 1.5) are not to be used.

### Latest Version: v2.19.6
- Docs updated to reflect Gemini 2.5-only strategy.
- Plan established to fix and test PBS NewsHour batch processing.

### Recent Changes
- **v2.19.6** (2025-07-22): Corrected model strategy to Gemini 2.5. Updated docs.
- **v2.19.6** (2025-07-21): Entity extraction simplification.
- **v2.19.5** (2025-07-19): Backend validation completed.

### Known Issues ⚠️
- Batch processing scripts (`pbs_fast_batch.py`) are outdated and require fixes before use.
- Vertex AI integration is disabled due to config/quota issues. Requires robust fallbacks.

### Roadmap 🗺️
- **Immediate**: Fix `pbs_fast_batch.py` script.
- **Next**: Run full test suite to ensure system health.
- **Soon**: Execute 30-day PBS NewsHour batch analysis with the corrected script.
- **Tracked Plan**: See GitHub Issue #1 for PBS test details.

### 🚀 NEXT SESSION: Fix and Test

**Detailed Plan (Tracked in GitHub Issue #1)**:
1.  **Implement Script Fixes**: Apply changes to `pbs_fast_batch.py` to use `VideoIntelligenceRetriever` correctly, add `tenacity` retries, and manage concurrency safely.
2.  **Run Full Test Suite**: Execute `poetry run pytest` to validate no regressions were introduced.
3.  **Test Single Video**: Process one PBS video to confirm the fix works end-to-end.
4.  **Execute Full Batch**: Run the full PBS NewsHour batch analysis.

**Ready-to-Run Commands:**
```bash
# Step 1: Fix the script (AI will propose the edit)
# Step 2: Run tests
poetry run pytest

# Step 3: Run the batch process
poetry run python examples/pbs_fast_batch.py
```