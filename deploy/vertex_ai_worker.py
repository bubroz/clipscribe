#!/usr/bin/env python3
"""
Vertex AI GPU Worker for Station10.media

Same as Cloud Run worker, but for Vertex AI Custom Jobs.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from google.cloud import storage
import tempfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app paths
sys.path.insert(0, '/app')

from transcribers.whisperx_transcriber import WhisperXTranscriber


async def process_video_vertex_ai():
    """
    Process video on Vertex AI GPU.
    
    Environment variables:
    - INPUT_VIDEO_GCS_PATH: gs://bucket/path/to/video.mp3
    - OUTPUT_GCS_PATH: gs://bucket/path/to/output/
    - GCP_PROJECT: GCP project ID
    - GCS_BUCKET: GCS bucket name
    """
    
    project_id = os.getenv('GCP_PROJECT')
    bucket_name = os.getenv('GCS_BUCKET')
    input_path = os.getenv('INPUT_VIDEO_GCS_PATH')
    output_path = os.getenv('OUTPUT_GCS_PATH')
    
    if not all([project_id, bucket_name, input_path, output_path]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    logger.info(f"Starting Vertex AI GPU worker")
    logger.info(f"Project: {project_id}")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Initialize GCS
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    
    # Initialize WhisperX with GPU
    logger.info("Initializing WhisperX with GPU...")
    transcriber = WhisperXTranscriber(
        model_name="large-v3",
        device="cuda",  # Use GPU
        enable_diarization=True
    )
    logger.info("✓ WhisperX initialized on GPU")
    
    start_time = time.time()
    
    # Parse GCS paths
    input_blob_name = input_path.replace(f'gs://{bucket_name}/', '')
    output_prefix = output_path.replace(f'gs://{bucket_name}/', '')
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Download from GCS
        logger.info(f"Downloading from GCS: {input_blob_name}")
        download_start = time.time()
        
        local_file = temp_path / "input.mp3"
        blob = bucket.blob(input_blob_name)
        blob.download_to_filename(str(local_file))
        
        download_time = time.time() - download_start
        logger.info(f"✓ Downloaded in {download_time:.1f}s")
        
        # Process with WhisperX
        logger.info("Processing with WhisperX on GPU...")
        process_start = time.time()
        
        result = await transcriber.transcribe_audio(str(local_file))
        
        process_time = time.time() - process_start
        logger.info(f"✓ Processed in {process_time:.1f}s ({process_time/60:.1f} minutes)")
        
        # Upload results to GCS
        logger.info(f"Uploading results to GCS: {output_prefix}")
        upload_start = time.time()
        
        # Transcript
        transcript_blob = bucket.blob(f"{output_prefix}/transcript.txt")
        transcript_blob.upload_from_string(result.text)
        
        # Full results JSON
        results_blob = bucket.blob(f"{output_prefix}/results.json")
        results_data = {
            "transcript": result.text,
            "duration": result.duration,
            "language": result.language,
            "confidence": result.confidence,
            "speakers": result.speaker_segments,
            "word_timestamps": result.word_level_timestamps[:100],
            "processing_time": process_time,
            "model": result.model
        }
        results_blob.upload_from_string(json.dumps(results_data, indent=2))
        
        upload_time = time.time() - upload_start
        logger.info(f"✓ Uploaded in {upload_time:.1f}s")
    
    # Calculate metrics
    total_time = time.time() - start_time
    
    # L4 GPU on Vertex AI: ~$0.60/hour = $0.01/minute
    gpu_minutes = process_time / 60
    gpu_cost = gpu_minutes * 0.01
    
    metrics = {
        "success": True,
        "duration_seconds": result.duration,
        "duration_minutes": result.duration / 60,
        "download_time": download_time,
        "processing_time": process_time,
        "processing_minutes": process_time / 60,
        "upload_time": upload_time,
        "total_time": total_time,
        "speakers_found": len(result.speaker_segments),
        "words_transcribed": len(result.word_level_timestamps),
        "confidence": result.confidence,
        "gpu_cost": gpu_cost,
        "realtime_factor": result.duration / process_time if process_time > 0 else 0
    }
    
    logger.info("="*80)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*80)
    logger.info(f"Video duration: {metrics['duration_minutes']:.1f} minutes")
    logger.info(f"Processing time: {metrics['processing_minutes']:.1f} minutes")
    logger.info(f"Realtime factor: {metrics['realtime_factor']:.1f}x")
    logger.info(f"Speakers found: {metrics['speakers_found']}")
    logger.info(f"GPU cost: ${metrics['gpu_cost']:.4f}")
    logger.info(f"Results: {output_path}")
    logger.info("="*80)
    
    # Write metrics to stdout for Vertex AI logging
    print(json.dumps({"status": "success", **metrics}))
    
    return metrics


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(process_video_vertex_ai())
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)

