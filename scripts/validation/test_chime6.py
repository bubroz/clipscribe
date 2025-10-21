#!/usr/bin/env python3
"""
Test CHiME-6 validation end-to-end.

This will process ONE CHiME-6 session and validate metrics.
No YouTube dependencies - direct audio file processing.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.validation.chime6_validator import CHiME6Validator


async def main():
    """Run CHiME-6 validation test."""
    
    print("="*80)
    print("CHIME-6 END-TO-END VALIDATION TEST")
    print("="*80)
    print()
    
    # Setup paths
    transcripts_dir = Path("validation_data/samples/chime6/transcriptions")
    audio_dir = Path("validation_data/chime6_audio/CHiME6_dev/CHiME6/audio/dev")
    output_path = Path("validation_data/results")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check if audio downloaded
    if not audio_dir.exists():
        print("❌ CHiME-6 audio not downloaded yet!")
        print()
        print("Run this first:")
        print("  ./scripts/validation/download_chime6_audio.sh")
        print()
        return 1
    
    # Initialize validator
    validator = CHiME6Validator(transcripts_dir, audio_dir, output_path)
    validator.load_transcripts("dev")
    
    # Show what we have
    print(f"Dev sessions available:")
    for session_id, data in validator.sessions.items():
        segments = data['segments']
        speakers = set(seg['speaker'] for seg in segments)
        duration = validator._time_to_seconds(segments[-1]['end_time'])
        print(f"  {session_id}: {len(segments)} segs, {len(speakers)} speakers, {duration/60:.1f} min")
    print()
    
    # Process first session
    test_session = list(validator.sessions.keys())[0]
    
    print(f"Testing with session: {test_session}")
    print("-"*80)
    
    try:
        result = await validator.validate_session(test_session, use_modal=True)
        
        print()
        print("="*80)
        print("CHIME-6 VALIDATION COMPLETE")
        print("="*80)
        print()
        
        if result.get('status') == 'success':
            print("✅ SUCCESS!")
            print()
            print("Ground Truth:")
            print(f"  Segments: {result['ground_truth']['segments']}")
            print(f"  Speakers: {result['ground_truth']['speakers']}")
            print(f"  Duration: {result['ground_truth']['duration_minutes']:.1f} min")
            print()
            print("ClipScribe Output:")
            print(f"  Segments: {result['clipscribe']['segments']}")
            print(f"  Speakers: {result['clipscribe']['speakers']}")
            print(f"  Processing: {result['clipscribe']['processing_time']:.1f} min")
            print(f"  Cost: ${result['clipscribe']['cost']:.4f}")
            print()
            print("Metrics:")
            print(f"  WER: {result['metrics']['wer']:.1%}")
            print(f"  Speaker Accuracy: {result['metrics']['speaker_accuracy']:.1%}")
            print(f"  Gemini Corrections: {result['metrics']['gemini_corrections']}")
            print()
            print("vs CHiME-6 Baseline (Track 2):")
            print(f"  Our WER: {result['metrics']['wer']:.1%}")
            print(f"  Baseline WER: 77.9%")
            print(f"  Improvement: {77.9 - result['metrics']['wer']*100:.1f} percentage points")
            print()
            
            # Success!
            return 0
            
        else:
            print(f"❌ Validation failed: {result.get('status')}")
            print(json.dumps(result, indent=2))
            return 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

