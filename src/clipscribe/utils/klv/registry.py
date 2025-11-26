"""
KLV Tag Registry.

Definitions for MISB ST 0601 tags, mapping them to human-readable names
and specific decoder functions.
"""

from .decoder import (
    decode_string, decode_uint, decode_int, decode_timestamp,
    decode_lat, decode_lon, decode_alt, decode_heading,
    decode_pitch, decode_roll, decode_fov, decode_slant_range,
    map_linear
)

class TagDef:
    def __init__(self, name, decoder):
        self.name = name
        self.decoder = decoder

# Generic decoders for reuse
def decode_angle(b): return map_linear(b, 0.0, 360.0, signed=False)
def decode_relative_angle(b): return map_linear(b, -180.0, 180.0, signed=True)

# MISB ST 0601.16 Tag Dictionary
TAG_REGISTRY = {
    1: TagDef("Checksum", decode_uint),
    2: TagDef("PrecisionTimeStamp", decode_timestamp),
    3: TagDef("MissionID", decode_string),
    4: TagDef("PlatformTailNumber", decode_string),
    5: TagDef("PlatformHeadingAngle", decode_heading),
    6: TagDef("PlatformPitchAngle", decode_pitch),
    7: TagDef("PlatformRollAngle", decode_roll),
    8: TagDef("PlatformTrueAirspeed", lambda b: map_linear(b, 0, 255, signed=False)), # Uint8
    9: TagDef("PlatformIndicatedAirspeed", lambda b: map_linear(b, 0, 255, signed=False)), # Uint8
    10: TagDef("PlatformDesignation", decode_string),
    11: TagDef("ImageSourceSensor", decode_string),
    12: TagDef("ImageCoordinateSystem", decode_string),
    13: TagDef("SensorLatitude", decode_lat),
    14: TagDef("SensorLongitude", decode_lon),
    15: TagDef("SensorTrueAltitude", decode_alt),
    16: TagDef("SensorHorizontalFOV", decode_fov),
    17: TagDef("SensorVerticalFOV", decode_fov),
    18: TagDef("SensorRelativeAzimuthAngle", decode_angle),
    19: TagDef("SensorRelativeElevationAngle", decode_relative_angle),
    20: TagDef("SensorRelativeRollAngle", decode_angle),
    21: TagDef("SlantRange", decode_slant_range),
    22: TagDef("TargetWidth", lambda b: map_linear(b, 0, 10000, signed=False)),
    23: TagDef("FrameCenterLatitude", decode_lat),
    24: TagDef("FrameCenterLongitude", decode_lon),
    25: TagDef("FrameCenterElevation", lambda b: map_linear(b, -900, 19000, signed=False)),
    # Target Location (if different from frame center)
    # Tags 26-33 are Offset Corners - complex structure, maybe skip for MVP or treat as Lat/Lon
    # ...
    65: TagDef("UASLDSVersionNumber", decode_uint),
    94: TagDef("MIISCoreIdentifier", decode_string),
}

def get_tag_def(tag_id: int) -> TagDef:
    return TAG_REGISTRY.get(tag_id, TagDef(f"UnknownTag_{tag_id}", lambda b: b.hex()))

