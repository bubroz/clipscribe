# Comprehensive Entity Extraction Validation Plan

**Date:** October 28, 2025  
**Goal:** Validate entity extraction across diverse content before building Week 5-8 features

---

## Current Status

✅ **Working:**
- Entity extraction pipeline functional
- Grok API integration working
- Processing: $0.08 per video, 5 min average

❌ **Issues Found:**
- Wrong "Medical" video (actually API tutorial)
- Only CONCEPT entities extracted (need PERSON, ORG, LOCATION)
- Only 2 videos tested
- No multi-speaker panels tested

---

## Validation Strategy

### Phase 1: Critical Gaps (2-3 videos, ~$0.20, 15 min)

Test what we MUST validate:

**1. Multi-Speaker Panel (5+ speakers)**
- **Video:** The View Oct 14
- **URL:** https://www.youtube.com/watch?v=U3w93r5QRb8
- **Duration:** 36 min
- **Why:** Critical for speaker diarization + entity attribution
- **Expected:** PERSON entities (panelists), ORG entities

**2. Tech/Politics Panel (4-5 speakers)**
- **Video:** All-In Podcast  
- **URL:** https://www.youtube.com/watch?v=IbnrclsPGPQ
- **Duration:** 88 min
- **Why:** Panel discussion, tech/politics overlap
- **Expected:** PERSON (panelists), ORG (companies), CONCEPT (tech topics)

**3. Political Interview (2 speakers)**
- **Video:** MTG Interview
- **URL:** https://www.youtube.com/watch?v=wlONOh_iUXY
- **Duration:** 71 min
- **Why:** Political entities, PERSON extraction
- **Expected:** PERSON (MTG, interviewer), ORG (political orgs), LOCATION

**Total:** ~195 min, $0.24, ~20 minutes processing

---

## Success Criteria

For each video, validate:

1. **Entity Type Diversity**
   - ✓ CONCEPT (terms, topics)
   - ✓ PERSON (named people)
   - ✓ ORG (organizations)
   - ✓ LOCATION (places, cities)

2. **Entity Count**
   - ✓ Minimum 10 entities per video
   - ✓ Entity-to-segment ratio > 0.02

3. **Relationship Quality**
   - ✓ Relationships link real entities
   - ✓ No obvious false relationships
   - ✓ At least 1 relationship per entity

4. **Speaker-Entity Attribution**
   - ✓ Entities linked to speakers who mentioned them
   - ✓ Speaker labels match ground truth

---

## Implementation

### Script: Comprehensive Validation

```bash
# Run validation on all 3 videos
poetry run python scripts/validation/comprehensive_validation.py

# Expected output:
# - Processing 3 videos
# - Extracting entities for each
# - Generating validation report
# - Identifying gaps
```

### Validation Report Structure

```json
{
  "total_videos": 3,
  "total_cost": 0.24,
  "total_time": "~20 minutes",
  "videos": [
    {
      "name": "The View Oct 14",
      "duration": 36,
      "speakers": 5,
      "entities": {
        "total": 25,
        "by_type": {
          "PERSON": 8,
          "ORG": 5,
          "CONCEPT": 10,
          "LOCATION": 2
        }
      },
      "relationships": 18,
      "validation": {
        "entity_diversity": "✅ PASS",
        "entity_count": "✅ PASS",
        "speaker_attribution": "✅ PASS"
      }
    }
  ],
  "overall_assessment": "READY" | "NEEDS_FIXES"
}
```

---

## Next Steps

1. **Create comprehensive validation script**
2. **Run validation (15-20 min)**
3. **Generate report**
4. **If PASS:** Proceed to Week 5-8 features
5. **If FAIL:** Fix issues, re-test

---

## Week 5-8 Features (Pending Validation)

Once validation passes:

1. **Auto-clip generation** - Create clips from interesting moments
2. **Entity search** - Search videos by entities mentioned
3. **Batch processing** - Process multiple videos efficiently
4. **Clip recommendations** - Suggest relevant clips based on entities

---

## Timeline

- **Now:** Create validation script (5 min)
- **+5 min:** Download 3 test videos (if not already)
- **+20 min:** Run validation
- **+5 min:** Review results
- **+10 min:** Fix any issues OR proceed to Week 5-8
- **Total:** ~45 minutes to either validated system or fixes

---

## Cost Estimate

- Validation: ~$0.24 (3 videos)
- Week 5-8 development: ~10 hours dev time
- Week 5-8 testing: ~$2.00 (20 videos)

**Total investment:** ~$3 to fully validated system with Week 5-8 features

