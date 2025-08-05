"""
video_splitter.py

A utility for splitting large video files into smaller, manageable chunks
using FFmpeg. This is essential for processing long-form content (e.g., >15 minutes)
without hitting API timeouts.
"""

import subprocess
import os
from pathlib import Path
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def get_video_duration(file_path: str) -> Optional[float]:
    """Gets the duration of a video file in seconds using ffprobe."""
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to get duration for {file_path}: {e}")
        return None

def split_video(
    file_path: str,
    chunk_duration: int = 600,  # 10 minutes
    overlap: int = 30,  # 30 seconds
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Splits a video file into smaller chunks with a specified overlap.

    Args:
        file_path: The path to the video file to split.
        chunk_duration: The duration of each chunk in seconds.
        overlap: The duration of the overlap between chunks in seconds.
        output_dir: The directory to save the chunks in. Defaults to a subfolder
                    in the same directory as the source file.

    Returns:
        A list of file paths to the generated chunks.
    """
    source_path = Path(file_path)
    if not source_path.exists():
        logger.error(f"Video file not found: {file_path}")
        return []

    duration = get_video_duration(file_path)
    if duration is None or duration <= chunk_duration:
        logger.info(f"Video is shorter than chunk duration, no splitting needed for {file_path}.")
        return [file_path]

    if output_dir:
        chunk_output_dir = Path(output_dir)
    else:
        chunk_output_dir = source_path.parent / f"{source_path.stem}_chunks"
    
    chunk_output_dir.mkdir(parents=True, exist_ok=True)
    
    chunk_files = []
    start_time = 0
    chunk_index = 0
    
    while start_time < duration:
        output_path = chunk_output_dir / f"{source_path.stem}_part_{chunk_index:03d}{source_path.suffix}"
        
        command = [
            "ffmpeg",
            "-i", str(source_path),
            "-ss", str(start_time),
            "-t", str(chunk_duration),
            "-c", "copy", # Use copy to avoid re-encoding, much faster
            "-y", # Overwrite output files
            str(output_path)
        ]

        try:
            logger.info(f"Creating chunk {chunk_index}: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True, text=True)
            chunk_files.append(str(output_path))
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to create chunk {chunk_index} for {file_path}: {e}")
            if isinstance(e, subprocess.CalledProcessError):
                logger.error(f"FFmpeg stderr: {e.stderr}")
            # Stop if one chunk fails
            return []
            
        start_time += chunk_duration - overlap
        chunk_index += 1

    logger.info(f"Successfully split video into {len(chunk_files)} chunks in {chunk_output_dir}")
    return chunk_files
