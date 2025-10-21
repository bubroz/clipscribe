"""
Modal processing helper for validation.

Downloads YouTube videos, uploads to GCS, processes with Modal GPU (WhisperX + Gemini).
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict
import json
import tempfile
from google.cloud import storage


async def process_youtube_with_modal(video_url: str, gcs_bucket: str = "clipscribe-validation") -> Optional[Dict]:
    """
    Process YouTube video with Modal GPU transcription.
    
    Pipeline:
      1. Download audio with yt-dlp
      2. Upload to GCS
      3. Call Modal transcription
      4. Download and parse result
    
    Args:
        video_url: YouTube URL
        gcs_bucket: GCS bucket for temporary storage
        
    Returns:
        Transcription result with segments, or None if failed
    """
    import modal
    
    print(f"    Processing: {video_url}")
    
    # Step 1: Download audio with yt-dlp
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        audio_file = tmpdir_path / "audio.mp3"
        
        print(f"    Downloading audio...")
        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "--no-check-certificate",  # Bypass SSL issues
            "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "-o", str(audio_file),
            video_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ❌ yt-dlp failed: {result.stderr[:200]}")
            return None
        
        if not audio_file.exists():
            print(f"    ❌ Audio file not created")
            return None
        
        print(f"    ✓ Downloaded: {audio_file.stat().st_size / 1024 / 1024:.1f}MB")
        
        # Step 2: Upload to GCS
        print(f"    Uploading to GCS...")
        
        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        
        # Use video ID as filename
        video_id = video_url.split('=')[-1] if '=' in video_url else 'unknown'
        gcs_path = f"validation/temp/{video_id}.mp3"
        
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(str(audio_file))
        
        gcs_url = f"gs://{gcs_bucket}/{gcs_path}"
        print(f"    ✓ Uploaded: {gcs_url}")
        
        # Step 3: Call Modal transcription
        print(f"    Processing with Modal (WhisperX + Gemini)...")
        
        try:
            # Get Modal class instance
            Station10Transcriber = modal.Cls.lookup("station10-transcription", "Station10Transcriber")
            
            # Call Modal method
            with Station10Transcriber() as transcriber:
                result_dict = transcriber.transcribe_from_gcs.remote(
                    gcs_input=gcs_url,
                    gcs_output=f"gs://{gcs_bucket}/validation/results/"
                )
            
            print(f"    ✓ Modal processing complete")
            print(f"      Speakers: {result_dict.get('speakers')}")
            print(f"      Duration: {result_dict.get('duration_minutes', 0):.1f} min")
            print(f"      Cost: ${result_dict.get('cost', 0):.4f}")
            
            # Step 4: Download result from GCS
            result_path = result_dict.get('gcs_output', '')
            if result_path:
                # Download transcript.json
                transcript_blob = bucket.blob(f"{result_path.replace('gs://' + gcs_bucket + '/', '')}transcript.json")
                
                if transcript_blob.exists():
                    transcript_json = json.loads(transcript_blob.download_as_text())
                    
                    # Add processing metadata
                    transcript_json['processing_cost'] = result_dict.get('cost', 0)
                    transcript_json['processing_minutes'] = result_dict.get('processing_minutes', 0)
                    
                    return transcript_json
            
            print(f"    ⚠️  No transcript found in GCS")
            return None
            
        except Exception as e:
            print(f"    ❌ Modal processing failed: {e}")
            import traceback
            traceback.print_exc()
            return None


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    else:
        return 'unknown'

