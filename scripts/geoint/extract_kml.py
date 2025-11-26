"""
Extract KML Flight Path.

Generates a Google Earth KML file from video telemetry.
Visualizes the drone path and camera footprint.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from clipscribe.extractors.metadata_extractor import MetadataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)

def generate_kml(metadata: List[Dict], output_path: str):
    """Generate KML file from metadata list."""
    
    # KML Header
    kml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        '  <name>ClipScribe GEOINT Extraction</name>',
        '  <Style id="dronePath">',
        '    <LineStyle>',
        '      <color>7f00ffff</color>', # Yellow
        '      <width>4</width>',
        '    </LineStyle>',
        '  </Style>',
        '  <Style id="sensorFootprint">',
        '    <LineStyle>',
        '      <color>7f0000ff</color>', # Red
        '      <width>2</width>',
        '    </LineStyle>',
        '  </Style>'
    ]
    
    # 1. Flight Path (LineString)
    coordinates = []
    for packet in metadata:
        lat = packet.get('SensorLatitude')
        lon = packet.get('SensorLongitude')
        alt = packet.get('SensorTrueAltitude')
        
        if lat is not None and lon is not None:
            coord_str = f"{lon},{lat},{alt if alt else 0}"
            coordinates.append(coord_str)
            
    if coordinates:
        kml.append('  <Placemark>')
        kml.append('    <name>Flight Path</name>')
        kml.append('    <styleUrl>#dronePath</styleUrl>')
        kml.append('    <LineString>')
        kml.append('      <extrude>1</extrude>')
        kml.append('      <tessellate>1</tessellate>')
        kml.append('      <altitudeMode>absolute</altitudeMode>')
        kml.append('      <coordinates>')
        kml.append('        ' + ' '.join(coordinates))
        kml.append('      </coordinates>')
        kml.append('    </LineString>')
        kml.append('  </Placemark>')
        
    # 2. Frame Center Path (Target Track)
    target_coords = []
    for packet in metadata:
        lat = packet.get('FrameCenterLatitude')
        lon = packet.get('FrameCenterLongitude')
        alt = packet.get('FrameCenterElevation', 0)
        
        if lat is not None and lon is not None:
            coord_str = f"{lon},{lat},{alt}"
            target_coords.append(coord_str)
            
    if target_coords:
        kml.append('  <Placemark>')
        kml.append('    <name>Sensor Target Track</name>')
        kml.append('    <styleUrl>#sensorFootprint</styleUrl>')
        kml.append('    <LineString>')
        kml.append('      <tessellate>1</tessellate>')
        kml.append('      <coordinates>')
        kml.append('        ' + ' '.join(target_coords))
        kml.append('      </coordinates>')
        kml.append('    </LineString>')
        kml.append('  </Placemark>')

    # KML Footer
    kml.append('</Document>')
    kml.append('</kml>')
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(kml))
    
    print(f"KML saved to {output_path}")

def main():
    input_video = "test_videos/geoint/Day Flight.mpg"
    output_kml = "test_videos/geoint/flight_path.kml"
    
    extractor = MetadataExtractor()
    # Extract ALL metadata (remove the break limit in extractor for prod, but for now it returns whatever it finds)
    # Wait, my MetadataExtractor currently returns ALL packets (I removed the limit in the loop, right? No, I didn't.)
    
    # I need to update MetadataExtractor to NOT limit packets for this script to work fully.
    # But wait, I implemented the generator in Parser, but the loop in MetadataExtractor processes the whole stream.
    # Ah, let's check MetadataExtractor code. It reads until EOF.
    
    metadata = extractor.extract_metadata(input_video)
    
    print(f"Extracted {len(metadata)} points.")
    generate_kml(metadata, output_kml)

if __name__ == "__main__":
    main()

