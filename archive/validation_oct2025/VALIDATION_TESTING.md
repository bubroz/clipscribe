# Modal GPU Validation Testing Guide

**Date:** October 19, 2025  
**Status:** Core infrastructure validated (1-speaker), multi-speaker/long video pending

---

## ✅ **Completed Tests**

### Test 1: Medical Video (16min, 1 speaker)
- **Result:** ✅ SUCCESS
- **Processing:** 1.4 min (11.6x realtime)
- **Cost:** $0.0251
- **Speakers:** 1 detected correctly
- **Margin:** 92.3%
- **Status:** PRODUCTION READY

---

## 🧪 **Pending Validation Tests**

### Test 2: The View (36min, 5+ speakers) - CRITICAL
**Purpose:** Validate multi-speaker diarization quality

**Video:** `gs://prismatic-iris-429006-g6-clipscribe/test/the_view_oct14.mp3`

**Run Command:**
```bash
cd /Users/base/Projects/clipscribe
poetry run python3 deploy/test_multi_speaker.py
```

**Expected Results:**
- Processing: ~3-4 minutes (10x realtime)
- Cost: ~$0.06-0.08
- **Speakers: 5+ detected**
- Quality: Accurate speaker boundaries

**Success Criteria:**
- ✅ Detects 3+ speakers (minimum)
- ✅ Processing <10 minutes
- ✅ Cost <$0.15
- ✅ No crashes or errors

**Validation:** User must review transcript to confirm speaker labels are accurate

---

### Test 3: MTG Interview (71min, 2 speakers)
**Purpose:** Validate longer duration + standard 2-speaker case

**Video:** `gs://prismatic-iris-429006-g6-clipscribe/test/mtg_interview.mp3`

**Run Command:**
```bash
poetry run modal run deploy/station10_modal.py::test_gcs_transcription \
  --gcs-path gs://prismatic-iris-429006-g6-clipscribe/test/mtg_interview.mp3
```

**Or use Python:**
```python
from modal import Function

transcribe = Function.lookup("station10-transcription", "Station10Transcriber.transcribe_from_gcs")
result = transcribe.remote(
    "gs://prismatic-iris-429006-g6-clipscribe/test/mtg_interview.mp3",
    "gs://prismatic-iris-429006-g6-clipscribe/test/modal_results/mtg/"
)
print(f"Speakers: {result['speakers']}, Cost: ${result['cost']:.4f}")
```

**Expected Results:**
- Processing: ~6-7 minutes (10x realtime)
- Cost: ~$0.12-0.15
- **Speakers: 2 detected**
- Duration validated: 71 minutes

**Success Criteria:**
- ✅ Completes without timeout
- ✅ Detects 2 speakers correctly
- ✅ Processing <15 minutes
- ✅ Cost <$0.20

---

### Test 4: API Endpoint (HTTP POST)
**Purpose:** Validate production API works

**Endpoint:** `https://zforristall--station10-transcription-api-transcribe.modal.run`

**Test with curl:**
```bash
curl -X POST \
  https://zforristall--station10-transcription-api-transcribe.modal.run/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://storage.googleapis.com/prismatic-iris-429006-g6-clipscribe/public/medical.mp3",
    "output_path": "gs://prismatic-iris-429006-g6-clipscribe/test/api_test/"
  }'
```

**Test with Python:**
```python
import httpx

response = httpx.post(
    "https://zforristall--station10-transcription-api-transcribe.modal.run/transcribe",
    json={
        "audio_url": "https://storage.googleapis.com/prismatic-iris-429006-g6-clipscribe/public/medical.mp3",
        "output_path": "gs://prismatic-iris-429006-g6-clipscribe/test/api_test/"
    },
    timeout=600  # 10 minutes
)

print(response.json())
```

**Expected Results:**
- HTTP 200 response
- JSON with transcript, speakers, cost
- Results uploaded to GCS

**Success Criteria:**
- ✅ API responds (not 500 error)
- ✅ Returns valid JSON
- ✅ Processing completes
- ✅ Results in GCS

---

## 📊 **Validation Summary Template**

After running all tests, fill this out:

### Test Results:
| Test | Duration | Speakers | Processing | Cost | Status |
|------|----------|----------|------------|------|--------|
| Medical (1 speaker) | 16min | 1 | 1.4min | $0.025 | ✅ PASS |
| The View (5+ speakers) | 36min | ? | ?min | $? | ⏳ PENDING |
| MTG Interview (2 speakers) | 71min | ? | ?min | $? | ⏳ PENDING |
| API Endpoint Test | 16min | 1 | ?min | $? | ⏳ PENDING |

### Overall Assessment:
- [ ] Multi-speaker diarization works well
- [ ] Long videos process without issues
- [ ] API endpoint is production-ready
- [ ] Costs match projections (<$0.05 per 30min)
- [ ] Ready for integration with Station10

### Blockers Found:
_(List any issues discovered during testing)_

### Next Steps:
_(Based on test results)_

---

## 🎯 **After Validation**

**If all tests pass:**
1. Update TECHNICAL_DEBT.md (mark multi-speaker as validated)
2. Update README.md (add multi-speaker checkmark)
3. Document actual performance in MODAL_VALIDATION_RESULTS.md
4. Proceed with Station10 API integration

**If any test fails:**
1. Document failure mode
2. Debug/fix issue
3. Re-test
4. Update documentation with limitations

