"""Video Transcriber Module - Handles video transcription and analysis."""

import asyncio
import logging
from typing import Dict, Any, Optional

from ..models import VideoTranscript, VideoIntelligence
from .transcriber import GeminiFlashTranscriber
from ..utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class VideoTranscriber:
    """Handles video transcription and initial analysis."""

    def __init__(
        self,
        use_pro: bool = True,
        performance_monitor: Optional[PerformanceMonitor] = None,
        api_key: Optional[str] = None
    ):
        """Initialize the video transcriber."""
        self.use_pro = use_pro
        self.performance_monitor = performance_monitor

        self.transcriber = GeminiFlashTranscriber(
            api_key=api_key,
            performance_monitor=performance_monitor,
            use_pro=use_pro
        )

    async def transcribe_video(
        self,
        media_file: str,
        metadata: Any,
        duration: int
    ) -> Dict[str, Any]:
        """
        Transcribe video and return analysis results.

        Args:
            media_file: Path to the video file
            metadata: Video metadata object
            duration: Video duration in seconds

        Returns:
            Dictionary containing transcription analysis

        Raises:
            Exception: If transcription fails
        """
        try:
            logger.info(f"Transcribing video: {metadata.title}")

            # Choose transcription method based on duration
            if duration > 900:  # 15 minutes threshold
                analysis = await self.transcriber.transcribe_large_video(
                    media_file, metadata, duration
                )
            else:
                analysis = await self.transcriber.transcribe_video(
                    media_file, metadata, duration
                )

            if not analysis or "error" in analysis:
                error_msg = analysis.get("error", "Unknown error") if analysis else "No analysis returned"
                raise Exception(f"Transcription failed: {error_msg}")

            logger.info(f"Successfully transcribed: {metadata.title}")
            return analysis

        except Exception as e:
            logger.error(f"Transcription failed for {media_file}: {e}")
            raise

    def create_transcript_object(
        self,
        analysis: Dict[str, Any],
        duration: int
    ) -> VideoTranscript:
        """
        Create VideoTranscript object from analysis results.

        Args:
            analysis: Transcription analysis results
            duration: Video duration in seconds

        Returns:
            VideoTranscript object
        """
        # Handle None analysis
        if analysis is None:
            analysis = {}

        # Generate time-based segments (placeholder implementation)
        segments = self._generate_segments(
            analysis.get("transcript", ""),
            duration
        )

        return VideoTranscript(
            full_text=analysis.get("transcript", ""),
            segments=segments,
            language=analysis.get("language", "en"),
            confidence=analysis.get("confidence_score", 0.95),
        )

    def _generate_segments(
        self,
        text: str,
        duration: int,
        segment_length: int = 30
    ) -> list:
        """
        Generate time-based segments from transcript.

        Args:
            text: Full transcript text
            duration: Video duration in seconds
            segment_length: Target segment length in seconds

        Returns:
            List of segment dictionaries
        """
        if not text:
            return []

        # Split text into words
        words = text.split()
        if not words:
            return []

        # Calculate words per segment
        total_segments = max(1, duration // segment_length)
        words_per_segment = len(words) / total_segments

        # Ensure step is at least 1
        segment_word_count = max(1, int(words_per_segment))

        segments = []

        for i in range(0, len(words), segment_word_count):
            # Calculate time boundaries
            start_time = (i / len(words)) * duration
            end_time = min(((i + segment_word_count) / len(words)) * duration, duration)

            # Get segment text
            segment_words = words[i : i + segment_word_count]
            segment_text = " ".join(segment_words)

            if segment_text.strip():  # Only add non-empty segments
                segments.append(
                    {
                        "start": round(start_time, 2),
                        "end": round(end_time, 2),
                        "text": segment_text.strip(),
                    }
                )

        # Ensure last segment ends at video duration
        if segments:
            segments[-1]["end"] = duration

        logger.debug(f"Generated {len(segments)} segments from {duration}s video")
        return segments

    def get_transcription_cost(self, analysis: Dict[str, Any]) -> float:
        """Extract processing cost from analysis."""
        if analysis is None:
            return 0.0
        return analysis.get("processing_cost", 0.0)
