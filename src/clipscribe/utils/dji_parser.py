"""
DJI/Consumer Drone Telemetry Parser.

Parses text-based telemetry found in subtitle tracks (SRT/ASS) of consumer drones
(DJI, Autel, etc.).
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SubtitleTelemetryParser:
    """Parses subtitle text for embedded telemetry."""

    def __init__(self):
        # Regex patterns for DJI SRT
        # Format: [latitude: 34.05223] [longitude: -118.24368] [rel_alt: 10.500 abs_alt: 150.200]
        self.dji_pattern = re.compile(
            r"\[latitude:\s*([-+]?\d*\.\d+)\]\s*\[longitude:\s*([-+]?\d*\.\d+)\]"
        )
        self.dji_alt_pattern = re.compile(
            r"\[rel_alt:\s*([-+]?\d*\.\d+)\s*abs_alt:\s*([-+]?\d*\.\d+)\]"
        )

        # Regex patterns for Autel/Other
        # GPS(34.0522, -118.2437, 15)
        self.autel_pattern = re.compile(
            r"GPS\(\s*([-+]?\d*\.\d+),\s*([-+]?\d*\.\d+),\s*([-+]?\d*\.\d+)"
        )

    def parse_subtitle_track(self, subtitle_content: str) -> List[Dict]:
        """
        Parse full subtitle content into telemetry points.

        Args:
            subtitle_content: Raw content of the .srt file

        Returns:
            List of normalized telemetry dictionaries
        """
        telemetry = []
        # Split by blocks (double newline usually separates SRT blocks)
        blocks = subtitle_content.strip().split("\n\n")

        for block in blocks:
            point = self._parse_block(block)
            if point:
                telemetry.append(point)

        return telemetry

    def _parse_block(self, block: str) -> Optional[Dict]:
        """Parse a single subtitle block."""
        lines = block.split("\n")
        if len(lines) < 3:
            return None  # Invalid block

        # Line 1: Index
        # Line 2: Timestamp (00:00:00,000 --> 00:00:01,000)
        # Line 3+: Content

        timestamp_line = lines[1]
        content = " ".join(lines[2:])  # Join rest

        # Parse Timestamp
        # We take the start time of the subtitle as the point time
        try:
            start_str = timestamp_line.split("-->")[0].strip()
            seconds = self._srt_time_to_seconds(start_str)
        except Exception:
            return None  # Skip if bad timestamp

        # Parse Telemetry
        lat = None
        lon = None
        alt = None

        # Try DJI
        dji_match = self.dji_pattern.search(content)
        if dji_match:
            lat = float(dji_match.group(1))
            lon = float(dji_match.group(2))

            alt_match = self.dji_alt_pattern.search(content)
            if alt_match:
                alt = float(alt_match.group(2))  # Use abs_alt
            else:
                alt = 0.0  # Fallback

        # Try Autel if no DJI
        if lat is None:
            autel_match = self.autel_pattern.search(content)
            if autel_match:
                lat = float(autel_match.group(1))
                lon = float(autel_match.group(2))
                alt = float(autel_match.group(3))

        if lat is not None and lon is not None:
            # Normalize to our schema
            # ST 0601 Mapping:
            # SensorLatitude -> lat
            # SensorLongitude -> lon
            # SensorTrueAltitude -> alt
            # PrecisionTimeStamp -> synthesize from video time?
            # Since we don't have absolute time, we might rely on relative correlation only.
            # Or we can assume file start time if available.

            # We map to the same keys as KLV so downstream processors work seamlessly
            return {
                "SensorLatitude": lat,
                "SensorLongitude": lon,
                "SensorTrueAltitude": alt,
                "video_time": seconds,  # Special field for relative correlation
                # Synthesize a timestamp relative to an epoch if needed, or leave empty
                # "PrecisionTimeStamp": ...
            }

        return None

    def _srt_time_to_seconds(self, time_str: str) -> float:
        """Convert '00:00:01,500' to 1.5"""
        # HH:MM:SS,mmm
        parts = time_str.replace(",", ".").split(":")
        if len(parts) != 3:
            return 0.0

        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds
