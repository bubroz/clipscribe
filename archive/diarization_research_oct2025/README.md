# Speaker Diarization Research Archive
**Dates:** October 20-22, 2025  
**Duration:** 3 days of deep research  
**Outcome:** 2x improvement, valuable learnings, strategic pivot

---

## What This Archive Contains

**Research documents:**
- `SPEAKER_DIARIZATION_RESEARCH.md` - Initial investigation
- `THRESHOLD_BINARY_SEARCH.md` - Systematic threshold optimization
- `GEMINI_SPEAKER_MERGER_RESEARCH.md` - Creative Gemini-based approach
- `CLUSTERING_THRESHOLD_SOLUTION.md` - Implementation details
- `CHIME6_WINNER_RESEARCH.md` - Analysis of winning approaches
- `DEEP_RESEARCH_PLAN.md` - Comprehensive research roadmap
- `COMPETITIVE_ANALYSIS.md` - Benchmarking context

**Test scripts:**
- `test_gemini_diarization.py` - Validated Gemini speaker counting
- `validate_gemini_timestamps.py` - Proved Gemini timestamps unreliable
- `test_pyannote_threshold.py` - Threshold parameter testing

**Supporting files:**
- `NEXT_STEPS_EXTERNAL_TERMINAL.sh` - Testing procedures
- `threshold_0.95_results.txt` - Test results

---

## Key Findings

### What Worked
✅ **Clustering threshold tuning:** 0.70 → 0.80 doubled speaker accuracy  
✅ **Speaker hints:** min/max_speakers prevents wild over-segmentation  
✅ **Binary search methodology:** Found optimal range (0.80-0.87)

### What Didn't Work
❌ **Gemini for timestamps:** Accurate speaker count, hallucinated timestamps  
❌ **Simple threshold to exact 4 speakers:** Binary collapse at 0.83-0.87  
❌ **Post-processing merging:** Adaptive thresholds, duplicate detection insufficient

### What We Learned
💡 **Winners use TS-VAD, not clustering** (completely different paradigm)  
💡 **pyannote is optimized for VoxConverse, struggles on CHiME-6**  
💡 **Far-field 4-speaker with overlap is HARD** (even for SOTA)  
💡 **Our transcription is EXCELLENT** (43.5% WER vs 77% baseline)

---

## Final Configuration

**Locked in for production:**
- Clustering threshold: 0.80
- min_speakers: 2
- max_speakers: 6

**Performance:**
- CHiME-6: 5 speakers detected (4 ground truth), 35% speaker accuracy
- Expected on easier datasets: 60-80% speaker accuracy

---

## Why We Stopped

**Strategic decision:** Speaker diarization is secondary to:
1. Transcription quality (already excellent)
2. Entity extraction (untested - core product)
3. Relationship accuracy (untested - core product)
4. Multi-dataset validation (1/8 complete)

**Further optimization requires:**
- Implementing TS-VAD (1-2 weeks)
- Multi-channel processing
- Not worth time investment

---

## References for Future

**If speaker diarization becomes critical priority:**

**Papers to read:**
1. "Target-Speaker Voice Activity Detection" (STC, CHiME-6 winner)
2. "pyannote.audio 2.1 speaker diarization pipeline" (Hervé Bredin)
3. "TS-SEP: Joint Diarization and Separation" (Boeddeker et al.)

**Approaches to try:**
1. TS-VAD implementation
2. Multi-channel beamformed audio
3. Dereverberation preprocessing (WPE)
4. Fine-tuning pyannote on CHiME-6 training data

---

**ARCHIVE STATUS:** Research complete, findings documented, moving on to core validation goals.

