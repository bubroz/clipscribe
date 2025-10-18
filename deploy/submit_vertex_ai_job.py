#!/usr/bin/env python3
"""
Submit WhisperX job to Vertex AI with GPU.

Usage:
    python deploy/submit_vertex_ai_job.py \
        --video gs://bucket/video.mp3 \
        --output gs://bucket/results/
"""

import argparse
import time
import logging
from google.cloud import aiplatform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def submit_gpu_job(
    project_id: str,
    location: str,
    video_gcs_path: str,
    output_gcs_path: str,
    gpu_type: str = "NVIDIA_L4",
    wait: bool = True,
    timeout_minutes: int = 30
):
    """
    Submit WhisperX processing job to Vertex AI with GPU.
    
    Args:
        project_id: GCP project ID
        location: Region (us-central1)
        video_gcs_path: Input video GCS path
        output_gcs_path: Output GCS path
        gpu_type: GPU type (NVIDIA_L4, NVIDIA_A100_80GB)
        wait: Wait for completion
        timeout_minutes: Maximum job runtime in minutes (default: 30)
    """
    
    # Initialize Vertex AI with staging bucket
    staging_bucket = f"gs://{project_id}-clipscribe"
    aiplatform.init(
        project=project_id, 
        location=location,
        staging_bucket=staging_bucket
    )
    
    logger.info(f"Vertex AI initialized with staging bucket: {staging_bucket}")
    
    # Create custom job with timeout protection
    timeout_seconds = timeout_minutes * 60
    job = aiplatform.CustomJob(
        display_name=f"station10-whisperx-{int(time.time())}",
        worker_pool_specs=[
            {
                "machine_spec": {
                    "machine_type": "g2-standard-4",  # L4 requires G2 machine type
                    "accelerator_type": gpu_type,
                    "accelerator_count": 1,
                },
                "replica_count": 1,
                "container_spec": {
                    "image_uri": f"gcr.io/{project_id}/station10-gpu-worker:latest",
                    "env": [
                        {"name": "INPUT_VIDEO_GCS_PATH", "value": video_gcs_path},
                        {"name": "OUTPUT_GCS_PATH", "value": output_gcs_path},
                        {"name": "GCP_PROJECT", "value": project_id},
                        {"name": "GCS_BUCKET", "value": project_id + "-clipscribe"},
                    ],
                },
            }
        ],
        # Automatic job termination after timeout
        timeout=f"{timeout_seconds}s",
    )
    
    print(f"Submitting job to Vertex AI...")
    print(f"  Project: {project_id}")
    print(f"  Region: {location}")
    print(f"  GPU: {gpu_type}")
    print(f"  Timeout: {timeout_minutes} minutes (auto-terminate)")
    print(f"  Input: {video_gcs_path}")
    print(f"  Output: {output_gcs_path}")
    print()
    
    # Submit job
    job.run(sync=wait)
    
    if wait:
        print()
        print("="*80)
        print("JOB COMPLETE")
        print("="*80)
        print(f"Job name: {job.resource_name}")
        print(f"State: {job.state}")
        print()
        print(f"Check results at: {output_gcs_path}")
    else:
        print(f"Job submitted: {job.resource_name}")
        print(f"Monitor at: https://console.cloud.google.com/vertex-ai/training/custom-jobs")
    
    return job


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit Vertex AI GPU job")
    parser.add_argument("--video", required=True, help="GCS path to video")
    parser.add_argument("--output", required=True, help="GCS path for output")
    parser.add_argument("--project", default="prismatic-iris-429006-g6")
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--gpu", default="NVIDIA_TESLA_T4", choices=["NVIDIA_L4", "NVIDIA_TESLA_T4", "NVIDIA_TESLA_A100"])
    parser.add_argument("--timeout", type=int, default=30, help="Job timeout in minutes (default: 30)")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for completion")
    
    args = parser.parse_args()
    
    submit_gpu_job(
        project_id=args.project,
        location=args.region,
        video_gcs_path=args.video,
        output_gcs_path=args.output,
        gpu_type=args.gpu,
        wait=not args.no_wait,
        timeout_minutes=args.timeout
    )

