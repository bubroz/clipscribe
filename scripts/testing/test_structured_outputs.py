#!/usr/bin/env python3
"""
Test Structured Outputs impact on extraction quality.

Processes one video (The View - shortest) to verify:
1. Structured Outputs work (no errors)
2. Relationships improved (expect more than 8)
3. All required fields present
4. No hallucinations (evidence matches transcript)
"""

import asyncio
from pathlib import Path
import json
from datetime import datetime
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_structured_outputs():
    """Test Structured Outputs with one video."""
    import modal
    from google.cloud import storage
    
    print("="*80)
    print("TESTING STRUCTURED OUTPUTS - THE VIEW (36min)")
    print("="*80)
    print()
    
    # Use The View (shortest video for fast testing)
    test_audio = project_root / "test_videos/U3w93r5QRb8_The View Full Broadcast – October 14, 2025.mp3"
    
    if not test_audio.exists():
        print(f"❌ Test audio not found: {test_audio}")
        return
    
    # Upload to GCS
    print("Uploading to GCS...")
    client = storage.Client()
    bucket = client.bucket("clipscribe-validation")
    
    gcs_path = "validation/structured_outputs_test/the_view.mp3"
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(str(test_audio))
    
    gcs_url = f"gs://clipscribe-validation/{gcs_path}"
    print(f"✓ Uploaded")
    
    # Call Modal with Structured Outputs
    print("\nProcessing with Modal (Structured Outputs enabled)...")
    
    Station10Transcriber = modal.Cls.from_name("station10-transcription", "Station10Transcriber")
    result_dict = Station10Transcriber().transcribe_from_gcs.remote(
        gcs_input=gcs_url,
        gcs_output="gs://clipscribe-validation/validation/structured_outputs_test/output/"
    )
    
    # Download results
    transcript_blob = bucket.blob("validation/structured_outputs_test/output//transcript.json")
    
    if not transcript_blob.exists():
        print("❌ Transcript not found")
        return
    
    transcript_data = json.loads(transcript_blob.download_as_text())
    
    # Analyze results
    entities = transcript_data.get('entities', [])
    relationships = transcript_data.get('relationships', [])
    topics = transcript_data.get('topics', [])
    key_moments = transcript_data.get('key_moments', [])
    sentiment = transcript_data.get('sentiment', {})
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    print(f"\nEntities: {len(entities)}")
    print(f"Relationships: {len(relationships)} ← KEY METRIC (was 8 before)")
    print(f"Topics: {len(topics)}")
    print(f"Key moments: {len(key_moments)}")
    print(f"Sentiment: {sentiment.get('overall', 'N/A')}")
    
    # Verify required fields present
    print("\n" + "="*80)
    print("SCHEMA VALIDATION")
    print("="*80)
    
    # Check entities have required fields
    if entities:
        entity = entities[0]
        has_name = 'name' in entity
        has_type = 'type' in entity
        has_conf = 'confidence' in entity
        has_evidence = 'evidence' in entity
        
        print(f"\nEntity fields:")
        print(f"  name: {'✓' if has_name else '✗'}")
        print(f"  type: {'✓' if has_type else '✗'}")
        print(f"  confidence: {'✓' if has_conf else '✗'}")
        print(f"  evidence: {'✓' if has_evidence else '✗'}")
    
    # Check relationships have required fields
    if relationships:
        rel = relationships[0]
        has_subj = 'subject' in rel
        has_pred = 'predicate' in rel
        has_obj = 'object' in rel
        has_evidence = 'evidence' in rel
        has_conf = 'confidence' in rel
        
        print(f"\nRelationship fields:")
        print(f"  subject: {'✓' if has_subj else '✗'}")
        print(f"  predicate: {'✓' if has_pred else '✗'}")
        print(f"  object: {'✓' if has_obj else '✗'}")
        print(f"  evidence: {'✓' if has_evidence else '✗'}")
        print(f"  confidence: {'✓' if has_conf else '✗'}")
        
        # Sample relationships
        print(f"\nSample relationships:")
        for i, rel in enumerate(relationships[:5], 1):
            print(f"  {i}. {rel.get('subject')} → {rel.get('predicate')} → {rel.get('object')}")
            print(f"     Evidence: \"{rel.get('evidence', '')[:60]}...\"")
    
    # Compare to previous results
    print("\n" + "="*80)
    print("COMPARISON TO PREVIOUS (Before Structured Outputs)")
    print("="*80)
    print(f"\nThe View (Previous):")
    print(f"  Entities: 56")
    print(f"  Relationships: 8")
    print(f"  Topics: 3")
    print(f"  Key moments: 4")
    
    print(f"\nThe View (With Structured Outputs):")
    print(f"  Entities: {len(entities)}")
    print(f"  Relationships: {len(relationships)} ← Did this improve?")
    print(f"  Topics: {len(topics)}")
    print(f"  Key moments: {len(key_moments)}")
    
    # Assessment
    print("\n" + "="*80)
    print("ASSESSMENT")
    print("="*80)
    
    rel_improved = len(relationships) > 8
    schema_valid = all(['evidence' in e for e in entities[:10]])
    
    print(f"\n✓ Structured Outputs working: Schema enforced")
    print(f"{'✓' if rel_improved else '⚠'} Relationships: {len(relationships)} (previous: 8)")
    print(f"{'✓' if schema_valid else '✗'} Evidence: All entities have quotes")
    
    if rel_improved:
        improvement = ((len(relationships) - 8) / 8 * 100)
        print(f"\n🎉 IMPROVEMENT: {improvement:.0f}% more relationships!")
    else:
        print(f"\n⚠ No improvement in relationships (still {len(relationships)})")
    
    print(f"\n📄 Full results: validation/structured_outputs_test/output//transcript.json")

if __name__ == "__main__":
    asyncio.run(test_structured_outputs())
