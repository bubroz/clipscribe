"""
Segment-based utilities for search and export.

Provides tools to search within segments and export to various subtitle formats.
"""

import json
import logging
import re
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class SegmentSearcher:
    """Search within transcript segments."""

    def __init__(self, segments: List[Dict[str, any]]):
        """
        Initialize with segments.

        Args:
            segments: List of segment dictionaries with text, start_time, end_time
        """
        self.segments = segments
        self._build_index()

    def _build_index(self):
        """Build search index for faster lookups."""
        self.text_index = {}
        for i, segment in enumerate(self.segments):
            text = segment.get("text", "").lower()
            words = text.split()
            for word in words:
                # Strip punctuation
                word = re.sub(r"[^\w\s]", "", word)
                if word:
                    if word not in self.text_index:
                        self.text_index[word] = []
                    self.text_index[word].append(i)

    def search(
        self,
        query: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        context_chars: int = 50,
    ) -> List[Dict]:
        """
        Search for query in segments.

        Args:
            query: Search query
            case_sensitive: Whether to match case
            whole_word: Match whole words only
            context_chars: Characters of context to show

        Returns:
            List of matching segments with metadata
        """
        results = []

        # Prepare search pattern
        if whole_word:
            pattern = r"\b" + re.escape(query) + r"\b"
        else:
            pattern = re.escape(query)

        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        for i, segment in enumerate(self.segments):
            text = segment.get("text", "")
            matches = list(regex.finditer(text))

            if matches:
                # Get context around matches
                contexts = []
                for match in matches:
                    start = max(0, match.start() - context_chars)
                    end = min(len(text), match.end() + context_chars)

                    context = text[start:end]
                    if start > 0:
                        context = "..." + context
                    if end < len(text):
                        context = context + "..."

                    contexts.append(
                        {"text": context, "match_start": match.start(), "match_end": match.end()}
                    )

                results.append(
                    {
                        "segment_index": i,
                        "start_time": segment.get("start_time", 0),
                        "end_time": segment.get("end_time", 0),
                        "text": text,
                        "matches": len(matches),
                        "contexts": contexts,
                        "timestamp": self._format_timestamp(segment.get("start_time", 0)),
                    }
                )

        return results

    def search_phrase(self, phrase: str, max_gap: int = 3) -> List[Dict]:
        """
        Search for a phrase that might span segments.

        Args:
            phrase: Multi-word phrase to search
            max_gap: Maximum segment gap to consider

        Returns:
            List of matching segment ranges
        """
        words = phrase.lower().split()
        if not words:
            return []

        results = []

        for i in range(len(self.segments)):
            # Check if phrase starts in this segment
            self.segments[i].get("text", "").lower()

            # Try to match the phrase starting here
            matched_segments = []
            remaining_words = words.copy()

            for j in range(i, min(i + max_gap, len(self.segments))):
                current_text = self.segments[j].get("text", "").lower()

                # Check how many words we can match
                current_text.split()
                matched_in_segment = []

                for word in remaining_words[:]:
                    if word in current_text:
                        matched_in_segment.append(word)
                        remaining_words.remove(word)
                        if not remaining_words:
                            break

                if matched_in_segment:
                    matched_segments.append(j)

                if not remaining_words:
                    # Found complete phrase
                    results.append(
                        {
                            "phrase": phrase,
                            "segment_range": (i, j),
                            "segments": matched_segments,
                            "start_time": self.segments[i].get("start_time", 0),
                            "end_time": self.segments[j].get("end_time", 0),
                            "timestamp": self._format_timestamp(
                                self.segments[i].get("start_time", 0)
                            ),
                        }
                    )
                    break

        return results

    def get_context(self, segment_index: int, before: int = 1, after: int = 1) -> Dict:
        """
        Get segment with surrounding context.

        Args:
            segment_index: Index of target segment
            before: Number of segments before
            after: Number of segments after

        Returns:
            Dictionary with target and context segments
        """
        start_idx = max(0, segment_index - before)
        end_idx = min(len(self.segments), segment_index + after + 1)

        return {
            "target": self.segments[segment_index],
            "before": self.segments[start_idx:segment_index],
            "after": self.segments[segment_index + 1 : end_idx],
            "full_text": " ".join(s.get("text", "") for s in self.segments[start_idx:end_idx]),
        }

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class SubtitleExporter:
    """Export segments to subtitle formats."""

    @staticmethod
    def to_srt(segments: List[Dict[str, any]], output_path: Optional[Path] = None) -> str:
        """
        Convert segments to SRT format.

        Args:
            segments: List of segments with text, start_time, end_time
            output_path: Optional path to save SRT file

        Returns:
            SRT formatted string
        """
        srt_lines = []

        for i, segment in enumerate(segments, 1):
            # Format: 00:00:00,000
            start = SubtitleExporter._seconds_to_srt_time(segment.get("start_time", 0))
            end = SubtitleExporter._seconds_to_srt_time(segment.get("end_time", 0))
            text = segment.get("text", "").strip()

            # Skip empty segments
            if not text:
                continue

            srt_lines.append(str(i))
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")  # Empty line between subtitles

        srt_content = "\n".join(srt_lines)

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(srt_content, encoding="utf-8")
            logger.info(f"SRT file saved to: {output_path}")

        return srt_content

    @staticmethod
    def to_vtt(segments: List[Dict[str, any]], output_path: Optional[Path] = None) -> str:
        """
        Convert segments to WebVTT format.

        Args:
            segments: List of segments
            output_path: Optional path to save VTT file

        Returns:
            VTT formatted string
        """
        vtt_lines = ["WEBVTT", ""]

        for segment in segments:
            start = SubtitleExporter._seconds_to_vtt_time(segment.get("start_time", 0))
            end = SubtitleExporter._seconds_to_vtt_time(segment.get("end_time", 0))
            text = segment.get("text", "").strip()

            if not text:
                continue

            vtt_lines.append(f"{start} --> {end}")
            vtt_lines.append(text)
            vtt_lines.append("")

        vtt_content = "\n".join(vtt_lines)

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(vtt_content, encoding="utf-8")
            logger.info(f"VTT file saved to: {output_path}")

        return vtt_content

    @staticmethod
    def to_youtube_chapters(
        segments: List[Dict[str, any]], min_chapter_duration: float = 10.0
    ) -> str:
        """
        Convert segments to YouTube chapter format.

        Args:
            segments: List of segments
            min_chapter_duration: Minimum duration for a chapter (YouTube requires 10s)

        Returns:
            YouTube chapter formatted string
        """
        chapters = []
        current_chapter = None

        for segment in segments:
            start_time = segment.get("start_time", 0)
            text = segment.get("text", "").strip()

            if not text:
                continue

            # Merge short segments
            if current_chapter:
                duration = start_time - current_chapter["start"]
                if duration < min_chapter_duration:
                    # Extend current chapter
                    current_chapter["text"] += " " + text
                    current_chapter["end"] = segment.get("end_time", start_time)
                    continue

            # Start new chapter
            if current_chapter:
                chapters.append(current_chapter)

            current_chapter = {
                "start": start_time,
                "end": segment.get("end_time", start_time),
                "text": text[:100],  # YouTube has character limits
            }

        # Add last chapter
        if current_chapter:
            chapters.append(current_chapter)

        # Format chapters
        chapter_lines = []
        for chapter in chapters:
            timestamp = SubtitleExporter._seconds_to_youtube_time(chapter["start"])
            # Clean text for chapter title
            title = re.sub(r"\s+", " ", chapter["text"])[:60]
            chapter_lines.append(f"{timestamp} {title}")

        return "\n".join(chapter_lines)

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT time format (00:00:00,000)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _seconds_to_vtt_time(seconds: float) -> str:
        """Convert seconds to VTT time format (00:00:00.000)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @staticmethod
    def _seconds_to_youtube_time(seconds: float) -> str:
        """Convert seconds to YouTube time format (0:00 or 1:23:45)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"


def load_segments_from_output(output_dir: Union[str, Path]) -> Optional[List[Dict]]:
    """
    Load segments from ClipScribe output directory.

    Args:
        output_dir: Path to output directory

    Returns:
        List of segments or None if not found
    """
    output_dir = Path(output_dir)
    core_file = output_dir / "core.json"

    if not core_file.exists():
        logger.error(f"Core file not found: {core_file}")
        return None

    try:
        with open(core_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("transcript_segments", [])
        if not segments:
            logger.warning("No segments found in core.json")

        return segments
    except Exception as e:
        logger.error(f"Error loading segments: {e}")
        return None
