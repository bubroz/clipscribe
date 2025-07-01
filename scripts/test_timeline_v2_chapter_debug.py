#!/usr/bin/env python3
"""Debug test for Timeline v2.0 chapter text extraction"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.timeline.temporal_extractor_v2 import TemporalExtractorV2, TemporalExtractionContext, TemporalMetadata
from src.clipscribe.retrievers.universal_video_client import Chapter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_chapter_text_extraction():
    """Test chapter text extraction with real data"""
    
    extractor = TemporalExtractorV2()
    
    # Realistic transcript from a 10-minute video
    test_transcript = """
    Welcome to today's show. We're going to talk about artificial intelligence and its impact on society.
    In recent years, AI has transformed many industries. Machine learning algorithms are now used everywhere,
    from healthcare to finance. Let me give you some examples.
    
    First, in healthcare, AI is being used to diagnose diseases more accurately. Doctors are using
    machine learning models to analyze medical images and detect cancer earlier than ever before.
    This is saving lives every day.
    
    Second, in finance, AI algorithms are detecting fraud in real-time. Banks are processing millions
    of transactions per second and identifying suspicious patterns that humans would miss.
    
    Third, in transportation, self-driving cars are becoming a reality. Companies like Tesla and Waymo
    are pushing the boundaries of what's possible with autonomous vehicles.
    
    But there are also concerns. Privacy advocates worry about surveillance. Ethicists question
    the decision-making processes of AI systems. And workers fear job displacement.
    
    These are complex issues that require careful consideration. We need to balance innovation
    with responsibility. The future of AI depends on the choices we make today.
    
    Thank you for watching. In our next segment, we'll dive deeper into specific AI applications
    and hear from experts in the field. Stay tuned.
    """
    
    # Create mock temporal metadata with realistic chapters for a 10-minute video
    temporal_metadata = TemporalMetadata(
        chapters=[
            Chapter(title="Introduction", start_time=0.0, end_time=60.0),
            Chapter(title="AI in Healthcare", start_time=60.0, end_time=180.0),
            Chapter(title="AI in Finance", start_time=180.0, end_time=300.0),
            Chapter(title="AI in Transportation", start_time=300.0, end_time=420.0),
            Chapter(title="Concerns and Ethics", start_time=420.0, end_time=540.0),
            Chapter(title="Conclusion", start_time=540.0, end_time=600.0),
        ],
        subtitles=None,
        sponsorblock_segments=[],
        video_metadata={'duration': 600},  # 10 minutes
        word_level_timing={},  # Empty to test fallback
        content_sections=[]
    )
    
    # Create extraction context
    context = TemporalExtractionContext(
        video_url="https://example.com/test",
        video_metadata=temporal_metadata.video_metadata,
        temporal_metadata=temporal_metadata,
        transcript_text=test_transcript,
        chapter_context=extractor._build_chapter_context(temporal_metadata),
        word_level_timing={}
    )
    
    # Test chapter text extraction
    print("\n=== Testing Chapter Text Extraction ===")
    print(f"Total transcript length: {len(test_transcript)} chars")
    print(f"Total words: {len(test_transcript.split())} words")
    print(f"Estimated duration: {(len(test_transcript.split()) / 150) * 60:.1f} seconds")
    print(f"Actual video duration: {temporal_metadata.video_metadata['duration']} seconds")
    
    for chapter in temporal_metadata.chapters:
        print(f"\n📖 Chapter: {chapter.title}")
        print(f"   Time: {chapter.start_time:.1f}s - {chapter.end_time:.1f}s")
        
        # Extract chapter text
        chapter_text = extractor._get_chapter_text(
            test_transcript,
            {},  # Empty word timing to test fallback
            chapter.start_time,
            chapter.end_time,
            video_duration=temporal_metadata.video_metadata['duration']  # Pass real duration!
        )
        
        print(f"   Extracted text length: {len(chapter_text)} chars")
        if chapter_text:
            print(f"   Preview: {chapter_text[:100]}...")
        else:
            print("   ⚠️  EMPTY TEXT EXTRACTED!")
            
        # Debug the calculation
        words = test_transcript.split()
        estimated_duration = (len(words) / 150) * 60
        print(f"   Debug: {len(words)} words, est duration: {estimated_duration:.1f}s")
        
        if estimated_duration > 0:
            start_word = int((chapter.start_time / estimated_duration) * len(words))
            end_word = int((chapter.end_time / estimated_duration) * len(words))
            print(f"   Debug: start_word={start_word}, end_word={end_word}")
            
            # Show what the bounds would be
            start_word = max(0, min(start_word, len(words)))
            end_word = max(start_word, min(end_word, len(words)))
            print(f"   Debug: adjusted start_word={start_word}, end_word={end_word}")


if __name__ == "__main__":
    asyncio.run(test_chapter_text_extraction()) 