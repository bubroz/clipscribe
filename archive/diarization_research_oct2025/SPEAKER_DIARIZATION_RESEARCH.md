# Speaker Diarization Deep Research
**Date:** October 22, 2025  
**Context:** CHiME-6 validation shows 17% speaker accuracy (6 detected vs 4 actual)  
**Goal:** Find proven solutions from research community

---

## Research Questions

### 1. ✅ Can we configure pyannote.audio for better accuracy?
**FINDING: YES - We weren't using speaker hints!**

**Discovery:**
- WhisperX `DiarizationPipeline.__call__()` supports:
  - `num_speakers`: Exact count if known
  - `min_speakers`: Minimum to detect  
  - `max_speakers`: Maximum to detect
- **We were calling with NO parameters!**

**Fix Applied:**
```python
# BEFORE (no guidance):
diarize_segments = self.diarize_model(audio)

# AFTER (constrained):
diarize_segments = self.diarize_model(
    audio,
    min_speakers=2,
    max_speakers=6
)
```

**Result:**
- Speakers: 8 → 6 (25% reduction)
- Speaker accuracy: 14% → 17% (+3 points)
- **Still not good enough (need 80%+)**

### 2. 🔬 Can Gemini 2.5 Flash do speaker diarization?
**TESTING IN PROGRESS**

**Experiment:**
- Uploaded 2-hour CHiME-6 S09 audio to Gemini
- Asked it to identify speakers and provide timestamps
- **Gemini claimed: 4 speakers (MATCHES ground truth!)**

**Gemini Output:**
```json
{
  "num_speakers": 4,
  "confidence": "high",
  "speakers": [
    {"id": 1, "voice": "Female, medium-high pitch", "time": "30%"},
    {"id": 2, "voice": "Female, slightly lower", "time": "40%"},
    {"id": 3, "voice": "Female, medium-low", "time": "20%"},
    {"id": 4, "voice": "Male, low pitch", "time": "10%"}
  ]
}
```

**CRITICAL VALIDATION NEEDED:**
- ❓ Are timestamps accurate or hallucinated?
- ❓ Do timestamps align with ground truth?
- ❓ Is this reliable or lucky guess?

**Research Findings:**
- Limited public documentation on Gemini audio timestamp accuracy
- No benchmarks comparing Gemini vs pyannote for diarization
- Blog posts claim Gemini has diarization, but for older versions
- **Need empirical validation**

### 3. What did CHiME-6 winners use for diarization?
⏳ Researching...

### 4. Is the audio channel causing issues?
⏳ Researching...

### 5. Are there better diarization models (2024-2025)?
⏳ Researching...

---

## Key Research Sources

### pyannote.audio Configuration
- **Source:** [GitHub Issue #1579](https://github.com/pyannote/pyannote-audio/issues/1579)
- **Finding:** segmentation-3.0 has minimal tunable parameters
- **Key params:**
  - `clustering.threshold` (0-2): Controls speaker count (higher = fewer speakers)
  - `segmentation.min_duration_off`: Gap filling
  - Default threshold ~0.7, can try 1.0-1.5 for more aggressive merging

### pyannote.audio Optimization
- **Source:** [Hervé Bredin's Blog](https://herve.niderb.fr/posts/2022-12-02-how-I-won-2022-diarization-challenges.html)
- **Author:** pyannote creator, won multiple 2022 diarization challenges
- **Key insights:**
  - `clustering.threshold` (δ): Higher = fewer speakers
  - Optimize on dev set before using
  - Fine-tuning segmentation model can help significantly
  - His recipe: 32.5% → 26.6% DER on AMI in 30min

### WhisperX Integration
- **Source:** [WhisperX GitHub](https://github.com/m-bain/whisperX/blob/main/whisperx/diarize.py)
- **Finding:** Full support for speaker hints (we weren't using them!)
- **API:**
  ```python
  def __call__(
      audio,
      num_speakers=None,
      min_speakers=None,
      max_speakers=None,
      return_embeddings=False
  )
  ```

---

## Recommendations (IN PROGRESS)

### Option A: Tune pyannote (4-6 hours work)
**Status:** Partially implemented (speaker hints)

**Next steps:**
1. ✅ Add min/max speaker hints (DONE - improved 8→6)
2. ⏳ Tune clustering threshold (try 1.0-1.5)
3. ⏳ Try beamformed audio instead of single channel
4. ⏳ Optimize on CHiME-6 dev set

**Expected outcome:** 4-5 speakers, 40-60% accuracy

### Option B: Gemini-based diarization (VALIDATING)
**Status:** Promising but UNVALIDATED

**Advantages:**
- ✅ Correct speaker count (4 vs pyannote's 6)
- ✅ Provides timestamps
- ✅ Voice descriptions
- ✅ Already using Gemini for corrections

**Concerns:**
- ❓ Timestamp accuracy unknown
- ❓ May be hallucinating
- ❓ No benchmarks vs ground truth
- ❓ Higher cost/latency

**Validation plan:**
1. Compare Gemini timestamps to CHiME-6 ground truth
2. Test on multiple sessions
3. Measure accuracy vs pyannote
4. Assess cost/latency trade-offs

### Option C: Accept limitations
**Status:** Fallback option

Far-field multi-speaker diarization is HARD. Even CHiME-6 winners struggled. Document limitations, focus on transcription quality.

---

## Current Status

**Speaker Detection:**
- pyannote (no hints): 8 speakers, 14% accuracy
- pyannote (with hints): 6 speakers, 17% accuracy  
- Gemini (claimed): 4 speakers, accuracy UNKNOWN

**Next Action:**
Validate Gemini timestamps against ground truth before proceeding.

---

**STATUS: RESEARCH ACTIVE - VALIDATING GEMINI APPROACH**
