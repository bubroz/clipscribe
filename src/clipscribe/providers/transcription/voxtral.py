"""Voxtral transcription provider (wraps existing VoxtralTranscriber)."""

import os
from typing import Optional

from clipscribe.transcribers.voxtral_transcriber import (
    VoxtralTranscriber,
    VoxtralTranscriptionResult,
)

from ..base import (
    ConfigurationError,
    TranscriptionProvider,
    TranscriptResult,
    TranscriptSegment,
)


class VoxtralProvider(TranscriptionProvider):
    """Mistral Voxtral API transcription (wraps existing VoxtralTranscriber).

    Features:
    - Mistral API integration with retry logic
    - $0.001/min cost (18x cheaper than GPU)
    - NO speaker diarization support

    Best for:
    - Single-speaker content (monologues, lectures, audiobooks)
    - Surveillance footage transcription
    - Budget-conscious processing

    Not suitable for:
    - Interviews, podcasts, meetings (use whisperx-modal or whisperx-local)

    Existing code: src/clipscribe/transcribers/voxtral_transcriber.py
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Voxtral provider.

        Args:
            api_key: Mistral API key (or from MISTRAL_API_KEY env var)

        Raises:
            ConfigurationError: If API key not provided
        """
        try:
            # Reuse existing VoxtralTranscriber!
            self.transcriber = VoxtralTranscriber(api_key=api_key or os.getenv("MISTRAL_API_KEY"))
        except ValueError as e:
            raise ConfigurationError(
                f"Voxtral configuration error: {e}\n"
                f"Set MISTRAL_API_KEY environment variable.\n"
                f"Get key from: https://console.mistral.ai"
            )

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "voxtral"

    @property
    def supports_diarization(self) -> bool:
        """Voxtral does not support speaker diarization (Nov 2025)."""
        return False

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        diarize: bool = True,
    ) -> TranscriptResult:
        """Transcribe audio file using Voxtral.

        Args:
            audio_path: Path to audio/video file
            language: Optional language code
            diarize: Must be False (Voxtral doesn't support speakers)

        Returns:
            TranscriptResult with segments and metadata

        Raises:
            ValueError: If diarize=True (not supported)
        """
        if diarize:
            raise ValueError(
                "Voxtral does not support speaker diarization.\n"
                "Use --transcription-provider whisperx-modal or whisperx-local for multi-speaker content."
            )

        # Call existing transcriber (preserves all features!)
        result: VoxtralTranscriptionResult = await self.transcriber.transcribe_audio(
            audio_path=audio_path,
            language=language,
        )

        # Convert to standardized format
        segments = []
        if result.segments:
            # Voxtral provides segment data
            segments = [
                TranscriptSegment(
                    start=seg.get("start", 0.0),
                    end=seg.get("end", 0.0),
                    text=seg.get("text", ""),
                    speaker=None,  # Voxtral doesn't provide speakers
                    confidence=seg.get("confidence", 1.0),
                )
                for seg in result.segments
            ]
        else:
            # Fallback: Single segment with full text
            segments = [
                TranscriptSegment(
                    start=0.0,
                    end=result.duration,
                    text=result.text,
                    speaker=None,
                )
            ]

        return TranscriptResult(
            segments=segments,
            language=result.language,
            duration=result.duration,
            speakers=0,  # No speaker diarization
            word_level=False,
            provider="voxtral",
            model=result.model,
            cost=result.cost,
            metadata={
                "confidence": result.confidence,
            },
        )

    def estimate_cost(self, duration_seconds: float) -> float:
        """Estimate Voxtral processing cost.

        Args:
            duration_seconds: Audio duration in seconds

        Returns:
            Estimated cost in USD ($0.001/min)
        """
        return (duration_seconds / 60) * 0.001

    def validate_config(self) -> bool:
        """Validate Voxtral configuration.

        Returns:
            True if API key is set, False otherwise
        """
        return bool(self.transcriber.api_key)
