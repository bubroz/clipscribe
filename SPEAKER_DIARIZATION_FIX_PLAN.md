# Speaker Diarization Fix Plan
**Critical Issue Identified by CHiME-6 Validation**  
**Date:** October 21, 2025 02:40 PDT

---

## The Problem (Quantified)

### **Validation Results (S09 - CHiME-6):**

**Transcription: WORLD-CLASS ✅**
- WER: 43.5% (vs winner: 42.7%, baseline: 77.9%)
- Beat baseline by 34.4 percentage points
- 0.8% from CHiME-6 challenge winner

**Speaker Diarization: BROKEN ❌**
- Detected: 7 speakers
- Actual: 4 speakers
- Speaker accuracy: 14.5%
- Over-segmentation: 3 extra speakers

### **Root Cause Analysis:**

**Speaker Distribution (S09):**
```
MAJOR (should be the 4 real speakers):
  SPEAKER_07: 766 segs (38.0%) - 33.1 min
  SPEAKER_06: 665 segs (33.0%) - 24.0 min
  SPEAKER_04: 241 segs (11.9%) - 9.4 min
  SPEAKER_03: 150 segs (7.4%)  - 7.9 min

MINOR (over-segmentation artifacts):
  SPEAKER_01: 94 segs (4.7%)   - 4.5 min
  SPEAKER_02: 68 segs (3.4%)   - 3.6 min
  SPEAKER_05: 34 segs (1.7%)   - 1.3 min
```

**Key Insights:**
1. **4 major speakers detected** (matches ground truth!)
2. **3 minor speakers** are artifacts (4.7%, 3.4%, 1.7%)
3. **50-60% of segments are <2s** (excessive fragmentation)
4. **Current 10% threshold too high** - misses speakers with 7-12%

---

## Current Algorithm (Broken)

```python
# Current thresholds (from station10_modal.py line 233):
major_speakers = [s for s, count in speaker_counts.items() if (count / total) > 0.10]

# Problems:
# 1. 10% threshold too high for 4+ speaker meetings
#    - In 4-speaker meeting, each speaker ≈ 25%
#    - But one speaker had only 7.4% (150 segs)
#    - Gets classified as "minor" and merged away!

# 2. Tiny speaker threshold too low (<1%)
#    - SPEAKER_05 at 1.7% should be merged
#    - SPEAKER_02 at 3.4% should be merged
#    - But algorithm only merges <1%

# 3. Gemini prompt too conservative
#    - Only checks A→B→A patterns with <3 words
#    - Misses most over-segmentation errors
#    - Only corrected 7/2018 segments (0.3%)
```

---

## The Fix (Comprehensive)

### **Fix #1: Adaptive Major Speaker Threshold**

**Old (broken):**
```python
major_speakers = [s for s, count in speaker_counts.items() if (count / total) > 0.10]
```

**New (adaptive):**
```python
# Adaptive threshold based on expected speaker count
num_speakers = len(speaker_counts)

if num_speakers <= 2:
    threshold = 0.10  # 10% for dyadic (works fine)
elif num_speakers <= 4:
    threshold = 0.05  # 5% for small meetings
elif num_speakers <= 8:
    threshold = 0.03  # 3% for medium meetings
else:
    threshold = 0.02  # 2% for large meetings

major_speakers = [s for s, count in speaker_counts.items() if (count / total) > threshold]

# Also ensure we keep at most expected_speakers + 2 buffer
# If we have 10 speakers but only 4-5 are major, something's wrong
```

### **Fix #2: More Aggressive Minor Speaker Merging**

**Old (broken):**
```python
tiny = [s for s, c in final_counts.items() if (c / len(cleaned)) < 0.01 and s not in major_set]
```

**New (aggressive):**
```python
# Merge speakers below adaptive threshold
# If major threshold is 5%, merge anything <5%
merge_threshold = threshold  # Same as major speaker threshold

tiny = [s for s, c in final_counts.items() 
        if (c / len(cleaned)) < merge_threshold and s not in major_set]

# Also merge based on absolute count if very low
absolute_min = 50  # Any speaker with <50 segments is suspicious in 2000+ seg meetings

really_tiny = [s for s, c in final_counts.items() 
               if c < absolute_min and s not in major_set]

speakers_to_merge = set(tiny + really_tiny)
```

### **Fix #3: Aggressive Duplicate Text Merging**

**NEW STEP (not in current algorithm):**

```python
# Step 0: Merge duplicate/similar text across different speakers
# This catches the "Vancouver Stanley Park" repetition issue

from difflib import SequenceMatcher

def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# For each pair of consecutive segments with different speakers
for i in range(len(segments) - 1):
    curr = segments[i]
    next_seg = segments[i+1]
    
    if curr['speaker'] != next_seg['speaker']:
        # Check if text is similar (>0.8 similarity)
        sim = text_similarity(curr['text'], next_seg['text'])
        if sim > 0.8:
            # Same utterance split across speakers - merge
            next_seg['speaker'] = curr['speaker']
            # Could also merge the segments themselves
```

### **Fix #4: Make Gemini More Aggressive**

**Old (too conservative):**
```python
# Only check A→B→A with <3 words
if (curr.get('speaker') == after.get('speaker') and 
    curr.get('speaker') != next_seg.get('speaker') and
    len(next_seg.get('text', '').split()) <= 3):
```

**New (comprehensive):**
```python
# Check multiple patterns:

# Pattern 1: A→B→A with short text (<3 words)
# Pattern 2: Rapid speaker switches (within 1 second)
# Pattern 3: Very short segments (<1s) with different speaker
# Pattern 4: Similar text with different speaker (duplicate detection)

problem_segments = []

for i in range(len(segments) - 2):
    curr = segments[i]
    next_seg = segments[i+1]
    after = segments[i+2]
    
    # Pattern 1: A→B→A
    is_aba = (curr.get('speaker') == after.get('speaker') and 
              curr.get('speaker') != next_seg.get('speaker'))
    
    # Pattern 2: Rapid switch
    time_gap = next_seg.get('start', 0) - curr.get('end', 0)
    is_rapid = time_gap < 0.5  # Less than 0.5s gap
    
    # Pattern 3: Very short
    duration = next_seg.get('end', 0) - next_seg.get('start', 0)
    is_very_short = duration < 1.0
    
    # Pattern 4: Duplicate text
    from difflib import SequenceMatcher
    text_sim = SequenceMatcher(None, 
                               curr.get('text', '').lower(),
                               next_seg.get('text', '').lower()).ratio()
    is_duplicate = text_sim > 0.7
    
    # Flag if ANY pattern matches
    if (is_aba or (is_rapid and is_very_short) or is_duplicate):
        problem_segments.append({...})

# Now Gemini will check MORE segments
# Limit to 50 instead of 20 (accept higher cost for better quality)
problem_segments = problem_segments[:50]
```

---

## Implementation Plan

### **Step 1: Update Speaker Cleanup (2 hours)**

File: `deploy/station10_modal.py`, function `_improve_speaker_quality`

**Changes:**
1. Add adaptive threshold based on speaker count
2. Add duplicate text detection step (Step 0)
3. Merge more aggressively (use adaptive threshold, not fixed 1%)
4. Add absolute minimum threshold (< 50 segments in 2000+ meetings)

**Test:** Re-run S09, expect 4-5 speakers (not 7)

### **Step 2: Update Gemini Verification (2 hours)**

File: `deploy/station10_modal.py`, function `_gemini_speaker_verification`

**Changes:**
1. Expand pattern detection (4 patterns instead of 1)
2. Increase limit (50 segments instead of 20)
3. Accept higher cost for better quality
4. Add duplicate text detection

**Test:** Re-run S09, expect more corrections (50-100 instead of 7)

### **Step 3: Tune pyannote.audio (1 hour)**

File: `deploy/station10_modal.py`, diarization model initialization

**Research:**
- Can we hint speaker count to pyannote?
- Can we adjust clustering threshold?
- Are there pyannote parameters we're not using?

**Test:** Does this reduce initial over-segmentation?

### **Step 4: Multi-Video Validation (2 hours)**

**Test on:**
- S09 (CHiME-6): 4 speakers expected → verify we get 4
- The View: 5-7 speakers expected → verify we get 5-7
- MTG: 2 speakers expected → verify we still get 2

**Target:** >80% speaker accuracy across all tests

### **Step 5: Re-run Validation (1 hour)**

- Re-process S09 with fixed diarization
- Calculate new metrics
- Compare to original (43.5% WER, 14.5% speaker acc)
- Target: 43-45% WER, >80% speaker accuracy

**Total effort:** 8 hours to fix properly

---

## Success Criteria

**Before resuming comprehensive validation, we must achieve:**

✅ **S09 (CHiME-6):** 4-5 speakers detected (not 7)  
✅ **Speaker accuracy:** >80% (up from 14.5%)  
✅ **WER maintained:** <45% (don't break transcription)  
✅ **The View:** 5-7 speakers (down from 10)  
✅ **MTG:** 2 speakers (verify we didn't break dyadic)  

**Only then resume validation.**

---

## Revised Timeline

**Week 1 (Revised): Fix Speaker Quality**
- Days 1-2: Validation infrastructure (DONE) ✅
- Day 3: CHiME-6 validation test (DONE) ✅
- **Days 4-6: FIX SPEAKER DIARIZATION (NOW)**
- Day 7: Re-validate, confirm >80% accuracy

**Week 2 (Unchanged): Phase 1 Validation**
- Process all datasets with FIXED quality
- Generate Phase 1 report

**Weeks 3-9: Proceed as planned**

**This is the hard right: Fix quality before validating quality.**

---

## Why This Is Right

**The validation did its job:**
- ✅ Proved transcription is world-class
- ✅ Revealed speaker diarization is broken
- ✅ Quantified the problem (14.5% accuracy)

**Now we fix it:**
- 🔧 Adaptive thresholds for multi-speaker
- 🔧 Duplicate text detection
- 🔧 More aggressive Gemini verification
- 🔧 Test until >80% accuracy

**THEN we validate comprehensively** with confidence in the quality.

**This is how rigorous engineering works: Measure → Fix → Validate.**

---

**Ready to start implementing the fixes?**

