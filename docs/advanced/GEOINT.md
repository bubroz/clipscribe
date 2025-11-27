# Geospatial Intelligence (GEOINT) Engine

*Last Updated: November 2025*
*Status: Beta / Prototype*

ClipScribe's GEOINT engine is a comprehensive, zero-dependency system for extracting, parsing, and visualizing geospatial telemetry from video files. It supports both military-standard KLV (MISB ST 0601) and consumer drone subtitles (DJI/Autel).

## Primary Use Case: Consumer Drones

**Focus:** Consumer drone telemetry (DJI, Autel) for OSINT analysis.

The primary use case for ClipScribe's GEOINT engine is extracting GPS coordinates from consumer drone footage. This enables OSINT analysts to:
- Verify geolocation claims in social media posts
- Analyze flight paths and timelines
- Correlate audio intelligence with geographic locations
- Validate video authenticity through coordinate analysis

**See:** [DJI Requirements](GEOINT_DJI_REQUIREMENTS.md) for exact file format and setup instructions.

**OSINT Workflows:** See [OSINT GEOINT Workflows](OSINT_GEOINT_WORKFLOWS.md) for use case examples.

## Enterprise/Future: Military KLV Support

**Status:** Implemented but limited test data available.

ClipScribe supports MISB ST 0601 (STANAG 4609) KLV metadata for military/government video feeds. However, due to operational security restrictions, publicly available test samples are extremely limited (essentially one: "Day Flight.mpg" from FFmpeg samples).

**When to use:** Government contracts, military video analysis, specialized intelligence operations.

**Limitation:** Requires access to classified or properly declassified video feeds with embedded KLV streams.

## Capabilities

1.  **Full Spectrum Extraction**:
    -   **Platform**: Latitude, Longitude, Altitude, Heading, Pitch, Roll.
    -   **Sensor**: Field of View (H/V), Look Angle.
    -   **Target**: Frame Center calculations (where the camera is looking).
2.  **Zero-Dependency Architecture**:
    -   Custom-built Python parser for SMPTE 336M KLV and MISB ST 0601.
    -   No heavy external libraries (removed `klvdata`).
    -   Pure Python implementation compatible with 3.12+.
3.  **Visualization**:
    -   **KML Export**: Generates Google Earth-ready mission files (`mission.kml`).
    -   **Interactive Maps**: Generates standalone HTML maps using Leaflet.js.
4.  **Intelligence Correlation**:
    -   Maps audio transcript segments to geospatial coordinates.
    -   Identifies "Visual Observations" based on camera telemetry (zoom/angle).

## Architecture

The engine is composed of three main layers:

### 1. Extraction (`src/clipscribe/extractors/metadata_extractor.py`)
-   Uses `ffmpeg` to dump the raw data stream (Stream #0:1 usually).
-   Detects format: KLV (Binary) vs. Subtitle (Text).
-   Routes to the appropriate parser.

### 2. Parsing (`src/clipscribe/utils/klv/`)
-   **`parser.py`**: Low-level byte stream parser. Handles Universal Key detection and BER (Basic Encoding Rules) length decoding.
-   **`decoder.py`**: Decodes raw bytes into human-readable values (Degrees, Meters) using MISB scaling factors.
-   **`registry.py`**: Extensible mapping of Tag IDs to decoding logic.

### 3. Processing (`src/clipscribe/processors/geoint_processor.py`)
-   **Correlation**: Aligns absolute Unix timestamps (from KLV) with relative video timestamps (from Transcript).
-   **Enrichment**: Adds `geoint` blocks to transcript segments.

## Data Model

We map standard MISB ST 0601 tags to a normalized schema:

| Tag | Name | ClipScribe Field | Units |
|-----|------|------------------|-------|
| 1 | Precision Time Stamp | `timestamp` | Unix Micros |
| 13 | Sensor Latitude | `sensor.lat` | Degrees |
| 14 | Sensor Longitude | `sensor.lon` | Degrees |
| 15 | Sensor True Altitude | `sensor.alt` | Meters (MSL) |
| 16 | Sensor Horizontal FOV | `sensor.hfov` | Degrees |
| 23 | Frame Center Lat | `target.lat` | Degrees |
| 24 | Frame Center Lon | `target.lon` | Degrees |

## Usage

The engine runs automatically during `clipscribe process` if a supported file type (`.mpg`, `.ts`, `.mkv`, `.mp4`) is detected.

```bash
# Process a video (auto-detects KLV)
clipscribe process flight_feed.mpg

# Output will include:
# - transcript.json (enriched with "geoint" fields)
# - mission.kml (Google Earth visualization)
# - mission_map.html (Interactive map)
```

### Output Example (JSON)

```json
{
  "transcript": {
    "segments": [
      {
        "text": "Target vehicle acquired at the intersection.",
        "start": 15.4,
        "end": 18.2,
        "geoint": {
          "timestamp": 1634523400123000,
          "sensor": {
            "lat": 34.12345,
            "lon": -118.67890,
            "alt": 1500.5
          },
          "target": {
            "lat": 34.12500,
            "lon": -118.68000
          },
          "likely_visual_observation": true
        }
      }
    ]
  }
}
```

## Roadmap

-   [ ] **Visual User Interface**: Render the KML/Map directly in the Streamlit dashboard.
-   [ ] **Real-time Stream Support**: Connect to RTP/UDP streams for live analysis.
-   [ ] **Search by Location**: "Show me all segments where the drone was over Sector 4."

