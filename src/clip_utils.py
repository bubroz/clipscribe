import os
from typing import Dict, List, Optional, Tuple, Any
from moviepy.editor import VideoFileClip
from config import setup_logger, GEMINI_MAX_TOKENS

# Initialize logger using centralized configuration
logger = setup_logger("clip_utils")

def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS string."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def parse_timestamp(timestamp: str) -> float:
    """Convert MM:SS string to seconds."""
    try:
        minutes, seconds = map(int, timestamp.split(":"))
        return minutes * 60 + seconds
    except ValueError:
        logger.error(f"Invalid timestamp format: {timestamp}")
        raise ValueError("Invalid timestamp format. Use MM:SS")

def find_word_boundaries(text: str, segments: List[Dict]) -> Tuple[float, float]:
    """Find exact start and end times for a text segment."""
    text = text.lower().strip()
    words = text.split()
    
    # Check token length for Gemini context window
    if len(text.split()) > GEMINI_MAX_TOKENS:
        logger.warning(f"Text length ({len(text.split())} tokens) exceeds Gemini's context window")
    
    start_time = None
    end_time = None
    
    # First try exact word-level matching
    for segment in segments:
        if 'words' in segment:
            for word_info in segment['words']:
                word = word_info['word'].lower()
                
                # Use v2 timing fields
                if word == words[0] and start_time is None:
                    start_time = float(word_info.get('startOffset', '0s').rstrip('s'))
                
                if word == words[-1]:
                    end_time = float(word_info.get('endOffset', '0s').rstrip('s'))
                    
    # If word-level matching fails, try segment-level
    if start_time is None or end_time is None:
        for segment in segments:
            segment_text = segment['text'].lower()
            if text in segment_text:
                start_time = float(segment.get('startOffset', '0s').rstrip('s'))
                end_time = float(segment.get('endOffset', '0s').rstrip('s'))
                break
    
    if start_time is None or end_time is None:
        logger.error(f"Could not find timing for text: {text}")
        return None, None
        
    logger.debug(f"Finding boundaries for text: {text}")
    logger.debug(f"Number of segments to search: {len(segments)}")
    
    # After finding times
    logger.debug(f"Found times: start={start_time}, end={end_time}")
    if start_time is None or end_time is None:
        logger.debug("Failed to find exact match, trying segment-level")
        
    return start_time, end_time

def get_processed_files(output_folder: str, video_dir: str) -> Dict[str, str]:
    """Get all processed files for a video."""
    files = os.listdir(os.path.join(output_folder, video_dir))
    return {
        'video': next(
            (f for f in files if f.endswith('.mp4')),
            None
        ),
        'processed': next(
            (f for f in files if f == 'processed.json'),
            None
        )
    }

def extract_segment_timing(segment: Dict[str, Any]) -> Tuple[float, float]:
    """Extract timing from a transcript segment using v2 fields."""
    try:
        start_time = float(segment.get('startOffset', '0s').rstrip('s'))
        end_time = float(segment.get('endOffset', '0s').rstrip('s'))
        return start_time, end_time
    except (ValueError, KeyError) as e:
        logger.error(f"Error extracting segment timing: {str(e)}")
        return 0.0, 0.0