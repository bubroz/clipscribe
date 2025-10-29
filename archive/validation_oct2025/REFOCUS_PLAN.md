# Refocus Plan: Back to Core Validation
**Date:** October 22, 2025  
**Status:** Stepping back from diarization rabbit hole

---

## What We Learned

### Speaker Diarization Deep Dive (Worth It)
✅ **Improved speaker accuracy 2x** (17% → 37%)  
✅ **Found optimal clustering threshold** (0.80)  
✅ **Validated Gemini limitations** (can't do precise timestamps)  
✅ **Discovered TS-VAD** (winner's approach - completely different paradigm)  
✅ **Confirmed transcription quality is EXCELLENT** (43.5% WER vs 77% baseline)

### Key Insight
**pyannote clustering isn't broken - it's just not the SOTA approach for far-field overlapping speech.**

Winners use TS-VAD (Target-Speaker VAD), which is a fundamentally different architecture that requires:
- Multi-channel processing
- Speaker profiles/embeddings
- Neural network predicting per-speaker activity
- 1-2 weeks to implement properly

---

## The Real Problem

**We got distracted optimizing speaker attribution when:**
1. Our transcription quality is ALREADY GREAT (44% better than baseline)
2. Entity extraction is UNTESTED (core ClipScribe value)
3. Speaker attribution is nice-to-have, not make-or-break
4. CHiME-6 is THE HARDEST dataset (should test easier ones first)

**Cart before horse:** Optimizing advanced features before validating core functionality.

---

## Refocus Strategy

### Phase 1: Document & Archive (30 min)
1. Move diarization research to archive/
2. Document findings in one summary file
3. Lock in threshold 0.80 as "good enough"
4. Clean up root directory

### Phase 2: Return to Validation Roadmap (CORE GOAL)
Focus on what actually matters:

**Week 1-2: AnnoMI (EASIER DATASET)**
- 2-speaker interviews (not 4-speaker far-field)
- Cleaner audio
- Focus on: Transcription WER + Entity extraction quality
- Expected: 70-80% speaker accuracy (vs 37% on CHiME-6)

**Week 3-4: AMI Corpus**
- Meeting scenarios
- Test NXT XML parser
- Validate transcription at scale

**Skip:** Deep diarization optimization on every dataset  
**Focus:** Transcription quality + entity extraction validation

### Phase 3: Measure What Matters
**Primary metrics:**
1. ✅ **WER (Word Error Rate)** - transcription accuracy
2. ✅ **Entity extraction F1** - our actual product feature
3. ✅ **Relationship accuracy** - knowledge graph quality
4. ⚠️ **Speaker accuracy** - nice-to-have, not critical

---

## Acceptance Criteria

### Good Enough Diarization
- ✅ 30-40% speaker accuracy on hard datasets (CHiME-6)
- ✅ 60-80% speaker accuracy on easy datasets (AnnoMI, AMI)
- ✅ Document limitations honestly
- ✅ Note TS-VAD as future improvement

### What Actually Matters  
- 🎯 WER < 50% across all datasets
- 🎯 Entity F1 > 70%
- 🎯 Relationship accuracy > 60%
- 🎯 Consistent across languages (English + Mandarin)

---

## Cleanup Actions

### Files to Archive
```
SPEAKER_DIARIZATION_RESEARCH.md
GEMINI_SPEAKER_MERGER_RESEARCH.md
CLUSTERING_THRESHOLD_SOLUTION.md
THRESHOLD_BINARY_SEARCH.md
CHIME6_WINNER_RESEARCH.md
DEEP_RESEARCH_PLAN.md
COMPETITIVE_ANALYSIS.md
test_gemini_diarization.py
validate_gemini_timestamps.py
NEXT_STEPS_EXTERNAL_TERMINAL.sh
RUN_THIS_IN_EXTERNAL_TERMINAL.txt
```

**Move to:** `archive/diarization_research_oct2025/`

### Files to Keep (Summary)
Create: `DIARIZATION_FINDINGS_SUMMARY.md`
- What we learned
- Final configuration (threshold 0.80)
- Limitations and future improvements
- Reference for paper

---

## Back on Track: Validation Roadmap

### Immediate Next Steps

**This Week:**
1. ✅ Clean up diarization research files
2. ✅ Test AnnoMI dataset (easier, 2-speaker)
3. ✅ Validate transcription + entity extraction together
4. ✅ Get first real validation results

**Next Week:**
1. Process all AnnoMI sessions
2. Generate Phase 1 validation report
3. Review results, decide if methodology works
4. Proceed to AMI or adjust approach

### Success Looks Like
- Clear WER benchmarks on multiple datasets
- Entity extraction validation working
- Honest assessment of strengths/limitations
- Data for academic paper

---

## Lessons Learned

**Don't optimize perfect speaker diarization if:**
1. Transcription is already great
2. It's not core product value
3. Winners use different architecture entirely
4. Easier datasets available to validate first

**Do focus on:**
1. Core product features (entity extraction)
2. Transcription quality (our actual strength)
3. Breadth over depth (test many datasets, not perfect one)
4. What makes ClipScribe unique

---

**READY TO CLEAN UP AND REFOCUS?**

Say the word and I'll:
1. Archive research files
2. Create summary document
3. Update CONTINUATION_PROMPT
4. Get us back on validation roadmap
5. Start AnnoMI testing (easier dataset)

