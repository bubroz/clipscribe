#!/usr/bin/env python3
"""
Test first end-to-end validation.

Process one AnnoMI conversation and calculate WER + speaker accuracy.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path so we can import scripts.validation
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now we can import
from scripts.validation.annomi_validator import AnnoMIValidator


async def main():
    """Run first validation test."""
    
    print("="*80)
    print("ANNOMI END-TO-END VALIDATION TEST")
    print("="*80)
    print()
    
    # Setup paths
    dataset_path = Path("validation_data/samples/annomi/AnnoMI-simple.csv")
    output_path = Path("validation_data/results")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize validator
    validator = AnnoMIValidator(dataset_path, output_path)
    validator.load_dataset()
    
    # Get conversations, find shortest long one for faster test
    long_convos = validator.get_long_conversations(min_utterances=100)
    
    # Find shortest (fastest to test)
    shortest_long = long_convos.sort_values('utterance_count').iloc[0]
    test_id = shortest_long.name
    
    print(f"\nTest conversation:")
    print(f"  ID: {test_id}")
    print(f"  Title: {shortest_long['title']}")
    print(f"  Utterances: {shortest_long['utterance_count']}")
    print(f"  Topic: {shortest_long['topic']}")
    print(f"  URL: {shortest_long['video_url']}")
    print()
    
    # Validate this conversation
    print("Starting validation...")
    print("-"*80)
    
    try:
        result = await validator.validate_conversation(test_id, use_modal=True)
        
        print()
        print("="*80)
        print("VALIDATION COMPLETE")
        print("="*80)
        print()
        
        if result.get('status') == 'success':
            print("✅ SUCCESS!")
            print()
            print("Ground Truth:")
            print(f"  Segments: {result['ground_truth']['segments']}")
            print(f"  Speakers: {result['ground_truth']['speakers']}")
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
            print("Speaker Mapping:")
            for cs_spk, gt_spk in result['speaker_mapping'].items():
                print(f"  {cs_spk} → {gt_spk}")
            print()
            
            # Save result
            result_file = output_path / f"test_result_{test_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ Result saved to {result_file}")
            
        else:
            print(f"❌ Validation failed: {result.get('status')}")
            print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

