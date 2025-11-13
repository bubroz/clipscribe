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

### 1. Voxtral vs WhisperX (Nov 2025) - RESEARCHED

**Speaker Diarization Status (Nov 2025):**
- ❌ **Voxtral does NOT support speaker diarization yet**
- 🔄 Mistral is "working on" speaker ID, emotion detection, advanced diarization
- 📅 "Inviting design partners" - NOT production-ready
- Source: https://mistral.ai/news/voxtral

**Cost comparison:**
- Voxtral: $0.001/min API (transcription only)
- WhisperX: $0.01836/min GPU (Modal A10G, includes diarization)
- WhisperX is 18x more expensive

**Accuracy comparison:**
- Voxtral: Good for transcription, but NO speaker attribution
- WhisperX: large-v3 + pyannote diarization (2-13 speakers)

**VERDICT:**
- ❌ **Cannot replace WhisperX in Modal path** (speaker diarization is critical)
- ✅ **Could use Voxtral for Local path** (if user doesn't need speakers)
- 💡 **Best of both worlds:** Make speaker diarization optional
  - Budget mode: Voxtral only ($0.001/min)
  - Full mode: WhisperX + diarization ($0.018/min)
- 🎯 **18x cost difference IS worth it** when speakers are needed (interviews, podcasts, meetings)

**Recommendation:** Keep WhisperX for Modal, optionally add Voxtral for Local budget mode

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

**Differences found (VALIDATED Nov 13):**
- ✅ Modal: 2 files - `transcript.json` (comprehensive, ALL intelligence) + `metadata.json` (stats)
- ✅ Local: 10+ files - separate txt, json, csv, gexf, graphml, md exports
- ✅ **Modal transcript.json contains:** segments, entities, relationships, topics, key_moments, sentiment, cost_breakdown, cache_stats, word_segments
- ❌ **Modal is missing:** GEXF/GraphML exports, CSV exports, Markdown reports
- ✅ **Local has all formats** including visualization exports

**CRITICAL FINDING:** Modal outputs are NOT incomplete - just a different export strategy!
- **Modal strategy:** Single comprehensive JSON (all data, one file)
- **Local strategy:** Multiple format exports (same data, many formats)

**Intelligence Quality:** SAME (both use Grok-4 extraction, same prompts, same schemas)

**Decision needed:**
1. Should Modal also generate GEXF/CSV/MD exports? (Easy to add)
2. Or is single JSON sufficient for cloud use case? (Simpler, smaller)
3. Could add export formatter that reads transcript.json → generates all formats

### 3. OpenRouter for Model Flexibility - RESEARCHED

**What is OpenRouter:**
- ✅ **Unified API gateway** for 200+ LLMs (OpenAI, Anthropic, Google, Meta, etc.)
- ✅ **Single API key** for all models
- ✅ **Smart routing** with fallbacks
- ❌ **Does NOT support local models** (Ollama, etc.)
- 💵 **Pricing:** Pass-through + small markup

**OpenRouter strengths:**
- Switch between cloud providers easily
- Automatic fallbacks (e.g., Claude → GPT if Claude down)
- Cost comparison across providers
- Good for multi-model experimentation

**OpenRouter weaknesses:**
- ❌ No local model support (requires cloud API)
- ❌ Extra layer = extra latency (~50-100ms)
- ❌ Dependency on third-party service
- ❌ Not useful for air-gapped deployments

**Alternative: LiteLLM**
- ✅ Supports 100+ providers INCLUDING Ollama (local)
- ✅ Can run locally (no third-party dependency)
- ✅ Unified interface: OpenAI format for all models
- ✅ Built-in retry logic, fallbacks, load balancing
- ✅ Better for ClipScribe's needs (local + cloud support)

**VERDICT:**
- ❌ **OpenRouter is NOT the right solution** (no local model support)
- ✅ **LiteLLM is better** (supports both cloud and local)
- 🎯 **Best approach:** Direct provider abstraction (see Task 4)
  - More control, less dependencies
  - Simpler codebase
  - Easier to test and debug

**Recommendation:** Build simple provider abstraction, skip OpenRouter/LiteLLM

### 4. Architecture for Local Model Replacement - DESIGNED

**Current dependencies:**
- Voxtral API (Mistral) - transcription
- Grok API (xAI) - intelligence extraction

**Future vision:**
- ✅ Support local models (Llama, Mistral local, etc.)
- ✅ Air-gapped deployment option
- ✅ Privacy-focused mode

**Provider Abstraction Pattern:**

```python
# src/clipscribe/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel

class TranscriptResult(BaseModel):
    """Standardized transcript output"""
    segments: List[Dict]
    language: str
    duration: float
    speakers: int = 0
    word_level: bool = False
    cost: float = 0.0
    
class IntelligenceResult(BaseModel):
    """Standardized intelligence output"""
    entities: List[Dict]
    relationships: List[Dict]
    topics: List[Dict]
    key_moments: List[Dict]
    sentiment: Dict
    cost: float = 0.0

class TranscriptionProvider(ABC):
    """Base class for all transcription providers"""
    
    @abstractmethod
    async def transcribe(
        self, 
        audio_path: str,
        language: str = None,
        diarize: bool = True
    ) -> TranscriptResult:
        pass
    
    @abstractmethod
    def estimate_cost(self, duration_seconds: float) -> float:
        pass

class IntelligenceProvider(ABC):
    """Base class for intelligence extraction"""
    
    @abstractmethod
    async def extract(
        self, 
        transcript: TranscriptResult,
        metadata: Dict = None
    ) -> IntelligenceResult:
        pass
    
    @abstractmethod
    def estimate_cost(self, transcript_length: int) -> float:
        pass
```

**Concrete Implementations:**

```python
# src/clipscribe/providers/transcription/
class VoxtralProvider(TranscriptionProvider):
    """Mistral Voxtral API (fast, cheap, no speakers)"""
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def transcribe(self, audio_path, language=None, diarize=False):
        # Voxtral doesn't support diarization yet
        if diarize:
            raise NotImplementedError("Voxtral doesn't support speaker diarization")
        # Call Voxtral API
        return TranscriptResult(...)
    
    def estimate_cost(self, duration_seconds):
        return (duration_seconds / 60) * 0.001  # $0.001/min

class WhisperXModalProvider(TranscriptionProvider):
    """WhisperX on Modal GPU (slower, expensive, best quality + speakers)"""
    async def transcribe(self, audio_path, language=None, diarize=True):
        # Upload to GCS, call Modal
        return TranscriptResult(...)
    
    def estimate_cost(self, duration_seconds):
        # GPU cost + network cost
        return (duration_seconds / 60 / 6) * 0.01836  # 6x realtime, $0.01836/min

class WhisperLocalProvider(TranscriptionProvider):
    """Local Whisper (free, slow, good quality, optional speakers)"""
    async def transcribe(self, audio_path, language=None, diarize=False):
        # Run locally with whisper + pyannote
        return TranscriptResult(...)
    
    def estimate_cost(self, duration_seconds):
        return 0.0  # Free

# src/clipscribe/providers/intelligence/
class GrokProvider(IntelligenceProvider):
    """xAI Grok (best quality, moderate cost)"""
    async def extract(self, transcript, metadata=None):
        # Current implementation
        return IntelligenceResult(...)
    
    def estimate_cost(self, transcript_length):
        tokens = transcript_length / 4
        return (tokens / 1_000_000) * 0.20  # $0.20/M input

class OllamaProvider(IntelligenceProvider):
    """Local Llama/Mistral via Ollama (free, privacy, slower)"""
    async def extract(self, transcript, metadata=None):
        # Call Ollama API
        return IntelligenceResult(...)
    
    def estimate_cost(self, transcript_length):
        return 0.0  # Free
```

**Configuration-Driven Selection:**

```yaml
# .clipscribe.yaml
transcription:
  provider: "voxtral"  # voxtral | whisperx-modal | whisper-local
  diarization: false   # Enable speaker detection
  language: "auto"     # or specific language code
  
intelligence:
  provider: "grok"     # grok | ollama | claude
  model: "grok-4-fast" # Provider-specific model
  
# Provider configs
providers:
  voxtral:
    api_key_env: "VOXTRAL_API_KEY"
  whisperx_modal:
    api_key_env: "MODAL_API_KEY"
  grok:
    api_key_env: "XAI_API_KEY"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3.2:90b"
```

**Runtime Usage:**

```python
# src/clipscribe/core/processor.py
from clipscribe.providers import get_provider

async def process_audio(audio_path: str):
    # Get providers from config
    transcriber = get_provider('transcription')
    extractor = get_provider('intelligence')
    
    # Process
    transcript = await transcriber.transcribe(audio_path)
    intelligence = await extractor.extract(transcript)
    
    return transcript, intelligence
```

**Benefits:**
- ✅ Easy to swap providers (change config, not code)
- ✅ Test with mocks (swap in TestProvider)
- ✅ Support air-gapped (use local providers)
- ✅ Future-proof (add new providers without changing core)
- ✅ Cost transparency (estimate before processing)

**Recommendation:** Implement provider abstraction in v3.0.0

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

**Next session should start with:** Implementation planning for v3.0.0 based on research findings below.

---

## 🎯 RESEARCH SYNTHESIS & RECOMMENDATIONS

### Research Complete (Nov 13, 2025)

All critical questions answered. Ready for v3.0.0 architectural planning.

### Key Findings Summary

**1. Voxtral vs WhisperX:**
- ❌ Voxtral does NOT support speaker diarization (Nov 2025)
- ✅ WhisperX + pyannote is REQUIRED for speaker attribution
- 💡 Could offer both: Voxtral (budget, no speakers) + WhisperX (full, with speakers)

**2. Modal Output Format:**
- ✅ Modal outputs are COMPREHENSIVE (all intelligence in transcript.json)
- ❌ Modal is missing GEXF/CSV/Markdown exports
- 💡 Easy to add: Export formatter that reads transcript.json → generates all formats

**3. OpenRouter:**
- ❌ Does NOT support local models (cloud-only)
- ✅ LiteLLM is better (supports Ollama + cloud)
- 💡 Best approach: Direct provider abstraction (simpler, more control)

**4. Provider Abstraction:**
- ✅ Design complete (see Task 4 above)
- ✅ Enables swappable transcription & intelligence providers
- ✅ Configuration-driven, easy to test, future-proof

### v3.0.0 Architectural Decisions

#### ✅ Decision 1: Remove Download Code

**APPROVED - Remove video download from ClipScribe core**

**Rationale:**
- Download is NOT core value (intelligence extraction is)
- Removes 15+ files, ~5,000 lines of fragile code
- Eliminates YouTube SABR bans, 403s, bot detection issues
- Professional users can obtain files themselves (yt-dlp)

**Implementation:**
```bash
# REMOVE entire download infrastructure
rm -rf src/clipscribe/retrievers/youtube_client.py
rm -rf src/clipscribe/retrievers/universal_video_client.py
rm -rf src/clipscribe/retrievers/video_retriever.py
# ... (15 files total)

# UPDATE CLI to file-only
clipscribe process "audio.mp3"  # ✅ KEEP
# clipscribe process video "URL"  # ❌ REMOVE

# UPDATE docs
docs/GETTING_FILES.md - "Use yt-dlp to obtain audio files"
```

**User Impact:**
- ❌ Can no longer pass URLs directly
- ✅ Must obtain files first (yt-dlp, download, GCS, etc.)
- ✅ Simpler, more reliable, faster CLI
- ✅ Clear separation: procurement (yt-dlp) vs analysis (ClipScribe)

#### ✅ Decision 2: Provider Abstraction Pattern

**APPROVED - Implement provider abstraction (see Task 4 design)**

**Benefits:**
- Support multiple transcription providers (Voxtral, WhisperX, local Whisper)
- Support multiple intelligence providers (Grok, Ollama, Claude)
- Easy testing (mock providers)
- Air-gapped deployment support
- Future-proof architecture

**Implementation Priority:** HIGH (foundation for v3.0.0)

#### ✅ Decision 3: Unified Output Format Strategy

**APPROVED - Unify outputs across Modal and Local paths**

**Strategy:**
1. **Core data structure:** Use Modal's comprehensive JSON (all intelligence in one file)
2. **Export formatters:** Add formatters that generate GEXF, CSV, Markdown from core JSON
3. **Both paths generate same core data**, different exports

**Implementation:**
```python
# Core processing (same for both Modal and Local)
result = {
    "segments": [...],
    "entities": [...],
    "relationships": [...],
    "topics": [...],
    "key_moments": [...],
    "sentiment": {...},
    "cost_breakdown": {...}
}

# Save core JSON (always)
save_json(result, "transcript.json")

# Generate exports (configurable)
if config.output_formats.gexf:
    generate_gexf(result, "knowledge_graph.gexf")
if config.output_formats.csv:
    generate_csv(result, "entities.csv", "relationships.csv")
if config.output_formats.markdown:
    generate_markdown(result, "report.md")
```

**Benefits:**
- Consistent data structure (easier to work with)
- Modal and Local produce identical intelligence
- User chooses export formats (GEXF for visualization, CSV for analysis, etc.)
- Easy to add new export formats later

#### ✅ Decision 4: Multi-Tier Transcription Options

**APPROVED - Offer budget and full-quality options**

**Tiers:**

1. **Budget Mode** (Voxtral only)
   - Cost: $0.001/min (~$0.03 for 30min)
   - Quality: Good transcription
   - Speakers: NO
   - Use case: Simple transcription, tight budget

2. **Standard Mode** (Voxtral + Grok)
   - Cost: $0.003/min (~$0.09 for 30min)
   - Quality: Good transcription + intelligence
   - Speakers: NO
   - Use case: Entity extraction without speaker attribution

3. **Full Mode** (WhisperX + Grok + Gemini verification)
   - Cost: $0.018/min (~$0.54 for 30min)
   - Quality: Best transcription + intelligence + speaker attribution
   - Speakers: YES (2-13 speakers with Gemini verification)
   - Use case: Interviews, podcasts, meetings

**Configuration:**
```yaml
# .clipscribe.yaml
mode: "full"  # budget | standard | full

# Or explicit provider selection
transcription:
  provider: "whisperx-modal"  # voxtral | whisperx-modal | whisper-local
  diarization: true
```

#### ✅ Decision 5: Modal Input Modes

**APPROVED - Support both GCS-only and auto-upload modes**

**Modes:**

```python
# Mode A: GCS-only (enterprise, large batches)
result = process_from_gcs(
    gcs_input="gs://bucket/file.mp3",
    gcs_output="gs://bucket/results/"
)

# Mode B: Auto-upload (convenience, single files)
result = process_file(
    local_path="audio.mp3",
    auto_upload_gcs=True  # Handles upload/download automatically
)
```

**Implementation:** Mode A exists (production-validated), Mode B is new convenience wrapper

### v3.0.0 Implementation Roadmap

**Phase 1: Foundation (Session 1-2)**
1. ✅ Research complete
2. ⬜ Implement provider abstraction (base classes + VoxtralProvider + GrokProvider)
3. ⬜ Refactor Local CLI to use providers
4. ⬜ Add configuration system (.clipscribe.yaml support)
5. ⬜ Comprehensive tests for provider system

**Phase 2: Download Removal (Session 2-3)**
1. ⬜ Identify all download-dependent code
2. ⬜ Remove download infrastructure (15+ files)
3. ⬜ Refactor CLI to file-only (remove `process video "URL"`)
4. ⬜ Update all documentation
5. ⬜ Validate all examples work with file paths

**Phase 3: Output Unification (Session 3-4)**
1. ⬜ Standardize core data structure (use Modal's JSON structure)
2. ⬜ Implement export formatters (GEXF, CSV, Markdown generators)
3. ⬜ Update Modal to generate all export formats
4. ⬜ Update Local to use same core structure
5. ⬜ Add format selection configuration

**Phase 4: Additional Providers (Session 4-5)**
1. ⬜ Implement WhisperXModalProvider
2. ⬜ Implement WhisperLocalProvider (optional)
3. ⬜ Implement OllamaProvider (optional)
4. ⬜ Add provider auto-detection and fallbacks
5. ⬜ Documentation for all providers

**Phase 5: Polish & Documentation (Session 5-6)**
1. ⬜ Comprehensive testing (all providers, all modes)
2. ⬜ Update all docs (README, CLI_REFERENCE, ARCHITECTURE)
3. ⬜ Migration guide (v2 → v3)
4. ⬜ CHANGELOG for v3.0.0
5. ⬜ Release

**Estimated Timeline:** 5-6 sessions for complete v3.0.0 transformation

**Breaking Changes:**
- ❌ URL input removed (users must provide file paths)
- ⚠️ Configuration format changed (new .clipscribe.yaml)
- ⚠️ Output format standardized (different file structure)
- ✅ Migration guide provided

**Benefits of v3.0.0:**
- ✅ Simpler, more reliable (no download issues)
- ✅ Flexible (swap transcription/intelligence providers)
- ✅ Unified outputs (Modal and Local produce same format)
- ✅ Air-gapped ready (supports local models)
- ✅ Cost transparent (estimate before processing)
- ✅ Future-proof (easy to add new providers)

---

**This document provides complete research context for v3.0.0 architectural transformation. Implementation can begin immediately.**

