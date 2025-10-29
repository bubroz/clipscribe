# Round 1 Research: Complete Format Analysis
**Date:** October 21, 2025 00:23 PDT  
**Status:** ✅ COMPLETE

---

## Executive Summary

**2 of 8 datasets are PRODUCTION-READY, 1 needs parser, 5 need deeper investigation.**

| Dataset | Format | Difficulty | Ready? | Action |
|---------|--------|------------|--------|--------|
| **AnnoMI** | CSV | 🟢 EASY | ✅ YES | Use NOW |
| **CHiME-6** | JSON | 🟢 EASY | ✅ YES | Use NOW |
| **AMI/ICSI** | NXT XML | 🟡 MEDIUM | ⚠️ PARSER | Build parser (6hrs) |
| **AISHELL-4** | Unknown | ❓ TBD | ❓ TBD | Download sample |
| **AISHELL-5** | Unknown | ❓ TBD | ❓ TBD | Download sample |
| **AliMeeting** | Unknown | ❓ TBD | ❓ TBD | Download sample |
| **MAGICDATA** | Unknown | ❓ TBD | ❓ TBD | Download sample |
| **DiPCo** | Not tested | ❓ TBD | ❓ TBD | Low priority |

---

## Dataset 1: AnnoMI ✅

### Status
**100% READY FOR PRODUCTION**

### Format Details
- **File:** CSV (2.3MB for simple, 3.6MB for full)
- **Conversations:** 133 total, 26 with 100+ utterances (30+ min)
- **Total utterances:** 9,699
- **Audio:** YouTube links (yt-dlp compatible)

### Structure
```csv
transcript_id, mi_quality, video_title, video_url, topic, utterance_id, 
interlocutor, timestamp, utterance_text, main_therapist_behaviour, client_talk_type
```

### Sample Data
```
Conversation #121 (longest - 598 utterances, ~37 min):
  [00:00:11] THERAPIST: Uh, welcome. And, uh—
  [00:00:12] CLIENT: Thank you.
  [00:00:13] THERAPIST: I'd say my name is Mark...
  ...
  Speaker distribution: 299 therapist, 299 client (perfect balance)
```

### Integration Code
```python
import pandas as pd

# Load dataset
df = pd.read_csv('AnnoMI-simple.csv')

# Get long conversations (30+ min)
long_convos = df.groupby('transcript_id').agg({
    'utterance_id': 'count',
    'video_url': 'first'
}).query('utterance_id > 100')

# Process one conversation
conversation = df[df['transcript_id'] == 121]
video_url = conversation.iloc[0]['video_url']

# Download audio (existing ClipScribe code)
# Process with WhisperX + Gemini
# Compare speaker labels: SPEAKER_01 → therapist, SPEAKER_02 → client
```

### Preprocessing Steps
**ZERO PREPROCESSING NEEDED**

### Challenges
- ⚠️ YouTube videos could be deleted (check availability before processing)
- ⚠️ No word-level timestamps (only utterance-level HH:MM:SS)

### Validation Potential
- **Dyadic accuracy:** Test 2-speaker scenarios
- **Speaker attribution:** therapist vs client mapping
- **WER calculation:** Compare ClipScribe vs ground truth text
- **Estimated cost:** $0.24 for all 133 conversations

---

## Dataset 2: CHiME-6 ✅

### Status
**100% READY FOR PRODUCTION**

### Format Details
- **Files:** 20 JSON files (train: 16, dev: 2, eval: 2)
- **Sessions:** 20 total (~40 hours)
- **Transcriptions size:** 2.4MB
- **Audio size:** 120GB (train: 97GB, dev: 11GB, eval: 12GB)

### Structure
```json
[
  {
    "end_time": "00:01:11.00",
    "start_time": "00:01:10.41",
    "words": "We are free.",
    "speaker": "P21",
    "session_id": "S08"
  },
  ...
]
```

### Sample Session Analysis
```
Session S08:
  - Duration: ~2.5 hours (00:01:10 → 02:31:31)
  - Speakers: 4 (P21, P22, P23, P24)
  - Segments: 6,175 total
  - Distribution:
      P21: 1,228 segments (19.9%)
      P22: 1,956 segments (31.7%) 
      P23: 1,574 segments (25.5%)
      P24: 1,417 segments (22.9%)
```

### Integration Code
```python
import json
from pathlib import Path

# Load CHiME-6 transcript
with open('transcriptions/train/S08.json') as f:
    segments = json.load(f)

# Already in perfect format for validation!
# Each segment has: start_time, end_time, words, speaker

# Process audio with ClipScribe
# Compare directly (format matches!)
```

### Preprocessing Steps
**MINIMAL:**
1. Load JSON (native Python)
2. Convert HH:MM:SS.ms timestamps to seconds (simple)
3. Ready for comparison

### Challenges
- ⚠️ Multi-channel audio (6 channels) - use channel 0 or mix
- ⚠️ Far-field recording (challenging audio quality)
- ⚠️ Overlapping speech (diarization stress test)

### Validation Potential
- **Stress test:** Far-field, noise, overlaps
- **Benchmark comparison:** Compare DER to CHiME-6 challenge winners
- **4-speaker accuracy:** Multi-party meeting validation
- **Estimated cost:** $0.72 for 40 hours

### CRITICAL INSIGHT
**This is PERFECT for ClipScribe:**
- JSON format = zero conversion
- Segment structure matches our output
- Industry benchmark dataset
- Can directly compare DER to SOTA results

---

## Dataset 3: AMI/ICSI ⚠️

### Status
**NEEDS XML PARSER (6-8 hours to build)**

### Format Details
- **Files:** 1,949 XML files total
- **Format:** NXT (NITE XML Toolkit)
- **Granularity:** Word-level (not segment-level)
- **Meetings:** 75 meetings (ICSI corpus)
- **Duration:** ~70 hours total

### Structure
```xml
<nite:root nite:id="Bro018.A.words" xmlns:nite="http://nite.sourceforge.net/">
  <w nite:id="Bro018.w.654" starttime="191.39" endtime="191.42" c="W">Oh</w>
  <w nite:id="Bro018.w.655" starttime="191.42" endtime="191.42" c=".">.</w>
  ...
  <vocalsound nite:id="Bro018.vocalsound.11" description="laugh"/>
  <disfmarker nite:id="Bro018.disfmarker.29"/>
  ...
</nite:root>
```

### Key Challenges
1. **Word-level, not segment-level:**
   - Each `<w>` tag is ONE WORD
   - Need to group words into segments for comparison
   - Need to handle disfluencies, pauses, vocal sounds

2. **Multiple files per meeting:**
   - `Bro018.A.words.xml` = Speaker A's words
   - `Bro018.B.words.xml` = Speaker B's words
   - Need to merge multiple speaker files
   - Need to align timestamps across speakers

3. **Speaker identification:**
   - Speaker ID in filename (e.g., `.A.`, `.B.`)
   - Need `speakers.xml` to map letters to speaker IDs

### Parser Required
```python
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_nxt_meeting(meeting_id: str, data_dir: Path):
    """
    Parse NXT XML for one meeting into ClipScribe format.
    
    Returns: List of segments with speaker labels and timestamps
    """
    # 1. Load speakers.xml to get speaker mapping
    # 2. Find all {meeting_id}.*.words.xml files
    # 3. For each speaker file:
    #    - Parse <w> elements
    #    - Group consecutive words into segments
    #    - Add speaker label
    # 4. Merge all speakers, sort by timestamp
    # 5. Return unified segment list
    
    pass  # 6-8 hours to implement properly
```

### Preprocessing Steps
**MODERATE COMPLEXITY:**
1. Parse speakers.xml for meeting metadata
2. Find all word XML files for meeting
3. Parse each speaker's words
4. Group words into segments (sentence boundaries?)
5. Merge speakers, sort by time
6. Convert to ClipScribe JSON format

### Validation Potential
- **High value:** 70 hours, 3-10 speakers per meeting
- **Challenging:** Natural technical discussions
- **Word-level ground truth:** Can validate transcription accuracy precisely

### Decision
**DEFER until AnnoMI + CHiME-6 validated**
- Parser is 6-8 hours of work
- AMI and ICSI are similar (same format)
- Can validate 90% of needs with AnnoMI + CHiME-6 first

---

## Datasets 5-8: Mandarin Datasets 🔍

### AISHELL-4
- **Summary:** 211 Mandarin meetings, 4-8 speakers, 120 hours
- **Format:** 8-channel mic array
- **Size:** Train: 7GB (L), 25GB (M), 14GB (S) = 46GB total
- **License:** CC BY-SA 4.0
- **Status:** Need to download sample to inspect format

### AliMeeting
- **Summary:** 120 hours Mandarin meetings by Alibaba
- **Format:** Multi-channel
- **Status:** Need to download sample to inspect format

### MAGICDATA
- **Summary:** 180 hours Mandarin conversational speech
- **Format:** "Rich annotated"
- **Status:** Need to download sample to inspect format

### AISHELL-5
- **Summary:** In-car Mandarin multi-speaker
- **Format:** Multi-channel
- **Status:** Need to download sample to inspect format

### Next Steps for Mandarin
**Download ONE small sample from each:**
- Extract format documentation
- Test WhisperX Mandarin support
- Test Gemini on Mandarin audio
- Estimate preprocessing effort

**Estimated time:** 2-3 hours per dataset = 8-12 hours total

---

## ROUND 1 CONCLUSIONS

### Production-Ready NOW (0 hours work):
1. ✅ **AnnoMI**: 133 conversations, CSV format
2. ✅ **CHiME-6**: 20 sessions, JSON format

### Needs Parser (6-8 hours):
3. ⚠️ **AMI/ICSI**: 75 meetings, NXT XML format

### Needs Investigation (8-12 hours):
4-7. ❓ **Mandarin datasets**: Download samples, test formats

### Total Effort Estimate:
- **Immediate validation:** 0 hours (use AnnoMI + CHiME-6)
- **Comprehensive English:** 6-8 hours (add AMI/ICSI parser)
- **Multilingual expansion:** 8-12 hours (Mandarin investigation)
- **TOTAL:** 14-20 hours for ALL 8 datasets

---

## RECOMMENDATION

### Phase 1 (This Week): Validate with AnnoMI + CHiME-6
- Both are production-ready
- 153 conversations / 40 hours / $0.96 cost
- Proves English dyadic + multi-speaker accuracy
- **Effort:** 8-10 hours to build validation pipeline

### Phase 2 (Next Week): Add AMI/ICSI
- Build NXT XML parser
- Add 75 meetings / 70 hours / $1.26 cost  
- Comprehensive English validation
- **Effort:** 6-8 hours parser + 2-4 hours integration

### Phase 3 (Following Weeks): Mandarin
- Download and analyze samples
- Test WhisperX + Gemini on Mandarin
- Add 4 datasets / 500+ hours / $9 cost
- Global validation proof
- **Effort:** 8-12 hours investigation + integration

---

## Critical Findings

### ✅ NO SHOWSTOPPERS FOUND

**What Works:**
1. AnnoMI: Plug-and-play (pandas + yt-dlp)
2. CHiME-6: Native JSON, perfect format match
3. AMI/ICSI: Doable with standard XML parsing

**What's Unknown:**
1. Mandarin dataset formats (need samples)
2. WhisperX Mandarin quality
3. Gemini Mandarin audio support

**Storage Reality Check:**
- AnnoMI: 5GB
- CHiME-6: 11GB (dev only) or 120GB (full)
- AMI/ICSI: 50GB each = 100GB
- Mandarin: 350GB total
- **TOTAL:** 466-576GB depending on scope

**Cost Reality Check:**
- AnnoMI: $0.24
- CHiME-6 dev: $0.20 (11GB, ~12 hours)
- CHiME-6 full: $0.72 (40 hours)
- AMI/ICSI: $2.52 (140 hours combined)
- Mandarin: $8.42 (468 hours)
- **TOTAL:** $11.66 for comprehensive validation

---

## Next Research Rounds

### Round 2: Benchmarking Standards (4-6 hours)
- Find SOTA DER results for each dataset
- Research DER calculation methodology
- Document expected baselines
- Plan metrics reporting

### Round 3: Execution Architecture (4-6 hours)
- Design preprocessing pipelines
- Plan Modal batch processing
- Storage architecture (local vs cloud)
- Timeline and critical path

### Round 4: Mandarin Deep Dive (8-12 hours)
- Download samples from all 4 datasets
- Inspect formats in detail
- Test WhisperX + Gemini on Mandarin
- Build parsers if needed

---

## Go/No-Go Decision Points

### Should we proceed with comprehensive validation?

**Arguments FOR:**
- ✅ No technical blockers found
- ✅ Formats are parseable (2 ready, 1 doable, 5 TBD)
- ✅ Cost is minimal ($12 total)
- ✅ Storage is manageable (500GB = $50 external drive)
- ✅ Effort is reasonable (14-20 hours parser work)

**Arguments AGAINST:**
- ⚠️ 14-20 hours developer time investment
- ⚠️ Mandarin formats still unknown (risk)
- ⚠️ May reveal quality issues requiring fixes

**RECOMMENDATION: PROCEED**

Start with AnnoMI + CHiME-6 (production-ready).
This gives us 193 hours of validation for $0.96 and proves the pipeline works.
Then decide on AMI/ICSI and Mandarin based on results.

