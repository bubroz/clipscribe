# Clustering Threshold Binary Search
**Date:** October 22, 2025  
**Problem:** Finding optimal threshold for 4 speakers

## Observations

| Threshold | Speakers | Accuracy | Status |
|-----------|----------|----------|--------|
| 0.70 | 6 | 17% | Too many |
| 0.95 | 2 | 37% | Too few |
| 1.20 | 2 | 37% | Too few |

**Pattern:** Binary collapse between 0.7-0.95

## Binary Search Strategy

```
Test range: 0.70 - 0.95
Target: 4 speakers (±1)

Round 1: Test 0.825 (midpoint)
├─ If 6 speakers → try 0.875 (higher)
├─ If 4 speakers → SUCCESS ✓
└─ If 2 speakers → try 0.775 (lower)

Round 2: Based on Round 1
Round 3: Fine-tune ±0.025
```

## Test Commands

**For each threshold, run in EXTERNAL terminal to avoid timeout:**

```bash
cd /Users/base/Projects/clipscribe

# 1. Update threshold in Modal
# Edit deploy/station10_modal.py line 182:
# CLUSTERING_THRESHOLD = 0.825  # (or whatever value)

# 2. Deploy
git add deploy/station10_modal.py
git commit -m "test(diarization): threshold 0.825"
git push
poetry run modal deploy deploy/station10_modal.py

# 3. Test
gsutil rm -r gs://clipscribe-validation/validation/results/ 2>/dev/null
poetry run python scripts/validation/test_chime6.py

# 4. Record results
# Speakers: X, Accuracy: Y%
```

## Next Tests

### Test 1: 0.80
Reasoning: Closer to 0.7 (which gave 6 speakers)
Expected: 4-6 speakers

### Test 2: 0.85  
Reasoning: Midpoint between 0.7 and 0.95
Expected: 3-4 speakers

### Test 3: Fine-tune
Based on Test 1+2 results

## Success Criteria

- ✅ 4 speakers detected (matches ground truth)
- ✅ Speaker accuracy >50%
- ✅ Consistent across multiple sessions

## Alternative If Binary Search Fails

If we can't find a threshold that gives 4 speakers:
→ Proceed to **Gemini Speaker Merger** approach
→ Use threshold that maximizes accuracy, let Gemini fix speaker count

