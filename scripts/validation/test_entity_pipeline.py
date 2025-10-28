#!/usr/bin/env python3
"""
Entity Extraction Pipeline Validation

Tests ClipScribe's core value proposition on diverse videos from MASTER_TEST_VIDEO_TABLE.md:
1. Transcription quality (WER)
2. Speaker diarization
3. Entity extraction with speaker attribution
4. Relationship mapping

This validates our ACTUAL product, not academic benchmarks.
"""

import asyncio
from pathlib import Path
import json
from datetime import datetime
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test videos from MASTER_TEST_VIDEO_TABLE.md
TEST_VIDEOS = [
    {
        "id": "P-6",
        "name": "Medical Education",
        "url": "https://youtu.be/lxFd5xAN4cg",
        "duration": "16 min",
        "speakers": 1,
        "type": "Medical",
        "why": "Baseline - single speaker, technical terms"
    },
    {
        "id": "P-1", 
        "name": "MTG Interview",
        "url": "https://www.youtube.com/watch?v=wlONOh_iUXY",
        "duration": "71 min",
        "speakers": 2,
        "type": "Political",
        "why": "Standard 2-speaker interview, political entities"
    },
    {
        "id": "View-1",
        "name": "The View Oct 14",
        "url": "https://www.youtube.com/watch?v=U3w93r5QRb8",
        "duration": "36 min",
        "speakers": "5+",
        "type": "Panel",
        "why": "Multi-speaker chaos, overlapping"
    },
    {
        "id": "Legal-1",
        "name": "Legal Analysis",
        "url": "https://www.youtube.com/watch?v=7iHl71nt49o",
        "duration": "60 min",
        "speakers": "2+",
        "type": "Legal",
        "why": "Legal jargon, multiple speakers"
    },
    {
        "id": "P-2",
        "name": "All-In Gaza/OpenAI",
        "url": "https://www.youtube.com/watch?v=IbnrclsPGPQ",
        "duration": "88 min",
        "speakers": "4-5",
        "type": "Tech Panel",
        "why": "Panel discussion, tech + politics"
    }
]


async def process_video_with_modal(video_url: str, video_name: str):
    """
    Process video through Modal (WhisperX + Gemini).
    
    Returns dict with:
    - transcript
    - speakers
    - entities (if extraction working)
    - relationships (if working)
    - metadata
    """
    from scripts.validation.modal_helper import process_youtube_with_modal
    
    print(f"\n{'='*80}")
    print(f"PROCESSING: {video_name}")
    print(f"URL: {video_url}")
    print(f"{'='*80}\n")
    
    try:
        result = await process_youtube_with_modal(
            video_url,
            gcs_bucket="clipscribe-validation"
        )
        return result
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_entities(result: dict, video_info: dict):
    """
    Analyze entity extraction results.
    
    Check:
    1. Were entities extracted?
    2. Do entities have speaker attribution?
    3. Are there relationships?
    4. Quality assessment
    """
    print(f"\n📊 ENTITY ANALYSIS: {video_info['name']}")
    print("-" * 80)
    
    # Check transcript
    transcript = result.get('transcript', {})
    segments = transcript.get('segments', [])
    
    print(f"\n✓ Transcript: {len(segments)} segments")
    
    # Check speakers
    speakers = set()
    for seg in segments:
        if 'speaker' in seg:
            speakers.add(seg['speaker'])
    
    print(f"✓ Speakers: {len(speakers)} detected")
    print(f"  Expected: {video_info['speakers']}")
    if len(speakers) == video_info['speakers'] or video_info['speakers'] == "2+":
        print(f"  ✅ Speaker count GOOD")
    else:
        print(f"  ⚠️ Speaker count off (expected {video_info['speakers']}, got {len(speakers)})")
    
    # Check entities (THE CRITICAL PART)
    # Note: Modal currently returns transcript only
    # Need to integrate entity extraction!
    
    entities = result.get('entities', [])
    relationships = result.get('relationships', [])
    
    if entities:
        print(f"\n✓ Entities: {len(entities)} extracted")
        
        # Check speaker attribution
        with_speakers = sum(1 for e in entities if 'mentioned_by' in e or 'speaker' in e)
        print(f"  Speaker-attributed: {with_speakers}/{len(entities)} ({with_speakers/len(entities)*100:.0f}%)")
        
        # Show sample entities
        print(f"\n  Sample entities:")
        for e in entities[:5]:
            speaker = e.get('mentioned_by', 'UNKNOWN')
            print(f"    - {e.get('name', 'N/A')} ({e.get('type', 'N/A')}) - Speaker: {speaker}")
    else:
        print(f"\n❌ NO ENTITIES EXTRACTED")
        print(f"   THIS IS THE PROBLEM - Entity extraction not integrated!")
    
    if relationships:
        print(f"\n✓ Relationships: {len(relationships)} found")
        for r in relationships[:3]:
            print(f"    - {r}")
    else:
        print(f"\n❌ NO RELATIONSHIPS EXTRACTED")
    
    return {
        'video': video_info['name'],
        'segments': len(segments),
        'speakers_detected': len(speakers),
        'speakers_expected': video_info['speakers'],
        'entities': len(entities),
        'relationships': len(relationships),
        'entity_extraction_working': len(entities) > 0
    }


async def main():
    """
    Test entity extraction pipeline on 5 diverse videos.
    
    This validates our ACTUAL product:
    - Not just transcription (table stakes)
    - But entity extraction + speaker attribution (core value)
    """
    
    print("="*80)
    print("STATION10.MEDIA ENTITY PIPELINE VALIDATION")
    print("="*80)
    print()
    print("Testing on 5 videos from MASTER_TEST_VIDEO_TABLE.md:")
    for v in TEST_VIDEOS:
        print(f"  {v['id']}: {v['name']} ({v['duration']}, {v['speakers']} speakers)")
    print()
    print("Will validate:")
    print("  1. Transcription works")
    print("  2. Speaker diarization works")
    print("  3. ✅ ENTITY EXTRACTION WORKS (core product!)")
    print("  4. ✅ SPEAKER-ENTITY ATTRIBUTION (differentiation!)")
    print("  5. ✅ RELATIONSHIP MAPPING (intelligence!)")
    print()
    print("="*80)
    
    results = []
    
    for video in TEST_VIDEOS:
        result = await process_video_with_modal(video['url'], video['name'])
        
        if result:
            analysis = analyze_entities(result, video)
            results.append(analysis)
        else:
            results.append({
                'video': video['name'],
                'status': 'FAILED'
            })
        
        # Save after each video
        output_path = Path("validation_data/entity_pipeline_test_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'videos_tested': len(results),
                'results': results
            }, f, indent=2)
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    working = sum(1 for r in results if r.get('entity_extraction_working', False))
    
    print(f"\nVideos tested: {len(results)}")
    print(f"Entity extraction working: {working}/{len(results)}")
    
    if working == 0:
        print("\n❌ CRITICAL: Entity extraction NOT integrated with Modal pipeline!")
        print("\nNEXT STEP: Integrate entity extraction into Modal transcription")
        print("Location: deploy/station10_modal.py")
        print("Need to add: Grok entity extraction after transcription")
    elif working < len(results):
        print(f"\n⚠️ Entity extraction partial - {working}/{len(results)} videos")
    else:
        print(f"\n✅ Entity extraction WORKING on all videos!")
        print("\nREADY FOR: Week 5-8 features (clip gen, search, batch)")
    
    print(f"\nResults saved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())

