#!/usr/bin/env python3
"""Test Timeline v2.0 event extraction without the broken quality filter"""

import asyncio
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.timeline.temporal_extractor_v2 import TemporalExtractorV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_event_extraction():
    """Test what Timeline v2.0 actually extracts"""
    
    extractor = TemporalExtractorV2()
    
    # Simple test transcript with temporal references
    test_transcript = """
    In 2018, the first Pegasus infections were discovered by researchers.
    
    Then in 2019, WhatsApp sued NSO Group after discovering that Pegasus was used
    to spy on 1,400 users including journalists and human rights activists.
    
    By 2020, the pandemic hit and surveillance technology use exploded globally.
    
    In July 2021, the Pegasus Project revealed that 50,000 phone numbers were
    potentially targeted by NSO Group's spyware.
    
    The investigation showed that Jamal Khashoggi's wife was targeted just days
    after his murder in October 2018.
    """
    
    # Mock entities
    entities = [
        {"name": "Pegasus", "type": "PRODUCT"},
        {"name": "NSO Group", "type": "ORGANIZATION"},
        {"name": "WhatsApp", "type": "ORGANIZATION"},
        {"name": "Jamal Khashoggi", "type": "PERSON"},
        {"name": "Pegasus Project", "type": "PROJECT"}
    ]
    
    # Test the fallback extraction directly
    events = await extractor._fallback_basic_extraction(
        video_url="https://example.com/test",
        transcript_text=test_transcript,
        entities=entities
    )
    
    print(f"\n🎯 Extracted {len(events)} temporal events:\n")
    
    for i, event in enumerate(events, 1):
        print(f"{i}. {event.description}")
        print(f"   Date: {event.date} (source: {event.date_source})")
        print(f"   Confidence: {event.confidence:.2f}")
        print(f"   Method: {event.extraction_method}")
        print(f"   Entities: {', '.join(event.involved_entities) if event.involved_entities else 'None'}")
        print()
    
    # Check date extraction success
    events_with_dates = [e for e in events if e.date_source != "pending_extraction"]
    print(f"✅ Date extraction: {len(events_with_dates)}/{len(events)} events have dates")
    
    # Now test applying date extraction
    print("\n📅 Testing date extraction on events...")
    from src.clipscribe.timeline.temporal_extractor_v2 import TemporalExtractionContext
    
    context = TemporalExtractionContext(
        video_url="https://example.com/test",
        video_metadata={"duration": 600},
        temporal_metadata=None,
        transcript_text=test_transcript,
        chapter_context={},
        word_level_timing={}
    )
    
    events_with_dates = await extractor._apply_content_date_extraction(events, context)
    
    print(f"\n📅 After date extraction: {len([e for e in events_with_dates if e.date_source != 'pending_extraction'])}/{len(events_with_dates)} events have dates\n")
    
    for i, event in enumerate(events_with_dates[:5], 1):  # Show first 5 events
        if event.date_source != "pending_extraction":
            print(f"{i}. {event.description[:60]}...")
            print(f"   Extracted date: {event.date} (confidence: {event.date_confidence:.2f})")
            print(f"   Original text: '{event.extracted_date_text}'")


if __name__ == "__main__":
    asyncio.run(test_event_extraction())
