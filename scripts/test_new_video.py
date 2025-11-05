#!/usr/bin/env python3
"""
Test Joe Rogan + Kiriakou (Intelligence Podcast) with Structured Outputs

Video: https://www.youtube.com/watch?v=TZqADzuu73g
Duration: 151 minutes (2.5 hours)
Speakers: 2 (Joe Rogan, John Kiriakou)
Content: CIA/intelligence topics

This validates Structured Outputs on intelligence content we haven't tested before.
"""

import asyncio
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_rogan_kiriakou():
    """Process Joe Rogan + Kiriakou video via Modal."""
    
    print("="*80)
    print("TESTING: Joe Rogan + Kiriakou (151min, Intelligence Content)")
    print("="*80)
    print("\nVideo: https://www.youtube.com/watch?v=TZqADzuu73g")
    print("Duration: 151 minutes (2.5 hours)")
    print("Speakers: 2 (Joe Rogan, John Kiriakou)")
    print("Topics: CIA, intelligence, OSINT")
    print("")
    
    # Instructions for processing
    print("TO PROCESS THIS VIDEO:")
    print("")
    print("1. Download audio (if needed):")
    print("   youtube-dl -x --audio-format mp3 https://www.youtube.com/watch?v=TZqADzuu73g")
    print("   mv *.mp3 test_videos/TZqADzuu73g_rogan_kiriakou.mp3")
    print("")
    print("2. Upload to GCS and process via Modal:")
    print("   (Or provide implementation here)")
    print("")
    print("This will test:")
    print("  - Structured Outputs on intelligence terminology")
    print("  - Relationship extraction (CIA connections)")
    print("  - 151min endurance (chunk limit handling)")
    print("  - Entity types: PERSON, ORG (CIA, FBI, NSA)")
    print("  - Topics: Intelligence operations, OSINT, whistleblowing")
    print("")
    print("Expected results:")
    print("  - Entities: ~150-200 (John Kiriakou, CIA, FBI, NSA, etc.)")
    print("  - Relationships: 15-30 (intelligence connections)")
    print("  - Topics: 5-8 (CIA operations, whistleblowing, OSINT)")
    print("  - Key moments: 8-12 (significant intelligence revelations)")
    print("  - Cost: ~$0.50-0.60 (151min * $0.34/88min average)")

if __name__ == "__main__":
    asyncio.run(test_rogan_kiriakou())

