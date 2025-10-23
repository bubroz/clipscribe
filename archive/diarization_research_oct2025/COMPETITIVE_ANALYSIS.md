# Competitive Analysis: Speaker Diarization Performance
**Date:** October 22, 2025  
**Our Performance:** 35% speaker accuracy with threshold 0.80

---

## Understanding Our Metric vs Industry Standards

**CRITICAL:** We're measuring **speaker accuracy** (% of segments with correct speaker), NOT **DER** (Diarization Error Rate).

### Our Metric: Speaker Accuracy
```
speaker_accuracy = correct_segments / total_segments
Our result: 35% (with 5 speakers vs 4 ground truth)
```

### Industry Metric: DER (Diarization Error Rate)
```
DER = (missed_speech + false_alarm + speaker_confusion) / total_speech_time
Lower is better (0% = perfect)
```

**We need to calculate DER to compare properly!**

---

## CHiME-6 Challenge Results (2020)

**Researching official results...**

### Track 1: Diarization-only
TBD - researching

### Track 2: Transcription + Diarization  
TBD - researching

---

## State-of-the-Art (2024-2025)

**Researching recent papers...**

---

## Commercial Systems

**Researching Otter.ai, Descript, etc...**

---

## Quick Assessment (Preliminary)

Based on our informal metric:
- **17% baseline** → **35% with tuning** = 2.06x improvement
- Still detecting 5 speakers vs 4 actual = room for improvement
- Need DER calculation for proper comparison

**Next:** Convert our results to DER for apples-to-apples comparison

---

**STATUS: RESEARCHING COMPETITIVE LANDSCAPE**

