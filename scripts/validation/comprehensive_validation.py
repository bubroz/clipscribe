#!/usr/bin/env python3
"""
Comprehensive Entity Extraction Validation

Tests entity extraction on diverse content types to validate:
- Entity type diversity (PERSON, ORG, LOCATION, CONCEPT)
- Multi-speaker panels
- Relationship quality
- Speaker-entity attribution
"""

import asyncio
from pathlib import Path
import json
from datetime import datetime
import sys
from typing import Dict, List
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Helper for timestamped progress
def log_progress(msg: str):
    """Print timestamped progress message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

# Test videos from MASTER_TEST_VIDEO_TABLE.md
COMPREHENSIVE_TEST_VIDEOS = [
    {
        "id": "P-2",
        "name": "All-In Podcast",
        "local_path": "test_videos/IbnrclsPGPQ_Trump Brokers Gaza Peace Deal, National Guard in C.mp3",
        "duration_min": 88,
        "speakers": 4,
        "type": "Tech/politics panel",
        "expected_entity_types": ["PERSON", "ORG", "LOCATION", "CONCEPT"]
    },
    {
        "id": "View-1",
        "name": "The View Oct 14",
        "local_path": "test_videos/U3w93r5QRb8_The View Full Broadcast – October 14, 2025.mp3",
        "duration_min": 36,
        "speakers": 5,
        "type": "Daily panel",
        "expected_entity_types": ["PERSON", "ORG", "CONCEPT"]
    },
    {
        "id": "P-1",
        "name": "MTG Interview",
        "local_path": "test_videos/wlONOh_iUXY_Marjorie Taylor Greene Emergency Podcast ｜ The Tim.mp3",
        "duration_min": 71,
        "speakers": 2,
        "type": "Political podcast",
        "expected_entity_types": ["PERSON", "ORG", "LOCATION", "CONCEPT"]
    },
]


async def process_video_with_modal(audio_path: Path, video_info: dict):
    """Process local video through Modal."""
    import modal
    from google.cloud import storage
    
    print(f"\n{'='*80}")
    log_progress(f"Processing {video_info['name']} ({video_info['duration_min']} min, {video_info['speakers']} speakers)")
    print(f"{'='*80}\n")
    
    if not audio_path.exists():
        log_progress(f"ERROR: File not found: {audio_path}")
        return None
    
    # Upload to GCS
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    log_progress(f"Uploading to GCS ({file_size_mb:.0f}MB)...")
    
    upload_start = time.time()
    client = storage.Client()
    bucket = client.bucket("clipscribe-validation")
    
    gcs_path = f"validation/local/{audio_path.name}"
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(str(audio_path))
    
    upload_time = time.time() - upload_start
    gcs_url = f"gs://clipscribe-validation/{gcs_path}"
    log_progress(f"Upload complete ({upload_time:.1f}s)")
    
    # Call Modal
    log_progress("Modal processing started...")
    
    try:
        modal_start = time.time()
        Station10Transcriber = modal.Cls.from_name("station10-transcription", "Station10Transcriber")
        result_dict = Station10Transcriber().transcribe_from_gcs.remote(
            gcs_input=gcs_url,
            gcs_output=f"gs://clipscribe-validation/validation/results/{video_info['id']}/"
        )
        
        modal_time = time.time() - modal_start
        log_progress(f"Modal complete: {result_dict.get('speakers', 0)} speakers, ${result_dict.get('cost', 0):.4f}, {result_dict.get('entities', 0)} entities ({modal_time:.1f}s)")
        
        # Download full transcript from GCS
        gcs_output = result_dict.get('gcs_output', '')
        if gcs_output:
            # Try multiple path patterns
            possible_paths = [
                f"{gcs_output.rstrip('/')}/transcript.json",
                f"{gcs_output.rstrip('/')}//transcript.json",
                f"validation/results/{video_info['id']}//transcript.json",
            ]
            
            transcript_json = None
            for path in possible_paths:
                blob_path = path.replace('gs://clipscribe-validation/', '')
                transcript_blob = bucket.blob(blob_path)
                
                if transcript_blob.exists():
                    log_progress("Downloading transcript from GCS...")
                    transcript_json = json.loads(transcript_blob.download_as_text())
                    result_dict.update(transcript_json)
                    break
            
            if transcript_json is None:
                log_progress("WARNING: Transcript not found")
        
        return result_dict
        
    except Exception as e:
        log_progress(f"ERROR: Modal processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_entities(result: dict, video_info: dict) -> dict:
    """Analyze entity extraction quality."""
    print(f"\n📊 ANALYSIS: {video_info['name']}")
    print("-" * 80)
    
    if not result:
        return {'status': 'failed'}
    
    # Extract data
    segments = result.get('segments', [])
    entities = result.get('entities', [])
    relationships = result.get('relationships', [])
    speakers = len(set(s.get('speaker') for s in segments if s.get('speaker')))
    
    print(f"✓ Segments: {len(segments)}")
    print(f"✓ Speakers: {speakers} (expected: {video_info['speakers']})")
    print(f"✓ Entities: {len(entities)}")
    print(f"✓ Relationships: {len(relationships)}")
    
    if entities:
        # Analyze entity types
        entity_types = {}
        for e in entities:
            etype = e.get('type', 'UNKNOWN')
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        print(f"\n📈 ENTITY TYPE DISTRIBUTION:")
        for etype, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {etype}: {count}")
        
        print(f"\n🔍 SAMPLE ENTITIES:")
        for i, e in enumerate(entities[:5]):
            name = e.get('name', 'N/A')
            etype = e.get('type', 'N/A')
            conf = e.get('confidence', 0)
            print(f"  {i+1}. {name} ({etype}, conf: {conf})")
        
        # Validation checks
        expected_types = video_info.get('expected_entity_types', [])
        found_types = set(entity_types.keys())
        
        print(f"\n✅ VALIDATION:")
        
        # Check entity type diversity
        has_diversity = len(entity_types) >= 2
        print(f"  Entity diversity: {'✅ PASS' if has_diversity else '❌ FAIL'} ({len(entity_types)} types)")
        
        # Check for expected types
        has_expected = any(t in found_types for t in expected_types)
        if expected_types:
            print(f"  Expected types: {'✅ PASS' if has_expected else '❌ FAIL'} (found: {found_types})")
        
        # Check entity count
        has_sufficient = len(entities) >= 10
        print(f"  Entity count: {'✅ PASS' if has_sufficient else '❌ FAIL'} ({len(entities)} entities)")
        
        # Check relationships
        has_relationships = len(relationships) >= 5
        rel_per_entity = len(relationships) / len(entities) if entities else 0
        print(f"  Relationships: {'✅ PASS' if has_relationships else '❌ FAIL'} ({len(relationships)} total, {rel_per_entity:.2f} per entity)")
        
        validation_score = sum([
            has_diversity,
            has_expected if expected_types else False,
            has_sufficient,
            has_relationships
        ]) / 4.0
        
        print(f"\n📊 VALIDATION SCORE: {validation_score*100:.0f}%")
        
        return {
            'status': 'success',
            'speakers': speakers,
            'segments': len(segments),
            'entities': len(entities),
            'relationships': len(relationships),
            'entity_types': entity_types,
            'validation_score': validation_score,
            'entity_extraction_working': True
        }
    else:
        print(f"❌ NO ENTITIES - Entity extraction not working!")
        return {
            'status': 'failed',
            'entity_extraction_working': False
        }


async def main():
    start_time = time.time()
    
    print("="*80)
    log_progress("STARTING COMPREHENSIVE VALIDATION")
    print("="*80)
    print(f"\nTesting {len(COMPREHENSIVE_TEST_VIDEOS)} videos:")
    for v in COMPREHENSIVE_TEST_VIDEOS:
        print(f"  - {v['name']} ({v['duration_min']} min, {v['speakers']} speakers)")
    print("="*80)
    
    results = []
    
    for i, video_info in enumerate(COMPREHENSIVE_TEST_VIDEOS, 1):
        log_progress(f"Video {i}/{len(COMPREHENSIVE_TEST_VIDEOS)}: {video_info['name']}")
        
        audio_path = project_root / video_info['local_path']
        
        # Process with Modal
        result = await process_video_with_modal(audio_path, video_info)
        
        # Analyze
        analysis = analyze_entities(result, video_info)
        analysis['video'] = video_info['name']
        analysis['video_id'] = video_info['id']
        results.append(analysis)
        
        elapsed = time.time() - start_time
        log_progress(f"Completed {i}/{len(COMPREHENSIVE_TEST_VIDEOS)} videos (elapsed: {elapsed/60:.1f}m)")
    
    # Summary
    total_time = time.time() - start_time
    
    print("\n" + "="*80)
    log_progress(f"VALIDATION COMPLETE ({total_time/60:.1f}m total)")
    print("="*80)
    
    total_videos = len(results)
    working = sum(1 for r in results if r.get('entity_extraction_working', False))
    avg_score = sum(r.get('validation_score', 0) for r in results) / total_videos if results else 0
    total_entities = sum(r.get('entities', 0) for r in results)
    
    print(f"Total videos: {total_videos}")
    print(f"Entity extraction working: {working}/{total_videos}")
    print(f"Total entities extracted: {total_entities}")
    print(f"Average validation score: {avg_score*100:.0f}%")
    
    if avg_score >= 0.75:
        log_progress("VALIDATION PASSED - Ready for Week 5-8 features!")
    elif avg_score >= 0.5:
        log_progress("VALIDATION PARTIAL - Some issues found, proceed with caution")
    else:
        log_progress("VALIDATION FAILED - Fix issues before proceeding")
    
    # Save results
    output_path = project_root / "validation_data" / "comprehensive_validation_results.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_videos': total_videos,
            'working_count': working,
            'average_score': avg_score,
            'videos': results,
            'overall_assessment': 'READY' if avg_score >= 0.75 else 'NEEDS_FIXES'
        }, f, indent=2)
    
    print(f"\n📄 Results saved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())

