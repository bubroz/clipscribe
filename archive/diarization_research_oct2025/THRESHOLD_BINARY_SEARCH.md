# Clustering Threshold Binary Search
**Date:** October 22, 2025  
**Status:** NARROWING IN - Found the range!

## Complete Results

| Threshold | Speakers | Accuracy | Distance | Notes |
|-----------|----------|----------|----------|-------|
| 0.70 | 6 | 17% | +2 | Default baseline |
| 0.80 | 5 | 35% | +1 | **VERY CLOSE** |
| 0.83 | ? | ? | ? | **Testing now...** |
| 0.87 | 2 | 38% | -2 | **CLIFF - too aggressive** |
| 0.95 | 2 | 37% | -2 | Way too aggressive |

## Key Finding: Narrow Optimal Range

**Sweet spot identified: 0.80 - 0.87**

```
0.70 ──────> 6 speakers (17%)
      ↓
0.80 ──────> 5 speakers (35%) ← Close!
      ↓
0.83 ──────> ? speakers (?) ← TESTING
      ↓
0.87 ──────> 2 speakers (38%) ← Cliff!
      ↓
0.95 ──────> 2 speakers (37%)
```

## Interesting Observation

**Accuracy improves even with wrong speaker count:**
- 5 speakers: 35% accuracy (2x baseline)
- 2 speakers: 38% accuracy (2.2x baseline)

**Hypothesis:** Aggressive merging reduces speaker confusion errors, improving word-level attribution accuracy even if total speaker count is wrong.

**This suggests:** Even if we can't hit exactly 4 speakers, we're making the system better!

## Next Test: 0.83

**Midpoint between 0.80 (5 speakers) and 0.87 (2 speakers)**

**Possible outcomes:**
- **BEST**: 4 speakers → SUCCESS! 🎯
- **Good**: 5 speakers → Try 0.85
- **Possible**: 3 speakers → Try 0.81
- **Unlikely**: 2 speakers → Cliff is steeper, use 0.80

## Decision Matrix

### If 0.83 gives 4 speakers:
1. ✅ Validate on S02 session
2. ✅ Test on AnnoMI dataset  
3. ✅ Lock in as production value
4. ✅ Document for paper

### If 0.83 gives 5 speakers:
1. Try 0.85 (closer to cliff)
2. Or accept 5 speakers + use Gemini merger

### If 0.83 gives 3 speakers:
1. Try 0.81 (between 0.80-0.83)
2. Fine-tune to exactly 4

### If 0.83 gives 2 speakers:
1. Cliff is sharper than expected
2. Use 0.80 as optimal (5 speakers, 35%)
3. Apply Gemini merger to reduce 5→4

## Success Metrics

✅ **Achieved:**
- Found smooth gradient (no binary collapse)
- Accuracy doubled from baseline (17%→38%)
- Narrowed to 0.07 threshold range

⏳ **In Progress:**
- Finding exact 4-speaker threshold
- Testing 0.83 now

🎯 **Ultimate Goal:**
- 4 speakers exactly
- 40-50% accuracy
- Generalizes to other sessions

## Fallback Plan

**If perfect 4-speaker threshold doesn't exist:**

**Option A: Use 0.80 + Gemini Merger**
- pyannote with threshold 0.80 → 5 speakers, 35%
- Gemini analyzes and merges duplicate → 4 speakers
- Expected final: 4 speakers, 45-55% accuracy

**Option B: Accept 5 speakers**
- Threshold 0.80 gives best accuracy (35%)
- Speaker count off by 1 is acceptable
- Focus on WER and transcription quality

**Option C: Dynamic thresholding**
- Short meetings: 0.80
- Long meetings: 0.83
- Adapt based on audio characteristics

---

**STATUS: TESTING 0.83 - Expect 4 speakers or very close!**
