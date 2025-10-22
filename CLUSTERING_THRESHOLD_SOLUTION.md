# Clustering Threshold Solution
**Date:** October 22, 2025  
**Problem:** pyannote over-segments (6 speakers detected vs 4 actual)  
**Solution:** Access underlying pyannote Pipeline and set clustering.threshold

---

## How It Works

**WhisperX Architecture:**
```
DiarizationPipeline (WhisperX wrapper)
  └── self.model = Pipeline (pyannote.audio)
        └── instantiate({params}) ← WE CAN CALL THIS!
```

**Key Discovery:**
- WhisperX's `DiarizationPipeline` stores pyannote's `Pipeline` as `self.model`
- pyannote's `Pipeline` has an `instantiate()` method
- We can call `instantiate()` to set clustering parameters!

---

## Implementation

### In Modal (station10_modal.py)

```python
# Current code (line 172):
self.diarize_model = DiarizationPipeline(
    use_auth_token=hf_token,
    device=self.device
)

# ADD THIS IMMEDIATELY AFTER:
# Configure clustering threshold for better speaker merging
self.diarize_model.model.instantiate({
    'clustering': {
        'threshold': 1.2,      # Higher = fewer speakers (default ~0.7)
        'method': 'centroid'   # Keep default clustering method
    }
})
print(f"✓ Diarization clustering threshold set to 1.2")
```

---

## Testing Strategy

### Phase 1: Find Optimal Threshold
Test different threshold values on CHiME-6 S09:

```python
thresholds_to_test = [0.7, 1.0, 1.2, 1.5, 1.8]

for threshold in thresholds_to_test:
    diarize_model.model.instantiate({
        'clustering': {'threshold': threshold}
    })
    
    # Run diarization
    result = process_audio(...)
    
    # Measure results
    print(f"Threshold {threshold}:")
    print(f"  Speakers detected: {num_speakers}")
    print(f"  Speaker accuracy: {accuracy}%")
```

**Expected results:**
- 0.7 (default): 6 speakers, 17% accuracy
- 1.0: 5 speakers, 30-40% accuracy
- 1.2: 4-5 speakers, 50-60% accuracy  ← TARGET
- 1.5: 3-4 speakers, 40-50% accuracy (too aggressive)
- 1.8: 2-3 speakers, 20-30% accuracy (way too aggressive)

### Phase 2: Validate on Multiple Sessions
Once optimal threshold found, test on:
- CHiME-6 S09 (4 speakers)
- CHiME-6 S02 (4 speakers)
- AnnoMI samples (2-4 speakers)

**Success criteria:**
- Speaker count within ±1 of ground truth
- Speaker accuracy >60%
- Consistent across sessions

---

## Advantages vs Gemini Approach

| Approach | Cost | Time | Accuracy | Complexity |
|---|---|---|---|---|
| Clustering threshold | **$0** | 30 min | Good (60%) | **Low** |
| Gemini merger | $0.05/file | 8 hours | Better (70%?) | High |

**Clustering threshold should be tried FIRST:**
- ✅ Free
- ✅ Fast to implement
- ✅ Low complexity
- ✅ Might solve problem entirely

**Only use Gemini if clustering fails**

---

## Research References

**pyannote.audio documentation:**
- `clustering.threshold` (δ): Controls speaker count
- Range: 0.0 to 2.0
- Higher values = more aggressive merging = fewer speakers
- Default: ~0.715 (optimized for benchmark datasets)

**Hervé Bredin (pyannote creator):**
> "clustering.threshold (δ in the report, between 0 and 2) controls the number of speakers (i.e. a higher value will result in less speakers)."

**Source:** https://herve.niderb.fr/posts/2022-12-02-how-I-won-2022-diarization-challenges.html

---

## Implementation Code

### Complete Fix for station10_modal.py

```python
# Line 172-176 (after creating DiarizationPipeline):
self.diarize_model = DiarizationPipeline(
    use_auth_token=hf_token,
    device=self.device
)

# NEW: Configure clustering threshold
# Research shows default ~0.7 is too conservative for our use case
# Testing range: 1.0-1.5 for better speaker merging
CLUSTERING_THRESHOLD = 1.2  # Tuned for 2-6 speaker meetings

self.diarize_model.model.instantiate({
    'clustering': {
        'threshold': CLUSTERING_THRESHOLD,
        'method': 'centroid'  # Keep default
    }
})
print(f"✓ Diarization model loaded with clustering threshold={CLUSTERING_THRESHOLD}")
```

### Test Script

```python
# scripts/test_clustering_threshold.py

import asyncio
from pathlib import Path
from scripts.validation.chime6_validator import CHiME6Validator

async def test_threshold(threshold: float):
    """Test specific clustering threshold on CHiME-6."""
    
    print(f"\n{'='*80}")
    print(f"TESTING CLUSTERING THRESHOLD: {threshold}")
    print(f"{'='*80}\n")
    
    # Modify Modal deployment to use this threshold
    # (requires redeployment for each threshold test)
    
    # Process S09
    validator = CHiME6Validator(...)
    result = await validator.validate_session("S09")
    
    print(f"\nResults with threshold={threshold}:")
    print(f"  Speakers detected: {result['speakers_detected']}")
    print(f"  Ground truth: {result['ground_truth_speakers']}")
    print(f"  Speaker accuracy: {result['speaker_accuracy']:.1f}%")
    print(f"  WER: {result['wer']:.1f}%")
    
    return result

async def main():
    thresholds = [0.7, 1.0, 1.2, 1.5]
    results = {}
    
    for threshold in thresholds:
        results[threshold] = await test_threshold(threshold)
    
    # Find best threshold
    best_threshold = max(results.items(), key=lambda x: x[1]['speaker_accuracy'])
    print(f"\n{'='*80}")
    print(f"BEST THRESHOLD: {best_threshold[0]}")
    print(f"Speaker accuracy: {best_threshold[1]['speaker_accuracy']:.1f}%")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Next Steps

1. **Implement fix** (5 min)
   - Add `instantiate()` call after DiarizationPipeline creation
   - Set threshold = 1.2 (educated guess)
   - Deploy to Modal

2. **Test on S09** (10 min)
   - Run validation
   - Check speaker count and accuracy
   - Compare to baseline (6 speakers, 17%)

3. **Tune if needed** (15 min)
   - If still over-segmented: try 1.5
   - If under-segmented: try 1.0
   - Find sweet spot

4. **Validate broadly** (30 min)
   - Test on S02
   - Test on AnnoMI
   - Ensure consistent improvement

**Total time: 1 hour**  
**Total cost: $0**

---

## Fallback Plan

**If clustering threshold doesn't get us to >60% accuracy:**
- Proceed to Gemini speaker merger approach
- Use clustering threshold AS BASELINE
- Gemini refines the already-improved results

**This gives us two layers:**
1. Clustering threshold (free, fast) → 4-5 speakers, 40-60% accuracy
2. Gemini merger (cheap, slower) → 4 speakers, 70-80% accuracy

---

**STATUS: READY TO IMPLEMENT - Simplest solution first**

