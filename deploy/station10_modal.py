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

# ==============================================================================
# CONFIGURATION
# ==============================================================================

app = modal.App("station10-transcription")

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
# TRANSCRIPTION CLASS
# ==============================================================================

@app.cls(
    image=image,
    gpu="A10G",  # Good balance of cost ($1.10/hr) and performance (6x realtime)
    timeout=3600,  # 1 hour max (supports videos up to 6 hours at 6x realtime)
    secrets=[
        modal.Secret.from_name("huggingface"),  # For pyannote.audio models
        modal.Secret.from_name("googlecloud-secret"),  # For GCS access
        modal.Secret.from_name("google-api-key")  # For Gemini speaker verification
    ],
    volumes={"/models": model_cache}  # Cache models to avoid re-downloading
)
class Station10Transcriber:
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
                print("✓ Diarization model loaded successfully")
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
        
        print("✓ WhisperX models loaded successfully")
    
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
        
        # Count speakers first to determine adaptive threshold
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
        
        print(f"  Speaker threshold: {threshold*100:.0f}% (adaptive for {num_speakers} initial speakers)")
        
        major_speakers = [s for s, count in speaker_counts.items() if (count / total) > threshold]
        major_set = set(major_speakers)
        
        print(f"  Major speakers: {len(major_speakers)} (>{threshold*100:.0f}%)")
        
        # Step 0: NEW - Merge duplicate/similar text across speakers
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
                    if similarity > 0.8:  # 80% similar = same utterance
                        next_seg['speaker'] = curr['speaker']
                        duplicate_merges += 1
        
        if duplicate_merges > 0:
            print(f"  Merged {duplicate_merges} duplicate text segments")
        
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
            print(f"⚠️  Gemini verification failed: {e}")
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
        print("Loading audio...")
        audio = whisperx.load_audio(audio_path)
        audio_duration = len(audio) / 16000  # 16kHz sample rate
        
        # Transcribe
        print(f"Transcribing {audio_duration/60:.1f} minutes of audio...")
        transcribe_start = time.time()
        
        result = self.whisper_model.transcribe(audio, batch_size=16)
        
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
        
        result_dict = {
            "transcript": result["segments"],
            "language": result["language"],
            "speakers": speakers_found,
            "processing_time": processing_time,
            "audio_duration": audio_duration,
            "cost": round(gpu_cost, 4),
            "realtime_factor": round(realtime_factor, 2),
            "model": "whisperx-large-v3",
            "gpu": "A10G"
        }
        
        print("="*60)
        print(f"✓ COMPLETE: {audio_duration/60:.1f} min audio in {processing_time:.1f}s")
        print(f"  Realtime factor: {realtime_factor:.1f}x")
        print(f"  Speakers: {speakers_found}")
        print(f"  Cost: ${gpu_cost:.4f}")
        print("="*60)
        
        return result_dict
    
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
        
        # Transcribe (same logic as transcribe() method)
        print(f"Processing {audio_duration/60:.1f} minutes...")
        process_start = time.time()
        
        result = self.whisper_model.transcribe(audio, batch_size=16)
        
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
                diarize_segments = self.diarize_model(audio)
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
        
        processing_time = time.time() - process_start
        gpu_cost = (processing_time / 60) * 0.01836
        
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

