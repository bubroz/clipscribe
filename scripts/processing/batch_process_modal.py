#!/usr/bin/env python3
"""
Batch process all 48 validation videos on Modal GPUs in parallel.

Uploads to GCS, processes in parallel, downloads results.
"""

import asyncio
import json
import sys
from pathlib import Path
from google.cloud import storage
import modal

# Load video inventory
with open('output/video_inventory.json', 'r') as f:
    inventory = json.load(f)

# GCS configuration
GCS_BUCKET = "clipscribe-validation"
GCS_INPUT_PREFIX = "batch_validation_nov2025/inputs/"
GCS_OUTPUT_PREFIX = "batch_validation_nov2025/outputs/"

print(f"{'='*80}")
print(f"BATCH PROCESSING 48 VIDEOS ON MODAL")
print(f"{'='*80}\n")
print(f"Total videos: {inventory['total_videos']}")
print(f"GCS bucket: {GCS_BUCKET}")
print(f"Processing: Parallel on multiple Modal GPU containers")
print(f"Expected time: 30-60 minutes")
print(f"\n{'='*80}\n")

# Upload all files to GCS
print("PHASE 1: Uploading videos to GCS...")
print("-" * 80)

client = storage.Client()
bucket = client.bucket(GCS_BUCKET)

uploaded_paths = []

for category, files in inventory['files'].items():
    print(f"\n{category}:")
    
    for video_file in files:
        video_path = Path(video_file)
        
        if not video_path.exists():
            print(f"  ⚠️  Skipping {video_path.name} - not found")
            continue
        
        # Upload to GCS
        gcs_path = f"{GCS_INPUT_PREFIX}{category}/{video_path.name}"
        blob = bucket.blob(gcs_path)
        
        if blob.exists():
            print(f"  ✓ {video_path.name} (already uploaded)")
        else:
            print(f"  ⬆️  Uploading {video_path.name} ({video_path.stat().st_size / (1024*1024):.0f}MB)...")
            blob.upload_from_filename(str(video_path))
            print(f"    ✅ Uploaded")
        
        uploaded_paths.append(f"gs://{GCS_BUCKET}/{gcs_path}")

print(f"\n✅ Phase 1 Complete: {len(uploaded_paths)} files uploaded to GCS")

# Process in parallel on Modal
print(f"\n{'='*80}")
print(f"PHASE 2: Processing on Modal GPUs (PARALLEL)")
print(f"{'='*80}\n")

ClipScribeTranscriber = modal.Cls.from_name("clipscribe-transcription", "ClipScribeTranscriber")

print(f"Processing {len(uploaded_paths)} videos in parallel...")
print(f"Each video processes independently on its own GPU container")
print(f"Progress will be logged to Modal dashboard\n")

# Create output paths
gcs_outputs = [
    f"gs://{GCS_BUCKET}/{GCS_OUTPUT_PREFIX}{Path(p).stem}/"
    for p in uploaded_paths
]

# Call batch processing
print(f"Calling Modal batch_transcribe_from_gcs...")
print(f"Monitor at: https://modal.com/apps/zforristall/main/deployed/clipscribe-transcription\n")

try:
    # Use Modal's .map() to process in parallel
    transcribe_fn = ClipScribeTranscriber().transcribe_from_gcs
    
    results = []
    for gcs_input, gcs_output in zip(uploaded_paths, gcs_outputs):
        print(f"  Queuing: {Path(gcs_input).name}")
        result = transcribe_fn.remote(gcs_input, gcs_output)
        results.append(result)
    
    print(f"\n✅ {len(results)} jobs queued on Modal!")
    print(f"\nResults will be saved to:")
    print(f"  gs://{GCS_BUCKET}/{GCS_OUTPUT_PREFIX}")
    
    print(f"\nTo monitor progress:")
    print(f"  1. Modal Dashboard: https://modal.com/apps/zforristall")
    print(f"  2. GCS Console: https://console.cloud.google.com/storage/browser/{GCS_BUCKET}/{GCS_OUTPUT_PREFIX}")
    print(f"  3. Command: poetry run modal app logs clipscribe-transcription")
    
    # Wait for all to complete
    print(f"\nWaiting for all jobs to complete...")
    print(f"This will take 30-60 minutes depending on video lengths")
    print(f"Longest videos process in parallel, so total time = longest video time\n")
    
    completed = 0
    failed = 0
    
    for i, result in enumerate(results, 1):
        try:
            # Result is already the return value (Modal handles waiting)
            if result.get('status') == 'success' or 'entities' in result:
                completed += 1
                entities = len(result.get('entities', []))
                cost = result.get('cost', 0)
                print(f"  [{i}/{len(results)}] ✅ {Path(uploaded_paths[i-1]).stem[:50]} - {entities} entities, ${cost:.4f}")
            else:
                failed += 1
                print(f"  [{i}/{len(results)}] ❌ Failed: {result.get('error', 'Unknown')}")
        except Exception as e:
            failed += 1
            print(f"  [{i}/{len(results)}] ❌ Error: {e}")
    
    print(f"\n{'='*80}")
    print(f"BATCH PROCESSING COMPLETE!")
    print(f"{'='*80}")
    print(f"  Completed: {completed}/{len(results)}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {completed/len(results)*100:.1f}%")
    print(f"\nResults saved to: gs://{GCS_BUCKET}/{GCS_OUTPUT_PREFIX}")
    
    # Save summary
    summary = {
        'total_videos': len(results),
        'completed': completed,
        'failed': failed,
        'gcs_output_prefix': f"gs://{GCS_BUCKET}/{GCS_OUTPUT_PREFIX}",
        'results': results
    }
    
    with open('output/batch_processing_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Summary saved to: output/batch_processing_summary.json")
    
except Exception as e:
    print(f"\n❌ Batch processing failed: {e}")
    import traceback
    traceback.print_exc()

