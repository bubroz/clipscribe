# Phase 1: Core Intelligence Features - Detailed Implementation Plan

**Timeline**: October 15 - December 31, 2025 (11 weeks)  
**Version Target**: v2.60.0  
**Status**: Ready to implement after cleanup

---

## Hardware & Infrastructure

### Local Development (Primary)
```
MacBook Pro M3 Max:
- 40-core GPU
- 64GB unified memory
- Perfect for WhisperX + batch processing
- Can run 10 videos concurrently
```

### Cloud Deployment (For Others/Future)
```
Google Cloud Run + GCS:
- On-demand processing
- Pay-per-use
- Auto-scaling
- Google Workspace integration (Chat, Gmail)
```

---

## Phase 1 Feature Breakdown

### 1.1 Batch Processing (Weeks 1-2)

**Goal**: Process 1-500 videos efficiently

**CLI Commands:**
```bash
# Submit batch
clipscribe batch submit urls.txt \
  --quality auto \
  --enable-clips \
  --output results/

# Monitor progress
clipscribe batch status abc123

# Fetch results
clipscribe batch fetch abc123
```

**Implementation**: Use existing Cloud Run Jobs infrastructure

**Status**: Not started  
**Dependencies**: None

---

### 1.2 Dual-Mode Transcription (Weeks 3-4)

**Goal**: Smart transcription with quality/speed tradeoffs

#### Mode 1: Fast (Voxtral + pyannote)
```
Use case: News, interviews, general content
Accuracy: 95-97%
Speed: 1-2x realtime
Cost: $0.01/video (Voxtral)
Diarization: pyannote (separate, adds 30-60s)

Pipeline:
1. Voxtral transcribes → 95% accurate, fast
2. pyannote identifies speakers → SPEAKER_00, SPEAKER_01
3. Merge: Align transcript with speaker segments
```

#### Mode 2: Accurate (WhisperX)
```
Use case: Medical, legal, technical, intelligence
Accuracy: 97-99%
Speed: 3-5x realtime (M3 Max)
Cost: $0 (local processing)
Diarization: Built-in (simultaneous with transcription)

Pipeline:
1. WhisperX transcribes + diarizes in one pass
2. Word-level timestamps
3. Speaker labels automatically aligned
```

**Auto-Detection Logic:**
```python
async def detect_content_type(video_metadata, sample_audio=None):
    """
    Detect if video needs high-accuracy transcription.
    
    Signals for WhisperX:
    - Keywords in title: medical, legal, court, deposition, technical, briefing
    - Channel type: medical schools, law firms, defense/intel channels
    - User flag: --quality accurate
    - Sample audio: Technical jargon detected
    
    Returns: "fast" or "accurate"
    """
    title_lower = video_metadata.title.lower()
    
    # High-stakes keywords
    high_stakes_keywords = [
        "medical", "legal", "court", "deposition", "briefing",
        "technical", "analysis", "intelligence", "classified",
        "testimony", "hearing", "clinical", "diagnosis"
    ]
    
    if any(keyword in title_lower for keyword in high_stakes_keywords):
        return "accurate"
    
    # Defense/intel channels (you can customize this list)
    intel_channels = ["CSIS", "RAND", "Brookings", "CFR"]
    if any(channel in video_metadata.channel for channel in intel_channels):
        return "accurate"
    
    # Default to fast mode
    return "fast"
```

**CLI:**
```bash
# Auto-detect (default)
clipscribe process video "medical-conference-url"
# → Detects "medical" → Uses WhisperX

# Force fast mode
clipscribe process video "url" --quality fast

# Force accurate mode
clipscribe process video "url" --quality accurate
```

**Status**: Not started  
**Dependencies**: None  
**Complexity**: Medium (two transcriber implementations)

---

### 1.3 Grok-Powered Speaker Identification (Week 4)

**Goal**: "SPEAKER_00" → "President Biden" (context-based)

**How it works:**
```python
async def identify_speakers(transcript_with_speakers, entities, video_metadata):
    """
    Use Grok to infer speaker identities from context.
    
    Grok analyzes:
    - What each speaker says
    - Entities mentioned when they speak
    - Context clues (titles, references)
    - Video title/description
    
    Returns: Speaker name guesses with confidence
    """
    
    prompt = f"""
Analyze this transcript and identify who each speaker likely is.

Video: {video_metadata.title}
Channel: {video_metadata.channel}

Transcript with speaker labels:
{transcript_with_speakers}

Entities identified:
{entities}

For each speaker (SPEAKER_00, SPEAKER_01, etc.), provide:
1. Most likely identity (name, title, or role)
2. Confidence (0-100%)
3. Evidence (quotes that reveal identity)

Be conservative - only identify when confident.
Return JSON.
"""
    
    speaker_ids = await grok.analyze(prompt)
    
    # Example output:
    {
      "SPEAKER_00": {
        "identity": "President Joe Biden",
        "confidence": 95,
        "evidence": [
          "References to 'my administration'",
          "Discusses presidential decisions",
          "Other speakers address as 'Mr. President'"
        ]
      },
      "SPEAKER_01": {
        "identity": "Reporter (Unknown)",
        "confidence": 60,
        "evidence": ["Asks questions", "No self-identification"]
      }
    }
```

**Accuracy expectations:**
- High-profile figures: 85-95% accuracy (Biden, Trump, etc.)
- Generic roles: 70-80% accuracy (reporter, analyst)
- Unknown speakers: Will say "Unknown" with low confidence

**User control:**
```bash
# Auto-identify speakers
clipscribe process video "url" --identify-speakers

# Manual override
clipscribe process video "url" --speakers "SPEAKER_00=Biden,SPEAKER_01=Reporter"

# Review and confirm
clipscribe process video "url" --identify-speakers --interactive
# Shows: "I think SPEAKER_00 is Biden (95% confident). Correct? [y/n]"
```

**Cost**: +$0.01 per video (Grok analysis)  
**Status**: Not started  
**Dependencies**: 1.2 (diarization must work first)

---

### 1.4 Intelligent Clip Recommendations (Week 5)

**Goal**: Grok finds 3-10 best clips based on multiple criteria

**Recommendation Engine:**
```python
class ClipRecommendationEngine:
    """
    Multi-objective clip recommendation.
    """
    
    async def recommend_clips(
        self,
        transcript_with_speakers,
        entities,
        relationships,
        objective="auto",  # or custom prompt
        max_clips=5
    ):
        """
        Recommend clips optimized for:
        1. Newsworthiness (controversial, significant statements)
        2. Social media virality (punchy quotes, <60s ideal)
        3. Information density (most facts per second)
        
        Args:
            objective: "auto" or custom instructions
            max_clips: How many clips to recommend
        """
        
        if objective == "auto":
            optimization_criteria = """
            Optimize for:
            1. Newsworthiness: Controversial, significant, or breaking statements
            2. Social media: Punchy, quotable, self-contained (30-90s ideal)
            3. Information density: Maximum facts/insights per second
            
            Prefer clips that:
            - Have clear speaker attribution
            - Are self-contained (make sense without context)
            - Contain specific facts/numbers/claims
            - Have emotional impact or controversy
            - Can stand alone as social media posts
            """
        else:
            # User provides custom criteria
            optimization_criteria = objective
        
        prompt = f"""
Analyze this video and recommend the top {max_clips} clips to extract.

{optimization_criteria}

For each recommended clip:
1. Start timestamp (seconds)
2. End timestamp (seconds)
3. Speaker (if identified)
4. Title/headline (8 words max)
5. Why it's valuable (newsworthiness score 1-10, virality score 1-10, info-density score 1-10)
6. Key entities mentioned
7. One-sentence summary
8. Suggested social media caption

Constraints:
- Clips can be any length (no platform limits)
- Must be self-contained (understandable without full video)
- Prefer 30-90s for social, but can be longer if valuable

Transcript:
{transcript_with_speakers}

Entities:
{entities}

Relationships:
{relationships}

Return JSON array.
"""
        
        recommendations = await self.grok.analyze(prompt)
        return recommendations
```

**Output Example:**
```json
[
  {
    "clip_id": 1,
    "start": 135,
    "end": 165,
    "duration": 30,
    "speaker": "President Biden",
    "title": "Biden Announces $500M Ukraine Military Aid",
    "scores": {
      "newsworthiness": 9,
      "virality": 8,
      "info_density": 7
    },
    "entities": ["Biden", "Ukraine", "$500M", "military aid"],
    "summary": "President announces major military aid package to Ukraine with specific dollar amount and timeline.",
    "social_caption": "BREAKING: Biden announces $500M military aid package to Ukraine, includes advanced weapons systems. Full context 🧵",
    "rationale": "Major policy announcement with specific figures, highly quotable, newsworthy"
  },
  ...
]
```

**CLI:**
```bash
# Auto-optimization (newsworthy + viral + dense)
clipscribe process video "url" --recommend-clips

# Custom optimization
clipscribe process video "url" --recommend-clips \
  --clip-objective "Find moments where Raytheon contracts are discussed"

# Interactive review
clipscribe process video "url" --recommend-clips --interactive
# Shows each recommendation, you approve/reject/modify
```

**Cost**: +$0.01-0.02 per video  
**Status**: Not started  
**Dependencies**: 1.2 (needs speaker data), 1.3 (needs entities)

---

### 1.5 Auto-Clip Generation (Week 6)

**Goal**: Generate approved clips as .mp4 files

**Implementation:**
```python
import ffmpeg
import json
from pathlib import Path

class VideoClipper:
    """Generate video clips with metadata."""
    
    def generate_clips(
        self,
        video_path,
        recommendations,
        output_dir,
        approved_clip_ids=None  # None = all, or [1,3,5] = specific
    ):
        """
        Generate video clips from recommendations.
        
        Args:
            video_path: Source video
            recommendations: From ClipRecommendationEngine
            output_dir: Where to save clips
            approved_clip_ids: Which clips to generate (None = all)
        """
        
        clips_generated = []
        
        for rec in recommendations:
            clip_id = rec['clip_id']
            
            # Skip if not approved
            if approved_clip_ids and clip_id not in approved_clip_ids:
                continue
            
            # Generate safe filename
            safe_title = self._sanitize_filename(rec['title'])
            output_path = output_dir / f"clip_{clip_id}_{safe_title}.mp4"
            
            # Extract clip with ffmpeg (frame-accurate, no re-encoding)
            try:
                (
                    ffmpeg
                    .input(video_path, ss=rec['start'], t=rec['duration'])
                    .output(
                        str(output_path),
                        vcodec='copy',      # No re-encoding (fast, lossless)
                        acodec='copy',
                        reset_timestamps=1,  # Start clip at 00:00
                        map_metadata=-1      # Clean metadata
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )
                
                # Create metadata sidecar file
                metadata_path = output_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump({
                        "title": rec['title'],
                        "speaker": rec.get('speaker'),
                        "duration": rec['duration'],
                        "scores": rec['scores'],
                        "entities": rec['entities'],
                        "summary": rec['summary'],
                        "social_caption": rec['social_caption'],
                        "source_video": video_path.name,
                        "source_timestamp": f"{rec['start']}-{rec['end']}"
                    }, f, indent=2)
                
                clips_generated.append({
                    "clip_path": output_path,
                    "metadata_path": metadata_path,
                    "recommendation": rec
                })
                
            except ffmpeg.Error as e:
                logger.error(f"Failed to generate clip {clip_id}: {e.stderr.decode()}")
        
        return clips_generated
```

**Workflow Options:**

#### Option A: Auto-Generate All (Non-Interactive)
```bash
clipscribe process video "url" --auto-clip

# Generates all recommended clips immediately
# Fast, no user input needed
```

#### Option B: Review Then Generate (Semi-Interactive)
```bash
clipscribe process video "url" --recommend-clips
# Shows recommendations with scores
# Saves recommendations.json

# Review recommendations.json, then:
clipscribe generate-clips abc123 --clips 1,3,5
# Generates only approved clips
```

#### Option C: Interactive Approval (Fully Interactive) ← **YOUR PREFERENCE**
```bash
clipscribe process video "url" --auto-clip --interactive

# Output:
# ═══ Clip Recommendation 1/5 ═══
# Title: Biden Announces $500M Ukraine Aid
# Duration: 30s (02:15 - 02:45)
# Speaker: President Biden
# Scores: Newsworthy: 9/10, Viral: 8/10, Dense: 7/10
# Summary: President announces major military aid package...
# 
# [G]enerate | [S]kip | [M]odify timestamps | [C]ustom prompt | [Q]uit
# > G
# ✓ Generated: clip_1_Biden_Announces_Ukraine_Aid.mp4

# ...continues for each recommendation
```

#### Option D: Custom Prompt Mode ← **YOUR REQUEST**
```bash
# Override Grok's default optimization
clipscribe process video "url" --auto-clip \
  --clip-prompt "Find every time Raytheon is mentioned with dollar amounts. Extract 10-second clips around each mention."

# Grok uses YOUR criteria instead of default
```

**Cost**: $0 (ffmpeg processing)  
**Time**: ~10-20s total for 5 clips  
**Output**: .mp4 files + .json metadata sidecars

**Status**: Not started  
**Dependencies**: 1.4 (clip recommendations)

---

### 1.6 Entity Search with Speaker Attribution (Week 7)

**Goal**: Search across all videos with speaker context

**Database Enhancement:**
```sql
-- Already have entities table
-- Add speaker attribution
ALTER TABLE entities ADD COLUMN speaker TEXT;
ALTER TABLE entities ADD COLUMN speaker_confidence REAL;

-- Search becomes powerful:
SELECT 
  e.name, 
  e.speaker,
  v.title, 
  v.processed_at
FROM entities e
JOIN videos v ON e.video_id = v.video_id
WHERE e.name LIKE '%Raytheon%'
  AND e.speaker LIKE '%Biden%'
ORDER BY v.processed_at DESC;

-- "Show me all times Biden mentioned Raytheon"
```

**CLI Commands:**
```bash
# Basic entity search
clipscribe search "Raytheon"
# Output: All videos mentioning Raytheon

# With speaker filter
clipscribe search "Raytheon" --speaker "Biden"
# Output: Only when Biden mentioned it

# Speaker-centric search
clipscribe search-speaker "Biden" --entity "Ukraine"
# Output: Everything Biden said about Ukraine

# Cross-video relationship search
clipscribe search-relationship "Trump" "Ukraine"
# Output: All videos discussing this relationship

# Stats
clipscribe stats --period 30days
# Shows: Videos processed, total cost, entity count, speakers identified
```

**Status**: Database ready, CLI commands not built  
**Dependencies**: 1.2 (speaker diarization), 1.3 (speaker identification)

---

## Technical Deep Dive: WhisperX Implementation

### Local Processing on M3 Max

```python
import whisperx
import torch

class WhisperXTranscriber:
    """
    High-accuracy transcription with built-in diarization.
    Optimized for Apple Silicon.
    """
    
    def __init__(self, device="mps"):  # Metal Performance Shaders for M-series
        """
        Initialize WhisperX for M3 Max.
        
        Device options:
        - "mps": Apple Silicon GPU (M1/M2/M3)
        - "cuda": NVIDIA GPU
        - "cpu": CPU only (slow)
        """
        self.device = device
        
        # Load Whisper Large V3 model
        self.model = whisperx.load_model(
            "large-v3",
            device=device,
            compute_type="float16",  # Half-precision for speed
            download_root="~/.cache/whisperx"
        )
        
        # Load alignment model (word-level timestamps)
        self.align_model, self.metadata = whisperx.load_align_model(
            language_code="en",
            device=device
        )
        
        # Load diarization pipeline
        self.diarize_model = whisperx.DiarizationPipeline(
            use_auth_token=os.getenv("HUGGINGFACE_TOKEN"),
            device=device
        )
        
        logger.info(f"WhisperX initialized on {device} with large-v3")
    
    async def transcribe(self, audio_path: str) -> Dict:
        """
        Transcribe with word-level timestamps and speaker diarization.
        
        Returns:
        {
          "text": "full transcript",
          "segments": [
            {
              "start": 0.5,
              "end": 5.2,
              "text": "transcript segment",
              "words": [
                {"word": "transcript", "start": 0.5, "end": 1.2, "speaker": "SPEAKER_00"},
                ...
              ],
              "speaker": "SPEAKER_00"
            }
          ],
          "speakers": {
            "SPEAKER_00": {"total_time": 145, "segments": 12},
            "SPEAKER_01": {"total_time": 89, "segments": 8}
          }
        }
        """
        
        # 1. Transcribe
        logger.info("WhisperX: Transcribing audio...")
        result = self.model.transcribe(
            audio_path,
            batch_size=16,  # M3 Max can handle large batches
            language="en"
        )
        
        # 2. Align for word-level timestamps
        logger.info("WhisperX: Aligning word timestamps...")
        result = whisperx.align(
            result["segments"],
            self.align_model,
            self.metadata,
            audio_path,
            device=self.device,
            return_char_alignments=False
        )
        
        # 3. Diarize speakers
        logger.info("WhisperX: Identifying speakers...")
        diarize_segments = self.diarize_model(audio_path)
        
        # 4. Assign speakers to words
        result = whisperx.assign_word_speakers(diarize_segments, result)
        
        # 5. Format output
        return self._format_output(result)
```

### Performance on M3 Max

**Benchmarks:**
```
5-minute video:
- Transcription: ~2 minutes
- Alignment: ~30 seconds
- Diarization: ~1 minute
- Speaker assignment: ~10 seconds
Total: ~4 minutes (0.8x realtime)

30-minute video:
- Total: ~25 minutes (0.83x realtime)

GPU memory: ~8GB per concurrent video
Max concurrent: 7-8 videos (with 64GB RAM)
```

**Batch processing on M3 Max:**
```python
# Process 10 videos with 2 at a time
clipscribe batch submit urls.txt --transcriber whisperx --workers 2
# Total time for 10 videos: ~40 minutes
# vs Voxtral: ~20 minutes
# Tradeoff: 2x slower, significantly more accurate
```

---

## Cost Analysis: Full Pipeline

### Standard Mode (Fast)
```
5-minute video, news content:
─────────────────────────────
Voxtral transcription: $0.01
pyannote diarization: $0 (local)
Grok speaker ID: $0.01
Grok entity extraction: $0.02
Grok clip recommendations: $0.01
ffmpeg clip generation (5 clips): $0
─────────────────────────────
Total: $0.05 per video
Time: ~4-5 minutes
```

### Accurate Mode (WhisperX)
```
5-minute video, medical/legal:
─────────────────────────────
WhisperX (local M3 Max): $0
Grok speaker ID: $0.01
Grok entity extraction: $0.02
Grok clip recommendations: $0.01
ffmpeg clip generation: $0
─────────────────────────────
Total: $0.04 per video
Time: ~5-6 minutes
```

### Batch (25 videos/day, mixed content)
```
Assumed: 80% fast mode, 20% accurate mode

20 videos × $0.05 (fast) = $1.00
5 videos × $0.04 (accurate) = $0.20
─────────────────────────────
Total: $1.20/day = $36/month

Time: ~2-3 hours processing on M3 Max
(Can run overnight or while working)
```

---

## Critical Clarifying Questions

### 1. **WhisperX Medical/Legal Performance**

I need to be honest - I haven't personally validated WhisperX on medical/legal content.

**Research needed:**
- Test on sample medical conference video
- Test on legal deposition (if you have access)
- Compare: Does it actually get technical terms right?

**Can you provide:**
- [ ] Sample medical/legal video URL for testing?
- [ ] Specific technical terms you need accurate (examples)?
- [ ] Acceptable error rate (99% = 1 word per 100 wrong)?

**I want to validate this before committing to implementation.**

### 2. **Speaker Identification Accuracy**

Grok-based speaker identification (Option B) is **experimental**.

**Realistic expectations:**
```
High confidence (>90%): Presidents, famous figures, clearly identified
Medium (70-90%): Roles mentioned in context ("the senator said...")
Low (<70%): Generic speakers, minimal context clues

Will guess: ~40% of the time
Will be correct: ~85% when it guesses
Will say "Unknown": ~60% of the time (conservative)
```

**Is this acceptable?** Or do you want manual speaker labeling?

### 3. **Clip Generation Workflow Details**

**Interactive mode - specific questions:**

When Grok recommends a clip and you want to modify it:

```
Grok recommends: 02:15 - 02:45 (30s)
You want: 02:10 - 03:00 (50s, more context)

Interface:
[M]odify timestamps
> M
Start time [02:15]: 02:10
End time [02:45]: 03:00
✓ Clip extended to 50s

OR:

[C]ustom prompt
> C
Custom instruction: "Extend to include the question that prompted this answer"
✓ Grok re-analyzes and suggests: 02:08 - 02:50
Accept? [y/n]: y
```

**Is this the level of control you want?**

### 4. **Batch Processing with Clips**

**If you submit 25 videos for batch processing:**

```bash
clipscribe batch submit urls.txt --auto-clip --interactive

# Problem: How to handle interactive for 25 videos?

Option A: Auto-generate all recommended clips (no interaction)
Option B: Generate recommendations, review batch in one session
Option C: Process videos, notify you, you review clips later
```

**Which workflow makes sense for batches?**

### 5. **Cloud Run for Others**

You mentioned "offering to anyone else" - clarify:

**Option A: Open source tool (they self-host)**
```
They:
- Install ClipScribe locally
- Use their own API keys
- Process on their hardware

You:
- Maintain code
- Provide documentation
- No infrastructure cost
```

**Option B: Hosted service (you run it for them)**
```
They:
- Upload videos via web interface
- Pay per video

You:
- Run Cloud Run infrastructure
- Pay for compute/storage
- Handle billing

Cost: Need to mark up pricing
```

**Which are you building toward?**

---

## My Recommendation: Updated Phase 1

Based on your answers, here's what I propose:

### Weeks 1-2: Batch Processing Foundation
- CLI batch commands
- GCS upload/download
- Job tracking

### Weeks 3-4: Dual-Mode Transcription
- Voxtral (fast mode)
- WhisperX (accurate mode)  
- Auto-detection based on content type
- **Test both on your actual content first**

### Week 5: Speaker Diarization & ID
- pyannote integration
- Grok-based speaker identification
- Manual override capability

### Week 6: Clip Recommendations
- Grok multi-objective optimization
- Custom prompt support
- Interactive approval workflow

### Week 7: Clip Generation
- ffmpeg auto-clipping
- Metadata sidecar files
- Batch clip export

### Week 8: Entity Search with Speakers
- CLI search commands
- Speaker-attributed entity search
- Cross-video relationship queries

### Weeks 9-11: Testing & Refinement
- Test on medical/legal content
- Validate speaker ID accuracy
- Refine clip recommendations
- Polish interactive workflows

---

**Before I update ROADMAP.md, answer my 5 clarifying questions so I get the implementation details exactly right.**
