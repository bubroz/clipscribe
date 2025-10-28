#!/usr/bin/env python3
"""
Entity Pipeline Test - Using LOCAL files (no YouTube download needed)

Tests entity extraction on already-downloaded videos.
"""

import asyncio
from pathlib import Path
import json
from datetime import datetime
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# Local test files we already have
LOCAL_TEST_FILES = [
    {
        "path": "test_videos/medical_lxFd5xAN4cg.mp3",
        "name": "Medical Education",
        "duration_min": 16,
        "speakers": 1,
        "type": "Medical"
    },
    {
        "path": "test_videos/legal_7iHl71nt49o.mp3",
        "name": "Legal Analysis",
        "duration_min": 60,
        "speakers": 2,
        "type": "Legal"
    }
    # Durov removed - 274 min takes too long for quick testing
]


async def process_local_file_with_modal(audio_path: Path, video_name: str):
    """Process local audio file through Modal (WhisperX + Gemini + Entities)."""
    import modal
    from google.cloud import storage
    
    print(f"\n{'='*80}")
    print(f"PROCESSING: {video_name}")
    print(f"File: {audio_path}")
    print(f"{'='*80}\n")
    
    if not audio_path.exists():
        print(f"❌ File not found: {audio_path}")
        return None
    
    # Upload to GCS
    print(f"  Uploading to GCS...")
    client = storage.Client()
    bucket = client.bucket("clipscribe-validation")
    
    gcs_path = f"validation/local/{audio_path.name}"
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(str(audio_path))
    
    gcs_url = f"gs://clipscribe-validation/{gcs_path}"
    print(f"  ✓ Uploaded: {gcs_url}")
    
    # Call Modal
    print(f"  Processing with Modal...")
    
    try:
        # CORRECT Modal 1.0+ API pattern - must instantiate first
        Station10Transcriber = modal.Cls.from_name("station10-transcription", "Station10Transcriber")
        result_dict = Station10Transcriber().transcribe_from_gcs.remote(
            gcs_input=gcs_url,
            gcs_output=f"gs://clipscribe-validation/validation/results/"
        )
        
        print(f"  ✓ Modal complete: {result_dict.get('speakers', 0)} speakers, ${result_dict.get('cost', 0):.4f}")
        
        # IMPORTANT: Download full transcript from GCS (Modal only returns summary)
        gcs_output = result_dict.get('gcs_output', '')
        if gcs_output:
            # Download transcript.json
            transcript_path = f"{gcs_output.rstrip('/')}/transcript.json"
            transcript_blob = bucket.blob(transcript_path.replace('gs://clipscribe-validation/', ''))
            
            if transcript_blob.exists():
                transcript_json = json.loads(transcript_blob.download_as_text())
                # Merge with result_dict to include entities/relationships
                result_dict.update(transcript_json)
            else:
                print(f"  ⚠ Transcript not found at {transcript_path}")
        
        return result_dict
        
    except Exception as e:
        print(f"  ❌ Modal processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_result(result: dict, video_info: dict):
    """Analyze if entity extraction is working."""
    print(f"\n📊 ANALYSIS: {video_info['name']}")
    print("-" * 80)
    
    if not result:
        print("❌ No result to analyze")
        return {'status': 'failed'}
    
    # Check transcript
    transcript = result.get('transcript', {})
    segments = transcript.get('segments', [])
    print(f"✓ Segments: {len(segments)}")
    
    # Check speakers
    speakers = result.get('speakers', 0)
    print(f"✓ Speakers: {speakers} detected (expected: {video_info['speakers']})")
    
    # THE CRITICAL CHECK: Entities
    entities = result.get('entities', [])
    relationships = result.get('relationships', [])
    
    if entities:
        print(f"✅ ENTITIES: {len(entities)} extracted")
        print(f"  Sample:")
        for e in entities[:3]:
            print(f"    - {e}")
    else:
        print(f"❌ NO ENTITIES - Not integrated yet!")
    
    if relationships:
        print(f"✅ RELATIONSHIPS: {len(relationships)}")
    else:
        print(f"❌ NO RELATIONSHIPS")
    
    return {
        'video': video_info['name'],
        'speakers': speakers,
        'entities': len(entities),
        'relationships': len(relationships),
        'entity_extraction_working': len(entities) > 0
    }


async def main():
    print("="*80)
    print("ENTITY EXTRACTION VALIDATION (LOCAL FILES)")
    print("="*80)
    print()
    
    results = []
    
    for video in LOCAL_TEST_FILES:
        audio_path = Path(video['path'])
        result = await process_local_file_with_modal(audio_path, video['name'])
        analysis = analyze_result(result, video)
        results.append(analysis)
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    
    working = sum(1 for r in results if r.get('entity_extraction_working', False))
    print(f"\nEntity extraction: {working}/{len(results)} videos")
    
    if working == 0:
        print("\n❌ Entity extraction NOT in Modal pipeline yet")
        print("\nNEXT: Integrate Grok entity extraction into Modal")
    else:
        print("\n✅ Entity extraction WORKING!")
        print("\nREADY: Week 5-8 features")
    
    # Save results
    output = Path("validation_data/entity_test_results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults: {output}")


if __name__ == "__main__":
    asyncio.run(main())

