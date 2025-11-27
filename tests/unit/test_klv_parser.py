import io
import pytest
from clipscribe.utils.klv.parser import KlvParser, parse_tlv, MISB_KEY


class TestKlvParser:
    def test_parse_single_packet(self):
        """Test parsing a single valid KLV packet."""
        # Construct a mock packet
        # Key: 16 bytes (Universal Key)
        # Length: BER encoded length (we'll use short form for simplicity, e.g., 5 bytes)
        # Value: 5 bytes of payload

        payload = b"\x01\x02\x03\x04\x05"
        length_byte = bytes([len(payload)])  # 0x05, short form BER

        stream_content = MISB_KEY + length_byte + payload
        stream = io.BytesIO(stream_content)

        parser = KlvParser(stream)
        packets = list(parser)

        assert len(packets) == 1
        assert packets[0] == payload

    def test_parse_multiple_packets(self):
        """Test parsing multiple packets in a stream."""
        payload1 = b"\xAA\xBB"
        packet1 = MISB_KEY + bytes([len(payload1)]) + payload1

        payload2 = b"\xCC\xDD\xEE"
        packet2 = MISB_KEY + bytes([len(payload2)]) + payload2

        stream = io.BytesIO(packet1 + packet2)
        parser = KlvParser(stream)
        packets = list(parser)

        assert len(packets) == 2
        assert packets[0] == payload1
        assert packets[1] == payload2

    def test_incomplete_packet(self):
        """Test that incomplete packets are handled gracefully."""
        # Key + Length but not enough value
        payload = b"\x01\x02"  # We say length is 5 but provide 2
        length_byte = b"\x05"

        stream_content = MISB_KEY + length_byte + payload
        stream = io.BytesIO(stream_content)

        parser = KlvParser(stream)
        packets = list(parser)

        # Should yield nothing or handle gracefully as per implementation
        # Current implementation logs warning and breaks
        assert len(packets) == 0

    def test_ber_length_parsing_long_form(self):
        """Test BER length parsing for long form (multi-byte length)."""
        # Let's simulate a payload of 255 bytes
        payload = b"\xFF" * 255
        # BER Long Form:
        # First byte: 1xxxxxxx -> 10000001 (0x81) -> 1 byte follows for length
        # Second byte: 255 (0xFF)
        length_bytes = b"\x81\xFF"

        stream_content = MISB_KEY + length_bytes + payload
        stream = io.BytesIO(stream_content)

        parser = KlvParser(stream)
        packets = list(parser)

        assert len(packets) == 1
        assert len(packets[0]) == 255

    def test_tlv_parsing(self):
        """Test parsing the Value part into Tag-Length-Value items."""
        # Tag 1: 1 byte value
        # Tag 2: 2 byte value

        # Tag 1 (0x01), Length 1 (0x01), Value (0xAA)
        tlv1 = b"\x01\x01\xAA"
        # Tag 2 (0x02), Length 2 (0x02), Value (0xBB, 0xCC)
        tlv2 = b"\x02\x02\xBB\xCC"

        payload = tlv1 + tlv2

        items = list(parse_tlv(payload))

        assert len(items) == 2
        assert items[0] == (1, b"\xAA")
        assert items[1] == (2, b"\xBB\xCC")
