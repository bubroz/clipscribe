"""
GEOINT Processor.

Orchestrates the full Geospatial Intelligence pipeline:
1. Extract KLV metadata
2. Correlate with transcript
3. Generate visualization (KML)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..exporters.geoint_exporter import GeoIntExporter
from ..extractors.metadata_extractor import MetadataExtractor
from ..processors.geo_correlator import GeoCorrelator

logger = logging.getLogger(__name__)


class GeoIntProcessor:
    """Orchestrator for GEOINT analysis."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.extractor = MetadataExtractor()
        self.exporter = GeoIntExporter(output_dir)

    def process(self, video_path: str, transcript_segments: List[Dict]) -> Optional[Dict]:
        """
        Run the GEOINT pipeline.

        Returns:
            Dict containing GEOINT results (telemetry, correlated events) or None if no data found.
        """
        logger.info(f"Starting GEOINT processing for {video_path}")

        try:
            # 1. Extract Telemetry
            telemetry = self.extractor.extract_metadata(video_path)

            if not telemetry:
                logger.info("No KLV metadata found. Skipping GEOINT analysis.")
                return None

            logger.info(f"Extracted {len(telemetry)} telemetry packets.")

            # 2. Correlate with Transcript
            if transcript_segments:
                try:
                    correlator = GeoCorrelator(telemetry)
                    enriched_segments = correlator.correlate(transcript_segments)

                    # Filter for segments that have geoint data
                    geo_events = [s for s in enriched_segments if "geoint" in s]
                    logger.info(
                        f"Correlated {len(geo_events)} transcript segments with location data."
                    )
                except Exception as e:
                    logger.error(f"Correlation failed: {e}")
                    enriched_segments = transcript_segments  # Fallback to original
                    geo_events = []
            else:
                logger.warning("No transcript segments provided for correlation.")
                enriched_segments = []
                geo_events = []

            # 3. Export KML
            try:
                kml_path = self.exporter.export_kml(telemetry, geo_events, filename="mission.kml")
            except Exception as e:
                logger.error(f"KML export failed: {e}")
                return None

            return {
                "telemetry_count": len(telemetry),
                "geo_events_count": len(geo_events),
                "kml_path": str(kml_path),
                "enriched_segments": enriched_segments,
            }

        except Exception as e:
            logger.error(f"Critical error in GEOINT pipeline: {e}")
            # Return None so main pipeline continues without GEOINT
            return None
