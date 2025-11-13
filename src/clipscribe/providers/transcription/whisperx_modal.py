"""WhisperX Modal GPU transcription provider (wraps existing station10_modal.py)."""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from modal import App
from google.cloud import storage
from google.oauth2 import service_account
from ..base import (
    TranscriptionProvider,
    TranscriptResult,
    TranscriptSegment,
    ConfigurationError,
    ProcessingError,
)

# Load environment variables (for GCS credentials)
load_dotenv()


class WhisperXModalProvider(TranscriptionProvider):
    """WhisperX on Modal GPU (wraps existing station10_modal.py).
    
    Features:
    - WhisperX large-v3 on A10G GPU
    - Speaker diarization (pyannote + Gemini verification)
    - Multi-sample language detection
    - OOM retry with cascading batch sizes
    - Speaker quality improvement
    - ~10x realtime processing
    
    Cost: ~$0.055 for 30min video
    Performance: ~10x realtime (30min video = 3min processing)
    
    Best for:
    - Multi-speaker content (interviews, podcasts, meetings)
    - Cloud processing (no local GPU needed)
    - Professional-grade transcription quality
    
    Requires:
    - Modal app deployed: modal deploy deploy/station10_modal.py
    - GCS bucket for temp storage
    - GOOGLE_APPLICATION_CREDENTIALS for GCS access
    
    Existing code: deploy/station10_modal.py
    """
    
    def __init__(self, gcs_bucket: Optional[str] = None):
        """Initialize WhisperX Modal provider.
        
        Args:
            gcs_bucket: GCS bucket for temp storage (or from env)
            
        Raises:
            ConfigurationError: If Modal app not deployed or GCS not configured
        """
        # Import Modal app and class
        # Modal SDK automatically handles connection to deployed app
        try:
            from deploy.station10_modal import app, ClipScribeTranscriber
            self.modal_app = app
            self.transcriber_cls = ClipScribeTranscriber
        except ImportError as e:
            raise ConfigurationError(
                f"Could not import Modal app: {e}\n"
                "Ensure deploy/station10_modal.py exists and Modal is installed:\n"
                "  poetry install\n"
                "Deploy the app:\n"
                "  poetry run modal deploy deploy/station10_modal.py"
            )
        
        # Initialize GCS client
        creds_json = os.getenv("SERVICE_ACCOUNT_JSON")
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if creds_json:
            # Use service account JSON from env
            service_account_info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            self.gcs_client = storage.Client(credentials=credentials)
        elif creds_path:
            # Use service account file
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            self.gcs_client = storage.Client(credentials=credentials)
        else:
            raise ConfigurationError(
                "GCS credentials required for Modal provider.\n"
                "Set one of:\n"
                "  export SERVICE_ACCOUNT_JSON='{...}'\n"
                "  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
            )
        
        # GCS bucket for temp storage
        self.gcs_bucket = gcs_bucket or os.getenv("GCS_BUCKET", "prismatic-iris-429006-g6-clipscribe")
    
    @property
    def name(self) -> str:
        """Provider identifier."""
        return "whisperx-modal"
    
    @property
    def supports_diarization(self) -> bool:
        """WhisperX Modal supports speaker diarization."""
        return True
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        diarize: bool = True,
    ) -> TranscriptResult:
        """Transcribe audio file using WhisperX on Modal GPU.
        
        Args:
            audio_path: Path to local audio/video file
            language: Optional language code (auto-detected if None)
            diarize: Enable speaker diarization
            
        Returns:
            TranscriptResult with full Modal intelligence (segments, speakers, entities, etc.)
            
        Raises:
            ProcessingError: If Modal processing fails
        """
        try:
            # Upload audio to GCS
            gcs_input = await self._upload_to_gcs(audio_path)
            gcs_output = gcs_input.replace(Path(audio_path).suffix, "_results/")
            
            # Call existing Modal code (ALL features preserved!)
            # Modal SDK: Instantiate class, call .remote() on methods
            # Modal automatically handles connection to deployed app
            transcriber = self.transcriber_cls()
            modal_result = transcriber.transcribe_from_gcs.remote(
                gcs_input=gcs_input,
                gcs_output=gcs_output,
            )
            
            # Download results from GCS
            transcript_data = await self._download_from_gcs(f"{gcs_output}transcript.json")
            
            # Convert to standardized format
            # Note: Modal's transcript.json already has comprehensive data!
            segments = [
                TranscriptSegment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text", ""),
                    speaker=seg.get("speaker"),
                    words=seg.get("words"),
                    confidence=seg.get("confidence", 1.0),
                )
                for seg in transcript_data.get("segments", [])
            ]
            
            return TranscriptResult(
                segments=segments,
                language=transcript_data.get("language", "en"),
                duration=transcript_data.get("duration", 0),
                speakers=transcript_data.get("speakers", 0),
                word_level=True,
                provider="whisperx-modal",
                model="whisperx-large-v3",
                cost=transcript_data.get("cost", 0),
                metadata={
                    "gpu": "A10G",
                    "realtime_factor": transcript_data.get("realtime_factor"),
                    "cost_breakdown": transcript_data.get("cost_breakdown", {}),
                    "cache_stats": transcript_data.get("cache_stats", {}),
                    "gcs_output": gcs_output,
                }
            )
            
        except Exception as e:
            raise ProcessingError(f"Modal processing failed: {e}")
    
    def estimate_cost(self, duration_seconds: float) -> float:
        """Estimate WhisperX Modal processing cost.
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated cost in USD (A10G GPU + Grok extraction)
        """
        # A10G: $0.01836/min processing, ~10x realtime
        processing_minutes = (duration_seconds / 60) / 10
        gpu_cost = processing_minutes * 0.01836
        
        # Add typical Grok extraction cost
        grok_cost = 0.005  # Typical for 30min video
        
        return gpu_cost + grok_cost
    
    def validate_config(self) -> bool:
        """Validate WhisperX Modal configuration.
        
        Returns:
            True if Modal app available and GCS configured
        """
        try:
            # Check Modal app and class imported
            if not hasattr(self, 'modal_app') or not hasattr(self, 'transcriber_cls'):
                return False
            # Check GCS client
            if not hasattr(self, 'gcs_client'):
                return False
            return True
        except:
            return False
    
    async def _upload_to_gcs(self, local_path: str) -> str:
        """Upload local file to GCS.
        
        Args:
            local_path: Path to local audio file
            
        Returns:
            GCS URI (gs://bucket/path/to/file.mp3)
        """
        # Create unique path in GCS
        import uuid
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(local_path).name
        blob_path = f"temp/whisperx/{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
        
        # Upload
        bucket = self.gcs_client.bucket(self.gcs_bucket)
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(local_path)
        
        gcs_uri = f"gs://{self.gcs_bucket}/{blob_path}"
        return gcs_uri
    
    async def _download_from_gcs(self, gcs_path: str) -> dict:
        """Download and parse JSON from GCS.
        
        Args:
            gcs_path: GCS path (with or without gs:// prefix)
            
        Returns:
            Parsed JSON dict
        """
        # Parse GCS path
        if gcs_path.startswith("gs://"):
            parts = gcs_path[5:].split("/", 1)
            bucket_name = parts[0]
            blob_path = parts[1]
        else:
            bucket_name = self.gcs_bucket
            blob_path = gcs_path
        
        # Download
        bucket = self.gcs_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        # Download to temp file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
            blob.download_to_filename(f.name)
            with open(f.name) as json_file:
                return json.load(json_file)

