#!/usr/bin/env python3
"""
Cloud Run GPU Worker for Station10.media

Processes videos with WhisperX on NVIDIA T4 GPU.
Downloads from GCS, processes, uploads results.
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


class CloudRunGPUWorker:
    """
    Premium tier worker - WhisperX on GPU.
    """
    
    def __init__(self):
        """Initialize worker with GCS client."""
        self.project_id = os.getenv('GCP_PROJECT', 'prismatic-iris-429006-g6')
        self.bucket_name = os.getenv('GCS_BUCKET', 'prismatic-iris-429006-g6-clipscribe')
        
        # Initialize GCS
        self.storage_client = storage.Client(project=self.project_id)
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
        # Initialize WhisperX with GPU
        logger.info("Initializing WhisperX with GPU...")
        self.transcriber = WhisperXTranscriber(
            model_name="large-v3",
            device="cuda",  # Force GPU
            enable_diarization=True
        )
        
        logger.info("GPU Worker initialized")
    
    async def process_video(
        self, 
        gcs_input_path: str,
        gcs_output_path: str
    ) -> dict:
        """
        Process video from GCS.
        
        Args:
            gcs_input_path: GCS path to video (gs://bucket/path/to/video.mp3)
            gcs_output_path: GCS path for results (gs://bucket/path/to/output/)
            
        Returns:
            Processing metrics (time, cost, speakers found, etc.)
        """
        
        start_time = time.time()
        
        # Parse GCS paths
        input_blob_name = gcs_input_path.replace(f'gs://{self.bucket_name}/', '')
        output_prefix = gcs_output_path.replace(f'gs://{self.bucket_name}/', '')
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download from GCS
            logger.info(f"Downloading from GCS: {input_blob_name}")
            download_start = time.time()
            
            local_file = temp_path / "input.mp3"
            blob = self.bucket.blob(input_blob_name)
            blob.download_to_filename(str(local_file))
            
            download_time = time.time() - download_start
            logger.info(f"Downloaded in {download_time:.1f}s")
            
            # Process with WhisperX
            logger.info("Processing with WhisperX on GPU...")
            process_start = time.time()
            
            result = await self.transcriber.transcribe_audio(str(local_file))
            
            process_time = time.time() - process_start
            logger.info(f"Processed in {process_time:.1f}s")
            
            # Upload results to GCS
            logger.info(f"Uploading results to GCS: {output_prefix}")
            upload_start = time.time()
            
            # Transcript
            transcript_blob = self.bucket.blob(f"{output_prefix}/transcript.txt")
            transcript_blob.upload_from_string(result.text)
            
            # Full results JSON
            results_blob = self.bucket.blob(f"{output_prefix}/results.json")
            results_blob.upload_from_string(json.dumps({
                "transcript": result.text,
                "duration": result.duration,
                "language": result.language,
                "confidence": result.confidence,
                "speakers": result.speaker_segments,
                "word_timestamps": result.word_level_timestamps[:100],  # First 100 words
                "processing_time": process_time,
                "model": result.model
            }, indent=2))
            
            upload_time = time.time() - upload_start
            logger.info(f"Uploaded in {upload_time:.1f}s")
        
        # Calculate metrics
        total_time = time.time() - start_time
        
        # GPU cost calculation
        # T4 GPU on Cloud Run: ~$0.35/hour = $0.00583/minute
        gpu_minutes = process_time / 60
        gpu_cost = gpu_minutes * 0.00583
        
        metrics = {
            "success": True,
            "duration_seconds": result.duration,
            "download_time": download_time,
            "processing_time": process_time,
            "upload_time": upload_time,
            "total_time": total_time,
            "speakers_found": len(result.speaker_segments),
            "words_transcribed": len(result.word_level_timestamps),
            "confidence": result.confidence,
            "gpu_cost": gpu_cost,
            "realtime_factor": result.duration / process_time if process_time > 0 else 0
        }
        
        logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
        
        return metrics


async def main():
    """Main entry point for Cloud Run."""
    
    # Get job parameters from environment
    input_path = os.getenv('INPUT_VIDEO_GCS_PATH')
    output_path = os.getenv('OUTPUT_GCS_PATH')
    
    if not input_path or not output_path:
        logger.error("Missing required env vars: INPUT_VIDEO_GCS_PATH, OUTPUT_GCS_PATH")
        sys.exit(1)
    
    # Process video
    worker = CloudRunGPUWorker()
    
    try:
        metrics = await worker.process_video(input_path, output_path)
        
        logger.info("="*80)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*80)
        logger.info(f"Video duration: {metrics['duration_seconds']/60:.1f} minutes")
        logger.info(f"Processing time: {metrics['processing_time']/60:.1f} minutes")
        logger.info(f"Realtime factor: {metrics['realtime_factor']:.1f}x")
        logger.info(f"Speakers found: {metrics['speakers_found']}")
        logger.info(f"GPU cost: ${metrics['gpu_cost']:.4f}")
        logger.info(f"Results: {output_path}")
        
        # Write metrics to stdout for Cloud Run logging
        print(json.dumps({"status": "success", **metrics}))
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

