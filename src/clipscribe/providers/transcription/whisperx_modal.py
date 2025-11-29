"""WhisperX Modal GPU transcription provider (wraps existing station10_modal.py)."""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account

from ..base import (
    ConfigurationError,
    ProcessingError,
    TranscriptionProvider,
    TranscriptResult,
    TranscriptSegment,
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
            from deploy.station10_modal import ClipScribeTranscriber, app

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
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info
            )
            self.gcs_client = storage.Client(credentials=credentials)
        elif creds_path:
            # Use service account file
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            self.gcs_client = storage.Client(credentials=credentials)
        else:
            # Try Application Default Credentials (works in Cloud Run, GKE, etc.)
            try:
                self.gcs_client = storage.Client()
            except Exception as e:
                raise ConfigurationError(
                    f"GCS credentials required for Modal provider: {e}\n"
                    "Set one of:\n"
                    "  export SERVICE_ACCOUNT_JSON='{...}'\n"
                    "  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json\n"
                    "Or run in GCP environment with Workload Identity"
                )

        # GCS bucket for temp storage
        self.gcs_bucket = gcs_bucket or os.getenv("GCS_BUCKET", "your-bucket-name")

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
            # Remove file extension, add _results (no trailing slash - Modal adds it)
            gcs_output = gcs_input.replace(Path(audio_path).suffix, "_results")

            # Call existing Modal code (ALL features preserved!)
            # Modal SDK: Must run within app context for @app.cls methods
            with self.modal_app.run():
                transcriber = self.transcriber_cls()
                transcriber.transcribe_from_gcs.remote(
                    gcs_input=gcs_input,
                    gcs_output=gcs_output,
                )

            # Modal returns status dict, not full transcript
            # Results were uploaded to GCS by Modal
            # Download BOTH files from GCS (comprehensive data)
            # Note: gcs_output is like "gs://bucket/path/file_results" (no trailing slash)
            transcript_json_path = f"{gcs_output}/transcript.json"
            metadata_json_path = f"{gcs_output}/metadata.json"

            transcript_data = await self._download_from_gcs(transcript_json_path)
            metadata_data = await self._download_from_gcs(metadata_json_path)

            # Convert to standardized format
            # Note: Modal's transcript.json has ALL data (segments with word-level speakers)
            segments = [
                TranscriptSegment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text", ""),
                    speaker=seg.get("speaker"),  # Segment-level speaker
                    words=seg.get("words"),  # Word-level includes speaker attribution
                    confidence=seg.get("confidence", 1.0),
                )
                for seg in transcript_data.get("segments", [])
            ]

            # Extract language and speakers from metadata.json (more reliable)
            # transcript.json may have null values at root level
            language = metadata_data.get("language", "en")
            speakers_count = metadata_data.get("speakers", 0)

            # If metadata.json doesn't have speakers, count from segments
            if speakers_count == 0 and segments:
                # Count unique speakers from word-level data
                unique_speakers = set()
                for seg in transcript_data.get("segments", []):
                    for word in seg.get("words", []):
                        speaker = word.get("speaker")
                        if speaker:
                            unique_speakers.add(speaker)
                speakers_count = len(unique_speakers)

            # Get cost and performance metrics
            duration = metadata_data.get("duration_minutes", 0) * 60
            processing_cost = transcript_data.get("cost", metadata_data.get("cost", 0))

            return TranscriptResult(
                segments=segments,
                language=language,
                duration=duration,
                speakers=speakers_count,
                word_level=True,
                provider="whisperx-modal",
                model="whisperx-large-v3",
                cost=processing_cost,
                metadata={
                    "gpu": "A10G",
                    "realtime_factor": metadata_data.get("realtime_factor"),
                    "processing_minutes": metadata_data.get("processing_minutes"),
                    "cost_breakdown": transcript_data.get("cost_breakdown", {}),
                    "cache_stats": transcript_data.get("cache_stats", {}),
                    "gcs_output": gcs_output,
                },
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
            if not hasattr(self, "modal_app") or not hasattr(self, "transcriber_cls"):
                return False
            # Check GCS client
            if not hasattr(self, "gcs_client"):
                return False
            return True
        except Exception:
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
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
            blob.download_to_filename(f.name)
            with open(f.name) as json_file:
                return json.load(json_file)
