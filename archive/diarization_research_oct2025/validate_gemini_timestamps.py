#!/usr/bin/env python3
"""
VALIDATION: Are Gemini's speaker timestamps accurate or hallucinated?

Compare Gemini's timestamps to ground truth CHiME-6 speaker labels.
"""

import json
from pathlib import Path

def parse_timestamp(ts: str) -> float:
    """Convert MM:SS or HH:MM:SS or HH:MM:SS.ss to seconds."""
    # Handle "00:01:05.58" format from CHiME-6
    parts = ts.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0

def validate_gemini_timestamps():
    """Check if Gemini's timestamps match ground truth."""
    
    # Load ground truth
    gt_path = Path("validation_data/samples/chime6/transcriptions/transcriptions/dev/S09.json")
    if not gt_path.exists():
        print(f"ERROR: Ground truth not found at {gt_path}")
        return
    
    with open(gt_path) as f:
        ground_truth = json.load(f)
    
    # Gemini's claimed speakers and timestamps
    gemini_speakers = {
        1: {
            "timestamps": ["00:02:40 - 00:02:42", "00:05:04 - 00:05:05", "00:09:55 - 00:09:58"],
            "description": "Female, medium-high pitch"
        },
        2: {
            "timestamps": ["00:00:00 - 00:00:08", "00:05:50 - 00:05:54", "00:10:07 - 00:10:13"],
            "description": "Female, slightly lower pitch"
        },
        3: {
            "timestamps": ["00:00:08 - 00:00:15", "00:07:05 - 00:07:07", "00:12:35 - 00:12:40"],
            "description": "Female, medium-low pitch"
        },
        4: {
            "timestamps": ["00:01:08 - 00:01:10", "00:03:07 - 00:03:09", "00:08:49 - 00:08:52"],
            "description": "Male, low pitch"
        }
    }
    
    print("="*80)
    print("GEMINI TIMESTAMP VALIDATION")
    print("="*80)
    print()
    
    # Check each Gemini timestamp against ground truth
    for speaker_id, data in gemini_speakers.items():
        print(f"\nGemini Speaker {speaker_id}: {data['description']}")
        print("-" * 80)
        
        for ts_range in data['timestamps'][:3]:  # Check first 3 timestamps
            start_str, end_str = ts_range.split(' - ')
            start_sec = parse_timestamp(start_str)
            end_sec = parse_timestamp(end_str)
            
            # Find what's ACTUALLY at this timestamp in ground truth
            actual_speakers = set()
            actual_text = []
            
            for seg in ground_truth:
                seg_start = parse_timestamp(seg['start_time'])
                seg_end = parse_timestamp(seg['end_time'])
                
                # Check if ground truth segment overlaps with Gemini's claimed time
                if not (seg_end < start_sec or seg_start > end_sec):
                    actual_speakers.add(seg['speaker'])
                    actual_text.append(seg['words'])
            
            if actual_speakers:
                print(f"  {ts_range}")
                print(f"    Gemini claims: Speaker {speaker_id}")
                print(f"    Ground truth:  {', '.join(sorted(actual_speakers))}")
                print(f"    Text: {' '.join(actual_text[:50])}...")
                
                # Check if it's a match (accounting for unknown speaker mapping)
                if len(actual_speakers) == 1:
                    print(f"    ✓ Single speaker detected")
                else:
                    print(f"    ✗ Multiple speakers or mismatch")
            else:
                print(f"  {ts_range}")
                print(f"    ✗ NO SPEECH in ground truth at this time")
    
    print()
    print("="*80)
    print("ANALYSIS")
    print("="*80)
    print()
    print("If Gemini's timestamps are accurate:")
    print("  - Ground truth should show speech at claimed times")
    print("  - Should be single speaker per timestamp")
    print("  - Text should match conversation context")
    print()
    print("If Gemini is hallucinating:")
    print("  - Timestamps won't align with ground truth")
    print("  - Multiple speakers or no speech at claimed times")
    print("  - Random/incorrect associations")

if __name__ == "__main__":
    validate_gemini_timestamps()

