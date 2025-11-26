# OSINT GEOINT Workflows

*Last Updated: November 2025*
*Status: Beta / Use Case Documentation*

This document provides practical workflows for using ClipScribe's GEOINT engine in OSINT (Open Source Intelligence) analysis.

## Workflow 1: Geolocation Verification

**Use Case:** Verify claims about where a video was recorded.

### Scenario
A social media post claims a video was recorded in "Gaza City" but you need to verify the actual GPS coordinates match the claim.

### Steps

1. **Obtain Raw Footage**
   - Request original video file (not re-encoded upload)
   - Ensure `.SRT` telemetry file is included
   - Verify telemetry was enabled during recording

2. **Process with ClipScribe**
   ```bash
   clipscribe process claimed_gaza_video.mp4
   ```

3. **Extract Coordinates**
   - Open `transcript.json`
   - Look for `geoint` blocks in transcript segments
   - Extract `sensor.lat` and `sensor.lon` values

4. **Verify Location**
   - Plot coordinates in Google Earth or mapping tool
   - Compare with claimed location
   - Check if coordinates match geographic features mentioned in audio

5. **Generate Report**
   - Use `mission.kml` for visual presentation
   - Document discrepancies between claims and actual coordinates
   - Correlate with audio transcript for context

### Example Output

```json
{
  "transcript": {
    "segments": [
      {
        "text": "We're here in Gaza City near the market",
        "start": 45.2,
        "end": 48.5,
        "geoint": {
          "sensor": {
            "lat": 31.3547,
            "lon": 34.3088,
            "alt": 120.5
          }
        }
      }
    ]
  }
}
```

**Analysis:** Coordinates (31.3547, 34.3088) correspond to Gaza City, verifying the claim.

## Workflow 2: Timeline Analysis

**Use Case:** Reconstruct the flight path and timeline of a drone operation.

### Scenario
Analyze a drone video to understand:
- Where did the drone start?
- What path did it take?
- What locations did it visit?
- How long was it at each location?

### Steps

1. **Process Video**
   ```bash
   clipscribe process drone_mission.mp4
   ```

2. **Visualize Flight Path**
   - Open `mission.kml` in Google Earth
   - Flight path renders as yellow line
   - Target track (where camera looking) renders as red line

3. **Extract Timeline**
   - Review `transcript.json` for `geoint` blocks with timestamps
   - Correlate audio events with geographic locations
   - Build timeline of: location → time → audio content

4. **Identify Key Locations**
   - Note coordinates where drone hovered (stationary periods)
   - Identify locations mentioned in audio
   - Map significant events to specific coordinates

### Example Analysis

```
00:00:00 - Takeoff: 34.0522, -118.2437 (Los Angeles)
00:02:15 - Hover: 34.0530, -118.2440 (Market area, 3 min hover)
00:05:30 - Transit: Moving northeast
00:08:45 - Target: 34.0550, -118.2450 (Intersection, visual observation)
00:12:00 - Return: Heading back to start
00:14:30 - Landing: 34.0522, -118.2437
```

## Workflow 3: Cross-Reference with Audio Intelligence

**Use Case:** Correlate what was said with where it was said.

### Scenario
A drone video contains audio commentary. You want to know:
- What locations were mentioned?
- Where was the drone when specific topics were discussed?
- Do the mentioned locations match the actual coordinates?

### Steps

1. **Process Video**
   ```bash
   clipscribe process commentary_flight.mp4
   ```

2. **Extract Entities**
   - Review `entities.json` for location mentions
   - Look for GPE (Geopolitical Entity) and LOC (Location) entities

3. **Correlate with GEOINT**
   - For each location entity, find corresponding transcript segment
   - Check if segment has `geoint` block
   - Compare mentioned location with actual GPS coordinates

4. **Identify Discrepancies**
   - If pilot says "We're over the port" but coordinates show airport
   - If coordinates don't match mentioned location
   - If altitude doesn't match described terrain

### Example Correlation

```json
{
  "entities": [
    {
      "name": "Port of Los Angeles",
      "type": "GPE",
      "evidence": "We're flying over the Port of Los Angeles now"
    }
  ],
  "transcript": {
    "segments": [
      {
        "text": "We're flying over the Port of Los Angeles now",
        "start": 120.5,
        "geoint": {
          "sensor": {
            "lat": 33.7326,
            "lon": -118.2656
          }
        }
      }
    ]
  }
}
```

**Analysis:** Coordinates (33.7326, -118.2656) match Port of Los Angeles location, confirming accuracy.

## Workflow 4: Social Media Claims Validation

**Use Case:** Verify authenticity of viral drone footage.

### Scenario
A video goes viral claiming to show "Russian forces in Ukraine" but you suspect it may be misattributed or staged.

### Steps

1. **Obtain Original File**
   - Request raw file from source (if possible)
   - Check if video has embedded telemetry
   - Verify file hasn't been re-encoded (loses telemetry)

2. **Extract Coordinates**
   ```bash
   clipscribe process viral_video.mp4
   ```

3. **Geolocation Analysis**
   - Plot coordinates on map
   - Check if location matches claimed country/region
   - Verify coordinates are plausible for claimed location
   - Check for coordinate anomalies (e.g., negative altitude, impossible speeds)

4. **Timestamp Analysis**
   - Extract timestamps from telemetry
   - Compare with claimed date/time
   - Check for timezone inconsistencies
   - Verify temporal consistency

5. **Audio-Geography Correlation**
   - Check if audio mentions match coordinates
   - Verify language/accent matches claimed location
   - Look for geographic references in transcript

### Red Flags

- Coordinates don't match claimed location
- Timestamps inconsistent with claimed date
- Audio mentions locations that don't match GPS
- Telemetry shows impossible flight characteristics
- No telemetry data (may indicate re-encoding/staging)

## Workflow 5: Multi-Video Analysis

**Use Case:** Analyze multiple drone videos from the same operation or location.

### Scenario
You have 5 drone videos from different angles of the same event. You want to:
- Map all flight paths
- Identify overlap areas
- Correlate events across videos
- Build comprehensive timeline

### Steps

1. **Process All Videos**
   ```bash
   for video in *.mp4; do
     clipscribe process "$video"
   done
   ```

2. **Extract All Coordinates**
   - Collect all `geoint` blocks from all `transcript.json` files
   - Build master coordinate list
   - Identify overlapping time periods

3. **Visualize Combined Paths**
   - Manually combine KML files or use GIS tool
   - Color-code by video source
   - Identify intersection points

4. **Cross-Reference Events**
   - Match audio events across videos by timestamp
   - Correlate geographic locations
   - Build unified timeline

## Best Practices

### Data Collection
- Always request raw files (not YouTube uploads)
- Verify telemetry is enabled before recording
- Document source and collection method
- Preserve original files for chain of custody

### Analysis
- Always verify coordinates manually (don't trust blindly)
- Cross-reference with other intelligence sources
- Document methodology and assumptions
- Present findings with appropriate confidence levels

### Reporting
- Include coordinate data in reports
- Provide visualizations (KML, maps)
- Document limitations and uncertainties
- Cite evidence (quotes, timestamps, coordinates)

## Limitations

- **Beta Status:** Feature needs real-world validation
- **Format Support:** Currently DJI/Autel only (military KLV has limited test data)
- **Accuracy:** Depends on GPS lock quality during recording
- **Privacy:** Coordinate data may be sensitive

## Tools Integration

### Google Earth
- Open `mission.kml` directly
- View flight path in 3D
- Measure distances
- Add annotations

### GIS Software
- Import coordinates to QGIS, ArcGIS
- Overlay with other intelligence layers
- Perform spatial analysis
- Generate custom visualizations

### Analysis Tools
- Import `transcript.json` to Python/Pandas
- Extract coordinates programmatically
- Build custom analysis pipelines
- Integrate with other OSINT tools

## Next Steps

For technical setup and file requirements, see [GEOINT_DJI_REQUIREMENTS.md](GEOINT_DJI_REQUIREMENTS.md).

For engine architecture and capabilities, see [GEOINT.md](GEOINT.md).

