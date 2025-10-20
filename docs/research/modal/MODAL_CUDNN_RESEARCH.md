# Modal cuDNN Compatibility Research

**Date:** October 20, 2025  
**Error:** `Unable to load libcudnn_cnn.so.9.1.0` - cuDNN library mismatch  
**Status:** BLOCKING - WhisperX won't run on Modal with current configuration

---

## 🔬 **ROOT CAUSE (Research-Based)**

### **The Error:**
```
Unable to load any of {libcudnn_cnn.so.9.1.0, libcudnn_cnn.so.9.1, libcudnn_cnn.so.9, libcudnn_cnn.so}
Invalid handle. Cannot load symbol cudnnCreateConvolutionDescriptor
Runner aborted on SIGABRT, exit code: 134
```

### **Why This Happens:**

**Current Configuration:**
- WhisperX 3.7.4 requires: `torch~=2.8.0` + `pyannote-audio>=3.3.2,<4.0.0`
- PyTorch 2.8.0 pip package bundles: `nvidia-cudnn-cu12==9.10.2.21`
- pyannote.audio internal components compiled against: cuDNN 9.1

**The Problem:**
- pyannote.audio tries to load `libcudnn_cnn.so.9.1.0`
- PyTorch provides `libcudnn_cnn.so.9.10`
- Binary incompatibility at the cuDNN level
- Cannot load required symbols → crash

---

## 📚 **RESEARCH FINDINGS**

### **From WhisperX Official pyproject.toml:**
```toml
dependencies = [
    "torch~=2.8.0",
    "torchaudio~=2.8.0",
    "pyannote-audio>=3.3.2,<4.0.0",
]

[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu128"
```

WhisperX DOES specify torch 2.8.0 with CUDA 12.8.

### **From WhisperX GitHub Issue #499:**
- pyannote-audio 3.x has had ongoing compatibility issues since 2023
- onnxruntime conflicts between faster-whisper and pyannote-audio
- Performance issues (slow diarization on CPU)
- **Still ongoing as of October 2025**

### **From Modal CUDA Docs:**
- Modal provides: CUDA Driver 12.8 + NVIDIA drivers 575.57.08
- Modal does NOT provide: cuDNN libraries (you must add them)
- Options:
  1. Use `pip_install("torch")` - torch bundles cuDNN via pip
  2. Use `nvidia/cuda:*-devel-*` base image - has cuDNN pre-installed

We're using option #1, but getting cuDNN version conflicts.

---

## 💡 **SOLUTIONS (Research-Based)**

### **Solution A: Use nvidia/cuda Base Image (RECOMMENDED)**

**Why:** Provides complete, compatible cuDNN installation

```python
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.1-cudnn9-runtime-ubuntu22.04",
        add_python="3.11"
    )
    .apt_install("ffmpeg")
    .pip_install(
        "whisperx",
        "pyannote.audio",  # Will use system cuDNN, not bundled
        "google-cloud-storage",
        "httpx",
    )
)
```

**Pros:**
- ✅ Complete cuDNN installation (all .so files)
- ✅ Known working configuration
- ✅ Used by TensorRT-LLM and other complex projects

**Cons:**
- ⚠️ Larger image (~3-4GB vs ~2GB)
- ⚠️ Slower first build (~5-10 min)

---

### **Solution B: Disable Diarization, Transcription Only**

**Why:** WhisperX transcription works fine, just diarization fails

```python
# In load_models():
self.diarize_model = None  # Skip diarization entirely

# Transcription will work without speaker labels
```

**Pros:**
- ✅ Works immediately
- ✅ Proves transcription pipeline
- ✅ Can add diarization later

**Cons:**
- ❌ No speaker labels (major feature loss)
- ❌ Defeats purpose of premium tier

---

### **Solution C: Use Older pyannote-audio 3.1.1**

**Why:** Might have better cuDNN compatibility

```python
image = image.pip_install(
    "whisperx",
    "pyannote.audio==3.1.1",  # Older version
    # ...
)
```

**Risk:** May not work, issue #499 shows problems date back to 2023

---

### **Solution D: Use pyannote-audio 2.1 (Old but Stable)**

**From WhisperX README:**
```python
from whisperx.diarize import DiarizationPipeline

diarize_model = DiarizationPipeline(
    model_name='pyannote/speaker-diarization@2.1',  # Old model
    use_auth_token=token,
    device='cuda'
)
```

**Pros:**
- ✅ Known working configuration
- ✅ No cuDNN issues

**Cons:**
- ❌ Lower quality (older model)
- ❌ Slower (no GPU optimizations of 3.x)

---

## 🎯 **RECOMMENDATION**

### **SHORT TERM (Tonight):**
**Use Solution B: Skip diarization, validate transcription works**

This proves:
- WhisperX transcription works on Modal
- GCS integration works
- Cost/performance is acceptable
- Can add diarization later

**Code change:** 1 line
**Time:** 5 minutes
**Risk:** Zero

---

### **MEDIUM TERM (This Weekend):**
**Use Solution A: nvidia/cuda base image with proper cuDNN**

This enables:
- Full diarization support
- Proper cuDNN installation
- Production-ready

**Code change:** 10 lines (change base image)
**Time:** 1-2 hours (image rebuild + testing)
**Risk:** Low (standard pattern from Modal docs)

---

## 📋 **IMPLEMENTATION PLAN**

### **Step 1: Validate Transcription Works (Tonight - 10 min)**

Disable diarization temporarily:

```python
# In Station10Transcriber.load_models():
self.diarize_model = None  # TODO: Fix cuDNN, enable later
print("✓ WhisperX transcription model loaded (diarization disabled)")
```

Test → Should work → Proves pipeline

---

### **Step 2: Fix cuDNN Properly (Weekend - 2 hours)**

Switch to nvidia/cuda base image:

```python
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.1-cudnn9-runtime-ubuntu22.04",
        add_python="3.11"
    )
    .apt_install("ffmpeg")
    .pip_install(...)
)
```

Test → Should work with diarization → Production ready

---

## 💰 **COST OF THE MISTAKE**

**Time spent on quick fixes:** 2 hours  
**Time proper research would take:** 30 minutes  
**Time wasted:** 1.5 hours

**Lesson:** Research first, implement second.

---

## 🚀 **IMMEDIATE ACTION**

**Option A: Disable diarization now, validate transcription (FAST)**
- 1 line change
- Test in 10 minutes
- Proves Modal works
- Add diarization later

**Option B: Fix cuDNN properly now (THOROUGH)**
- Switch to nvidia/cuda base image
- Rebuild (~10 min)
- Test with diarization
- Takes 1-2 hours total

**Which do you want?**

I recommend A (validate transcription works), then B (add diarization tomorrow).

But your call - I've done the proper research now.

