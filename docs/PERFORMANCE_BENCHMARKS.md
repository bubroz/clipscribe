# Performance Benchmarks (v3.0.0)

**Validated:** November 13, 2025  
**Hardware:** Apple Silicon (M3 Max 64GB)  
**Test Files:** Real audio from test_videos/

---

## Provider Performance

### Voxtral (Mistral API)

**Test:** 7.1min earnings call

| Metric | Value |
|--------|-------|
| Processing Time | ~15 seconds |
| Realtime Factor | 0.35x (API latency) |
| Memory Usage | <500MB |
| CPU Usage | <10% |
| Cost | $0.008 ($0.0071 Voxtral + $0.0010 Grok) |
| Cost/Min | $0.001 |
| Speakers | 0 (not supported) |

**Best for:** Single-speaker, budget-conscious, fast turnaround

---

### WhisperX Local (Apple Silicon CPU)

**Test 1:** 16.3min medical (single-speaker)

| Metric | Value |
|--------|-------|
| Processing Time | 21 minutes |
| Realtime Factor | 1.3x |
| Memory Usage | ~3GB peak |
| CPU Usage | 80-100% (single core) |
| Cost | $0.002 (FREE transcription!) |
| Speakers | 1 detected |
| Entities | 20 |

**Test 2:** 36.2min The View (12-speaker panel)

| Metric | Value |
|--------|-------|
| Processing Time | 48 minutes |
| Realtime Factor | 1.33x |
| Memory Usage | ~3-4GB |
| CPU Usage | 80-100% |
| Cost | $0.003 (FREE transcription!) |
| Speakers | **12 detected** |
| Entities | **45** |

**Best for:** Multi-speaker, privacy, FREE processing

**Device:** CPU mode (MPS not supported by faster-whisper)

---

### WhisperX Modal (A10G Cloud GPU)

**Test:** 30min Palantir interview

| Metric | Value |
|--------|-------|
| Processing Time | 3.7 minutes |
| Realtime Factor | 8.5x |
| GPU | A10G (24GB VRAM) |
| Cost | $0.0575 ($0.0551 GPU + $0.0024 Grok) |
| Cost/Min | $0.0018/min processing |
| Speakers | 2 detected |
| Entities | 17 |
| Latency Overhead | GCS upload/download (~30 sec) |

**Best for:** Cloud processing, professional quality, scalability

---

## Cost Comparison (30min Video)

| Provider | Transcription | Intelligence | Total | Speakers |
|----------|---------------|--------------|-------|----------|
| Voxtral | $0.030 | $0.005 | **$0.035** | ❌ No |
| WhisperX Local | **FREE** | $0.005 | **$0.005** | ✅ Yes (up to 12) |
| WhisperX Modal | $0.054 | $0.005 | **$0.059** | ✅ Yes |

**Winner: WhisperX Local** - FREE transcription, multi-speaker support!

---

## File Format Performance

**MP3:** ✅ All providers (native support)  
**MP4:** ✅ WhisperX Local (transcription works, diarization may fail gracefully)  
**WAV, M4A, WEBM:** ⏳ Not yet tested (likely work with WhisperX)

---

## Scalability

**WhisperX Local:**
- Single file at a time
- CPU-bound (one core)
- Sequential processing

**WhisperX Modal:**
- Parallel processing (multiple GPUs)
- Serverless scaling
- Batch processing support

**For 10 files (30min each):**
- Local: ~6 hours sequential
- Modal: ~40 minutes parallel (15 GPUs)

