# v3.0.0 Architecture Research & Planning

**Created:** November 12, 2025 (end of epic transformation session)  
**Status:** Research phase - deep investigation needed before refactoring  
**Priority:** High - architectural decision that affects entire project

---

## Strategic Decision

**Remove video download from ClipScribe core.**

**Rationale:**
- Download is NOT our core value (intelligence extraction is)
- Source of reliability issues (YouTube SABR bans, 403s, bot detection)
- 15+ files, ~5,000 lines of complex, fragile code
- Better as separate concern (procurement vs analysis)

**New Vision:**
"ClipScribe: Professional intelligence extraction from audio/video files. Two modes (Cloud GPU, Local API), same intelligence quality."

---

## Current State Analysis

### Two Production Paths (Both Functional):

**Path 1: Cloud/Modal (GPU-Powered)**
```
Input: GCS path (gs://bucket/file.mp3)
  ↓
Modal: WhisperX GPU transcription (A10G, 10-11x realtime)
Modal: pyannote speaker diarization (2-13 speakers)
Modal: Grok intelligence extraction
  ↓
Output: transcript.json + metadata.json to GCS
```
- ✅ Validated Nov 12: 20 videos, $0.073/video
- ✅ NO download issues
- ✅ Speaker diarization
- ✅ Serverless scaling
- ❓ Output format: Simple (2 JSON files)

**Path 2: Local/CLI (API-Based)**
```
Input: File path (local MP3/MP4)
  ↓
Voxtral: API transcription (Mistral, $0.001/min)
Grok: Intelligence extraction (xAI, $0.20/$0.50/M tokens)
  ↓
Output: 10+ files (txt, json, csv, gexf, md, etc.) locally
```
- ✅ Voxtral transcription works
- ✅ Grok extraction works
- ❌ Bugs found in chunked extraction (fixed today)
- ❓ Output format: Comprehensive (10+ files)
- ❌ Currently has download code (to be removed)

---

## Critical Investigation Questions

### 1. Voxtral vs WhisperX (Nov 2025)

**Need to research:**
- Does Voxtral now support speaker diarization?
- Accuracy comparison (WER, handling accents, etc.)
- Cost comparison:
  - Voxtral: $0.001/min API
  - WhisperX: $0.01836/min GPU (Modal A10G)
  - WhisperX is 18x more expensive - worth it?

**Questions:**
- Could Voxtral replace WhisperX in Modal path?
- Would we lose speaker diarization quality?
- Performance impact (API latency vs GPU speed)?
- Is WhisperX's quality advantage worth 18x cost?

**Action needed:** Deep comparison testing

### 2. Output Format Reconciliation

**Modal outputs (from code):**
```json
{
  "transcript": [...segments with speakers...],
  "language": "en",
  "speakers": 2,
  "entities": [...],
  "relationships": [...],
  "topics": [...],
  "key_moments": [...],
  "sentiment": {...},
  "processing_time": 420.5,
  "cost": 0.073,
  "model": "whisperx-large-v3+grok-4-fast"
}
```

**Local outputs (from code):**
```
output/20251112_platform_id/
├── transcript.txt
├── transcript.json
├── entities.json
├── entities.csv
├── relationships.json
├── relationships.csv
├── topics.json
├── knowledge_graph.gexf (CRITICAL!)
├── knowledge_graph.graphml
├── summary.md
├── metadata.json
├── manifest.json
└── report.md
```

**Differences found:**
- ❓ Modal: Returns dict, uploads 2 files (transcript.json, metadata.json)
- ❓ Local: Saves 10+ files in structured directory
- ❓ Modal: Missing GEXF, CSV, markdown reports?
- ❓ Local: Has all formats
- **CRITICAL:** Are Modal outputs incomplete? Or designed differently?

**Action needed:**
1. Check actual Modal GCS uploads (what files are there?)
2. Compare intelligence quality (same entities/relationships?)
3. Decide: Unified format or clearly separate?

### 3. OpenRouter for Model Flexibility

**Research needed:**
- What is OpenRouter? (API routing service)
- Does it support local models?
- Integration effort?
- Cost implications?
- Would it help with "future local model replacement"?

**Alternative approaches:**
- LiteLLM (unified API wrapper)
- Direct integration points (Ollama for local, OpenRouter for cloud)
- Abstract model interface in ClipScribe

**Action needed:** Research model abstraction patterns

### 4. Architecture for Local Model Replacement

**Current dependencies:**
- Voxtral API (Mistral) - transcription
- Grok API (xAI) - intelligence extraction

**Future vision:**
- Support local models (Llama, Mistral local, etc.)
- Air-gapped deployment option
- Privacy-focused mode

**Design questions:**
- How to abstract transcription provider?
- How to abstract intelligence extraction?
- Configuration-driven model selection?
- Fallback chains (cloud → local)?

**Possible architecture:**
```python
class TranscriptionProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_path): ...

class VoxtralProvider(TranscriptionProvider):
    # API-based

class WhisperXProvider(TranscriptionProvider):
    # GPU-based (Modal)

class OllamaProvider(TranscriptionProvider):
    # Local model

# Select at runtime
provider = config.get_transcription_provider()
transcript = await provider.transcribe(audio)
```

**Action needed:** Design provider abstraction

### 5. Cloud vs Local - Equal Support

**User needs both equally. Implications:**

**Must maintain:**
- Both code paths (can't remove one)
- Both output formats (or unify them)
- Both documented equally
- Both tested equally

**Considerations:**
- Should outputs be identical? (Modal generates GEXF too?)
- Or clearly different products? (Cloud=simple, Local=comprehensive)
- Configuration to control output formats?
- User expectation management?

---

## Architectural Decisions Needed

### Decision 1: Modal Input Modes

**Question:** Should Modal accept local files or only GCS paths?

**Option A: GCS-only (current)**
```python
# Requires manual upload
modal_result = transcriber.transcribe_from_gcs(
    gcs_input="gs://bucket/file.mp3",
    gcs_output="gs://bucket/results/"
)
```

**Option B: Auto-upload mode**
```python
# ClipScribe handles upload
modal_result = transcriber.process_file(
    local_path="video.mp3",
    auto_upload_gcs=True
)
```

**Recommendation:** Support both (A for enterprise, B for convenience)

### Decision 2: Local CLI File-Only

**Question:** Remove URL support entirely?

**Proposal:**
```bash
# REMOVE: clipscribe process video "URL"
# KEEP: clipscribe process "file.mp3"

# Note in docs: "Use yt-dlp to obtain files"
```

**Benefits:**
- Removes 15 files (~5,000 lines)
- No download reliability issues
- Clear focus on intelligence
- Simpler testing

**Trade-offs:**
- Users must obtain files themselves
- Acceptable for professional users

**Recommendation:** Yes, remove URL support from core

### Decision 3: Output Format Strategy

**Question:** Should Modal and Local have same outputs?

**Option A: Unified**
- Modal generates ALL formats (GEXF, CSV, MD, etc.)
- Same directory structure
- Same file names
- Benefits: Consistency, user expectation
- Cost: More Modal code, larger uploads

**Option B: Different by Design**
- Modal: Minimal (transcript.json, metadata.json)
- Local: Comprehensive (10+ formats)
- Benefits: Optimized for use case
- Cost: User confusion, need clear docs

**Option C: Configurable**
- Both support all formats
- User chooses what to generate
- Benefits: Flexibility
- Cost: Complexity

**Recommendation:** Need to investigate what Modal ACTUALLY outputs now

### Decision 4: Download Service

**Question:** What to do with download code?

**Option A: Separate CLI command**
```bash
clipscribe download "URL"  # Simple yt-dlp wrapper
```

**Option B: Completely separate repo/tool**

**Option C: Just documentation**
```markdown
# Getting Files

Use yt-dlp:
```bash
yt-dlp -x --audio-format mp3 "URL"
```
```

**Recommendation:** Option C - Document yt-dlp, don't maintain download code

---

## Research Tasks for Next Session

### Task 1: Voxtral Capabilities Check (30 min)

**Investigate:**
- Does Voxtral support speaker diarization now? (Nov 2025)
- WER comparison vs WhisperX
- Cost: Voxtral ($0.001/min) vs WhisperX ($0.018/min)
- Could we use Voxtral in Modal instead of WhisperX?

**Sources:**
- Mistral AI documentation
- Voxtral API docs
- Recent benchmarks

### Task 2: Modal Output Inspection (20 min)

**Check actual Nov 12 validation outputs:**
```bash
cd output/gcs_results/outputs
ls */  # What files exist?
cat */transcript.json | jq keys  # What's in transcript.json?
cat */metadata.json | jq keys  # What's in metadata.json?
```

**Questions:**
- Does Modal output GEXF files?
- Are CSVs generated?
- Is markdown report included?
- Or just raw JSON?

### Task 3: OpenRouter Research (30 min)

**Investigate:**
- What is OpenRouter exactly?
- Does it support local models (Ollama)?
- Pricing model
- Integration complexity
- Benefits for ClipScribe

**Alternative:**
- LiteLLM
- Direct Ollama integration
- Custom provider abstraction

### Task 4: Provider Abstraction Design (45 min)

**Design pattern:**
```python
# Abstract providers
class TranscriptionProvider(ABC):
    async def transcribe(audio_path) -> TranscriptResult

class IntelligenceProvider(ABC):
    async def extract(transcript) -> Intelligence

# Concrete implementations
VoxtralTranscription, WhisperXTranscription, OllamaTranscription
GrokIntelligence, ClaudeIntelligence, LocalLlamaIntelligence

# Configuration-driven
config:
  transcription: "voxtral"  # or "whisperx", "ollama"
  intelligence: "grok"  # or "claude", "llama-local"
```

**Benefits:**
- Easy to swap providers
- Test with mocks
- Support air-gapped deployments
- Future-proof

### Task 5: Compare Local vs Modal Execution (60 min)

**Test same file through both paths:**
```bash
# Local
clipscribe process "test.mp3" --output-dir local_test/

# Modal (if deployed)
modal run ... --input test.mp3

# Compare:
- Entities extracted (same?)
- Relationships (same?)
- Output files (different?)
- Quality (WhisperX vs Voxtral transcripts)
```

---

## Immediate Next Steps (For Next Session)

**Priority 1: Research & Document**
1. Voxtral vs WhisperX capabilities (definitive answer)
2. Modal actual output formats (check real files)
3. OpenRouter feasibility
4. Design provider abstraction pattern

**Priority 2: Architectural Planning**
1. v3.0.0 scope definition
2. Download removal plan
3. Output format unification strategy
4. Provider abstraction implementation

**Priority 3: Execution**
1. Remove download code
2. Refactor CLI to file-first
3. Implement provider abstractions
4. Reconcile output formats
5. Update all documentation
6. Comprehensive testing

**Estimated:** 2-3 sessions for complete v3.0.0 transformation

---

## Session Handoff Notes

**What works:**
- Modal GPU path (validated, production-ready)
- Local Voxtral transcription (works)
- Local Grok extraction (chunking bug fixed!)

**What's broken:**
- Local CLI chunked extraction HAD bugs (fixed in commit 6f0e4aa)
- YouTube download (403 SABR blocks)

**What's unclear:**
- Voxtral vs WhisperX capabilities (need Nov 2025 research)
- Modal output completeness (need to check GCS uploads)
- Output format reconciliation strategy
- OpenRouter integration approach

**Token usage this session:** 520K (52%)

**Commits today:** 10 (all pushed, all validated)

**Next session should start with:** Deep research on questions above, then comprehensive v3.0.0 architectural planning.

---

**This document provides complete context for continuing the v3.0.0 architectural transformation in a fresh session.**

