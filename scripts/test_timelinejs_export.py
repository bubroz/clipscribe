#!/usr/bin/env python3
"""Test TimelineJS export functionality with real Timeline v2.0 data."""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clipscribe.utils.timeline_js_formatter import TimelineJSFormatter
from clipscribe.timeline.models import ConsolidatedTimeline, TemporalEvent, DatePrecision, EventType

async def test_timelinejs_export():
    """Test TimelineJS export with sample Timeline v2.0 data."""
    
    print("🧪 Testing TimelineJS Export Functionality...")
    print("=" * 50)
    
    # Create sample temporal events
    events = [
        TemporalEvent(
            event_id="evt_001",
            content_hash="hash1",
            date=datetime(2018, 12, 15),
            date_precision=DatePrecision.DAY,
            date_confidence=0.95,
            extracted_date_text="December 15, 2018",
            date_source="transcript_content",
            description="Pegasus spyware discovered targeting human rights activists",
            event_type=EventType.FACTUAL,
            involved_entities=["Pegasus", "NSO Group", "Human Rights Activists"],
            source_videos=["https://youtube.com/watch?v=6ZVj1_SE4Mo"],
            video_timestamps={"https://youtube.com/watch?v=6ZVj1_SE4Mo": 120.5},
            chapter_context="Chapter 2: Discovery",
            extraction_method="timeline_v2",
            confidence=0.85
        ),
        TemporalEvent(
            event_id="evt_002", 
            content_hash="hash2",
            date=datetime(2021, 7, 18),
            date_precision=DatePrecision.EXACT,
            date_confidence=0.98,
            extracted_date_text="July 18, 2021, at 3:00 PM",
            date_source="news_report",
            description="Pegasus Project reveals 50,000 potential surveillance targets",
            event_type=EventType.REPORTED,
            involved_entities=["Pegasus Project", "NSO Group", "50,000 targets"],
            source_videos=["https://youtube.com/watch?v=xYMWTXIkANM"],
            video_timestamps={"https://youtube.com/watch?v=xYMWTXIkANM": 45.2},
            chapter_context="Chapter 1: Introduction",
            extraction_method="timeline_v2_enhanced",
            confidence=0.92
        ),
        TemporalEvent(
            event_id="evt_003",
            content_hash="hash3",
            date=datetime(2026, 1, 1),
            date_precision=DatePrecision.YEAR,
            date_confidence=0.7,
            extracted_date_text="next year",
            date_source="inference",
            description="Expected regulatory changes for surveillance technology",
            event_type=EventType.INFERRED,
            involved_entities=["Surveillance Technology", "Regulation"],
            source_videos=["https://youtube.com/watch?v=6ZVj1_SE4Mo"],
            video_timestamps={"https://youtube.com/watch?v=6ZVj1_SE4Mo": 300.0},
            chapter_context="Chapter 5: Future Outlook",
            extraction_method="content_extraction",
            confidence=0.65
        )
    ]
    
    # Create consolidated timeline
    timeline = ConsolidatedTimeline(
        events=events,
        video_sources=[
            "https://youtube.com/watch?v=6ZVj1_SE4Mo",
            "https://youtube.com/watch?v=xYMWTXIkANM"
        ]
    )
    
    # Initialize formatter
    formatter = TimelineJSFormatter()
    
    # Convert to TimelineJS format
    print("\n📊 Converting Timeline v2.0 to TimelineJS3 format...")
    timeline_js = formatter.format_timeline(
        timeline,
        title="Pegasus Spyware Investigation Timeline",
        description="A comprehensive timeline of the Pegasus spyware scandal"
    )
    
    # Display results
    print(f"\n✅ Conversion successful!")
    print(f"📌 Timeline events: {len(timeline_js['events'])}")
    print(f"📝 Title: {timeline_js['title']['text']['headline']}")
    
    # Show sample event
    if timeline_js['events']:
        event = timeline_js['events'][0]
        print(f"\n🔍 Sample Event:")
        print(f"  Date: {event['start_date']}")
        print(f"  Headline: {event['text']['headline']}")
        print(f"  Group: {event.get('group', 'N/A')}")
        if 'media' in event:
            print(f"  Media URL: {event['media']['url']}")
    
    # Save to test output
    output_path = Path("output/test_timeline_js.json")
    output_path.parent.mkdir(exist_ok=True)
    formatter.save_timeline(timeline_js, output_path)
    
    print(f"\n💾 Saved test output to: {output_path}")
    
    # Validate structure
    print(f"\n🔧 Validating TimelineJS3 structure...")
    required_fields = ['title', 'events']
    for field in required_fields:
        if field in timeline_js:
            print(f"  ✓ {field} present")
        else:
            print(f"  ✗ {field} MISSING")
    
    # Check event structure
    if timeline_js['events']:
        event = timeline_js['events'][0]
        event_fields = ['start_date', 'text']
        print(f"\n🔧 Validating event structure:")
        for field in event_fields:
            if field in event:
                print(f"  ✓ {field} present")
            else:
                print(f"  ✗ {field} MISSING")
    
    print("\n✨ TimelineJS export test complete!")
    
    # Show how to view in TimelineJS
    print("\n📖 To view in TimelineJS:")
    print("1. Upload the JSON to https://timeline.knightlab.com/")
    print("2. Or integrate with your web application")
    print("3. The timeline will render with interactive navigation")
    
    return timeline_js

if __name__ == "__main__":
    result = asyncio.run(test_timelinejs_export())
    print(f"\n🎉 Test completed successfully!")
    print(f"📊 Generated {len(result['events'])} timeline events") 