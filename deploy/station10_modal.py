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

# Container image with WhisperX, pyannote.audio, and dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        # WhisperX and audio processing
        "whisperx",
        "pyannote.audio",
        "torch==2.8.0",
        "torchaudio==2.8.0",
        
        # Audio utilities
        "librosa==0.10.2",
        "soundfile==0.13.1",
        
        # Google Cloud integration
        "google-cloud-storage",
        
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
        modal.Secret.from_name("huggingface-secret"),  # For pyannote.audio models
        modal.Secret.from_name("googlecloud-secret")  # For GCS access
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
        
        # Load diarization pipeline
        hf_token = os.getenv("HF_TOKEN")  # Modal's standard HF token key
        if not hf_token:
            print("WARNING: No HF_TOKEN found. Diarization may fail.")
            print("Create secret 'huggingface-secret' with key 'HF_TOKEN' in Modal UI")
        
        try:
            self.diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=hf_token,
                device=self.device
            )
            print("✓ Models loaded successfully")
        except Exception as e:
            print(f"WARNING: Diarization model failed to load: {e}")
            print("Will transcribe without speaker labels")
            self.diarize_model = None
    
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
        
        # Speaker diarization
        speakers_found = 0
        if self.diarize_model:
            print("Running speaker diarization...")
            diarize_start = time.time()
            
            try:
                diarize_segments = self.diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
                
                # Count unique speakers
                speakers_found = len(set(
                    seg.get("speaker", "UNKNOWN") 
                    for seg in result["segments"]
                ))
                
                diarize_time = time.time() - diarize_start
                print(f"✓ Diarization complete in {diarize_time:.1f}s")
                print(f"✓ Found {speakers_found} speakers")
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
                speakers_found = len(set(seg.get("speaker") for seg in result["segments"]))
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
            "language": result["language"],
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
        modal.Secret.from_name("huggingface-secret"),
        modal.Secret.from_name("googlecloud-secret")
    ]
)
@modal.web_endpoint(method="POST")
def api_transcribe(request: dict) -> dict:
    """
    Production API endpoint for Station10 transcription.
    
    Usage:
        POST https://YOUR_WORKSPACE--station10-transcription-api-transcribe.modal.run
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
    audio_url = request.get("audio_url")
    output_path = request.get("output_path")
    
    if not audio_url:
        return {"status": "error", "error": "Missing audio_url parameter"}
    
    try:
        transcriber = Station10Transcriber()
        
        # If GCS output specified, use GCS integration
        if output_path and output_path.startswith("gs://"):
            if audio_url.startswith("gs://"):
                result = transcriber.transcribe_from_gcs.remote(audio_url, output_path)
            else:
                # Download to GCS first, then process
                # (for simplicity, just transcribe and return)
                result = transcriber.transcribe.remote(audio_url)
        else:
            # Standard transcription
            result = transcriber.transcribe.remote(audio_url)
        
        return {"status": "success", **result}
    
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==============================================================================
# LOCAL TESTING
# ==============================================================================

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

