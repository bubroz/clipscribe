# Documentation Validation Protocol

**Last Updated:** November 12, 2025  
**Purpose:** Ensure documentation reflects actual runtime behavior, not assumptions

---

## Core Principle

**Documentation must match reality across three sources:**
1. **Production code** (what can execute)
2. **Recent logs** (what actually executed)
3. **Live testing** (what executes now)

**If any source contradicts the docs, the docs are wrong.**

---

## When to Validate

### Required:
- ✅ After major feature releases
- ✅ After architectural changes
- ✅ When workflows change
- ✅ Before significant documentation updates

### Recommended:
- Every 90 days (quarterly review)
- When users report confusion
- After fixing major bugs
- When onboarding new developers

---

## Three-Source Validation Method

### Source 1: Code Analysis

**Read actual production code:**

```bash
# Find what ACTUALLY runs in production
grep -r "@app\.cls\|@app\.function" deploy/
grep -r "def process\|async def.*process" src/clipscribe/commands/
grep -r "class.*Processor\|class.*Retriever" src/clipscribe/
```

**Trace execution paths:**
1. Start at entry point (CLI or API)
2. Follow function calls
3. Note component interactions
4. Verify data flow direction
5. Check error handling paths

**Questions to answer:**
- Which components are actually invoked?
- What's the execution order?
- Are "optional" components actually used?
- Are there dead code paths documented as active?

### Source 2: Log Analysis

**Find recent successful runs:**

```bash
# Check validation reports
find . -name "*validation*" -type f -mtime -30

# Check processing logs
ls -lt logs/ output/ | head -20

# Check test results
find tests/ -name "*.log" -o -name "*results.json"
```

**Extract from logs:**
- Actual steps executed (not theoretical)
- Actual timing/performance
- Actual costs incurred
- Actual errors encountered
- Actual component interactions

**Compare to documented workflows:**
- Does order match?
- Are steps missing/extra?
- Are metrics accurate?

### Source 3: Live Testing

**Run minimal test case:**

```bash
# Test local CLI
poetry run clipscribe process video "SHORT_TEST_VIDEO_URL" --output-dir /tmp/test

# Test Modal (if deployed)
modal run deploy/station10_modal.py::test_function

# Test API endpoints
poetry run python -c "from src.clipscribe.api.entity_search import search_entities; ..."
```

**Capture and verify:**
- Does it run without errors?
- Does output match documented schema?
- Is performance as claimed?
- Are prerequisites accurate?

---

## Validation Checklist

### For Each Documentation File:

- [ ] **Code validates** - All documented components exist and are used
- [ ] **Logs confirm** - Recent runs match documented behavior
- [ ] **Test passes** - Live execution works as described
- [ ] **Examples work** - Copy-pasteable and functional
- [ ] **Metrics sourced** - All numbers have dates and sources
- [ ] **No speculation** - Only documented confirmed behavior
- [ ] **Timestamp added** - "Validated: [date]" at top

### For Each Workflow Diagram:

- [ ] **Sequence accurate** - Steps happen in documented order
- [ ] **Components exist** - All boxes represent real code
- [ ] **Arrows correct** - Data flows match actual code
- [ ] **No missing steps** - All critical steps shown
- [ ] **Error paths shown** - Fallbacks/retries documented
- [ ] **Tested end-to-end** - Diagram matches live execution

### For Each Code Example:

- [ ] **Syntax correct** - Code parses without errors
- [ ] **Imports work** - All imports resolve
- [ ] **Example runs** - Actually executes without errors
- [ ] **Output matches** - Produces documented results
- [ ] **Prerequisites clear** - Setup requirements stated
- [ ] **Tested date** - "Tested: [date]" in comments

---

## Red Flags (Documentation Smells)

### Immediate Concerns:
- ❌ "Should" or "will" without concrete dates
- ❌ "Currently" or "now" without version/date
- ❌ Examples that can't be copy-pasted
- ❌ Metrics without source or date
- ❌ "Deprecated" without verification
- ❌ Components mentioned but not in code
- ❌ Diagrams with boxes that don't map to real components

### Warning Signs:
- ⚠️  Docs older than code (Last Updated < git log date)
- ⚠️  Pricing/performance claims without source
- ⚠️  "Planned" features mixed with current
- ⚠️  Workflows without validation timestamps
- ⚠️  Prerequisites not testable
- ⚠️  Examples without expected output

---

## Validation Workflow

### 1. Discovery Phase (30-60 min)

**Identify reality:**
```bash
# What runs in production?
find deploy/ -name "*.py" -exec grep -l "app\.cls\|app\.function" {} \;

# What's the CLI entry point?
poetry run clipscribe --help

# Recent successful executions?
ls -lt output/ logs/ | head -20
```

**Document findings:**
- Production code paths
- Recent execution evidence
- Available workflows

### 2. Comparison Phase (60-90 min)

**For each doc, create comparison matrix:**

| Claim | Documented | Code Shows | Logs Show | Live Test | Status |
|-------|-----------|-----------|-----------|-----------|--------|
| Step 1 | X | X | X | X | ✅ Match |
| Step 2 | Y | Z | Z | Z | ❌ Fix doc |
| Feature A | Exists | Missing | N/A | N/A | ❌ Remove claim |

**Focus areas:**
- Workflows (execution order)
- Architecture (component interactions)
- API (endpoints, schemas, performance)
- Metrics (costs, speed, quality)
- Examples (do they run?)

### 3. Correction Phase (60-120 min)

**Fix each discrepancy:**

1. **Determine truth** - Which source is authoritative?
   - Code > Logs > Tests (code is ultimate truth)
   - Recent logs > old logs
   - Successful execution > theoretical design

2. **Update documentation** - Match reality exactly
   - No softening ("should" → "does")
   - No speculation (remove unverified claims)
   - Add sources ("Validated Nov 12, 2025")

3. **Retest** - Verify fix is accurate
   - Does updated doc now match code?
   - Does updated diagram reflect actual flow?
   - Do updated examples work?

### 4. Validation Phase (30 min)

**Final verification:**

```bash
# All examples compile/parse
find docs/ examples/ -name "*.py" -exec python -m py_compile {} \;

# No legacy references
grep -r "deprecated\|planned\|will\|should" docs/ | grep -v "Validated:"

# All docs timestamped
grep -L "Validated:" docs/*.md
```

**Manual checks:**
- Click every link (no 404s)
- Run every example (works?)
- Verify every metric (sourced?)
- Test every workflow (succeeds?)

---

## Common Fixes

### "CLI Deprecated" (When It's Not)

**Wrong:**
```markdown
**Note:** Local CLI (`clipscribe process`) is currently deprecated. Use Modal workflow below.
```

**Right:**
```markdown
ClipScribe supports two workflows:
1. **Modal GPU** - Serverless, scalable (recommended for batch processing)
2. **Local CLI** - Direct, simple (good for single videos)

Both are production-ready. Choose based on your needs.

**Validated:** Nov 12, 2025 - Both workflows tested and working
```

### Theoretical Components (Not Actually Used)

**Wrong:**
```markdown
3. Process with ComponentX (handles Y)
4. ComponentX sends to ComponentZ
```

**Right:**
(If ComponentX exists in code but isn't actually called)
```markdown
3. Process directly with ComponentZ
   
Note: ComponentX exists for future use but is not currently in production path.
```

Or just remove ComponentX from docs entirely if truly unused.

### Old Metrics (Undated or Unsourced)

**Wrong:**
```markdown
Processing speed: 10x realtime
Cost: $0.05 per video
```

**Right:**
```markdown
Processing speed: 10-11x realtime (validated Nov 12, 2025, 20 videos, A10G GPU)
Cost: $0.073 per video (avg of 20 videos, Nov 12, 2025)
  - GPU: $0.071 (96.3%)
  - Grok: $0.005 (6.7%)
Source: output/VALIDATION_REPORT_NOV11.md
```

### Broken Examples

**Wrong:**
```python
# This example (copy-pasted from old code, never tested)
from clipscribe import OldClass  # ImportError!
result = OldClass().process()
```

**Right:**
```python
# Tested: Nov 12, 2025
from src.clipscribe.retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2

retriever = VideoIntelligenceRetrieverV2()
result = await retriever.process_url("https://...")
# Expected output: VideoIntelligence object with entities, relationships, topics
```

---

## Quality Metrics

### Documentation Health Score

**Green (Healthy):**
- All workflows tested in last 30 days
- All examples run successfully
- All metrics sourced and dated
- No "TODO" or "planned" without dates
- All three sources agree

**Yellow (Needs Attention):**
- Some workflows >90 days since validation
- Some examples untested
- Some metrics undated
- Minor discrepancies between sources

**Red (Critical):**
- Workflows documented but don't work
- Examples that error
- Metrics contradicted by code/logs
- Major discrepancies (like "deprecated" when working)

---

## Validation Report Template

After validation, create:

```markdown
# Documentation Validation Report

**Date:** Nov 12, 2025
**Validator:** [Name]
**Scope:** All docs/ + README.md

## Summary

- Files validated: 8
- Discrepancies found: 12
- Discrepancies fixed: 12
- Tests run: 15
- Examples verified: 8

## Findings

### Critical Issues:
1. WORKFLOW.md claimed "CLI deprecated" - FALSE (command works)
2. Cost calculations used wrong pricing (50-67x too low)
3. Model references inconsistent (5 different names)

### Minor Issues:
1. Some diagrams had theoretical components
2. Some examples missing validation timestamps
3. Some metrics undated

### Validated Components:
- ✅ Modal GPU workflow (works as documented)
- ✅ Local CLI workflow (works, was incorrectly labeled deprecated)
- ✅ Entity extraction (matches documented behavior)
- ✅ Cost calculations (now accurate with correct pricing)

## Recommendations

1. Add validation timestamps to all docs
2. Test all examples quarterly
3. Verify metrics against latest runs
4. Use this protocol for all future updates
```

---

## Integration with Development

### Pre-Commit Hook (Recommended)

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for documentation changes
docs_changed=$(git diff --cached --name-only | grep "docs/\|README.md")

if [ -n "$docs_changed" ]; then
    echo "Documentation changed - validation recommended:"
    echo "$docs_changed"
    echo ""
    echo "Have you:"
    echo "- Tested examples?"
    echo "- Verified against code?"
    echo "- Added 'Validated: $(date +%Y-%m-%d)' timestamp?"
    echo ""
    read -p "Continue commit? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
```

### CI/CD Integration

```yaml
# .github/workflows/validate-docs.yml
name: Validate Documentation

on:
  pull_request:
    paths:
      - 'docs/**'
      - 'README.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check for validation timestamps
        run: |
          # Fail if docs changed without validation timestamp update
          git diff origin/main docs/ README.md | grep "Validated:"
      - name: Test code examples
        run: |
          find docs/ -name "*.md" -exec grep -l "```python" {} \; | while read f; do
            # Extract and test Python examples
            echo "Testing examples in $f"
          done
```

---

## Success Criteria

Documentation is validated when:

1. ✅ All three sources agree (code, logs, live test)
2. ✅ All examples tested and working
3. ✅ All metrics sourced and dated
4. ✅ All workflows end-to-end verified
5. ✅ All diagrams match code execution
6. ✅ No speculation or unverified claims
7. ✅ Validation timestamps on all docs
8. ✅ Report generated documenting process

---

**Use this protocol for every documentation update to maintain accuracy and trustworthiness.**

