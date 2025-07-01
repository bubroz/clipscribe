#!/usr/bin/env python3
"""Simple debug test for Timeline v2.0"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.timeline.temporal_extractor_v2 import TemporalExtractorV2

logging.basicConfig(level=logging.DEBUG)


async def test_simple():
    """Test basic Timeline v2.0 extraction"""
    
    extractor = TemporalExtractorV2()
    
    # Simple test transcript
    test_transcript = """
    In January 2021, the investigation began. The team discovered evidence 
    of surveillance on February 15th. By March 2021, they had confirmed 
    multiple incidents. The report was published on April 1, 2021.
    """
    
    # Mock entities
    test_entities = [
        {"name": "investigation team", "type": "ORG", "confidence": 0.9},
        {"name": "surveillance", "type": "EVENT", "confidence": 0.8}
    ]
    
    test_url = "https://example.com/test"
    
    print("Testing Timeline v2.0 extraction...")
    events = await extractor.extract_temporal_events(
        test_url,
        test_transcript,
        test_entities
    )
    
    print(f"\nExtracted {len(events)} events:")
    for event in events:
        print(f"- {event.description}")
        print(f"  Date: {event.date}")
        print(f"  Type: {event.event_type}")
        print(f"  Entities: {event.involved_entities}")
        print()


if __name__ == "__main__":
    asyncio.run(test_simple()) 