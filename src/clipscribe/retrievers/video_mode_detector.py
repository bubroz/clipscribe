"""
Video Mode Detector - Intelligently choose between audio-only and full video processing.

This module analyzes video characteristics to determine if visual content is important
for transcription accuracy 
"""

import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import subprocess
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class VideoAnalysis:
    """Results of video content analysis."""

    has_slides: bool = False
    has_code: bool = False
    has_diagrams: bool = False
    has_significant_text: bool = False
    scene_changes_per_minute: float = 0.0
    recommended_mode: str = "audio"  # "audio" or "video"
    confidence: float = 0.0
    reasoning: str = ""


class VideoModeDetector:
    """
    Detect whether a video needs visual processing or audio-only is sufficient.

    This saves costs by only using video mode when visual content adds value.
    """

    # Thresholds for detection
    SCENE_CHANGE_THRESHOLD = 5.0  # scenes per minute
    TEXT_DETECTION_THRESHOLD = 0.3  # 30% of frames with text

    def __init__(self):
        """Initialize the video mode detector."""
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("ffmpeg not found - will default to audio mode")
            return False

    async def analyze_video(self, video_path: str) -> VideoAnalysis:
        """
        Analyze video to determine if visual content is important.

        Args:
            video_path: Path to video file

        Returns:
            VideoAnalysis with recommendations
        """
        analysis = VideoAnalysis()

        if not self.ffmpeg_available:
            analysis.reasoning = "ffmpeg not available - defaulting to audio mode"
            return analysis

        try:
            # 1. Detect scene changes (indicates visual content variation)
            scene_changes = await self._detect_scene_changes(video_path)
            analysis.scene_changes_per_minute = scene_changes

            # 2. Sample frames for text detection
            has_text, text_confidence = await self._detect_text_in_frames(video_path)
            analysis.has_significant_text = has_text

            # 3. Check video metadata for clues
            metadata = await self._get_video_metadata(video_path)

            # 4. Make recommendation
            analysis = self._make_recommendation(analysis, metadata)

        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            analysis.reasoning = f"Analysis failed: {e}"

        return analysis

    async def _detect_scene_changes(self, video_path: str) -> float:
        """Detect scene changes per minute."""
        try:
            # Use ffmpeg scene detection
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-vf",
                "select='gt(scene,0.4)',showinfo",
                "-f",
                "null",
                "-",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # Count scene changes from output
            scene_count = len(re.findall(r"Parsed_showinfo", result.stderr))

            # Get video duration
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})", result.stderr)
            if duration_match:
                hours, minutes, seconds = map(int, duration_match.groups())
                total_minutes = hours * 60 + minutes + seconds / 60

                if total_minutes > 0:
                    return scene_count / total_minutes

        except Exception as e:
            logger.error(f"Scene detection failed: {e}")

        return 0.0

    async def _detect_text_in_frames(self, video_path: str) -> Tuple[bool, float]:
        """Sample frames and detect if they contain significant text."""
        # This is a simplified version - in production you'd use OCR
        # For now, we'll use heuristics based on video type

        # Check if filename suggests content type
        filename_lower = video_path.lower()

        # High text probability patterns
        text_patterns = [
            "tutorial",
            "course",
            "lecture",
            "presentation",
            "slides",
            "code",
            "programming",
            "demo",
        ]

        for pattern in text_patterns:
            if pattern in filename_lower:
                return True, 0.8

        # Low text probability patterns
        audio_patterns = ["podcast", "interview", "discussion", "briefing", "news", "talk"]

        for pattern in audio_patterns:
            if pattern in filename_lower:
                return False, 0.2

        return False, 0.5

    async def _get_video_metadata(self, video_path: str) -> Dict:
        """Get video metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                video_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return json.loads(result.stdout)

        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return {}

    def _make_recommendation(self, analysis: VideoAnalysis, metadata: Dict) -> VideoAnalysis:
        """Make recommendation based on analysis."""
        reasons = []
        video_score = 0

        # Check scene changes
        if analysis.scene_changes_per_minute > self.SCENE_CHANGE_THRESHOLD:
            video_score += 30
            reasons.append(f"High scene changes ({analysis.scene_changes_per_minute:.1f}/min)")

        # Check for text
        if analysis.has_significant_text:
            video_score += 40
            reasons.append("Significant text detected")

        # Check resolution (high res often means detailed content)
        for stream in metadata.get("streams", []):
            if stream.get("codec_type") == "video":
                height = stream.get("height", 0)
                if height >= 1080:
                    video_score += 10
                    reasons.append("High resolution video")

        # Make decision
        if video_score >= 50:
            analysis.recommended_mode = "video"
            analysis.confidence = min(video_score / 100, 0.95)
            analysis.reasoning = "Visual content important: " + ", ".join(reasons)
        else:
            analysis.recommended_mode = "audio"
            analysis.confidence = 1.0 - (video_score / 100)
            analysis.reasoning = "Audio sufficient: " + (
                ", ".join(reasons) if reasons else "Standard video content"
            )

        # Special cases
        if "code" in analysis.reasoning.lower() or "slides" in analysis.reasoning.lower():
            analysis.has_code = True
            analysis.has_slides = True

        return analysis


class SmartVideoRetriever:
    """
    Enhanced video retriever that intelligently chooses processing mode.
    """

    def __init__(self):
        self.mode_detector = VideoModeDetector()

    async def process_video(self, url: str, force_mode: Optional[str] = None):
        """
        Process video with intelligent mode selection.

        Args:
            url: Video URL
            force_mode: Force "audio" or "video" mode
        """
        if force_mode:
            mode = force_mode
            analysis = VideoAnalysis(recommended_mode=mode, reasoning=f"Forced {mode} mode")
        else:
            # Download small portion to analyze
            # Run detection
            analysis = await self.mode_detector.analyze_video("sample.mp4")
            mode = analysis.recommended_mode

        logger.info(f"Using {mode} mode: {analysis.reasoning}")

        if mode == "video":
            # Use video processing pipeline
            return await self._process_with_video(url)
        else:
            # Use current audio-only approach
            return await self._process_with_audio(url)

    async def _process_with_audio(self, url: str):
        """Process video using audio-only mode."""
        # Placeholder implementation - would integrate with actual video processor
        return {"mode": "audio", "url": url, "status": "processed"}

    async def _process_with_video(self, url: str):
        """Process video using full video mode."""
        # Placeholder implementation - would integrate with actual video processor
        return {"mode": "video", "url": url, "status": "processed"}
