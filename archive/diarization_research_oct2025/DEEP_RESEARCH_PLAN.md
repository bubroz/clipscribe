# Deep Research Plan: Speaker Diarization
**Date:** October 22, 2025  
**Status:** Parallel track while testing thresholds

## Current State

**Simple threshold tuning showing:**
- Binary collapse behavior (6→2 speakers between 0.7-0.95)
- Accuracy doubled (17%→37%) but speaker count wrong
- Need binary search to find sweet spot

**While testing thresholds, research these in parallel:**

---

## Research Track 1: Understanding the Binary Collapse

**Question:** Why does threshold jump from 6→2 speakers with no 4-speaker middle ground?

**Hypotheses:**
1. **Embedding space has 2 major clusters** (2 actual speaker groups)
2. **Threshold crosses critical boundary** where all minor speakers merge
3. **Audio quality issue** - 2 speakers dominate, others are noise

**Investigation:**
1. Extract pyannote's raw speaker embeddings
2. Visualize with t-SNE/UMAP
3. Calculate silhouette scores for k=2,3,4,5,6 clusters
4. See if there ARE 4 natural clusters in embedding space

**Code to write:**
```python
# scripts/analyze_speaker_embeddings.py
# Extract embeddings from pyannote
# Visualize clustering structure
# Determine optimal k from embeddings
```

---

## Research Track 2: Advanced Gemini Audio Analysis

**Experiments to run:**

### Experiment 1: Pairwise Speaker Comparison
```python
# Give Gemini two 10-sec clips
# Ask: "Are these the same person? Confidence 0-100%"
# Build similarity matrix
# Apply threshold-free hierarchical clustering
```

**Why this matters:** Bypasses pyannote's threshold entirely, uses Gemini's voice understanding.

### Experiment 2: Voice Fingerprinting
```python
# Extract 5 samples per detected speaker (from pyannote's 6)
# Ask Gemini to describe each voice uniquely
# Use descriptions to group similar voices
# Map back to original segments
```

**Why this matters:** Gemini might distinguish voices pyannote can't.

### Experiment 3: Transcript-Aware Grouping
```python
# Give Gemini: transcript + voice samples
# Ask: "Using both voice AND conversation context, group speakers"
# Leverage: "Same person wouldn't argue with themselves"
```

**Why this matters:** Multi-modal might beat audio-only.

---

## Research Track 3: CHiME-6 Audio Source Analysis

**Current:** Using `S09_U04.CH1.wav` (single channel, array mic)

**Available:**
- `S09_P25.wav` - Close-mic recording of speaker P25
- `S09_U04.CH1-4.wav` - 4 channels from array
- Beamformed audio (if we process it)

**Tests:**
1. Run same pipeline on close-mic audio
2. Test each of 4 channels separately
3. Research if beamforming helps diarization
4. Check what CHiME-6 winners used

**Why this matters:** We might be using wrong audio source.

---

## Research Track 4: Literature Deep Dive

**Papers to read:**

1. **CHiME-6 Challenge Winner Papers**
   - What system achieved best DER?
   - What audio preprocessing?
   - What diarization approach?

2. **Recent Diarization Papers (2024-2025)**
   - pyannote 3.0 vs 3.1 improvements
   - End-to-end neural diarization (EEND)
   - Self-supervised learning approaches

3. **Gemini Audio Capabilities**
   - Official Gemini audio documentation
   - Community experiments with speaker analysis
   - Known limitations and workarounds

**Output:** Summary document with actionable insights.

---

## Research Track 5: Alternative Approaches

### Approach A: Use pyannote Embeddings Directly
```python
# Instead of pyannote's clustering, use its embeddings
# Apply our own clustering (DBSCAN, spectral, etc.)
# Tune clustering parameters for our use case
# Bypass threshold parameter entirely
```

### Approach B: Hybrid Ensemble
```python
# Run multiple diarization approaches:
# 1. pyannote with threshold 0.8
# 2. pyannote with threshold 0.9  
# 3. Gemini-based grouping
# Vote/consensus mechanism
```

### Approach C: Fine-tune pyannote Model
```python
# Use CHiME-6 training data
# Fine-tune pyannote's segmentation model
# Optimize for far-field 4-speaker scenarios
# (Most expensive, multi-day effort)
```

---

## Execution Priority

**IMMEDIATE (Today):**
1. ✅ Binary search thresholds (0.80, 0.85, 0.90)
2. ⏳ Analyze speaker embeddings (understand binary collapse)

**SHORT-TERM (This week):**
1. Gemini pairwise comparison experiment
2. CHiME-6 audio source testing
3. Literature review (winner approaches)

**MEDIUM-TERM (If needed):**
1. Hybrid ensemble approach
2. Custom embedding clustering
3. Gemini voice fingerprinting

**LONG-TERM (If all else fails):**
1. Fine-tune pyannote model
2. Try alternative diarization models
3. Accept limitations, document findings

---

## Success Metrics

**Minimum Viable:**
- 4 speakers (±1)
- 50% speaker accuracy
- Consistent across sessions

**Target:**
- 4 speakers (exact)
- 70% speaker accuracy
- Works on AnnoMI too

**Stretch:**
- 4 speakers (exact)
- 80%+ speaker accuracy
- Publication-grade results

---

## Next Session Plan

**Run in external terminal to avoid timeouts:**

1. Test threshold 0.80 → record results
2. Test threshold 0.85 → record results
3. Based on results, either:
   - ✅ Found sweet spot (4 speakers) → validate broadly
   - ❌ Still binary (2 or 6) → proceed to Gemini experiments
4. Update research plan with findings

---

**STATUS: BINARY SEARCH IN PROGRESS**
**PARALLEL: DEEP RESEARCH READY TO LAUNCH**

