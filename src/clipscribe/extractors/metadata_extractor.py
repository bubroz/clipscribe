"""
Metadata Extractor for GEOINT Analysis.

Extracts KLV (Key-Length-Value) metadata from video files (MKV, TS, MPG)
compliant with MISB ST 0601 / STANAG 4609 standards.

Also supports consumer drone telemetry via subtitle track parsing (DJI/Autel).

Uses ffmpeg to stream data track and parses packets.
"""

import logging
import subprocess
from typing import Dict, List

from ..utils.klv.parser import KlvParser, parse_tlv
from ..utils.klv.registry import get_tag_def

# Configure logging
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts and parses KLV metadata from video files."""

    def __init__(self):
        pass

    def extract_metadata(self, video_path: str) -> List[Dict]:
        """
        Extract KLV metadata from a video file.

        Args:
            video_path: Path to the video file (MKV, TS, MPG)

        Returns:
            List of metadata packets with timestamps and telemetry
        """
        logger.info(f"Extracting metadata from {video_path}")

        # 1. Try KLV Extraction (Military/Gov Standard)
        klv_data = self._extract_klv(video_path)
        if klv_data:
            logger.info(f"Found {len(klv_data)} KLV packets.")
            return klv_data

        # 2. Try Subtitle Extraction (Consumer Drones - DJI/Autel)
        logger.info("No KLV metadata found. Checking for subtitle telemetry...")
        subtitle_data = self._extract_subtitle_telemetry(video_path)
        if subtitle_data:
            logger.info(f"Found {len(subtitle_data)} subtitle telemetry points.")
            return subtitle_data

        logger.warning("No telemetry found in video.")
        return []

    def _extract_klv(self, video_path: str) -> List[Dict]:
        """Extract MISB KLV metadata."""
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-map",
            "0:1",  # Data stream usually 0:1 or 0:d
            "-codec",
            "copy",
            "-f",
            "data",
            "-",
        ]

        telemetry_data = []

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=1024 * 1024
            )

            parser = KlvParser(process.stdout)

            for raw_packet_body in parser:
                packet_data = {}

                # raw_packet_body contains the TLV sequence (Value of the Universal Set)
                for tag, value_bytes in parse_tlv(raw_packet_body):
                    tag_def = get_tag_def(tag)

                    try:
                        decoded_value = tag_def.decoder(value_bytes)
                        packet_data[tag_def.name] = decoded_value
                    except Exception:
                        # logger.debug(f"Failed to decode tag {tag} ({tag_def.name}): {e}")
                        pass

                if packet_data:
                    telemetry_data.append(packet_data)

            return telemetry_data

        except Exception as e:
            logger.error(f"KLV extraction failed: {e}")
            return []

    def _extract_subtitle_telemetry(self, video_path: str) -> List[Dict]:
        """Extract telemetry from subtitle tracks (DJI/Autel)."""
        try:
            # Extract subtitle track 0 as text (srt)
            cmd = ["ffmpeg", "-i", video_path, "-map", "0:s:0", "-f", "srt", "-"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            stdout, _ = process.communicate()

            if not stdout:
                return []

            content = stdout.decode("utf-8", errors="ignore")

            from ..utils.dji_parser import SubtitleTelemetryParser

            parser = SubtitleTelemetryParser()
            return parser.parse_subtitle_track(content)

        except Exception as e:
            # Expected failure for videos without subtitles
            logger.debug(f"Subtitle extraction failed (likely no track): {e}")
            return []

    def correlate_with_transcript(
        self, metadata: List[Dict], transcript_segments: List[Dict]
    ) -> List[Dict]:
        """
        Correlate timestamped metadata with transcript segments.

        Args:
            metadata: List of telemetry points (must have 'PrecisionTimeStamp' or 'video_time')
            transcript_segments: List of transcript segments from WhisperX

        Returns:
            Enriched transcript segments with location data
        """
        # Note: Timestamp correlation requires video start time.
        # Metadata uses absolute Unix microsecond timestamps.
        # Transcript uses relative seconds from start.
        # We need to find the video start time from the metadata (first packet).

        if not metadata:
            return transcript_segments

        enriched_segments = []

        # Determine correlation mode: Absolute (KLV) or Relative (DJI)
        mode = "absolute"
        if "video_time" in metadata[0]:
            mode = "relative"

        start_time_seconds = 0.0
        if mode == "absolute":
            # Find start time (min timestamp in metadata)
            timestamps = [
                m.get("PrecisionTimeStamp") for m in metadata if "PrecisionTimeStamp" in m
            ]
            if not timestamps:
                logger.warning("No PrecisionTimeStamp found in KLV metadata; cannot correlate.")
                return transcript_segments
            start_time_micros = min(timestamps)
            start_time_seconds = start_time_micros / 1_000_000.0

        for segment in transcript_segments:
            seg_start = segment.get("start", 0)
            seg_end = segment.get("end", 0)

            points = []

            if mode == "absolute":
                # Calculate absolute time range for segment
                abs_start = start_time_seconds + seg_start
                abs_end = start_time_seconds + seg_end

                points = [
                    m
                    for m in metadata
                    if "PrecisionTimeStamp" in m and abs_start <= m["PrecisionTimeStamp"] <= abs_end
                ]
            else:
                # Relative correlation (DJI)
                points = [
                    m
                    for m in metadata
                    if "video_time" in m and seg_start <= m["video_time"] <= seg_end
                ]

            if points:
                # Attach centroid or first point
                center_point = points[len(points) // 2]

                segment["geoint"] = {
                    "lat": center_point.get("SensorLatitude"),
                    "lon": center_point.get("SensorLongitude"),
                    "alt": center_point.get("SensorTrueAltitude"),
                    "heading": center_point.get("PlatformHeadingAngle"),
                    "count": len(points),
                }

            enriched_segments.append(segment)

        return enriched_segments
