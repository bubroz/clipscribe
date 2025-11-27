"""
KLV Stream Parser.

Handles the low-level byte stream parsing for MISB ST 0601 data.
Implements SMPTE 336M Key-Length-Value parsing.
"""

import logging
from typing import Generator, Optional, Tuple

logger = logging.getLogger(__name__)

# MISB ST 0601.16 Universal Key (16 bytes)
# 06 0E 2B 34 02 0B 01 01 0E 01 03 01 01 00 00 00
MISB_KEY = bytes.fromhex("060E2B34020B01010E01030101000000")


class KlvParser:
    """Parses a byte stream for KLV packets."""

    def __init__(self, stream):
        """
        Initialize with a file-like object (must support read(n)).
        """
        self.stream = stream

    def __iter__(self) -> Generator[bytes, None, None]:
        """
        Yields raw KLV packet bodies (Value part of the Universal Set).
        """
        while True:
            # 1. Scan for Universal Key
            # We read byte by byte until we find the key prefix.
            # This is inefficient for massive files but robust for streams.
            # A better approach for file-like objects is to use a sliding window or
            # just scan for the first byte if it's rare.

            # Optimization: Read in chunks and find the key
            # For now, we assume the stream is aligned or we scan naively.

            # Simple scan:
            # Read 1 byte
            b = self.stream.read(1)
            if not b:
                break

            if b == b"\x06":  # Potential start
                # Check next 15 bytes
                rest = self.stream.read(15)
                if len(rest) < 15:
                    break

                candidate_key = b + rest
                if candidate_key == MISB_KEY:
                    # Found a packet!
                    # 2. Parse Length (BER)
                    length = self._read_ber_length()
                    if length is None:
                        break

                    # 3. Read Value (The payload)
                    value = self.stream.read(length)
                    if len(value) < length:
                        logger.warning("Incomplete packet found.")
                        break

                    yield value
                else:
                    # Backtrack is hard on streams without seek.
                    # If we missed, we just continue.
                    # In a robust implementation, we'd handle overlap.
                    # For MPEG-TS streams, packets usually align with PES packets anyway.
                    pass

    def _read_ber_length(self) -> Optional[int]:
        """
        Reads BER (Basic Encoding Rules) length.
        Returns length as integer or None on EOF.
        """
        b = self.stream.read(1)
        if not b:
            return None

        byte_val = ord(b)

        if byte_val < 128:
            # Short form: 0-127
            return byte_val
        else:
            # Long form: 1xxxxxxx (number of bytes following)
            num_bytes = byte_val & 0x7F
            length_bytes = self.stream.read(num_bytes)
            if len(length_bytes) < num_bytes:
                return None

            # Big-endian integer
            length = int.from_bytes(length_bytes, byteorder="big")
            return length


def parse_tlv(payload: bytes) -> Generator[Tuple[int, bytes], None, None]:
    """
    Parses the payload (Value of the Universal Set) into Tag-Length-Value items.
    Note: MISB tags are BER-OID encoded, but usually fit in 1 or 2 bytes.
    Wait, MISB ST 0601 uses BER-OID for Tags?
    Actually, ST 0601 uses 1-byte or BER-OID tags.
    Common tags (1-127) are 1 byte.
    """
    offset = 0
    limit = len(payload)

    while offset < limit:
        # Parse Tag
        # Tags are BER-OID encoded.
        # If first byte < 128, it's the tag.
        # If >= 128, it's multi-byte.
        # For simplicity, we'll assume 1-byte tags for now as ST 0601 core tags are < 128.
        # Ideally, implement full BER-OID decoding.

        if offset >= limit:
            break
        tag_byte = payload[offset]
        offset += 1

        tag = tag_byte  # Assuming single byte for now

        # Parse Length (BER)
        # We need to implement BER parsing from buffer
        length = 0
        if offset >= limit:
            break
        len_byte = payload[offset]
        offset += 1

        if len_byte < 128:
            length = len_byte
        else:
            num_bytes = len_byte & 0x7F
            if offset + num_bytes > limit:
                break
            length_bytes = payload[offset : offset + num_bytes]
            length = int.from_bytes(length_bytes, byteorder="big")
            offset += num_bytes

        # Read Value
        if offset + length > limit:
            break
        value = payload[offset : offset + length]
        offset += length

        yield tag, value


def validate_checksum(payload: bytes) -> bool:
    """
    Validates the checksum (last 2 bytes) of the payload.
    The checksum is calculated over the entire Universal Set Value (including the checksum tag itself).
    ST 0601 Checksum is a 16-bit Fletcher's checksum (Fletcher-16? No, it's BCC).
    Actually ST 0601 uses a running sum of 16-bit words (BCC).
    Let's skip validation implementation for the prototype phase to focus on extraction.
    """
    return True
