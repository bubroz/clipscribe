"""
GEOINT Exporter.

Generates KML and GeoJSON files for geospatial intelligence visualization.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class GeoIntExporter:
    """Exports GEOINT data to visualization formats."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_kml(self, telemetry: List[Dict], events: List[Dict] = None, filename: str = "mission.kml"):
        """
        Generate a rich KML file with flight path, target track, and event pins.
        """
        kml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2">',
            '<Document>',
            '  <name>ClipScribe Intelligence Mission</name>',
            '  <Style id="dronePath">',
            '    <LineStyle><color>ff00ffff</color><width>4</width></LineStyle>', # Yellow (AABBGGRR)
            '  </Style>',
            '  <Style id="targetPath">',
            '    <LineStyle><color>ff0000ff</color><width>4</width></LineStyle>', # Red
            '  </Style>',
            '  <Style id="lookVector">',
            '    <LineStyle><color>7fcccccc</color><width>1</width></LineStyle>', # Gray, semi-transparent
            '  </Style>',
            '  <Style id="eventPin">',
            '    <IconStyle><scale>1.2</scale></IconStyle>',
            '  </Style>'
        ]
        
        # 1. Flight Path (Sensor Location)
        sensor_coords = []
        for p in telemetry:
            if p.get('SensorLatitude') is not None:
                # Lon, Lat, Alt
                sensor_coords.append(f"{p['SensorLongitude']},{p['SensorLatitude']},{p.get('SensorTrueAltitude', 0)}")
        
        if sensor_coords:
            kml.append(self._create_linestring("Flight Path", "#dronePath", sensor_coords, altitude_mode="absolute"))

        # 2. Target Track (Frame Center)
        target_coords = []
        for p in telemetry:
            if p.get('FrameCenterLatitude') is not None:
                target_coords.append(f"{p['FrameCenterLongitude']},{p['FrameCenterLatitude']},{p.get('FrameCenterElevation', 0)}")
        
        if target_coords:
            kml.append(self._create_linestring("Target Track", "#targetPath", target_coords, altitude_mode="clampToGround"))

        # 3. Look Vectors (Connect Sensor to Target periodically)
        # Draw a line every ~10 seconds or 100 frames to visualize perspective
        step = 30 # Adjust based on density
        for i in range(0, len(telemetry), step):
            p = telemetry[i]
            if p.get('SensorLatitude') is not None and p.get('FrameCenterLatitude') is not None:
                s_coord = f"{p['SensorLongitude']},{p['SensorLatitude']},{p.get('SensorTrueAltitude', 0)}"
                t_coord = f"{p['FrameCenterLongitude']},{p['FrameCenterLatitude']},{p.get('FrameCenterElevation', 0)}"
                kml.append(self._create_linestring(f"Look Vector {i}", "#lookVector", [s_coord, t_coord], altitude_mode="absolute"))

        # 4. Event Pins (Audio/Intel Events)
        if events:
            for event in events:
                geoint = event.get('geoint', {})
                # Prefer target location for the pin
                lat = None
                lon = None
                
                if 'target' in geoint and geoint['target'].get('lat') is not None:
                    lat = geoint['target']['lat']
                    lon = geoint['target']['lon']
                elif 'sensor' in geoint and geoint['sensor'].get('lat') is not None:
                    lat = geoint['sensor']['lat']
                    lon = geoint['sensor']['lon']
                
                if lat is not None and lon is not None:
                    # Description
                    desc = event.get('text', 'Event')
                    kml.append(self._create_placemark(f"Event: {desc[:30]}...", desc, lon, lat))
        
        kml.append('</Document>')
        kml.append('</kml>')
        
        out_path = self.output_dir / filename
        with open(out_path, 'w') as f:
            f.write('\n'.join(kml))
        
        logger.info(f"KML exported to {out_path}")
        return out_path

    def export_interactive_map(self, telemetry: List[Dict], events: List[Dict] = None, filename: str = "mission_map.html"):
        """
        Generate a standalone HTML map using Leaflet.js (zero dependency).
        """
        # Prepare Data
        sensor_path = []
        target_path = []
        map_center = [0, 0]
        
        for p in telemetry:
            if p.get('SensorLatitude') is not None:
                sensor_path.append([p['SensorLatitude'], p['SensorLongitude']])
            if p.get('FrameCenterLatitude') is not None:
                target_path.append([p['FrameCenterLatitude'], p['FrameCenterLongitude']])
                
        if target_path:
            map_center = target_path[len(target_path)//2]
        elif sensor_path:
            map_center = sensor_path[len(sensor_path)//2]
            
        event_markers = []
        if events:
            for event in events:
                geoint = event.get('geoint', {})
                lat = None
                lon = None
                if 'target' in geoint and geoint['target'].get('lat') is not None:
                    lat = geoint['target']['lat']
                    lon = geoint['target']['lon']
                elif 'sensor' in geoint and geoint['sensor'].get('lat') is not None:
                    lat = geoint['sensor']['lat']
                    lon = geoint['sensor']['lon']
                    
                if lat is not None:
                    desc = event.get('text', 'Event').replace("'", "\\'")
                    event_markers.append({'lat': lat, 'lon': lon, 'desc': desc})

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ClipScribe Mission Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ width: 100%; height: 100vh; }}
        .info-box {{
            position: absolute; top: 10px; right: 10px; z-index: 1000;
            background: white; padding: 10px; border-radius: 5px;
            box-shadow: 0 0 5px rgba(0,0,0,0.3); font-family: sans-serif;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-box">
        <h3>Mission Intelligence</h3>
        <p><strong>Sensor Path:</strong> Yellow</p>
        <p><strong>Target Track:</strong> Red</p>
        <p><strong>Events:</strong> {len(event_markers)}</p>
    </div>
    <script>
        var map = L.map('map').setView({map_center}, 14);

        // Satellite Layer (Esri)
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Tiles &copy; Esri'
        }}).addTo(map);
        
        // Street Layer Overlay
        var streets = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors'
        }});

        var sensorPath = {json.dumps(sensor_path)};
        var targetPath = {json.dumps(target_path)};
        
        // Draw Paths
        if (sensorPath.length > 0) {{
            L.polyline(sensorPath, {{color: 'yellow', weight: 3, opacity: 0.8}}).addTo(map);
        }}
        
        if (targetPath.length > 0) {{
            L.polyline(targetPath, {{color: 'red', weight: 3, opacity: 0.8, dashArray: '5, 10'}}).addTo(map);
        }}
        
        // Add Markers
        var markers = {json.dumps(event_markers)};
        markers.forEach(function(m) {{
            L.marker([m.lat, m.lon])
             .bindPopup(m.desc)
             .addTo(map);
        }});
        
        // Fit Bounds
        var bounds = L.latLngBounds(sensorPath.concat(targetPath));
        map.fitBounds(bounds);
        
        L.control.layers({{"Satellite": map}}, {{"Streets": streets}}).addTo(map);
    </script>
</body>
</html>
"""
        out_path = self.output_dir / filename
        with open(out_path, 'w') as f:
            f.write(html_content)
            
        logger.info(f"Interactive map exported to {out_path}")
        return out_path

    def _create_linestring(self, name, style, coords, altitude_mode="clampToGround"):
        return f"""
  <Placemark>
    <name>{name}</name>
    <styleUrl>{style}</styleUrl>
    <LineString>
      <extrude>1</extrude>
      <tessellate>1</tessellate>
      <altitudeMode>{altitude_mode}</altitudeMode>
      <coordinates>
        {' '.join(coords)}
      </coordinates>
    </LineString>
  </Placemark>"""

    def _create_placemark(self, name, description, lon, lat):
        return f"""
  <Placemark>
    <name>{name}</name>
    <description>{description}</description>
    <styleUrl>#eventPin</styleUrl>
    <Point>
      <coordinates>{lon},{lat},0</coordinates>
    </Point>
  </Placemark>"""
