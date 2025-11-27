"""WhisperX local transcription provider for M3 Max (wraps existing WhisperXTranscriber)."""

import os
from typing import Optional

from dotenv import load_dotenv

from clipscribe.transcribers.whisperx_transcriber import (
    WhisperXTranscriber,
    WhisperXTranscriptionResult,
)

from ..base import (
    ConfigurationError,
    TranscriptionProvider,
    TranscriptResult,
    TranscriptSegment,
)

# Load environment variables (for HUGGINGFACE_TOKEN)
load_dotenv()


class WhisperXLocalProvider(TranscriptionProvider):
    """WhisperX local transcription on M3 Max (wraps existing WhisperXTranscriber).

    Features:
    - WhisperX large-v3
    - Speaker diarization (pyannote)
    - FREE ($0 processing cost)
    - Metal/CUDA/CPU support

    Note: Existing WhisperXTranscriber indicates faster-whisper doesn't support MPS yet,
    so it uses CPU on M3 Max. Performance still good (3-5x realtime on CPU).

    Performance (M3 Max 64GB, CPU mode):
    - ~3-5x realtime
    - 30min video: ~6-10min processing
    - FREE!

    Best for:
    - M3 Max local processing
    - Privacy-sensitive content
    - Cost-conscious processing
    - Offline/air-gapped environments

    Requires:
    - M3 Max Mac (or other Metal-capable GPU)
    - HuggingFace token for pyannote models (HF_TOKEN env var)

    Existing code: src/clipscribe/transcribers/whisperx_transcriber.py
    """

    def __init__(self):
        """Initialize WhisperX local provider.

        Raises:
            ConfigurationError: If HuggingFace token not set or WhisperX not installed
        """
        # Check HuggingFace token for diarization
        # Note: WhisperXTranscriber expects HUGGINGFACE_TOKEN (not HF_TOKEN)
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            raise ConfigurationError(
                "HUGGINGFACE_TOKEN required for speaker diarization.\n"
                "Get token from: https://huggingface.co/settings/tokens\n"
                "Set via: export HUGGINGFACE_TOKEN=your_token\n"
                "Or disable diarization: --no-diarize"
            )

        # Check if WhisperX can be imported
        try:
            import whisperx
        except ImportError:
            raise ConfigurationError(
                "WhisperX not installed.\n"
                "Install via: poetry install\n"
                "This includes whisperx and pyannote-audio."
            )

        # Reuse existing WhisperXTranscriber!
        # It auto-detects device (CUDA, MPS fallback to CPU, or CPU)
        try:
            self.transcriber = WhisperXTranscriber(
                model_name="large-v3",
                device=None,  # Auto-detect
                compute_type="float16",
                enable_diarization=True,
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize WhisperX: {e}\n" "Ensure WhisperX models can be downloaded."
            )

        # Store actual device used
        self.actual_device = self.transcriber.device

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "whisperx-local"

    @property
    def supports_diarization(self) -> bool:
        """WhisperX supports speaker diarization via pyannote."""
        return True

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        diarize: bool = True,
    ) -> TranscriptResult:
        """Transcribe audio file using local WhisperX.

        Args:
            audio_path: Path to audio/video file
            language: Optional language code
            diarize: Enable speaker diarization

        Returns:
            TranscriptResult with segments, speakers, and word-level timing
        """
        # Call existing transcriber (preserves all features!)
        # Note: Diarization is controlled at init time, not per-call
        result: WhisperXTranscriptionResult = await self.transcriber.transcribe_audio(
            audio_path=audio_path,
            language=language or "en",
        )

        # Convert word-level timestamps to segments
        segments = []
        if result.word_level_timestamps:
            # Group words into segments for consistency with other providers
            # WhisperX provides word-level, we'll keep it that way
            current_segment = []
            current_speaker = None
            segment_start = None

            for word_data in result.word_level_timestamps:
                word_speaker = word_data.get("speaker")

                # Start new segment on speaker change or if no current segment
                if current_speaker != word_speaker and current_segment:
                    # Save current segment
                    segments.append(
                        TranscriptSegment(
                            start=segment_start,
                            end=current_segment[-1].get("end", 0),
                            text=" ".join(w.get("word", "") for w in current_segment),
                            speaker=current_speaker,
                            words=current_segment,
                        )
                    )
                    current_segment = []
                    current_speaker = word_speaker
                    segment_start = word_data.get("start", 0)

                if not current_segment:
                    segment_start = word_data.get("start", 0)
                    current_speaker = word_speaker

                current_segment.append(word_data)

            # Add final segment
            if current_segment:
                segments.append(
                    TranscriptSegment(
                        start=segment_start,
                        end=current_segment[-1].get("end", 0),
                        text=" ".join(w.get("word", "") for w in current_segment),
                        speaker=current_speaker,
                        words=current_segment,
                    )
                )
        else:
            # Fallback: Single segment
            segments = [
                TranscriptSegment(
                    start=0.0,
                    end=result.duration,
                    text=result.text,
                    speaker=None,
                )
            ]

        # Count unique speakers
        speakers = len(set(seg.speaker for seg in segments if seg.speaker))

        return TranscriptResult(
            segments=segments,
            language=result.language,
            duration=result.duration,
            speakers=speakers,
            word_level=True,
            provider="whisperx-local",
            model=result.model,
            cost=0.0,  # FREE!
            metadata={
                "device": self.actual_device,
                "confidence": result.confidence,
                "speaker_segments": (
                    len(result.speaker_segments) if hasattr(result, "speaker_segments") else 0
                ),
            },
        )

    def estimate_cost(self, duration_seconds: float) -> float:
        """WhisperX local is FREE!

        Args:
            duration_seconds: Audio duration (unused)

        Returns:
            0.0 (no cost for local processing)
        """
        return 0.0

    def validate_config(self) -> bool:
        """Validate WhisperX local configuration.

        Returns:
            True if HUGGINGFACE_TOKEN set and WhisperX available
        """
        # Note: WhisperXTranscriber expects HUGGINGFACE_TOKEN
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            return False

        try:
            import whisperx

            return True
        except ImportError:
            return False
