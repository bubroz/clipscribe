# DJI Drone Telemetry Requirements

*Last Updated: November 2025*
*Status: Beta / Requirements Specification*

This document specifies the exact requirements for DJI drone video files to enable geolocation intelligence extraction in ClipScribe.

## File Format Requirements

### Required Files

**Option 1: Separate Files (Most Common)**
- Video file: `.MP4` or `.MOV` (H.264 or H.265 encoded)
- Telemetry file: `.SRT` (SubRip subtitle format) with same base filename
- Example: `DJI_0042.MP4` + `DJI_0042.SRT`

**Option 2: Embedded Subtitles**
- Video file with subtitle track embedded in container
- ClipScribe will extract using `ffmpeg` automatically

### File Location

Files must be **raw recordings** directly from the drone's SD card or DJI Fly/Go app export. Re-encoded or uploaded videos (YouTube, etc.) typically lose telemetry data.

## Enabling Telemetry Recording

### DJI Fly App (Mini 3, Mini 4, Air 3, Mavic 3)

1. Open DJI Fly app
2. Go to Settings (gear icon)
3. Navigate to Camera → Subtitles
4. Toggle **ON**
5. Future recordings will include GPS telemetry in subtitle track

### DJI Go 4 App (Phantom 4, Mavic 2, older models)

1. Open DJI Go 4 app
2. Go to Settings
3. Navigate to Video Captions
4. Enable **Video Captions**
5. Future recordings will include telemetry

### Verification

After recording, check that `.SRT` file exists alongside video file. Open `.SRT` in text editor and verify it contains lines like:

```
[latitude: 34.05223] [longitude: -118.24368] [rel_alt: 10.500 abs_alt: 150.200]
```

## Supported Drone Models

**Fully Supported:**
- DJI Mini 3 Pro / Mini 4 Pro
- DJI Mavic 3 / Mavic 3 Pro
- DJI Air 2S / Air 3
- DJI Phantom 4 Pro / Phantom 4 RTK

**Partially Supported (may require format adjustments):**
- DJI FPV (limited telemetry)
- DJI Avata (limited telemetry)
- Autel EVO series (different format, parser supports it)

**Not Supported:**
- FPV racing drones (no GPS telemetry)
- DIY drones (no standard format)

## Test Sample Requirements

### Duration

**Minimum:** 2 minutes (enough for meaningful telemetry)
**Optimal:** 5-10 minutes (good balance of data vs processing time)
**Maximum:** No limit (ClipScribe handles long flights)

### Flight Profiles

For comprehensive testing, collect samples with different patterns:

1. **Stationary Hover**
   - Drone stays in one location
   - Tests minimal movement handling
   - Good for testing altitude accuracy

2. **Linear Flight**
   - Straight line A → B
   - Tests continuous tracking
   - Good for testing coordinate interpolation

3. **Orbit/Circle**
   - Circling a subject
   - Tests curved path handling
   - Good for testing heading calculations

4. **Altitude Change**
   - Takeoff to high altitude
   - Tests Z-axis (altitude) tracking
   - Good for testing 3D visualization

### Geography

**Diversity helps but not required:**
- Urban (buildings, streets)
- Rural (fields, open space)
- Coastal (water boundaries)
- Different countries/timezones (tests timestamp handling)

## Privacy Considerations

### Data Sensitivity

Drone telemetry contains:
- Exact GPS coordinates (where drone was)
- Timestamps (when flight occurred)
- Altitude data (how high drone flew)

**Recommendations:**
- Use flights over public/non-sensitive locations
- Parks, beaches, your own property are ideal
- Avoid military bases, private property, restricted airspace
- If privacy is concern, send only `.SRT` file (not video)

### Sharing Guidelines

When requesting samples from others:
- Ask for flights over public locations
- Offer to accept `.SRT` file only (no video needed)
- Explain that only GPS data is needed for testing
- Respect any privacy concerns

## Validation Checklist

Before processing a DJI file, verify:

- [ ] `.SRT` file exists (or subtitles embedded in video)
- [ ] `.SRT` contains GPS coordinates (open in text editor, look for `[latitude:` and `[longitude:`)
- [ ] Coordinates are real (not `0.0, 0.0` or `NULL`)
- [ ] Video file is playable (not corrupted)
- [ ] Files are from same flight (matching timestamps)

## Processing

Once files meet requirements:

```bash
# Process DJI video (auto-detects SRT telemetry)
clipscribe process DJI_0042.MP4

# Output includes:
# - transcript.json (with geoint blocks)
# - mission.kml (Google Earth visualization)
# - mission_map.html (Interactive map)
```

## Troubleshooting

**No telemetry found:**
- Check that `.SRT` file exists and is in same directory
- Verify telemetry was enabled in DJI app before recording
- Try extracting subtitles manually: `ffmpeg -i video.mp4 -map 0:s:0 subtitles.srt`

**Coordinates are zero:**
- GPS may not have locked before recording
- Check that flight was outdoors (GPS requires clear sky view)
- Verify drone model supports GPS telemetry

**Processing fails:**
- Ensure video file is not corrupted
- Check that ClipScribe has read permissions
- Verify `ffmpeg` is installed and accessible

## Next Steps

Once you have validated DJI samples:
1. Process them through ClipScribe
2. Verify `mission.kml` opens correctly in Google Earth
3. Check that flight path matches actual flight
4. Report any issues or edge cases

For OSINT workflows and use cases, see `OSINT_GEOINT_WORKFLOWS.md`.

