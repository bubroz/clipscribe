#!/usr/bin/env python3
"""
Process ONLY the remaining videos that haven't been completed yet.

Checks GCS outputs, skips completed videos, processes remaining with fixed Modal code.
"""

import modal
import json
from pathlib import Path
from google.cloud import storage

# Load inventory
with open('output/video_inventory.json', 'r') as f:
    inventory = json.load(f)

GCS_BUCKET = "clipscribe-validation"
GCS_OUTPUT_PREFIX = "batch_validation_nov2025/outputs/"

print("Checking what's already completed...")

# Get list of completed videos from GCS
client = storage.Client()
bucket = client.bucket(GCS_BUCKET)

completed_videos = set()
blobs = bucket.list_blobs(prefix=GCS_OUTPUT_PREFIX)
for blob in blobs:
    # Extract video name from path
    parts = blob.name.split('/')
    if len(parts) > 2:
        video_name = parts[2]  # outputs/video_name/file
        completed_videos.add(video_name)

print(f"✅ Completed: {len(completed_videos)} videos")
print(f"⏳ Remaining: {inventory['total_videos'] - len(completed_videos)} videos")

# Find remaining videos
remaining = []
all_files = []
for category, files in inventory['files'].items():
    all_files.extend(files)

for video_file in all_files:
    video_path = Path(video_file)
    if not video_path.exists():
        continue
    
    video_name = video_path.stem
    
    # Check if already completed
    if video_name in completed_videos:
        continue
    
    remaining.append(video_path)

print(f"\nRemaining videos to process: {len(remaining)}")

if len(remaining) == 0:
    print("\n✅ ALL VIDEOS ALREADY PROCESSED!")
    exit(0)

print(f"\nProcessing {len(remaining)} remaining videos with FIXED Modal code...")
print(f"Fixes applied:")
print(f"  ✅ Multi-sample language detection")
print(f"  ✅ Language validation (corrects Tamil/Ukrainian→English)")
print(f"  ✅ Cascading OOM retry (batch_size 16→8→4→2→1)")
print(f"  ✅ GPU memory clearing")
print(f"\nStarting...\n")

ClipScribeTranscriber = modal.Cls.from_name("clipscribe-transcription", "ClipScribeTranscriber")

completed_count = 0
failed_count = 0

for i, video_path in enumerate(remaining, 1):
    gcs_input = f"gs://{GCS_BUCKET}/batch_validation_nov2025/inputs/story1_ai_companies/{video_path.name}"
    gcs_output = f"gs://{GCS_BUCKET}/{GCS_OUTPUT_PREFIX}{video_path.stem}/"
    
    print(f"[{i}/{len(remaining)}] {video_path.stem[:60]}...")
    
    try:
        result = ClipScribeTranscriber().transcribe_from_gcs.remote(gcs_input, gcs_output)
        
        entities = len(result.get('entities', []))
        cost = result.get('cost', 0)
        
        print(f"  ✅ SUCCESS: {entities} entities, ${cost:.4f}")
        completed_count += 1
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        failed_count += 1

print(f"\n{'='*80}")
print(f"FINAL RESULTS")
print(f"{'='*80}")
print(f"  Completed: {completed_count}/{len(remaining)}")
print(f"  Failed: {failed_count}")
print(f"  Success rate: {completed_count/len(remaining)*100:.1f}%")
print(f"\nTotal videos processed (including earlier): {len(completed_videos) + completed_count}/48")
print(f"{'='*80}")
EOF

