"""
Generate Demo Interactive Map.

Creates a sample HTML map using extracted telemetry and mock events.
Demonstrates the 'Visual Observer' capability.
"""

import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from clipscribe.exporters.geoint_exporter import GeoIntExporter

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    telemetry_path = "test_videos/geoint/day_flight_telemetry.json"
    output_dir = Path("test_videos/geoint")
    
    print(f"Loading telemetry from: {telemetry_path}")
    
    try:
        with open(telemetry_path, 'r') as f:
            telemetry = json.load(f)
    except FileNotFoundError:
        print("Error: Telemetry file not found. Run 'extract_full_telemetry.py' first.")
        return

    print(f"Loaded {len(telemetry)} points.")
    
    # Mock Visual Observations (simulating Grok output)
    # We need to find valid timestamps in the telemetry to correlate
    # Telemetry has 'PrecisionTimeStamp' (Unix micros)
    
    if not telemetry:
        print("No telemetry data.")
        return

    # Find start/end times
    timestamps = [p['PrecisionTimeStamp'] for p in telemetry if 'PrecisionTimeStamp' in p]
    start_micros = min(timestamps)
    
    # Create synthetic events at T+10s, T+60s, T+120s
    mock_events = []
    
    event_offsets = [
        (10, "Visual: Vehicle moving East on main road"),
        (45, "Visual: Person observed near building entrance"),
        (90, "Visual: Target compound in view"),
        (150, "Visual: Convoy forming at intersection")
    ]
    
    from clipscribe.processors.geo_correlator import GeoCorrelator
    
    # We use the Correlator to find the right location for these times
    correlator = GeoCorrelator(telemetry)
    
    # Create dummy transcript segments to feed the correlator
    segments = []
    for offset, text in event_offsets:
        segments.append({
            "start": offset,
            "end": offset + 2.0,
            "text": text
        })
        
    print("Correlating events...")
    enriched_events = correlator.correlate(segments)
    
    # Generate Map
    exporter = GeoIntExporter(output_dir)
    map_path = exporter.export_interactive_map(telemetry, enriched_events, filename="demo_mission_map.html")
    
    print(f"\nSUCCESS: Interactive map generated at:")
    print(f"{map_path}")
    print("\nOpen this file in your browser to see the flight path and events.")

if __name__ == "__main__":
    main()

