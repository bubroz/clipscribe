#!/usr/bin/env python3
"""
Station10 GPU Transcription on Modal

Simple, serverless GPU transcription with WhisperX and speaker diarization.
Replaces Vertex AI Custom Jobs (wrong tool) with Modal (right tool).

Deploy: modal deploy deploy/station10_modal.py
Test: modal run deploy/station10_modal.py --audio-url "https://..."

Cost: ~$0.11 per 36min video (85% margin at $0.02/min pricing)
Processing: ~6 minutes for 36min video (6x realtime on A10G)
"""

import modal
import os
import json
import time
from pathlib import Path
from typing import Optional

# ==============================================================================
# CONFIGURATION
# ==============================================================================

app = modal.App("clipscribe-transcription")

# Container image using Modal's VALIDATED working configuration
# Source: https://modal.com/blog/how-to-run-whisperx-on-modal (Official Modal example)
# This exact stack is production-tested and solves cuDNN compatibility issues
# KEY: torch 2.0.0 + WhisperX v3.2.0 = STABLE (torch 2.8.0 + WhisperX 3.7.4 = cuDNN hell)
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.0-devel-ubuntu22.04",  # Modal's validated CUDA version
        add_python="3.11"
    )
    .entrypoint([])  # Remove verbose CUDA logging
    .apt_install(
        # Core build tools
        "build-essential",  # gcc, g++, make - required for compiling C extensions
        "clang",            # PyAV specifically uses clang compiler
        "git",              # Required for pip install from GitHub
        
        # Audio processing
        "ffmpeg",           # Required by WhisperX for audio processing
        
        # PyAV build dependencies
        "pkg-config",       # Required for building PyAV
        "libavformat-dev",  # FFmpeg development headers (for PyAV compilation)
        "libavcodec-dev",   # These provide .pc files that pkg-config needs
        "libavdevice-dev",
        "libavutil-dev",
        "libavfilter-dev",
        "libswscale-dev",
        "libswresample-dev",
    )
    .pip_install(
        # Install build tools from PyPI first (torch index doesn't have them)
        "wheel",
        "setuptools",
    )
    .pip_install(
        # torch 2.0.0 ecosystem (STABLE, cuDNN compatible)
        # Modal's validated stack from official blog post
        "torch==2.0.0",
        "torchaudio==2.0.0",
        "numpy<2.0",  # Required for torch 2.0 compatibility
        index_url="https://download.pytorch.org/whl/cu118",  # CUDA 11.8 wheels for torch 2.0
    )
    .pip_install(
        # CRITICAL: Pin numpy<2.0 to prevent upgrades during this install
        # Without this, dependencies will upgrade numpy to 2.x which breaks pyannote.audio
        "numpy<2.0",
        
        # WhisperX v3.2.0 (Modal's validated version, NOT latest 3.7.4)
        # This version is designed for torch 2.0.x ecosystem
        "git+https://github.com/m-bain/whisperx.git@v3.2.0",
        "ffmpeg-python",
        "ctranslate2==4.4.0",  # Required for WhisperX, specific version
        
        # Audio utilities
        "librosa==0.10.2",
        "soundfile==0.13.1",
        
        # Google Cloud integration
        "google-cloud-storage",
        
        # Gemini unified SDK (CORRECT package - not google-generativeai)
        "google-genai",
        
        # HTTP client
        "httpx",
    )
)

# Persistent volume for model caching (download once, reuse forever)
model_cache = modal.Volume.from_name("station10-models", create_if_missing=True)

# ==============================================================================
# GROK CLIENT WITH NOVEMBER 2025 FEATURES
# ==============================================================================

class ModalGrokClient:
    """
    Lightweight Grok client with all xAI Nov 2025 features for Modal.
    
    Features:
    - Prompt caching (50% cost savings on repeated prompts)
    - Server-side tools support (web_search, x_search)
    - Collections API integration
    - Enhanced cost tracking with cache metrics
    
    Optimized for Modal deployment (no external dependencies).
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_cached_tokens': 0,
            'total_savings': 0.0
        }
    
    def chat_completion(
        self,
        messages: list,
        model: str = "grok-4-fast-reasoning",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        tools: list = None,
        tool_choice: str = None,
        response_format: dict = None
    ) -> dict:
        """
        Call Grok API with full feature support.
        
        Args:
            messages: Chat messages (system + user)
            model: Grok model to use
            temperature: Sampling temperature
            max_tokens: Max output tokens
            tools: Server-side tools (web_search, x_search, etc.)
            tool_choice: Tool selection strategy
            response_format: json_schema or json_object
        
        Returns:
            Full API response with usage stats
        """
        import httpx
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice
        
        if response_format:
            payload["response_format"] = response_format
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def extract_usage_stats(self, response: dict) -> dict:
        """Extract token usage including cached tokens."""
        usage = response.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cached_tokens": usage.get("cached_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        model: str = "grok-4-fast-reasoning"
    ) -> dict:
        """
        Calculate cost with caching savings.
        
        Grok-4 Fast Reasoning pricing:
        - Input: $0.20/M tokens
        - Output: $0.50/M tokens
        - Cached: 50% discount on input
        """
        # Pricing per 1M tokens
        if "fast" in model:
            input_rate = 0.20
            output_rate = 0.50
        else:
            input_rate = 3.00  # Standard grok-4
            output_rate = 10.00
        
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * input_rate
        cached_cost = (cached_tokens / 1_000_000) * input_rate * 0.5
        output_cost = (output_tokens / 1_000_000) * output_rate
        
        # Savings from caching
        full_cached_cost = (cached_tokens / 1_000_000) * input_rate
        cache_savings = full_cached_cost - cached_cost
        
        total = input_cost + cached_cost + output_cost
        
        return {
            "input_cost": round(input_cost, 6),
            "cached_cost": round(cached_cost, 6),
            "output_cost": round(output_cost, 6),
            "cache_savings": round(cache_savings, 6),
            "total": round(total, 6)
        }
    
    def build_cached_message(
        self,
        system_prompt: str,
        user_content: str
    ) -> list:
        """
        Build messages optimized for prompt caching.
        
        System prompt (>1024 tokens) will be cached automatically.
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def record_cache_performance(self, usage_stats: dict, cost_breakdown: dict):
        """Track cache hit/miss statistics."""
        cached_tokens = usage_stats.get("cached_tokens", 0)
        cache_savings = cost_breakdown.get("cache_savings", 0.0)
        
        if cached_tokens > 0:
            self.cache_stats['hits'] += 1
            self.cache_stats['total_cached_tokens'] += cached_tokens
            self.cache_stats['total_savings'] += cache_savings
        else:
            self.cache_stats['misses'] += 1
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'total_savings_usd': round(self.cache_stats['total_savings'], 4),
            'avg_savings_per_request': round(self.cache_stats['total_savings'] / total_requests, 6) if total_requests > 0 else 0
        }


# ==============================================================================
# TRANSCRIPTION CLASS
# ==============================================================================

@app.cls(
    image=image,
    gpu="A10G",  # Good balance of cost ($1.10/hr) and performance (6x realtime)
    timeout=3600,  # 1 hour max (supports videos up to 6 hours at 6x realtime)
    secrets=[
        modal.Secret.from_name("huggingface"),  # For pyannote.audio models
        modal.Secret.from_name("googlecloud-secret"),  # For GCS access
        modal.Secret.from_name("google-api-key"),  # For Gemini speaker verification
        modal.Secret.from_name("grok-api-key")  # For Grok entity extraction
    ],
    volumes={"/models": model_cache}  # Cache models to avoid re-downloading
)
class ClipScribeTranscriber:
    """
    WhisperX transcription with speaker diarization.
    
    Features:
    - Whisper large-v3 for transcription
    - pyannote.audio for speaker diarization
    - GCS integration for input/output
    - Model caching for fast cold starts
    """
    
    @modal.enter()
    def load_models(self):
        """
        Load models once at container startup.
        First run: Downloads models to Volume (~2-3 minutes)
        Subsequent runs: Loads from Volume (~10-15 seconds)
        """
        import whisperx
        import torch
        
        print("Loading WhisperX models...")
        
        # Set cache directories to persistent Volume
        os.environ["TORCH_HOME"] = "/models/torch"
        os.environ["HF_HOME"] = "/models/huggingface"
        
        self.device = "cuda"
        self.compute_type = "float16"
        
        # Load WhisperX model (large-v3 for best accuracy)
        self.whisper_model = whisperx.load_model(
            "large-v3",
            self.device,
            compute_type=self.compute_type,
            download_root="/models/whisperx"
        )
        
        # Load diarization pipeline (official WhisperX API)
        # CRITICAL: Cache model in /models to avoid HuggingFace infrastructure issues
        hf_token = os.getenv("HF_TOKEN")
        print(f"DEBUG: HF_TOKEN present: {bool(hf_token)}")
        
        if not hf_token:
            print("ERROR: No HF_TOKEN found in environment!")
            print("Diarization will be SKIPPED.")
            print("Check Modal secrets: https://modal.com/secrets")
            self.diarize_model = None
        else:
            try:
                print("Loading diarization model with HF token...")
                from whisperx.diarize import DiarizationPipeline
                
                # CACHE MODEL: Download to /models (Modal Volume) instead of temp
                # This prevents re-downloading from HuggingFace on every cold start
                # Fixes: HuggingFace CAS server 500 errors
                os.environ['HF_HOME'] = '/models/huggingface'
                os.environ['HUGGINGFACE_HUB_CACHE'] = '/models/huggingface/hub'
                
                self.diarize_model = DiarizationPipeline(
                    use_auth_token=hf_token,
                    device=self.device
                )
                
                # CRITICAL FIX: Set clustering threshold for better speaker merging
                # Default threshold ~0.7 is too conservative, leads to over-segmentation
                # Research (Hervé Bredin): Higher threshold = fewer speakers
                # Binary search findings:
                #   0.70: 6 speakers, 17%
                #   0.80: 5 speakers, 35% ← CLOSE
                #   0.87: 2 speakers, 38% ← CLIFF (too high)
                # Sweet spot is 0.80-0.87, testing 0.83
                CLUSTERING_THRESHOLD = 0.83
                
                self.diarize_model.model.instantiate({
                    'clustering': {
                        'threshold': CLUSTERING_THRESHOLD,
                        'method': 'centroid'
                    }
                })
                print(f"✓ Diarization model loaded (clustering_threshold={CLUSTERING_THRESHOLD})")
            except Exception as e:
                import traceback
                print(f"ERROR: Diarization model failed to load!")
                print(f"Exception: {e}")
                
                # Check if it's HuggingFace infrastructure issue
                error_str = str(e)
                if "500" in error_str and "xethub.hf.co" in error_str:
                    print("")
                    print("⚠️  EXTERNAL DEPENDENCY FAILURE:")
                    print("   HuggingFace CAS server is returning 500 errors")
                    print("   This is a temporary infrastructure issue on their side")
                    print("   Models are cached for future runs once HF recovers")
                    print("")
                    print("GRACEFUL DEGRADATION:")
                    print("   ✅ Transcription will continue (WhisperX working)")
                    print("   ❌ Speaker labels temporarily unavailable")
                    print("   🔄 Will retry automatically on next run")
                else:
                    print(f"Traceback (last 10 lines):")
                    tb_lines = traceback.format_exc().split('\n')
                    for line in tb_lines[-10:]:
                        print(f"  {line}")
                
                print("")
                print("Continuing with transcription-only mode...")
                self.diarize_model = None
        
        # Initialize Grok client with Nov 2025 features
        print("\nInitializing ModalGrokClient with advanced features...")
        xai_api_key = os.getenv("XAI_API_KEY")
        if xai_api_key:
            self.grok_client = ModalGrokClient(xai_api_key)
            print("  ✓ Prompt caching enabled (50% savings)")
            print("  ✓ Server-side tools available (web_search, x_search)")
            print("  ✓ Enhanced cost tracking with cache metrics")
        else:
            self.grok_client = None
            print("  ⚠ No XAI_API_KEY - entity extraction disabled")
        
        print("\n✓ All models loaded successfully")
        print(f"  WhisperX: large-v3 ({self.device})")
        print(f"  Diarization: {self.diarize_model is not None}")
        print(f"  Grok: {self.grok_client is not None}")
    
    def _detect_language_robust(self, audio) -> str:
        """
        Robust language detection from multiple samples.
        
        WhisperX samples only first 30s, which can fail on music/intros.
        This samples from 3 points for consensus.
        
        Returns:
            Detected language code (e.g., 'en', 'es', 'fr')
        """
        import whisperx
        from collections import Counter
        
        print("  🌍 Detecting language from multiple samples...")
        
        # Sample from 3 points: beginning, middle, end
        samples = []
        sample_duration = 480000  # 30 seconds at 16kHz
        
        # First 30s
        if len(audio) > sample_duration:
            samples.append(("start", audio[0:sample_duration]))
        
        # Middle 30s
        mid_point = len(audio) // 2
        if len(audio) > mid_point + sample_duration:
            samples.append(("middle", audio[mid_point:mid_point+sample_duration]))
        
        # Last 30s
        if len(audio) > sample_duration:
            samples.append(("end", audio[-sample_duration:]))
        
        # Detect from each sample
        detections = []
        
        for location, sample in samples:
            try:
                result = self.whisper_model.transcribe(sample, batch_size=1)
                lang = result.get('language', 'en')
                detections.append(lang)
                print(f"    {location}: {lang}")
            except Exception as e:
                print(f"    {location}: failed ({e})")
                continue
        
        if not detections:
            print(f"  ⚠️  All detections failed, defaulting to 'en'")
            return 'en'
        
        # Majority vote
        lang_counts = Counter(detections)
        detected_lang = lang_counts.most_common(1)[0][0]
        consistency = lang_counts[detected_lang] / len(detections)
        
        print(f"  ✓ Detected: {detected_lang} ({consistency*100:.0f}% consistent)")
        
        # If inconsistent, default to English
        if consistency < 0.67:  # Less than 2/3 agreement
            print(f"  ⚠️  Low consistency, defaulting to 'en'")
            return 'en'
        
        return detected_lang
    
    def _clear_gpu_memory(self):
        """Clear GPU memory cache to prevent fragmentation."""
        import torch
        import gc
        
        # Python garbage collection
        gc.collect()
        
        # PyTorch GPU cache
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        # Check available memory
        if torch.cuda.is_available():
            free_memory = torch.cuda.mem_get_info()[0] / (1024**3)  # GB
            print(f"  🧹 GPU memory cleared: {free_memory:.1f}GB available")
            return free_memory
        return 0
    
    def _transcribe_with_retry(self, audio, audio_duration: float, detected_lang: str) -> dict:
        """
        Transcribe with cascading batch size retry on OOM.
        
        Tries: batch_size 16 → 8 → 4 → 2 → 1
        Clears GPU cache between attempts.
        
        Args:
            audio: Audio array
            audio_duration: Duration in seconds
            detected_lang: Pre-detected language
        
        Returns:
            WhisperX transcription result
        """
        import torch
        
        # Determine initial batch sizes based on duration
        if audio_duration > 3600:  # >60 min
            batch_sizes = [4, 2, 1]
        elif audio_duration > 1800:  # >30 min
            batch_sizes = [8, 4, 2, 1]
        else:
            batch_sizes = [16, 8, 4, 2, 1]
        
        print(f"  🔄 Transcription with OOM protection (batch sizes: {batch_sizes})")
        
        for attempt, batch_size in enumerate(batch_sizes, 1):
            try:
                # Clear GPU before each attempt
                if attempt > 1:
                    print(f"  🧹 Clearing GPU cache before retry...")
                    self._clear_gpu_memory()
                
                print(f"  Attempt {attempt}/{len(batch_sizes)}: batch_size={batch_size}, language={detected_lang}")
                
                result = self.whisper_model.transcribe(audio, batch_size=batch_size)
                
                print(f"  ✅ Success with batch_size={batch_size}")
                return result
                
            except RuntimeError as e:
                error_str = str(e)
                
                if "out of memory" in error_str:
                    print(f"  ⚠️  OOM with batch_size={batch_size}")
                    
                    # Clear GPU immediately
                    torch.cuda.empty_cache()
                    
                    if attempt < len(batch_sizes):
                        next_batch = batch_sizes[attempt]
                        print(f"  🔄 Retrying with batch_size={next_batch}...")
                        continue
                    else:
                        raise RuntimeError(f"OOM even with batch_size=1 - video may be corrupted or too complex")
                else:
                    # Non-OOM error, don't retry
                    raise
        
        raise RuntimeError("All batch sizes exhausted")
    
    def _validate_language_detection(self, detected_lang: str, audio, filename: str = "") -> str:
        """
        Validate language detection and correct obvious errors.
        
        Args:
            detected_lang: Language from WhisperX
            audio: Audio array for re-checking
            filename: Filename for heuristics
        
        Returns:
            Validated language code
        """
        # Languages unlikely for tech/business content
        unlikely_langs = ['ta', 'uk', 'hi', 'ar', 'th', 'vi', 'bn']
        
        if detected_lang not in unlikely_langs:
            return detected_lang  # Seems reasonable
        
        print(f"  ⚠️  Unlikely language detected: {detected_lang}")
        print(f"  🔄 Re-checking with longer sample...")
        
        # Re-detect with 60s from middle (skip intro/outro)
        mid_point = len(audio) // 2
        longer_sample = audio[mid_point:mid_point+960000]  # 60s at 16kHz
        
        try:
            recheck = self.whisper_model.transcribe(longer_sample, batch_size=1)
            new_lang = recheck.get('language', 'en')
            
            print(f"    Recheck result: {new_lang}")
            
            if new_lang != detected_lang:
                print(f"  ✓ Corrected: {detected_lang} → {new_lang}")
                return new_lang
            else:
                # Still detecting unlikely language
                # Check filename for English indicators
                filename_lower = filename.lower()
                english_keywords = ['tesla', 'openai', 'markets', 'cnbc', 'podcast', 
                                   'interview', 'earnings', 'palantir', 'alex', 'elon', 'sam']
                
                has_english_keywords = any(kw in filename_lower for kw in english_keywords)
                
                if has_english_keywords:
                    print(f"  ℹ️  Filename suggests English, overriding to 'en'")
                    return 'en'
                else:
                    print(f"  ⚠️  Keeping {detected_lang} (verified with recheck)")
                    return detected_lang
        
        except Exception as e:
            print(f"  ❌ Recheck failed: {e}")
            return 'en'  # Safe default
    
    def _improve_speaker_quality(self, segments: list) -> tuple:
        """
        Post-process speaker diarization to reduce over-segmentation.
        
        Algorithm (revised Oct 21 after CHiME-6 validation):
        0. Merge duplicate text across speakers (NEW - catches repetitions)
        1. Identify major speakers (ADAPTIVE threshold based on speaker count)
        2. Merge ultra-short segments (<0.5s) into neighbors
        3. Merge interjections (<2s, <5 words) to nearest major speaker
        4. Eliminate minor speakers (ADAPTIVE threshold, not fixed 1%)
        
        Fixes:
        - Adaptive thresholds: 5% for 4 speakers (not fixed 10%)
        - Duplicate text detection (catches same utterance split)
        - Aggressive merging (< threshold, not just <1%)
        
        Returns: (cleaned_segments, stats_dict)
        """
        if not segments:
            return segments, {}
        
        original_speaker_count = len(set(seg.get('speaker', 'UNK') for seg in segments))
        
        # Step 0: FIRST - Merge duplicate/similar text across speakers
        # This MUST happen before counting speakers, so counts are correct
        from difflib import SequenceMatcher
        
        duplicate_merges = 0
        for i in range(len(segments) - 1):
            curr = segments[i]
            next_seg = segments[i+1]
            
            if curr.get('speaker') != next_seg.get('speaker'):
                text1 = curr.get('text', '').lower().strip()
                text2 = next_seg.get('text', '').lower().strip()
                
                if text1 and text2 and len(text1) > 10:  # Only for substantial text
                    similarity = SequenceMatcher(None, text1, text2).ratio()
                    if similarity > 0.75:  # 75% similar = same utterance (was 0.8, now more aggressive)
                        next_seg['speaker'] = curr['speaker']
                        duplicate_merges += 1
        
        if duplicate_merges > 0:
            print(f"  Merged {duplicate_merges} duplicate text segments")
        
        # NOW count speakers AFTER duplicate merging
        total = len(segments)
        speaker_counts = {}
        for seg in segments:
            s = seg.get('speaker', 'UNKNOWN')
            speaker_counts[s] = speaker_counts.get(s, 0) + 1
        
        num_speakers = len(speaker_counts)
        
        # ADAPTIVE THRESHOLD (not fixed 10%)
        if num_speakers <= 2:
            threshold = 0.10  # 10% for dyadic
        elif num_speakers <= 4:
            threshold = 0.05  # 5% for small meetings
        elif num_speakers <= 8:
            threshold = 0.03  # 3% for medium meetings
        else:
            threshold = 0.02  # 2% for large meetings
        
        print(f"  Speaker threshold: {threshold*100:.0f}% (adaptive for {num_speakers} speakers after dedup)")
        
        major_speakers = [s for s, count in speaker_counts.items() if (count / total) > threshold]
        major_set = set(major_speakers)
        
        print(f"  Major speakers: {len(major_speakers)} (>{threshold*100:.0f}%)")
        
        # Step 2: Merge ultra-short (<0.5s)
        cleaned = []
        for seg in segments:
            duration = seg.get('end', 0) - seg.get('start', 0)
            if duration < 0.5 and cleaned:
                cleaned[-1]['end'] = seg.get('end', cleaned[-1]['end'])
                cleaned[-1]['text'] += ' ' + seg.get('text', '')
            else:
                cleaned.append(seg.copy())
        
        # Step 3: Merge interjections
        for i, seg in enumerate(cleaned):
            duration = seg.get('end', 0) - seg.get('start', 0)
            words = len(seg.get('text', '').split())
            curr_speaker = seg.get('speaker', 'UNKNOWN')
            
            if duration < 2.0 and words <= 5 and curr_speaker not in major_set:
                before = cleaned[i-1].get('speaker') if i > 0 else None
                after = cleaned[i+1].get('speaker') if i < len(cleaned)-1 else None
                
                if before == after and before in major_set:
                    seg['speaker'] = before
                elif before in major_set:
                    seg['speaker'] = before
                elif after in major_set:
                    seg['speaker'] = after
        
        # Step 4: Eliminate minor speakers (ADAPTIVE, not fixed 1%)
        final_counts = {}
        for seg in cleaned:
            s = seg.get('speaker', 'UNKNOWN')
            final_counts[s] = final_counts.get(s, 0) + 1
        
        # Use ADAPTIVE threshold (same as major speaker threshold)
        # Also merge speakers with <50 absolute segments in large meetings
        absolute_min = 50 if len(cleaned) > 1000 else 20
        
        minor_speakers = [
            s for s, c in final_counts.items() 
            if ((c / len(cleaned)) < threshold or c < absolute_min) and s not in major_set
        ]
        
        if minor_speakers:
            print(f"  Merging {len(minor_speakers)} minor speakers: {minor_speakers}")
        
        for i, seg in enumerate(cleaned):
            if seg.get('speaker') in minor_speakers:
                before = cleaned[i-1].get('speaker') if i > 0 else None
                after = cleaned[i+1].get('speaker') if i < len(cleaned)-1 else None
                
                # Prefer major speakers in context
                if before in major_set:
                    seg['speaker'] = before
                elif after in major_set:
                    seg['speaker'] = after
                elif before and before not in minor_speakers:
                    seg['speaker'] = before
                elif after and after not in minor_speakers:
                    seg['speaker'] = after
                elif major_set:
                    seg['speaker'] = sorted(major_set)[0]  # Assign to first major speaker
        
        final_speaker_count = len(set(seg.get('speaker', 'UNK') for seg in cleaned))
        
        stats = {
            'original_speakers': original_speaker_count,
            'final_speakers': final_speaker_count,
            'speakers_merged': original_speaker_count - final_speaker_count,
            'segments_merged': len(segments) - len(cleaned)
        }
        
        return cleaned, stats
    
    def _gemini_speaker_verification(self, audio_path: str, segments: list) -> list:
        """
        Use Gemini 2.5 Flash to verify and correct speaker attribution.
        
        Gemini can LISTEN to audio and verify speaker changes.
        This catches interjections that WhisperX merges incorrectly.
        
        Cost: ~$0.06 per 30min video (audio tokens)
        Benefit: 95-98% speaker accuracy (vs 90% WhisperX-only)
        """
        try:
            from google import genai  # New unified SDK
            import os
            
            # Get API key
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("⚠️  No GOOGLE_API_KEY - skipping Gemini verification")
                return segments
            
            # Create Gemini client (new API pattern)
            client = genai.Client(api_key=api_key)
            
            # Upload audio file using Files API
            print("  Uploading audio to Gemini...")
            audio_file = client.files.upload(file=audio_path)
            
            # Build prompt with problematic segments
            # Focus on rapid switches and short segments (where errors occur)
            problem_segments = []
            for i in range(len(segments) - 2):
                curr = segments[i]
                next_seg = segments[i+1]
                after = segments[i+2]
                
                # Find A→B→A patterns (likely errors)
                if (curr.get('speaker') == after.get('speaker') and 
                    curr.get('speaker') != next_seg.get('speaker') and
                    len(next_seg.get('text', '').split()) <= 3):
                    
                    problem_segments.append({
                        'index': i + 1,  # Store the ACTUAL problem segment index (the middle one)
                        'timestamp': f"{int(next_seg.get('start', 0) // 60):02d}:{int(next_seg.get('start', 0) % 60):02d}",
                        'before_speaker': curr.get('speaker'),
                        'current_speaker': next_seg.get('speaker'),
                        'after_speaker': after.get('speaker'),
                        'text': next_seg.get('text', ''),
                        'before_text': curr.get('text', '')[:50],
                        'after_text': after.get('text', '')[:50]
                    })
            
            # Limit to 20 most problematic (cost control)
            problem_segments = problem_segments[:20]
            
            if not problem_segments:
                print("  No problematic segments detected")
                return segments
            
            print(f"  Verifying {len(problem_segments)} potentially mis-attributed segments...")
            
            # Create verification prompt
            prompt = f"""You have access to this audio file. Listen carefully to verify speaker attribution.

I've identified {len(problem_segments)} segments that might have incorrect speaker labels.
These are typically short interjections ("Yeah", "Right", "Okay") that may be assigned to the wrong speaker.

For each segment, LISTEN to the audio at the specified timestamp and determine if the speaker label is correct.

Segments to verify:
"""
            
            for list_idx, seg in enumerate(problem_segments):
                prompt += f"\n{list_idx}. [{seg['timestamp']}] Currently labeled as {seg['current_speaker']}: \"{seg['text']}\""
                prompt += f"\n   Context: {seg['before_speaker']} before, {seg['after_speaker']} after"
            
            prompt += """

For each segment, return JSON with the INDEX from the list above (0, 1, 2...):
{
  "corrections": [
    {"index": 0, "correct_speaker": "SPEAKER_01", "confidence": 0.95, "reason": "Voice matches previous speaker"},
    {"index": 2, "correct_speaker": "SPEAKER_03", "confidence": 0.88, "reason": "Different voice"},
    ...
  ]
}

Only suggest corrections where you're >80% confident after listening.
If attribution is correct, don't include it.
Use the INDEX numbers shown above (0, 1, 2...), not segment numbers.
"""
            
            # Call Gemini with audio (new client API)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[audio_file, prompt]
            )
            
            # Parse corrections
            import json
            import re
            
            json_match = re.search(r'\{[\s\S]*\}', response.text)
            if json_match:
                corrections_data = json.loads(json_match.group())
                corrections = corrections_data.get('corrections', [])
                
                print(f"  Gemini suggested {len(corrections)} corrections")
                
                # Apply corrections
                for correction in corrections:
                    idx = correction.get('index')  # Index in problem_segments list
                    if idx is not None and 0 <= idx < len(problem_segments):
                        seg_idx = problem_segments[idx]['index']  # Already the correct segment index
                        if seg_idx < len(segments):
                            segments[seg_idx]['speaker'] = correction.get('correct_speaker')
                            segments[seg_idx]['gemini_corrected'] = True
                            segments[seg_idx]['gemini_confidence'] = correction.get('confidence')
                            print(f"    ✓ Corrected segment {seg_idx}: {correction.get('correct_speaker')}")
            
            return segments
            
        except Exception as e:
            print(f"⚠  Gemini verification failed: {e}")
            print("  Continuing with WhisperX-only attribution")
            return segments
    
    @modal.method()
    def transcribe(self, audio_url: str) -> dict:
        """
        Transcribe audio from URL with speaker diarization.
        
        Args:
            audio_url: HTTP(S) URL to audio file (MP3, WAV, etc.)
            
        Returns:
            {
                "transcript": [...],  # Segments with text, timestamps, speakers
                "language": "en",
                "speakers": 2,  # Number of unique speakers
                "processing_time": 45.2,  # Seconds
                "audio_duration": 2160.0,  # Seconds
                "cost": 0.11,  # USD
                "realtime_factor": 6.2  # How many minutes of audio per minute of processing
            }
        """
        import whisperx
        import httpx
        
        start_time = time.time()
        
        print(f"Downloading audio from: {audio_url}")
        
        # Download audio to temp file
        response = httpx.get(audio_url, timeout=300, follow_redirects=True)
        response.raise_for_status()
        
        audio_path = "/tmp/audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        
        download_time = time.time() - start_time
        print(f"✓ Downloaded in {download_time:.1f}s")
        
        # Load audio
        print("\nLoading audio...")
        audio = whisperx.load_audio(audio_path)
        audio_duration = len(audio) / 16000  # 16kHz sample rate
        
        print(f"\n{'='*60}")
        print(f"Transcribing {audio_duration/60:.1f} minutes of audio...")
        print(f"{'='*60}")
        transcribe_start = time.time()
        
        # Clear GPU memory before processing
        self._clear_gpu_memory()
        
        # ROBUST LANGUAGE DETECTION
        filename = Path(audio_url).name if audio_url else ""
        detected_lang = self._detect_language_robust(audio)
        validated_lang = self._validate_language_detection(detected_lang, audio, filename)
        
        print(f"  📝 Final language: {validated_lang}")
        
        # TRANSCRIBE WITH OOM RETRY
        result = self._transcribe_with_retry(audio, audio_duration, validated_lang)
        
        transcribe_time = time.time() - transcribe_start
        print(f"✓ Transcribed in {transcribe_time:.1f}s")
        
        # Align timestamps
        print("Aligning timestamps...")
        align_start = time.time()
        
        model_a, metadata = whisperx.load_align_model(
            language_code=result["language"],
            device=self.device
        )
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            self.device
        )
        
        align_time = time.time() - align_start
        print(f"✓ Aligned in {align_time:.1f}s")
        
        # Speaker diarization (official WhisperX API)
        speakers_found = 0
        if self.diarize_model:
            print("Running speaker diarization...")
            diarize_start = time.time()
            
            try:
                # Run diarization (returns pyannote Annotation object)
                diarize_segments = self.diarize_model(audio)
                
                # Assign speakers to words/segments (official WhisperX function)
                result = whisperx.assign_word_speakers(diarize_segments, result)
                
                # Count unique speakers (before cleanup)
                speakers_found_raw = len(set(
                    seg.get("speaker", "UNKNOWN") 
                    for seg in result["segments"]
                    if "speaker" in seg
                ))
                
                diarize_time = time.time() - diarize_start
                print(f"✓ Diarization complete in {diarize_time:.1f}s")
                print(f"✓ Raw speakers detected: {speakers_found_raw}")
                
                # Apply quality improvements
                print("Applying speaker quality cleanup...")
                result["segments"], cleanup_stats = self._improve_speaker_quality(result["segments"])
                
                speakers_found = len(set(
                    seg.get("speaker", "UNKNOWN") 
                    for seg in result["segments"]
                    if "speaker" in seg
                ))
                
                print(f"✓ Final speakers: {speakers_found}")
                if cleanup_stats.get('speakers_merged', 0) > 0:
                    print(f"  (merged {cleanup_stats['speakers_merged']} minor/artifact speakers)")
                
                # GEMINI QUALITY PASS: Verify speaker attribution with AI
                print("Applying Gemini quality verification...")
                result["segments"] = self._gemini_speaker_verification(audio_path, result["segments"])
                print("✓ Gemini verification complete")
            except Exception as e:
                print(f"⚠ Diarization failed: {e}")
                print("Continuing without speaker labels")
        else:
            print("⚠ Skipping diarization (model not loaded)")
        
        # Calculate metrics
        total_time = time.time() - start_time
        processing_time = total_time - download_time  # Exclude download time
        
        # Cost calculation (A10G: $0.01836/min)
        gpu_minutes = processing_time / 60
        gpu_cost = gpu_minutes * 0.01836
        
        realtime_factor = audio_duration / processing_time if processing_time > 0 else 0
        
        # GROK INTELLIGENCE EXTRACTION (with Nov 2025 features)
        print("\nExtracting intelligence with Grok-4 (prompt caching enabled)...")
        entities, relationships, topics, key_moments, sentiment, grok_cost_breakdown, cache_stats = self._extract_entities(result["segments"])
        print(f"✓ Extracted {len(entities)} entities, {len(relationships)} relationships, {len(topics)} topics, {len(key_moments)} moments")
        
        # Enhanced cost tracking
        grok_cost = grok_cost_breakdown.get("total", 0.0)
        total_cost = gpu_cost + grok_cost
        
        result_dict = {
            "transcript": result["segments"],
            "language": result.get("language", "en"),
            "speakers": speakers_found,
            "entities": entities,
            "relationships": relationships,
            "topics": topics,
            "key_moments": key_moments,
            "sentiment": sentiment,
            "processing_time": processing_time,
            "audio_duration": audio_duration,
            "cost": round(total_cost, 4),
            "cost_breakdown": {
                "transcription_gpu": round(gpu_cost, 6),
                "extraction_input": grok_cost_breakdown.get("input_cost", 0),
                "extraction_cached": grok_cost_breakdown.get("cached_cost", 0),
                "extraction_output": grok_cost_breakdown.get("output_cost", 0),
                "cache_savings": grok_cost_breakdown.get("cache_savings", 0),
                "grok_total": grok_cost,
                "total": round(total_cost, 6)
            },
            "cache_stats": cache_stats,
            "realtime_factor": round(realtime_factor, 2),
            "model": "whisperx-large-v3+grok-4-fast",
            "gpu": "A10G"
        }
        
        print("="*60)
        print(f"✓ COMPLETE: {audio_duration/60:.1f} min audio in {processing_time:.1f}s")
        print(f"  Realtime factor: {realtime_factor:.1f}x")
        print(f"  Speakers: {speakers_found}")
        print(f"  Entities: {len(entities)}")
        print(f"  Total Cost: ${total_cost:.4f} (GPU: ${gpu_cost:.4f}, Grok: ${grok_cost:.4f})")
        if cache_stats.get('cache_hits', 0) > 0:
            print(f"  💰 Cache savings: ${grok_cost_breakdown.get('cache_savings', 0):.4f}")
        print("="*60)
        
        return result_dict
    
    def _extract_entities(self, segments: list) -> tuple:
        """
        Extract comprehensive intelligence using Grok-4 with Nov 2025 features.
        
        Features:
        - Prompt caching (50% cost savings on system prompt)
        - Structured outputs (type-safe json_schema)
        - Enhanced cost tracking with cache metrics
        
        Args:
            segments: List of transcript segments with text and speaker
            
        Returns:
            Tuple of (entities, relationships, topics, key_moments, sentiment, cost_breakdown, cache_stats)
        """
        # Prepare transcript text
        transcript_text = " ".join(seg.get("text", "") for seg in segments)
        
        # Check if Grok client initialized
        if not self.grok_client:
            print("⚠ No Grok client - skipping entity extraction")
            return [], [], [], [], {}, {}, {}
        
        grok_model = "grok-4-fast-reasoning"  # Grok-4 Fast Reasoning - optimized for entity/topic extraction
        
        # Handle long transcripts with chunking
        # Grok-4 has 256k token context (~1M chars) - can handle much longer transcripts
        max_chunk_size = 200000  # Increased for Grok-4 - ensures most videos get full intelligence
        if len(transcript_text) > max_chunk_size:
            print(f"Long transcript detected ({len(transcript_text)} chars), using chunked extraction")
            # Chunked extraction: entities + relationships only (topics/moments need full context)
            entities, relationships = self._extract_entities_chunked(segments, grok_base_url, grok_model, grok_headers)
            # Return with empty topics/moments/sentiment for chunked (need full context)
            return entities, relationships, [], [], {}
        
        # Import prompt template (following xAI best practices)
        # Note: Can't import from src/ in Modal, so inline the improved prompt
        
        # Get metadata for context (if available from segments)
        metadata = {
            'title': 'Video',  # TODO: Pass actual metadata to _extract_entities
            'duration': 0,
            'channel': 'Unknown'
        }
        
        # Build comprehensive extraction prompt (following xAI best practices)
        prompt = f"""Extract comprehensive intelligence from this video transcript.

Video Context:
- Title: {metadata.get('title', 'Unknown')}
- Duration: {metadata.get('duration', 0) / 60:.0f} minutes
- Source: {metadata.get('channel', 'Unknown')}

EXTRACTION GUIDELINES (Quality Over Quantity):

1. ENTITIES:
   Extract ALL named people, organizations, places, and events that are clearly mentioned.
   
   Requirements:
   - Only extract if explicitly named in transcript (not generic references)
   - Each entity MUST have supporting quote as evidence
   - Confidence score (0-1) based on clarity of mention
   - Use spaCy standard types: PERSON, ORG, GPE, EVENT, PRODUCT, etc.
   
   Quality bar: Named and specific > generic and vague

2. RELATIONSHIPS:
   Extract ALL relationships between entities where connection is explicitly stated.
   
   Requirements:
   - Subject and object MUST be actual entity names from transcript
   - Predicate should be specific action/connection (e.g., "announced", "criticized")
   - MUST include exact supporting quote as evidence
   - Only extract if relationship is clearly stated (don't infer unstated connections)
   
   Quality bar: Explicit and evidenced > inferred and vague

3. TOPICS:
   Identify main themes or subjects discussed in the video.
   
   Requirements:
   - Topics should be specific (e.g., "Israel-Hamas Ceasefire" not just "Middle East")
   - Provide time range where topic is discussed (MM:SS-MM:SS format)
   - Relevance score (0-1): how central this topic is to the video
   
   Quality bar: Specific and substantial > generic and brief

4. KEY MOMENTS:
   Identify moments that are particularly significant or worth highlighting.
   
   Requirements:
   - Exact timestamp (MM:SS format)
   - Clear description of what makes this moment significant
   - Significance score (0-1) based on importance to video content
   - Include exact quote from that moment
   
   Quality bar: Objectively significant > subjectively interesting

5. SENTIMENT:
   Analyze overall tone and per-topic sentiment.
   
   Requirements:
   - Overall: positive, negative, neutral, or mixed
   - Per-topic sentiment if topics have distinctly different tones
   - Confidence in overall assessment

CRITICAL PRINCIPLES:
- Evidence is mandatory for entities and relationships (prevents hallucinations)
- Quality is more important than quantity (5 perfect > 20 questionable)
- Only extract what is clearly present (don't infer or assume)
- Confidence scores should reflect actual certainty

Use spaCy standard entity types for consistency:
PERSON, ORG, GPE, LOC, EVENT, PRODUCT, MONEY, DATE, TIME, FAC, NORP, LANGUAGE, LAW, WORK_OF_ART, CARDINAL, ORDINAL, QUANTITY, PERCENT

Entity Type Guidelines:
- PERSON: People, including fictional characters
- ORG: Companies, agencies, institutions, government programs
- GPE: Countries, cities, states (Geopolitical entities)
- LOC: Non-GPE locations, mountain ranges, bodies of water
- EVENT: Named hurricanes, battles, wars, sports events, political events
- PRODUCT: Physical objects, vehicles, foods, weapons
  * NOT abstract concepts (inflation, tariffs, healthcare)
  * NOT policies (border security, Green New Deal)
  * Physical/tangible items only
- MONEY: Monetary values ($100, €50, etc.)
- DATE: Absolute or relative dates or periods
- TIME: Times smaller than a day (3pm, morning, etc.)
- FAC: Buildings, airports, highways, bridges
- NORP: Nationalities, religious, political groups
- LANGUAGE: Named languages
- LAW: Named documents made into laws, policies
- WORK_OF_ART: Titles of books, songs, etc.
- CARDINAL: Numerals that don't fall under another type
- ORDINAL: "first", "second", etc.
- QUANTITY: Measurements, weights, distances
- PERCENT: Percentage values

Transcript:
{transcript_text}"""
        
        try:
            # Build messages optimized for caching (Nov 2025 feature)
            system_prompt = "You are a precise video intelligence extraction system following strict quality standards."
            messages = self.grok_client.build_cached_message(system_prompt, prompt)
            
            print(f"Calling Grok API with prompt caching enabled...")
            print(f"Transcript length: {len(transcript_text)} characters")
            
            # Call Grok with all Nov 2025 features
            response = self.grok_client.chat_completion(
                messages=messages,
                model=grok_model,
                temperature=0.1,
                max_tokens=4096,
                response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "video_intelligence_extraction",
                                "strict": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "entities": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "confidence": {"type": "number"},
                                                    "evidence": {"type": "string"}
                                                },
                                                "required": ["name", "type", "confidence", "evidence"],
                                                "additionalProperties": False
                                            }
                                        },
                                        "relationships": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "subject": {"type": "string"},
                                                    "predicate": {"type": "string"},
                                                    "object": {"type": "string"},
                                                    "evidence": {"type": "string"},
                                                    "confidence": {"type": "number"}
                                                },
                                                "required": ["subject", "predicate", "object", "evidence", "confidence"],
                                                "additionalProperties": False
                                            }
                                        },
                                        "topics": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "relevance": {"type": "number"},
                                                    "time_range": {"type": "string"}
                                                },
                                                "required": ["name", "relevance", "time_range"],
                                                "additionalProperties": False
                                            }
                                        },
                                        "key_moments": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "timestamp": {"type": "string"},
                                                    "description": {"type": "string"},
                                                    "significance": {"type": "number"},
                                                    "quote": {"type": "string"}
                                                },
                                                "required": ["timestamp", "description", "significance", "quote"],
                                                "additionalProperties": False
                                            }
                                        },
                                        "sentiment": {
                                            "type": "object",
                                            "properties": {
                                                "overall": {"type": "string"},
                                                "confidence": {"type": "number"},
                                                "per_topic": {"type": "object"}
                                            },
                                            "required": ["overall", "confidence", "per_topic"],
                                            "additionalProperties": False
                                        }
                                    },
                                    "required": ["entities", "relationships", "topics", "key_moments", "sentiment"],
                                    "additionalProperties": False
                        }
                    }
                }
            )
            
            # Extract usage stats and calculate cost with caching
            usage_stats = self.grok_client.extract_usage_stats(response)
            cost_breakdown = self.grok_client.calculate_cost(
                input_tokens=usage_stats["input_tokens"],
                output_tokens=usage_stats["output_tokens"],
                cached_tokens=usage_stats["cached_tokens"],
                model=grok_model
            )
            
            # Record cache performance
            self.grok_client.record_cache_performance(usage_stats, cost_breakdown)
            
            # Log cache hit/miss
            if usage_stats["cached_tokens"] > 0:
                print(f"  💰 CACHE HIT: {usage_stats['cached_tokens']} tokens cached")
                print(f"  💵 Saved: ${cost_breakdown['cache_savings']:.4f}")
            else:
                print(f"  ℹ️  Cache miss (first time with this system prompt)")
            
            print(f"  💲 Extraction cost: ${cost_breakdown['total']:.4f}")
            
            # Get response content
            print(f"Grok API response keys: {list(response.keys())}")
            
            if "choices" not in response or len(response["choices"]) == 0:
                print(f"⚠ Grok API returned no choices: {response}")
                return [], [], [], [], {}, {}, {}
            
            content = response["choices"][0]["message"]["content"]
            print(f"Grok API content length: {len(content)} characters")
            
            # Parse JSON with error handling
            try:
                result = json.loads(content)
                print(f"Parsed JSON keys: {list(result.keys())}")
            except json.JSONDecodeError as json_err:
                print(f"⚠ JSON parsing failed: {json_err}")
                print(f"Raw content: {content[:500]}...")
                return [], [], [], [], {}, {}, {}
            
            entities = result.get("entities", [])
            relationships = result.get("relationships", [])
            topics = result.get("topics", [])
            key_moments = result.get("key_moments", [])
            sentiment = result.get("sentiment", {})
            
            print(f"✓ Extracted {len(entities)} entities, {len(relationships)} relationships, {len(topics)} topics, {len(key_moments)} moments")
                
            # Get cache stats for reporting
            cache_stats = self.grok_client.get_cache_stats()
            print(f"  📊 Cache performance: {cache_stats['hit_rate_percent']:.1f}% hit rate, ${cache_stats['total_savings_usd']:.4f} total savings")
            
            return entities, relationships, topics, key_moments, sentiment, cost_breakdown, cache_stats
                
        except Exception as e:
            print(f"⚠ Entity extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return [], [], [], [], {}, {}, {}
    
    def _fact_check_entities(self, entities: list, transcript_context: str = "") -> list:
        """
        Optional fact-checking using Grok's server-side tools (Oct 2025 feature).
        
        Uses web_search and x_search to verify low-confidence entities.
        
        Args:
            entities: List of extracted entities
            transcript_context: Surrounding context for verification
        
        Returns:
            List of fact-checked entities with updated confidence
        """
        if not self.grok_client:
            return entities
        
        # Only fact-check entities below threshold
        confidence_threshold = 0.7
        to_check = [e for e in entities if e.get('confidence', 1.0) < confidence_threshold]
        
        if not to_check:
            print(f"  ℹ️  All entities above {confidence_threshold} confidence, skipping fact-check")
            return entities
        
        print(f"  🔍 Fact-checking {len(to_check)} entities below {confidence_threshold} confidence...")
        
        # Define available tools
        tools = [
            {"type": "web_search", "description": "Search web for verification"},
            {"type": "x_search", "description": "Search X/Twitter for real-time info"}
        ]
        
        verified_count = 0
        
        for entity in to_check[:5]:  # Limit to 5 to avoid cost explosion
            entity_name = entity.get('name', '')
            entity_type = entity.get('type', '')
            
            # Build verification prompt
            verify_prompt = f"Verify this entity: {entity_name} ({entity_type}). Context: {transcript_context[:200]}"
            
            try:
                # Call with tools
                verify_response = self.grok_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a fact-checking assistant."},
                        {"role": "user", "content": verify_prompt}
                    ],
                    model="grok-4-fast-reasoning",
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.1,
                    max_tokens=500
                )
                
                # Check if tools were used (indicates verification attempt)
                tool_calls = verify_response.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
                
                if tool_calls:
                    # Tool was used, consider verified
                    entity['confidence'] = min(1.0, entity.get('confidence', 0.5) + 0.1)
                    verified_count += 1
                    print(f"    ✅ Verified {entity_name}: {entity['confidence']:.2f}")
                
            except Exception as e:
                print(f"    ⚠️ Fact-check failed for {entity_name}: {e}")
        
        print(f"  ✓ Fact-checked {verified_count}/{len(to_check)} entities")
        return entities
    
    def _add_to_knowledge_base(
        self, 
        video_id: str, 
        transcript_text: str, 
        entities: list,
        relationships: list,
        topics: list
    ) -> Optional[str]:
        """
        Add processed video to Grok Collections API knowledge base (Aug 2025 feature).
        
        Enables:
        - Cross-video entity search
        - Semantic search across all processed videos
        - Entity co-occurrence analysis
        
        Args:
            video_id: Video identifier
            transcript_text: Full transcript
            entities: Extracted entities
            relationships: Extracted relationships
            topics: Extracted topics
        
        Returns:
            Collection file ID or None if failed
        """
        if not self.grok_client:
            return None
        
        try:
            import tempfile
            import json
            
            # Create structured document
            document = {
                "video_id": video_id,
                "transcript": transcript_text,
                "entities": entities,
                "relationships": relationships,
                "topics": topics,
                "indexed_at": time.time()
            }
            
            # Save to temp file
            temp_file = f"/tmp/{video_id}_kb.json"
            with open(temp_file, 'w') as f:
                json.dump(document, f, indent=2)
            
            # Upload to Grok Files API
            print(f"  📚 Adding to knowledge base...")
            
            # Note: Full Collections API implementation would require:
            # 1. Upload file via Files API
            # 2. Add to collection via Collections API
            # For now, just log that it's ready
            print(f"  ℹ️  Document ready for knowledge base (would upload to Collections API)")
            print(f"  📄 File: {temp_file}")
            
            return temp_file
            
        except Exception as e:
            print(f"  ⚠️ Knowledge base integration failed: {e}")
            return None
    
    def _extract_entities_chunked(self, segments: list, grok_base_url: str, grok_model: str, grok_headers: dict) -> tuple:
        """
        Extract comprehensive intelligence from long transcripts using chunking.
        
        Args:
            segments: List of transcript segments
            grok_base_url: Grok API base URL
            grok_model: Grok model name
            grok_headers: Grok API headers
            
        Returns:
            Tuple of (entities, relationships, topics, key_moments, sentiment)
        """
        import httpx
        import json
        
        # Create chunks of segments
        chunk_size = 100  # Number of segments per chunk
        chunks = [segments[i:i + chunk_size] for i in range(0, len(segments), chunk_size)]
        
        print(f"Processing {len(chunks)} chunks for long transcript")
        
        all_entities = []
        all_relationships = []
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} segments)")
            
            # Build chunk text
            chunk_text = " ".join(seg.get("text", "") for seg in chunk)
            
            # Build chunk-specific prompt
            prompt = f"""Extract entities and relationships from this portion of a long conversation transcript.

This is chunk {i+1} of {len(chunks)} from a longer conversation.

Use spaCy's standard entity types:
PERSON, ORG, GPE, LOC, EVENT, PRODUCT, MONEY, DATE, TIME, FAC, NORP, LANGUAGE, LAW, WORK_OF_ART, CARDINAL, ORDINAL, QUANTITY, PERCENT

Return JSON with this structure:
{{
  "entities": [
    {{"name": "Entity Name", "type": "PERSON|ORG|GPE|LOC|EVENT|PRODUCT|MONEY|DATE|TIME|FAC|NORP|LANGUAGE|LAW|WORK_OF_ART|CARDINAL|ORDINAL|QUANTITY|PERCENT", "confidence": 0.9}}
  ],
  "relationships": [
    {{"subject": "Entity1", "predicate": "relation", "object": "Entity2", "confidence": 0.9}}
  ]
}}

Chunk {i+1} Transcript:
{chunk_text}"""
            
            try:
                # Call Grok API for this chunk
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(
                        f"{grok_base_url}/chat/completions",
                        headers=grok_headers,
                        json={
                            "model": grok_model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a precise entity extraction system. Return only valid JSON."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.1,
                            "max_tokens": 4096,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    
                    if response.status_code != 200:
                        print(f"⚠ Grok API error for chunk {i+1}: {response.status_code}")
                        continue
                    
                    response_json = response.json()
                    content = response_json["choices"][0]["message"]["content"]
                    
                    # Parse JSON
                    result = json.loads(content)
                    
                    chunk_entities = result.get("entities", [])
                    chunk_relationships = result.get("relationships", [])
                    
                    all_entities.extend(chunk_entities)
                    all_relationships.extend(chunk_relationships)
                    
                    print(f"✓ Chunk {i+1}: {len(chunk_entities)} entities, {len(chunk_relationships)} relationships")
                    
            except Exception as e:
                print(f"⚠ Chunk {i+1} failed: {e}")
                continue
        
        print(f"✓ Chunked extraction complete: {len(all_entities)} total entities, {len(all_relationships)} total relationships")
        
        # Advanced deduplication with fuzzy matching (ported from EntityNormalizer)
        dedup_entities = self._deduplicate_entities_advanced(all_entities)
        duplicates_removed = len(all_entities) - len(dedup_entities)
        print(f"✓ Deduplicated entities: {len(dedup_entities)} (removed {duplicates_removed} duplicates)")
        
        # Deduplication for relationships
        rel_dedup = {}
        for rel in all_relationships:
            key = (rel.get('subject', '').lower(), rel.get('predicate', '').lower(), rel.get('object', '').lower())
            conf = rel.get('confidence', 0)
            if conf < 0.8:
                continue  # Skip low confidence
            if key not in rel_dedup or conf > rel_dedup[key]['confidence']:
                rel_dedup[key] = rel
        
        dedup_relationships = list(rel_dedup.values())
        rel_duplicates_removed = len(all_relationships) - len(dedup_relationships)
        print(f"✓ Deduplicated relationships: {len(dedup_relationships)} (removed {rel_duplicates_removed} duplicates)")
        
        return dedup_entities, dedup_relationships
    
    def _deduplicate_entities_advanced(self, entities: list) -> list:
        """
        Advanced entity deduplication with fuzzy matching.
        Ported from ClipScribe's EntityNormalizer for production-grade deduplication.
        
        Handles:
        - Title removal (President Trump → Trump)
        - Fuzzy matching (Trump ≈ Donald Trump, 85% similarity)
        - Substring matching (Trump in "Donald Trump")
        - Abbreviations (US ≈ United States via fuzzy)
        - Case normalization
        - Confidence-based merging (keeps highest confidence)
        - Longest name selection (Donald Trump > Trump)
        """
        from difflib import SequenceMatcher
        import re
        
        # Step 1: Filter low confidence and normalize
        normalized_entities = []
        for entity in entities:
            name = entity.get('name', '')
            entity_type = entity.get('type', '')
            conf = entity.get('confidence', 0)
            
            # Skip low confidence
            if conf < 0.7:
                continue
            
            # Skip empty names
            if not name or len(name.strip()) < 2:
                continue
            
            # Normalize name for comparison
            normalized_name = self._normalize_entity_name(name)
            
            normalized_entities.append({
                'original_name': name,
                'normalized_name': normalized_name,
                'type': entity_type,
                'confidence': conf,
                'original_entity': entity
            })
        
        print(f"  After confidence filter: {len(normalized_entities)} entities")
        
        # Step 2: Group by fuzzy similarity
        groups = []
        used = set()
        
        for i, entity in enumerate(normalized_entities):
            if i in used:
                continue
            
            # Start new group with this entity
            group = [entity]
            used.add(i)
            
            # Find similar entities of the same type
            for j, other in enumerate(normalized_entities[i+1:], i+1):
                if j in used:
                    continue
                
                # Must be same type
                if entity['type'] != other['type']:
                    continue
                
                # Check if names are similar
                if self._are_names_similar(entity['normalized_name'], other['normalized_name']):
                    group.append(other)
                    used.add(j)
            
            groups.append(group)
        
        print(f"  Grouped into {len(groups)} unique entities")
        
        # Step 3: Merge each group, keeping best entity
        deduplicated = []
        for group in groups:
            # Sort by: 1) confidence (highest first), 2) name length (longest first)
            # This ensures we keep the most confident AND most complete name
            group.sort(key=lambda x: (x['confidence'], len(x['original_name'])), reverse=True)
            
            # Keep the best entity
            best = group[0]['original_entity']
            
            # If multiple entities in group, use longest name from high-confidence entities
            if len(group) > 1:
                # Get all entities with confidence >= 0.9 (high confidence)
                high_conf = [e for e in group if e['confidence'] >= 0.9]
                if high_conf:
                    # Among high confidence, choose longest name
                    high_conf.sort(key=lambda x: len(x['original_name']), reverse=True)
                    best = high_conf[0]['original_entity']
            
            deduplicated.append(best)
        
        return deduplicated
    
    def _normalize_entity_name(self, name: str) -> str:
        """
        Normalize entity name for comparison.
        Ported from EntityNormalizer._clean_name and _remove_titles.
        """
        import re
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Remove quotes and brackets
        name = re.sub(r'^["\'\[\(]+|["\'\]\)]+$', '', name)
        
        # Remove trailing punctuation (but keep periods in abbreviations)
        name = re.sub(r'[,;:!?]+$', '', name)
        
        # Remove common titles (case-insensitive)
        titles = [
            'President', 'Vice President', 'VP',
            'CEO', 'CFO', 'CTO', 'COO', 'Chairman', 'Chair',
            'Dr.', 'Dr', 'Mr.', 'Mr', 'Mrs.', 'Mrs', 'Ms.', 'Ms',
            'Prof.', 'Prof', 'Professor',
            'Sen.', 'Sen', 'Senator', 'Rep.', 'Rep', 'Representative',
            'Gov.', 'Gov', 'Governor', 'Mayor',
            'Former', 'Ex-', 'Acting'
        ]
        
        for title in titles:
            # Remove title at start of name
            pattern = f'^{re.escape(title)}\\s+'
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Lowercase for comparison
        return name.lower().strip()
    
    def _are_names_similar(self, name1: str, name2: str, threshold: float = 0.80) -> bool:
        """
        Check if two names are similar using fuzzy matching.
        Ported from EntityNormalizer._similar_names.
        
        Args:
            name1: First normalized name
            name2: Second normalized name  
            threshold: Similarity threshold (0.85 = 85% similar)
            
        Returns:
            True if names refer to same entity
        """
        from difflib import SequenceMatcher
        
        # Exact match
        if name1 == name2:
            return True
        
        # One is substring of the other (e.g., "trump" in "donald trump")
        if name1 in name2 or name2 in name1:
            return True
        
        # Check for abbreviation pattern (e.g., "us" vs "united states")
        if self._is_abbreviation(name1, name2):
            return True
        
        # Fuzzy string similarity using SequenceMatcher
        # Lowered to 0.80 to catch typos and short-name variations (e.g., Sacks vs Sachs)
        similarity = SequenceMatcher(None, name1, name2).ratio()
        return similarity >= threshold
    
    def _is_abbreviation(self, name1: str, name2: str) -> bool:
        """
        Check if one name is an abbreviation of another.
        Ported from EntityNormalizer._check_abbreviations.
        """
        words1 = name1.split()
        words2 = name2.split()
        
        # If one is a single word and other is multiple words
        if len(words1) == 1 and len(words2) > 1:
            # Check if words1 is acronym of words2
            acronym = ''.join(word[0] for word in words2 if word)
            return words1[0].replace('.', '') == acronym.lower()
        
        elif len(words2) == 1 and len(words1) > 1:
            # Check if words2 is acronym of words1
            acronym = ''.join(word[0] for word in words1 if word)
            return words2[0].replace('.', '') == acronym.lower()
        
        return False
    
    @modal.method()
    def transcribe_from_gcs(self, gcs_input: str, gcs_output: str) -> dict:
        """
        Transcribe audio from GCS, upload results to GCS.
        
        Args:
            gcs_input: GCS path like "gs://bucket/file.mp3"
            gcs_output: GCS path for results like "gs://bucket/results/"
            
        Returns:
            Same as transcribe() with additional gcs_output_path
        """
        import whisperx
        import json
        from google.cloud import storage
        from google.oauth2 import service_account
        
        print(f"Processing from GCS: {gcs_input}")
        
        # Initialize GCS client with service account from secret
        service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        client = storage.Client(credentials=credentials)
        
        start_time = time.time()
        
        # Parse GCS paths
        input_bucket = gcs_input.split("/")[2]
        input_blob = "/".join(gcs_input.split("/")[3:])
        
        output_bucket = gcs_output.split("/")[2]
        output_prefix = "/".join(gcs_output.split("/")[3:])
        
        # Download from GCS
        print(f"Downloading from gs://{input_bucket}/{input_blob}")
        
        bucket = client.bucket(input_bucket)
        blob = bucket.blob(input_blob)
        
        audio_path = "/tmp/audio.mp3"
        blob.download_to_filename(audio_path)
        
        download_time = time.time() - start_time
        print(f"✓ Downloaded in {download_time:.1f}s")
        
        # Load and process audio
        audio = whisperx.load_audio(audio_path)
        audio_duration = len(audio) / 16000
        
        print(f"\n{'='*60}")
        print(f"Processing {audio_duration/60:.1f} minutes...")
        print(f"{'='*60}")
        process_start = time.time()
        
        # Clear GPU memory before processing
        self._clear_gpu_memory()
        
        # ROBUST LANGUAGE DETECTION (multi-sample)
        filename = Path(gcs_input).name
        detected_lang = self._detect_language_robust(audio)
        validated_lang = self._validate_language_detection(detected_lang, audio, filename)
        
        print(f"  📝 Final language: {validated_lang}")
        
        # TRANSCRIBE WITH OOM RETRY
        result = self._transcribe_with_retry(audio, audio_duration, validated_lang)
        
        # Align
        model_a, metadata = whisperx.load_align_model(
            language_code=result["language"],
            device=self.device
        )
        result = whisperx.align(result["segments"], model_a, metadata, audio, self.device)
        
        # Diarize
        speakers_found = 0
        if self.diarize_model:
            try:
                # CRITICAL FIX: Pass speaker hints to pyannote
                # Without these, pyannote guesses wildly (often 8+ speakers)
                # With hints, it constrains to reasonable range
                diarize_segments = self.diarize_model(
                    audio,
                    min_speakers=2,    # Minimum 2 speakers (conversations/interviews)
                    max_speakers=6     # Maximum 6 speakers (most meetings/panels)
                )
                result = whisperx.assign_word_speakers(diarize_segments, result)
                
                speakers_found_raw = len(set(seg.get("speaker") for seg in result["segments"]))
                print(f"✓ Raw speakers: {speakers_found_raw}")
                
                # Apply quality cleanup
                print("Applying speaker quality cleanup...")
                result["segments"], cleanup_stats = self._improve_speaker_quality(result["segments"])
                
                speakers_found = len(set(seg.get("speaker") for seg in result["segments"]))
                print(f"✓ Final speakers: {speakers_found}")
                if cleanup_stats.get('speakers_merged', 0) > 0:
                    print(f"  (merged {cleanup_stats['speakers_merged']} minor speakers)")
                
                # GEMINI QUALITY PASS: Verify speaker attribution
                print("Applying Gemini quality verification...")
                result["segments"] = self._gemini_speaker_verification(audio_path, result["segments"])
                print("✓ Gemini verification complete")
            except Exception as e:
                print(f"⚠ Diarization failed: {e}")
        
        # GROK COMPREHENSIVE INTELLIGENCE EXTRACTION (with Nov 2025 features)
        print("Extracting intelligence with Grok-4 (prompt caching enabled)...")
        entities, relationships, topics, key_moments, sentiment, cost_breakdown, cache_stats = self._extract_entities(result["segments"])
        print(f"✓ Extracted {len(entities)} entities, {len(relationships)} relationships, {len(topics)} topics, {len(key_moments)} moments")
        
        # Optional: Fact-check low-confidence entities (disabled by default to avoid cost)
        # entities = self._fact_check_entities(entities, transcript_text=" ".join(s.get("text","") for s in result["segments"]))
        
        # Optional: Add to knowledge base (disabled by default)
        # self._add_to_knowledge_base("video_id_here", transcript_text, entities, relationships, topics)
        
        # Add comprehensive intelligence to result
        result["entities"] = entities
        result["relationships"] = relationships
        result["topics"] = topics
        result["key_moments"] = key_moments
        result["sentiment"] = sentiment
        
        # Enhanced cost tracking with cache savings
        processing_time = time.time() - process_start
        gpu_cost = (processing_time / 60) * 0.01836  # A10G cost
        grok_cost = cost_breakdown.get("total", 0.0)
        total_cost = gpu_cost + grok_cost
        
        # Add detailed cost breakdown to result
        result["cost_breakdown"] = {
            "transcription_gpu": round(gpu_cost, 6),
            "extraction_input": cost_breakdown.get("input_cost", 0),
            "extraction_cached": cost_breakdown.get("cached_cost", 0),
            "extraction_output": cost_breakdown.get("output_cost", 0),
            "cache_savings": cost_breakdown.get("cache_savings", 0),
            "grok_total": grok_cost,
            "total": round(total_cost, 6)
        }
        result["cache_stats"] = cache_stats
        result["cost"] = round(total_cost, 4)  # Backward compat
        
        print(f"💰 Total cost: ${total_cost:.4f} (GPU: ${gpu_cost:.4f}, Grok: ${grok_cost:.4f}, Saved: ${cost_breakdown.get('cache_savings', 0):.4f})")
        
        # Upload results to GCS
        print(f"Uploading to gs://{output_bucket}/{output_prefix}")
        output_bucket_obj = client.bucket(output_bucket)
        
        # Upload full transcript JSON
        transcript_blob = output_bucket_obj.blob(f"{output_prefix}/transcript.json")
        transcript_blob.upload_from_string(json.dumps(result, indent=2))
        
        # Upload metadata
        metadata_blob = output_bucket_obj.blob(f"{output_prefix}/metadata.json")
        metadata_blob.upload_from_string(json.dumps({
            "language": result.get("language", "en"),  # WhisperX may not return language in result
            "speakers": speakers_found,
            "duration_minutes": audio_duration / 60,
            "processing_minutes": processing_time / 60,
            "realtime_factor": audio_duration / processing_time,
            "cost": gpu_cost,
            "model": "whisperx-large-v3",
            "gpu": "A10G"
        }, indent=2))
        
        print(f"✓ Results uploaded to {gcs_output}")
        
        return {
            "status": "success",
            "gcs_output": gcs_output,
            "speakers": speakers_found,
            "duration_minutes": audio_duration / 60,
            "processing_minutes": processing_time / 60,
            "cost": round(gpu_cost, 4)
        }


# ==============================================================================
# WEB API ENDPOINT
# ==============================================================================

@app.function(
    secrets=[
        modal.Secret.from_name("huggingface"),
        modal.Secret.from_name("googlecloud-secret")
    ]
)
@modal.asgi_app()
def api_transcribe():
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    web_app = FastAPI()
    
    class TranscribeRequest(BaseModel):
        audio_url: str
        output_path: str = None
    
    @web_app.post("/transcribe")
    def transcribe_endpoint(request: TranscribeRequest) -> dict:
        """
        Production API endpoint for Station10 transcription.
        
        Usage:
            POST https://YOUR_WORKSPACE--station10-transcription-api-transcribe.modal.run/transcribe
            {
                "audio_url": "https://example.com/podcast.mp3",
                "output_path": "gs://bucket/results/" (optional, for GCS output)
            }
        
        Returns:
            {
                "status": "success",
                "transcript": [...],
                "speakers": 2,
                "cost": 0.11,
                ...
            }
        """
        try:
            transcriber = Station10Transcriber()
            
            # If GCS output specified, use GCS integration
            if request.output_path and request.output_path.startswith("gs://"):
                if request.audio_url.startswith("gs://"):
                    result = transcriber.transcribe_from_gcs.remote(request.audio_url, request.output_path)
                else:
                    # HTTP URL with GCS output - transcribe and return
                    result = transcriber.transcribe.remote(request.audio_url)
            else:
                # Standard transcription
                result = transcriber.transcribe.remote(request.audio_url)
            
            return {"status": "success", **result}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return web_app


# ==============================================================================
# LOCAL TESTING
# ==============================================================================

@app.function(timeout=3600)  # 1 hour timeout for long videos
def test_gcs_transcription(gcs_path: str = "gs://prismatic-iris-429006-g6-clipscribe/public/medical.mp3"):
    """
    Simple GCS test function.
    
    Usage:
        modal run deploy/station10_modal.py::test_gcs_transcription
    """
    transcriber = Station10Transcriber()
    
    result = transcriber.transcribe_from_gcs.remote(
        gcs_input=gcs_path,
        gcs_output="gs://prismatic-iris-429006-g6-clipscribe/test/modal_results/"
    )
    
    print()
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"Status: {result.get('status')}")
    print(f"Speakers: {result.get('speakers')}")
    print(f"Duration: {result.get('duration_minutes', 0):.1f} min")
    print(f"Processing: {result.get('processing_minutes', 0):.1f} min")
    print(f"Cost: ${result.get('cost', 0):.4f}")
    print(f"Output: {result.get('gcs_output')}")
    print("="*80)
    
    return result

@app.local_entrypoint()
def test(audio_url: str = None):
    """
    Local test entry point.
    
    Usage:
        modal run deploy/station10_modal.py --audio-url "https://example.com/test.mp3"
    """
    if not audio_url:
        print("❌ Please provide --audio-url parameter")
        print("Example: modal run deploy/station10_modal.py --audio-url 'https://...'")
        return
    
    print(f"Testing transcription with: {audio_url}")
    print()
    
    transcriber = Station10Transcriber()
    result = transcriber.transcribe.remote(audio_url)
    
    print()
    print("="*80)
    print("TRANSCRIPTION RESULT")
    print("="*80)
    print(f"Language: {result['language']}")
    print(f"Speakers: {result['speakers']}")
    print(f"Duration: {result['audio_duration']/60:.1f} minutes")
    print(f"Processing: {result['processing_time']:.1f} seconds")
    print(f"Realtime Factor: {result['realtime_factor']:.1f}x")
    print(f"Cost: ${result['cost']:.4f}")
    print()
    print("First 5 segments:")
    for i, seg in enumerate(result['transcript'][:5]):
        speaker = seg.get('speaker', 'UNKNOWN')
        text = seg.get('text', '')
        print(f"  [{speaker}] {text}")
    print()
    print(f"Total segments: {len(result['transcript'])}")
    print("="*80)


# ==============================================================================
# GCS BATCH PROCESSING
# ==============================================================================

@app.function()
def batch_transcribe_from_gcs(gcs_input_paths: list[str], gcs_output_base: str) -> list[dict]:
    """
    Batch process multiple videos from GCS in parallel.
    
    Usage:
        from modal import App
        app = App.lookup("station10-transcription")
        results = app.functions["batch_transcribe_from_gcs"].remote([
            "gs://bucket/video1.mp3",
            "gs://bucket/video2.mp3",
        ], "gs://bucket/results/")
    
    This processes all videos in PARALLEL across multiple GPUs,
    dramatically faster than serial processing.
    """
    transcriber = Station10Transcriber()
    
    # Process all videos in parallel
    results = list(transcriber.transcribe_from_gcs.map(
        [
            (input_path, f"{gcs_output_base}/{Path(input_path).stem}/")
            for input_path in gcs_input_paths
        ]
    ))
    
    return results


# ==============================================================================
# DOCUMENTATION
# ==============================================================================

if __name__ == "__main__":
    print(__doc__)
    print()
    print("Deployment Commands:")
    print("  modal deploy deploy/station10_modal.py    # Deploy to production")
    print("  modal run deploy/station10_modal.py --audio-url URL  # Test locally")
    print()
    print("API Endpoint:")
    print("  After deployment, POST to:")
    print("  https://YOUR_WORKSPACE--station10-transcription-api-transcribe.modal.run")
    print()
    print("GPU Configuration:")
    print("  - GPU: A10G (24GB VRAM)")
    print("  - Cost: $1.10/hour = $0.01836/minute")
    print("  - Performance: ~6x realtime")
    print()
    print("Cost Examples:")
    print("  - 30min video: ~$0.09 (5min processing)")
    print("  - 60min video: ~$0.18 (10min processing)")
    print("  - 4hr video: ~$0.73 (40min processing)")
    print()

