# Validation Dataset Research - Round 1: Format Deep Dive
**Date:** October 21, 2025  
**Researcher:** AI Assistant  
**Goal:** Download samples, inspect formats, test parsers, document preprocessing

---

## Research Methodology

**For Each Dataset:**
1. Download ONE sample (not full dataset)
2. Inspect directory structure
3. Examine file formats
4. Test parsing/conversion
5. Document preprocessing steps
6. Identify blockers/challenges

**Success Criteria:**
- Can we extract audio + transcript?
- Can we convert to ClipScribe format?
- What tools/libraries are needed?

---

## Dataset 1: AnnoMI (EASIEST - Starting Here)

### Download Status
✅ **COMPLETE** - Cloned from GitHub in 10 seconds

### File Structure
```
validation_data/samples/annomi/
├── .git/
├── AnnoMI-simple.csv  (2.3 MB)
├── AnnoMI-full.csv    (3.6 MB)
└── README.md          (6.5 KB)
```

### Format Analysis
```
CSV Structure:
- Total utterances: 9,699
- Total transcripts: 133
- Unique videos: 119 (some videos have multiple transcript versions)

Columns in AnnoMI-simple.csv:
  - transcript_id: Unique conversation ID
  - mi_quality: "high" or "low" (quality label)
  - video_title: YouTube video title
  - video_url: Direct YouTube link
  - topic: Conversation topic (e.g., "reducing alcohol consumption")
  - utterance_id: Ordering index within conversation
  - interlocutor: "therapist" or "client" (speaker label)
  - timestamp: Format "HH:MM:SS"
  - utterance_text: Exact transcript text
  - main_therapist_behaviour: "reflection", "question", "therapist_input", "other"
  - client_talk_type: "change", "neutral", "sustain"

Conversation lengths (utterance counts):
  Mean: 73 utterances
  Median: 47 utterances
  Max: 598 utterances (conversation #121)
  100+ utterances: 26 conversations (likely 30+ minutes)
```

### Audio Extraction
```bash
# Test URL: https://www.youtube.com/watch?v=dDygm-rh6hk
# Video: "MI in health care" (37:32 duration, 598 utterances)

✅ yt-dlp works perfectly
✅ Duration: 37:32 (2,252 seconds)
✅ Audio format: opus 96kbps (27MB), perfect quality
✅ Video available (if needed for visual verification)

Sample conversation:
  [00:00:11] THERAPIST: Uh, welcome. And, uh—
  [00:00:12] CLIENT: Thank you.
  [00:00:13] THERAPIST: I'd say my name is Mark and I work here at Green...
  [00:00:17] CLIENT: Mm-hmm.
  ...
  
Speaker distribution: 299 therapist, 299 client (perfect balance)
```

### Parsing Test
```python
✅ pandas reads CSV natively (no conversion needed)
✅ Can group by transcript_id to get conversations
✅ Timestamps are clean HH:MM:SS format
✅ Speaker labels are clear: "therapist" vs "client"

# Working code:
import pandas as pd
df = pd.read_csv('AnnoMI-simple.csv')
conversation = df[df['transcript_id'] == 121]  # Get specific conversation
# Ready for validation pipeline
```

### Preprocessing Steps
```
ZERO PREPROCESSING NEEDED:
1. Read CSV with pandas (done)
2. Download audio via yt-dlp (existing ClipScribe code)
3. Process with WhisperX + Gemini
4. Compare speakers: Map SPEAKER_01 → therapist, SPEAKER_02 → client
5. Calculate metrics

Integration: 100% compatible with existing ClipScribe architecture
```

### Challenges Identified
- ✅ None - this is plug-and-play
- ⚠️ YouTube videos could be deleted/private (check availability)
- ⚠️ Some conversations <30min (filter by utterance_count > 100)

### Ready for ClipScribe?
✅ **YES** - Can build validation pipeline TODAY

**Estimated effort:** 4-6 hours to build validator
**Processing cost:** $0.24 for all 133 conversations
**Value:** HIGH - immediate validation of dyadic accuracy

---

## Dataset 2: CHiME-6 (JSON Format - Priority #2)

### Download Status
⏳ Waiting...

### File Structure
```
TBD
```

### Format Analysis
```
TBD
```

### Audio Extraction
```
TBD
```

### Parsing Test
```python
# TBD
```

### Preprocessing Steps
```
TBD
```

### Challenges Identified
- [ ] TBD

### Ready for ClipScribe?
⏳ Waiting...

---

## Dataset 3: AMI Meeting Corpus (NXT XML - Complex)

### Download Status
⏳ Waiting...

### File Structure
```
TBD
```

### Format Analysis
```
TBD
```

### NXT Parser Test
```python
# TBD - test nxt-python or custom parser
```

### Preprocessing Steps
```
TBD
```

### Challenges Identified
- [ ] TBD

### Ready for ClipScribe?
⏳ Waiting...

---

## Dataset 4: ICSI Meeting Corpus

### Download Status
⏳ Waiting...

### File Structure
```
TBD
```

### Format Analysis
```
TBD
```

### Parsing Test
```python
# TBD
```

### Preprocessing Steps
```
TBD
```

### Challenges Identified
- [ ] TBD

### Ready for ClipScribe?
⏳ Waiting...

---

## Dataset 5: AISHELL-4 (Mandarin)

### Download Status
⏳ Waiting...

### File Structure
```
TBD
```

### Format Analysis
```
TBD
```

### Parsing Test
```python
# TBD
```

### Multilingual Test
```
TBD - test WhisperX + Gemini on Mandarin sample
```

### Preprocessing Steps
```
TBD
```

### Challenges Identified
- [ ] TBD

### Ready for ClipScribe?
⏳ Waiting...

---

## Dataset 6: AliMeeting (Mandarin)

### Download Status
⏳ Waiting...

### File Structure
```
TBD
```

### Format Analysis
```
TBD
```

### Parsing Test
```python
# TBD
```

### Preprocessing Steps
```
TBD
```

### Challenges Identified
- [ ] TBD

### Ready for ClipScribe?
⏳ Waiting...

---

## Dataset 7: MAGICDATA (Mandarin)

### Download Status
⏳ Waiting...

### File Structure
```
TBD
```

### Format Analysis
```
TBD
```

### Parsing Test
```python
# TBD
```

### Preprocessing Steps
```
TBD
```

### Challenges Identified
- [ ] TBD

### Ready for ClipScribe?
⏳ Waiting...

---

## Dataset 8: AISHELL-5 (Mandarin)

### Download Status
⏳ Waiting...

### File Structure
```
TBD
```

### Format Analysis
```
TBD
```

### Parsing Test
```python
# TBD
```

### Preprocessing Steps
```
TBD
```

### Challenges Identified
- [ ] TBD

### Ready for ClipScribe?
⏳ Waiting...

---

## Research Findings Summary

### Overall Assessment
⏳ Research in progress...

### Format Compatibility Matrix
| Dataset | Audio Format | Transcript Format | Conversion Needed | Difficulty |
|---------|--------------|-------------------|-------------------|------------|
| AnnoMI | TBD | TBD | TBD | TBD |
| CHiME-6 | TBD | TBD | TBD | TBD |
| AMI | TBD | TBD | TBD | TBD |
| ICSI | TBD | TBD | TBD | TBD |
| AISHELL-4 | TBD | TBD | TBD | TBD |
| AliMeeting | TBD | TBD | TBD | TBD |
| MAGICDATA | TBD | TBD | TBD | TBD |
| AISHELL-5 | TBD | TBD | TBD | TBD |

### Tools Required
- [ ] TBD

### Showstoppers Found
- [ ] TBD

### Recommended Approach
TBD - will update after testing all datasets

---

## Next Steps

After Round 1 completes:
- [ ] Round 2: Benchmarking standards research
- [ ] Round 3: Execution architecture design
- [ ] Round 4: Build comprehensive validation pipeline

---

**STATUS: RESEARCH STARTING - UPDATING IN REAL-TIME**

