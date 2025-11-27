"""
KLV Value Decoders.

Functions to convert binary KLV values into human-readable types
based on MISB ST 0601 encoding rules.
"""


def decode_string(value: bytes) -> str:
    """Decode ASCII/UTF-8 string."""
    return value.decode("utf-8", errors="replace").strip()


def decode_uint(value: bytes) -> int:
    """Decode unsigned integer (big-endian)."""
    return int.from_bytes(value, byteorder="big", signed=False)


def decode_int(value: bytes) -> int:
    """Decode signed integer (big-endian)."""
    return int.from_bytes(value, byteorder="big", signed=True)


def decode_timestamp(value: bytes) -> float:
    """
    Decode Precision Time Stamp (Tag 2).
    Microseconds since 1970-01-01 00:00:00 UTC.
    """
    micros = decode_uint(value)
    return micros / 1_000_000.0


def map_linear(value_bytes: bytes, min_val: float, max_val: float, signed: bool = True) -> float:
    """
    Decode linear mapping.
    Maps the full range of the integer (based on byte length) to [min_val, max_val].

    Formula: y = mx + b
    """
    # 1. Get integer value
    if signed:
        int_val = int.from_bytes(value_bytes, byteorder="big", signed=True)
        # Max range for signed N bytes: -2^(8N-1) .. 2^(8N-1)-1
        bits = len(value_bytes) * 8
        max_int = (1 << (bits - 1)) - 1
        # Total span of integer: 2^bits - 1 (approx)
        # Actually, MISB defines mapping carefully.
        # For Lat (int32): -2^31 maps to -90, 2^31-1 maps to 90.

        # Simple robust scale:
        # normalized = int_val / 2^(bits-1)  -> range roughly -1 to 1
        # But we want strict mapping.

        total_range = max_val - min_val
        int_range = (1 << bits) - 1

        # Shift to unsigned for easier math?
        # Let's stick to the formula: val = int_val * (range / 2^bits) ??
        # No, ST 0601 usually maps the full int range.

        # Standard MISB mapping for signed values (Lat/Lon):
        # Degrees = (Int32 / 2^32) * 360 ? No.

        # Let's use the "Range" scalar.
        # Scale = (Max - Min) / (2^Bits - 1)
        # Value = Int * Scale + Offset?

        # For Lat (Tag 13): Map Int32 to +/- 90.
        # The spec says: "Map -(2^31) .. (2^31 - 1) to +/- 90"
        # Resolution approx 0.000000042 degrees.

        # value = int_val * (range / 2^32) is common approximation.
        # Or int_val * (180.0 / 4294967294.0)

        # Let's use: value = int_val * ((max_val - min_val) / (1 << bits)) + min_val ??
        # No, if signed, min_val corresponds to min_int.

        # Correct logic for signed:
        # range_val = max_val - min_val
        # max_int = (1 << (bits)) - 1  <-- wait, for signed?
        # let's treat as ratio of full scale.

        # Ratio = (int_val - int_min) / (int_max - int_min)
        # Val = Ratio * (max_val - min_val) + min_val

        int_min = -(1 << (bits - 1))
        int_max = (1 << (bits - 1)) - 1

        ratio = (int_val - int_min) / (int_max - int_min)
        return ratio * (max_val - min_val) + min_val

    else:
        # Unsigned
        int_val = int.from_bytes(value_bytes, byteorder="big", signed=False)
        bits = len(value_bytes) * 8
        max_int = (1 << bits) - 1

        return (int_val / max_int) * (max_val - min_val) + min_val


# Specific decoders using the generic ones
def decode_lat(value: bytes) -> float:
    # Tag 13: Sensor Latitude. Int32. Range -90 to +90.
    return map_linear(value, -90.0, 90.0, signed=True)


def decode_lon(value: bytes) -> float:
    # Tag 14: Sensor Longitude. Int32. Range -180 to +180.
    return map_linear(value, -180.0, 180.0, signed=True)


def decode_alt(value: bytes) -> float:
    # Tag 15: Sensor True Altitude. Uint16. Range -900 to +19000 meters.
    return map_linear(value, -900.0, 19000.0, signed=False)


def decode_heading(value: bytes) -> float:
    # Tag 5: Platform Heading. Uint16. Range 0 to 360.
    return map_linear(value, 0.0, 360.0, signed=False)


def decode_pitch(value: bytes) -> float:
    # Tag 6: Platform Pitch. Int16. Range -20 to +20.
    return map_linear(value, -20.0, 20.0, signed=True)


def decode_roll(value: bytes) -> float:
    # Tag 7: Platform Roll. Int16. Range -50 to +50.
    return map_linear(value, -50.0, 50.0, signed=True)


def decode_fov(value: bytes) -> float:
    # Tag 16/17: Horizontal/Vertical FOV. Uint16. Range 0 to 180.
    return map_linear(value, 0.0, 180.0, signed=False)


def decode_slant_range(value: bytes) -> float:
    # Tag 21: Slant Range. Uint32. Range 0 to 5,000,000 meters.
    return map_linear(value, 0.0, 5000000.0, signed=False)
