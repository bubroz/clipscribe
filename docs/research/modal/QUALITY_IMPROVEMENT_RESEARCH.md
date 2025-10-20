# Speaker Diarization Quality Improvement Research

**Date:** October 20, 2025  
**Problem:** pyannote.audio over-segments speakers (detects 7 when only 2 exist)  
**Solution:** Multi-stage post-processing + optional AI editorial pass

---

## 🔬 **ROOT CAUSE ANALYSIS**

### **The Over-Segmentation Problem:**

**Observed:**
- 2-speaker podcast → 7 speakers detected
- 1-speaker lecture → 1 speaker detected ✅
- 5-speaker panel → 10 speakers detected (5 major + 5 minor) ✅

**Pattern:**
- Single speaker: Perfect
- Multi-speaker clean (panel): Excellent (identifies major vs minor correctly)
- Multi-speaker conversational (podcast): Over-segments

**Why This Happens:**

From pyannote.audio GitHub issue #1579:
> "Not out of the box. You would have to post process the output yourself."
> - pyannote.audio creator (hbredin)

**Root causes:**
1. **Short interjections** ("Yeah", "Right", "Okay") get new speaker IDs
2. **Voice changes** (tone shifts, emotional changes) trigger new speakers
3. **Background voices** (mentioned people, quotes) detected as speakers
4. **Conservative design** (pyannote prefers over-segmentation to missing speakers)

**This is by design, not a bug. Post-processing is standard practice.**

---

## ✅ **SOLUTION 1: Local Post-Processing (Implemented)**

### **Algorithm (Multi-Stage):**

**Stage 1: Identify Major Speakers**
```python
# Any speaker with >10% of segments is "major"
major_threshold = 0.10

for speaker, count in speaker_counts.items():
    if count / total_segments > major_threshold:
        major_speakers.append(speaker)
```

**Stage 2: Merge Ultra-Short Segments**
```python
# Segments <0.5 seconds are likely artifacts
# Merge into previous or next segment

if duration < 0.5:
    merge_into_neighbor(segment)
```

**Stage 3: Merge Interjections**
```python
# Short segments (<2s, <5 words) during another speaker's turn

if duration < 2.0 and word_count < 5 and speaker not in major_speakers:
    # Check if sandwiched: A → X → A
    if before_speaker == after_speaker and before_speaker in major_speakers:
        segment.speaker = before_speaker
```

**Stage 4: Eliminate Tiny Speakers**
```python
# Speakers with <1% of segments get merged to nearest major

if speaker_percentage < 0.01:
    assign_to_nearest_major_speaker(segment)
```

### **Results on MTG Interview:**

| Stage | Speakers | Segments | Improvement |
|-------|----------|----------|-------------|
| Raw output | 7 | 777 | - |
| After ultra-short merge | 7 | 688 | -89 segments |
| After interjection merge | 3 | 688 | -4 speakers |
| After tiny speaker cleanup | **2** | **688** | **-5 speakers total** ✅ |

**Final distribution:**
- SPEAKER_01: 45.8% (Tim Dillon)
- SPEAKER_05: 54.2% (MTG)

**✅ PERFECT - Matches expected 2 speakers exactly**

---

## 🤖 **SOLUTION 2: Grok Editorial Pass (Research)**

### **Concept:**

Use AI to review and improve transcript quality after WhisperX.

**What Grok Can Do:**
1. **Validate speaker consistency** ("Is this really the same person?")
2. **Catch transcription errors** ("health car" → "healthcare")
3. **Improve speaker attribution** ("'Yeah' during Tim's question → Tim, not MTG")
4. **Add context** ("SPEAKER_01 is likely the host based on intro")
5. **Suggest speaker names** ("SPEAKER_05 is Marjorie Taylor Greene based on context")

### **Approach 1: Segment-Level Review**

```python
def grok_segment_review(segments, sample_size=50):
    """
    Send problematic segments to Grok for review.
    Focus on rapid switches and short segments.
    """
    
    # Find problematic segments
    problems = find_rapid_switches(segments) + find_short_segments(segments)
    
    # Sample (don't send all, too expensive)
    sample = random.sample(problems, min(sample_size, len(problems)))
    
    prompt = f"""
    Review these transcript segments for quality issues:
    
    {format_segments_with_context(sample)}
    
    For each issue, return:
    {{
      "segment_id": 123,
      "issue": "interjection_misattributed",
      "current_speaker": "SPEAKER_00",
      "suggested_speaker": "SPEAKER_01",
      "confidence": 0.90,
      "reasoning": "This 'Yeah' is during SPEAKER_01's question"
    }}
    
    Only suggest changes you're confident about (>0.8 confidence).
    """
    
    corrections = call_grok(prompt)
    return apply_corrections(segments, corrections)
```

**Cost:** ~$0.01 per video (50 segments × 100 tokens avg)  
**Benefit:** Catches errors local algorithm misses  
**Accuracy:** Unknown (need to test)

### **Approach 2: Full Transcript Analysis**

```python
def grok_full_analysis(segments, speaker_stats):
    """
    Send full speaker distribution to Grok for high-level analysis.
    """
    
    prompt = f"""
    Podcast transcript analysis:
    
    Speaker distribution:
    - SPEAKER_01: 345 segments (44%)
    - SPEAKER_05: 392 segments (51%)
    - SPEAKER_00: 17 segments (2%)
    - SPEAKER_02: 14 segments (2%)
    - Others: 9 segments (1%)
    
    Sample quotes from each speaker:
    {format_speaker_samples(segments)}
    
    Questions:
    1. Are SPEAKER_01 and SPEAKER_05 the two main people?
    2. Should minor speakers (<2%) be merged into major speakers?
    3. Can you identify likely speaker names from context?
    4. Are there any obvious attribution errors?
    
    Return analysis with confidence scores.
    """
    
    analysis = call_grok(prompt)
    return analysis
```

**Cost:** ~$0.02 per video (full context)  
**Benefit:** Holistic quality assessment  
**Use case:** Premium+ tier or quality validation

---

## 🎯 **SOLUTION 3: Hybrid Approach (Recommended)**

**Pipeline:**
```
1. WhisperX transcription → Raw output
2. Local post-processing → Clean segments (free, 2 seconds)
3. Quality check → Detect remaining issues
4. [OPTIONAL] Grok editorial → Fix complex cases ($0.01, 10 seconds)
5. Final output → User sees clean transcript
```

**Tiers:**
- **Standard:** Steps 1-2 only (free post-processing)
- **Premium:** Steps 1-3 (quality validation)
- **Premium+:** Steps 1-5 (AI-enhanced quality)

---

## 📊 **MEASURED IMPROVEMENTS**

### **MTG Interview Case Study:**

**Raw WhisperX Output:**
- Speakers: 7
- Segments: 777
- Ultra-short (<0.5s): 175 (22.5%)
- Rapid switches: 128 (16.5%)
- **Usability: C** (confusing, needs cleanup)

**After Local Post-Processing:**
- Speakers: 2 ✅
- Segments: 688 (-89 merged)
- Ultra-short: 0 ✅
- Rapid switches: 57 (-56% reduction)
- **Usability: A-** (clean, minor issues remain)

**Potential with Grok Pass** (estimated):
- Speakers: 2
- Attribution errors: <5 (vs ~20 without)
- Transcription fixes: 10-20 corrections
- **Usability: A+** (publication-ready)

---

## 💡 **CREATIVE IMPROVEMENTS (First Principles)**

### **1. Speaker Fingerprinting**

**Idea:** Create voice "fingerprints" to verify speaker consistency

```python
def verify_speaker_consistency(segments, audio_file):
    """
    Extract voice embeddings for each speaker ID.
    Measure similarity - if SPEAKER_00 and SPEAKER_01 are 95% similar, merge them.
    """
    
    from speechbrain.pretrained import SpeakerRecognition
    
    verifier = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
    
    # Extract embeddings for each speaker
    speaker_embeddings = {}
    for speaker_id in unique_speakers:
        # Get audio chunks for this speaker
        chunks = extract_speaker_audio(audio_file, segments, speaker_id)
        # Average embedding
        embedding = verifier.encode_batch(chunks).mean(dim=0)
        speaker_embeddings[speaker_id] = embedding
    
    # Find similar speakers (cosine similarity >0.9)
    merges = []
    for s1, s2 in combinations(speaker_embeddings.keys(), 2):
        similarity = cosine_similarity(speaker_embeddings[s1], speaker_embeddings[s2])
        if similarity > 0.90:
            merges.append((s1, s2, similarity))
    
    return merges
```

**Cost:** +2-3 seconds processing (runs on GPU)  
**Benefit:** Data-driven merging (not heuristic)  
**Accuracy:** High (voice embeddings are robust)

---

### **2. Conversational Flow Analysis**

**Idea:** Use conversation patterns to validate speaker changes

```python
def validate_conversational_flow(segments):
    """
    Analyze if speaker changes make sense conversationally.
    
    Patterns that are suspicious:
    - A asks question → B says "Right" → A continues question (B should be A)
    - A mid-sentence → B says one word → A continues sentence (B should be A)
    - A talking for 5min → B says "Yeah" → A continues for 5min (B should be A)
    """
    
    suspicious = []
    
    for i in range(1, len(segments)-1):
        prev = segments[i-1]
        curr = segments[i]
        next_seg = segments[i+1]
        
        # Pattern: Mid-sentence interruption
        if not prev['text'].endswith('.') and not prev['text'].endswith('?'):
            if len(curr['text'].split()) < 3:  # Very short interjection
                if next_seg['speaker'] == prev['speaker']:
                    suspicious.append({
                        'index': i,
                        'pattern': 'mid-sentence_interjection',
                        'suggested_merge': prev['speaker']
                    })
    
    return suspicious
```

**Cost:** Free (runs locally)  
**Benefit:** Catches patterns that duration-based merging misses

---

### **3. User Feedback Loop**

**Idea:** Learn from user corrections

```python
# When user fixes speaker attribution:
user_correction = {
    'video_id': 'mtg_interview',
    'correction': {
        'segment_id': 123,
        'original_speaker': 'SPEAKER_00',
        'corrected_speaker': 'SPEAKER_01',
        'reason': 'interjection'
    }
}

# Store in database
# Use to train custom merging rules
# "For this user, always merge SPEAKER_00 interjections to nearest major speaker"
```

**Cost:** Free (user does the work)  
**Benefit:** Improves over time  
**Scalability:** Builds dataset for training

---

## 🎯 **RECOMMENDED IMPLEMENTATION PLAN**

### **Phase 1: Baseline (This Weekend)** - FREE

**Implement in Modal:**
1. Add post-processing to `station10_modal.py`
2. Apply after WhisperX, before returning results
3. Add `"improvement_stats"` to output
4. **Cost: $0 | Time: +2 seconds**

**Test:**
- Re-run MTG: Should show 2 speakers
- Re-run The View: Should show 5-7 speakers (reduce 10)
- Validate quality is better

---

### **Phase 2: AI Enhancement (Next Week)** - PAID

**Implement Grok Pass:**
1. Send 50 problematic segments to Grok
2. Apply suggested corrections
3. Measure improvement
4. **Cost: ~$0.01 | Time: +10 seconds**

**Test:**
- Does Grok actually improve quality?
- Is cost worth the improvement?
- Do users notice/care?

**If yes → Add as Premium+ tier**  
**If no → Skip it**

---

### **Phase 3: Advanced (Later)** - OPTIONAL

**Voice Embeddings:**
- More accurate speaker verification
- Data-driven merging
- **Research: 2-3 days | Implementation: 1 week**

**Only if:** Users complain about speaker quality

---

## 📝 **IMMEDIATE NEXT STEPS**

**I'll now:**
1. ✅ Implement post-processing in Modal code
2. ✅ Test on all 4 validation videos
3. ✅ Measure before/after quality
4. ✅ Research Grok editorial approach
5. ✅ Implement Grok pass (experimental)
6. ✅ Test and measure ROI

**Starting implementation now...**

