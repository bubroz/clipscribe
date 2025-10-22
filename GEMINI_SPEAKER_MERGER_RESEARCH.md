# Gemini Speaker Merger: Deep Analysis
**Date:** October 22, 2025  
**Problem:** pyannote over-segments (6 detected vs 4 actual speakers)  
**Hypothesis:** Use Gemini to merge over-segmented speakers by voice similarity

---

## Core Insight

**pyannote is good at:** Detecting speaking segments  
**pyannote is bad at:** Distinguishing similar voices (over-segments)

**Gemini is good at:** Analyzing voice characteristics, similarity  
**Gemini is bad at:** Precise timestamps, word-level alignment

**Synthesis:** Use each for what it's best at.

---

## Architecture Options

### Option A: Single-Pass Grouping (SIMPLEST)
```
1. pyannote detects 6 speakers (Speaker_0 through Speaker_5)
2. Extract one 10-15 sec audio clip per detected speaker
   - Choose high-confidence segments
   - Avoid overlapping speech
   - Get clean voice samples
3. Upload all 6 clips to Gemini in ONE request
4. Prompt: "Listen to these 6 voice samples. Group by actual voice similarity."
5. Gemini responds: {"Person 1": [0, 3], "Person 2": [1, 5], "Person 3": [2], "Person 4": [4]}
6. Remap all segments: Speaker_0 → Person_1, Speaker_3 → Person_1, etc.
```

**Pros:**
- ✅ Simple architecture
- ✅ One API call per file
- ✅ Uses Gemini's strength (voice analysis)

**Cons:**
- ❓ Relies on single Gemini call (what if it's wrong?)
- ❓ Need good representative clips
- ❓ No validation mechanism

**Cost:** ~$0.01-0.05 per 2-hour file (one Gemini audio call)

---

### Option B: Pairwise Validation (MORE ROBUST)
```
1. pyannote detects 6 speakers
2. Extract clips for all speakers
3. For each pair of speakers (A, B):
   - Give Gemini samples from A and B
   - Ask: "Are these the same person? Confidence?"
4. Build similarity matrix:
   [
     [1.0, 0.2, 0.3, 0.9, 0.1, 0.4],  // Speaker_0 vs all
     [0.2, 1.0, 0.1, 0.2, 0.8, 0.3],  // Speaker_1 vs all
     ...
   ]
5. Apply clustering threshold: merge pairs with >0.7 similarity
6. Iteratively merge until stable
```

**Pros:**
- ✅ More robust (validates each merge)
- ✅ Provides confidence scores
- ✅ Can tune threshold empirically

**Cons:**
- ❌ O(n²) Gemini calls (expensive!)
- ❌ For 6 speakers: 15 API calls
- ❌ Slower processing

**Cost:** ~$0.15-0.75 per 2-hour file (15 calls for 6 speakers)

---

### Option C: Hybrid (BEST OF BOTH)
```
1. pyannote detects 6 speakers
2. Use pyannote's OWN speaker embeddings first
   - pyannote already generates 512-dim embeddings per speaker
   - Calculate cosine similarity between embeddings
   - Pre-merge high-similarity pairs (>0.85)
3. If still >4 speakers, use Gemini as validator
   - Only analyze remaining ambiguous speakers
   - Gemini makes final grouping decision
4. Apply merged speaker labels
```

**Pros:**
- ✅ Uses free pyannote embeddings first
- ✅ Only calls Gemini when needed
- ✅ Best accuracy (two validation layers)

**Cons:**
- ⚠️ More complex architecture
- ⚠️ Need to implement embedding similarity

**Cost:** ~$0.00-0.05 per file (Gemini only if embeddings insufficient)

---

## Technical Implementation Details

### 1. Extracting Representative Clips

**Challenge:** Get clean, representative audio for each detected speaker.

**Strategy:**
```python
def extract_speaker_sample(diarization_df, speaker_id, audio, duration=10):
    """
    Extract the BEST sample for a speaker.
    
    Criteria:
    1. High confidence segment
    2. No overlapping speakers
    3. Long enough (10+ seconds)
    4. Clear voice (good signal)
    """
    speaker_segs = diarization_df[diarization_df['speaker'] == speaker_id]
    
    # Find segments with no overlap
    clean_segments = []
    for idx, seg in speaker_segs.iterrows():
        # Check if ANY other speaker overlaps this time
        overlaps = diarization_df[
            (diarization_df['speaker'] != speaker_id) &
            (diarization_df['start'] < seg['end']) &
            (diarization_df['end'] > seg['start'])
        ]
        
        if len(overlaps) == 0 and (seg['end'] - seg['start']) >= duration:
            clean_segments.append(seg)
    
    if not clean_segments:
        # Fallback: longest segment even with overlap
        clean_segments = speaker_segs.nlargest(1, 'duration')
    
    # Take first clean segment
    seg = clean_segments[0]
    start_sample = int(seg['start'] * SAMPLE_RATE)
    end_sample = int(min(seg['start'] + duration, seg['end']) * SAMPLE_RATE)
    
    return audio[start_sample:end_sample]
```

**Improvement:** Extract MULTIPLE samples per speaker, give Gemini best evidence.

---

### 2. Gemini Prompting Strategy

**Critical:** Prompt engineering determines success.

**Version 1 (Basic):**
```
You have 6 audio clips from a meeting. Each clip is labeled Speaker_0 through Speaker_5.

TASK: Listen carefully and determine how many DISTINCT people are actually speaking.

Some "speakers" might be the SAME person (the diarization system over-segmented).

Output JSON:
{
  "actual_speakers": 4,
  "groupings": {
    "Person_1": ["Speaker_0", "Speaker_3"],
    "Person_2": ["Speaker_1", "Speaker_5"],
    "Person_3": ["Speaker_2"],
    "Person_4": ["Speaker_4"]
  },
  "confidence": "high/medium/low"
}
```

**Version 2 (With Context):**
```
You are helping fix speaker diarization errors.

CONTEXT: An automated system detected 6 speakers in a 2-hour meeting audio.
However, the ground truth shows there are actually 4 people.
This means 2 of the detected "speakers" are duplicates (same person incorrectly split).

AUDIO SAMPLES: I'm providing 10-second clips of each detected speaker.

YOUR TASK: 
1. Listen to all 6 voice samples
2. Identify which samples are the SAME person
3. Group duplicate speakers together
4. Provide voice characteristics for each actual person

Focus on:
- Pitch and tone
- Speaking style
- Gender
- Voice timbre

Output format: [JSON schema]
```

**Version 3 (With Examples):**
```
EXAMPLE of over-segmentation error:
- Speaker_A: Female, high pitch, speaking about topic X
- Speaker_D: Female, high pitch, speaking about topic Y
→ These are the SAME person! (just different conversation segments)

Now analyze these 6 speakers...
```

**Best practice:** Provide context, examples, and clear output format.

---

### 3. Validation Strategy

**How do we know if it works?**

**Test on CHiME-6:**
```python
def validate_gemini_merger():
    # Ground truth: 4 speakers (P25, P26, P27, P28)
    
    # Step 1: pyannote detects 6 speakers
    pyannote_speakers = run_pyannote(audio)  # Returns 6
    
    # Step 2: Gemini merges
    gemini_grouping = gemini_merge_speakers(pyannote_speakers)
    merged_speakers = apply_grouping(pyannote_speakers, gemini_grouping)
    
    # Step 3: Measure accuracy
    # Map merged speakers to ground truth (P25, P26, P27, P28)
    accuracy = calculate_speaker_accuracy(merged_speakers, ground_truth)
    
    print(f"Before: {len(pyannote_speakers)} speakers, {baseline_accuracy}% accuracy")
    print(f"After:  {len(merged_speakers)} speakers, {accuracy}% accuracy")
    
    # SUCCESS if:
    # - Speaker count: 6 → 4
    # - Accuracy: 17% → 60%+
```

**Validation criteria:**
- ✅ Correct speaker count (within 1 of ground truth)
- ✅ Accuracy improvement (>2x baseline)
- ✅ Consistent across multiple sessions

---

## Cost-Benefit Analysis

### Clustering Threshold Tuning (FREE)
- Cost: $0
- Time: 15 minutes
- Expected improvement: 6 → 5 speakers, 17% → 30% accuracy
- **Try this FIRST**

### Gemini Single-Pass Merger (CHEAP)
- Cost: $0.01-0.05 per file
- Time: 2-3 hours to implement
- Expected improvement: 6 → 4 speakers, 17% → 60% accuracy
- **Try if threshold tuning insufficient**

### Gemini Pairwise Validation (EXPENSIVE)
- Cost: $0.15-0.75 per file
- Time: 4-5 hours to implement
- Expected improvement: Same as single-pass but more robust
- **Only if single-pass unreliable**

### Hybrid Embedding + Gemini (OPTIMAL)
- Cost: $0.00-0.05 per file (Gemini only when needed)
- Time: 6-8 hours to implement
- Expected improvement: Best accuracy, lowest cost
- **Production solution if we commit**

---

## Decision Tree

```
START: pyannote detects 6 speakers, 17% accuracy

↓
Try clustering threshold tuning (15 min, $0)
├─ Works (4-5 speakers, 40%+ accuracy) → DONE ✓
└─ Doesn't work (still 6 speakers, <30% accuracy) → Continue

↓
Implement Gemini Single-Pass Merger (3 hours, $0.05/file)
├─ Works (4 speakers, 60%+ accuracy) → DONE ✓
└─ Unreliable (varies widely) → Continue

↓
Upgrade to Hybrid Embedding + Gemini (8 hours, $0.02/file)
└─ Production-ready solution ✓
```

---

## Recommended Approach

### Phase 1: Quick Validation (TODAY)
1. ✅ Tune clustering threshold (0.7 → 1.0 → 1.5)
2. ✅ Test on CHiME-6 S09
3. ✅ Measure improvement

**If Phase 1 insufficient:**

### Phase 2: Gemini Proof of Concept (TOMORROW)
1. Extract speaker samples (implement quality extraction)
2. Build Gemini single-pass merger
3. Test on CHiME-6 (multiple sessions)
4. Validate accuracy improvement

**If Phase 2 successful:**

### Phase 3: Production Implementation (NEXT WEEK)
1. Implement hybrid embedding + Gemini approach
2. Add to Modal pipeline
3. Validate on all 8 datasets
4. Document in academic paper

---

## Open Questions

1. **Sample quality:** How many samples per speaker? One 10-sec or multiple 5-sec?
2. **Overlapping speech:** How to handle far-field audio with constant overlap?
3. **Gemini consistency:** Does it give same grouping on re-run?
4. **Embedding threshold:** What cosine similarity = "same speaker"?
5. **Edge cases:** What if Gemini says 3 speakers when we detect 6?

---

## Next Action

**IMMEDIATE:** Test clustering threshold tuning (15 min, free, might solve everything)

**Command to run:**
```bash
# Modify Modal code to add clustering.threshold parameter
# Test values: 0.7 (default), 1.0, 1.2, 1.5
# Measure speaker count and accuracy for each
```

If that doesn't solve it, proceed to Gemini approach.

---

**STATUS: READY TO IMPLEMENT - Starting with simplest solution**

