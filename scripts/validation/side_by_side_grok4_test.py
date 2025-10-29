#!/usr/bin/env python3
"""
Side-by-side comparison of Grok-4 variants on actual video data.

Tests:
- grok-4-0709 (current local ClipScribe)
- grok-4-fast-reasoning (optimized for reasoning tasks)

Measures:
- Entity extraction quality
- Topic extraction quality
- Key moments extraction quality
- Processing time
- Token usage
- Cost
"""

import asyncio
from pathlib import Path
import json
from datetime import datetime
import sys
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Use The View as test (smaller, faster for comparison)
TEST_VIDEO = {
    "id": "View-1",
    "name": "The View Oct 14",
    "local_path": "test_videos/U3w93r5QRb8_The View Full Broadcast – October 14, 2025.mp3",
    "duration_min": 36,
    "speakers": 5,
}

async def test_model(model_name: str, audio_path: Path):
    """Test a specific Grok model."""
    import modal
    from google.cloud import storage
    
    print(f"\n{'='*80}")
    print(f"TESTING: {model_name}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    # Upload to GCS
    print(f"Uploading to GCS...")
    client = storage.Client()
    bucket = client.bucket("clipscribe-validation")
    
    gcs_path = f"validation/model_comparison/{model_name}_{audio_path.name}"
    blob = bucket.blob(gcs_path)
    
    if not blob.exists():
        blob.upload_from_filename(str(audio_path))
    
    gcs_url = f"gs://clipscribe-validation/{gcs_path}"
    print(f"✓ Uploaded: {gcs_url}")
    
    # Temporarily update Modal to use this model
    # (We'll need to deploy twice - once for each model)
    print(f"\n⚠️  NOTE: Deploy Modal with model={model_name} before running this test")
    print(f"     Edit deploy/station10_modal.py line 666")
    print(f"     Current: grok_model = \"grok-4-0709\"")
    print(f"     Change to: grok_model = \"{model_name}\"")
    print(f"     Then: poetry run modal deploy deploy/station10_modal.py")
    print()
    
    input(f"Press Enter when Modal is deployed with {model_name}...")
    
    # Call Modal
    print(f"Processing with Modal ({model_name})...")
    
    try:
        Station10Transcriber = modal.Cls.from_name("station10-transcription", "Station10Transcriber")
        result_dict = Station10Transcriber().transcribe_from_gcs.remote(
            gcs_input=gcs_url,
            gcs_output=f"gs://clipscribe-validation/validation/model_comparison/{model_name}/"
        )
        
        # Download transcript
        gcs_output = result_dict.get('gcs_output', '')
        transcript_blob = bucket.blob(f"validation/model_comparison/{model_name}//transcript.json")
        
        if transcript_blob.exists():
            transcript_json = json.loads(transcript_blob.download_as_text())
            result_dict.update(transcript_json)
        
        processing_time = time.time() - start_time
        
        # Analyze results
        entities = result_dict.get('entities', [])
        relationships = result_dict.get('relationships', [])
        topics = result_dict.get('topics', [])
        key_moments = result_dict.get('key_moments', [])
        sentiment = result_dict.get('sentiment', {})
        
        print(f"\n📊 RESULTS FOR {model_name}:")
        print(f"  Processing time: {processing_time:.1f}s")
        print(f"  Cost: ${result_dict.get('cost', 0):.4f}")
        print(f"  Entities: {len(entities)}")
        print(f"  Relationships: {len(relationships)}")
        print(f"  Topics: {len(topics)}")
        print(f"  Key moments: {len(key_moments)}")
        print(f"  Sentiment: {sentiment.get('overall', 'N/A') if sentiment else 'N/A'}")
        
        # Sample outputs
        if topics:
            print(f"\n  Sample topics:")
            for topic in topics[:3]:
                print(f"    - {topic.get('name', topic) if isinstance(topic, dict) else topic}")
        
        if key_moments:
            print(f"\n  Sample key moments:")
            for moment in key_moments[:2]:
                timestamp = moment.get('timestamp', 'N/A')
                desc = moment.get('description', 'N/A')[:60]
                print(f"    - [{timestamp}] {desc}")
        
        return {
            "model": model_name,
            "processing_time": processing_time,
            "cost": result_dict.get('cost', 0),
            "entities": len(entities),
            "relationships": len(relationships),
            "topics": len(topics),
            "key_moments": len(key_moments),
            "sentiment": sentiment.get('overall', 'N/A') if sentiment else 'N/A',
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "model": model_name,
            "success": False,
            "error": str(e)
        }

async def main():
    """Run side-by-side comparison."""
    
    audio_path = project_root / TEST_VIDEO['local_path']
    
    if not audio_path.exists():
        print(f"❌ File not found: {audio_path}")
        return
    
    print("=" * 80)
    print("GROK-4 SIDE-BY-SIDE COMPARISON")
    print("=" * 80)
    print(f"\nTest video: {TEST_VIDEO['name']} ({TEST_VIDEO['duration_min']}min)")
    print(f"Models: grok-4-0709 vs grok-4-fast-reasoning")
    print()
    
    # Test both models
    models_to_compare = ["grok-4-0709", "grok-4-fast-reasoning"]
    
    results = []
    for model in models_to_compare:
        result = await test_model(model, audio_path)
        results.append(result)
    
    # Comparison
    print("\n" + "=" * 80)
    print("SIDE-BY-SIDE COMPARISON")
    print("=" * 80)
    
    print(f"\n{'Metric':<20} {'grok-4-0709':<20} {'grok-4-fast-reasoning':<20}")
    print("-" * 80)
    
    metrics = ['entities', 'relationships', 'topics', 'key_moments', 'processing_time', 'cost']
    
    for metric in metrics:
        val1 = results[0].get(metric, 'N/A')
        val2 = results[1].get(metric, 'N/A')
        print(f"{metric:<20} {str(val1):<20} {str(val2):<20}")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if results[0].get('success') and results[1].get('success'):
        if results[1]['topics'] >= results[0]['topics'] and results[1]['key_moments'] >= results[0]['key_moments']:
            print("\n✅ USE grok-4-fast-reasoning")
            print("   - Equal or better quality")
            print("   - Optimized for reasoning tasks (entity/topic extraction)")
        else:
            print("\n✅ USE grok-4-0709")
            print("   - Better quality")
            print("   - Proven in local ClipScribe")
    
    # Save comparison
    with open("grok4_comparison_results.json", 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "test_video": TEST_VIDEO['name'],
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Comparison saved: grok4_comparison_results.json")

if __name__ == "__main__":
    asyncio.run(main())

