"""Utility functions for filename handling."""

import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: The filename to sanitize
        max_length: Maximum length of the filename (default: 200)
    
    Returns:
        A sanitized filename safe for all operating systems
    """
    # Remove or replace invalid characters
    # Keep alphanumeric, spaces, hyphens, underscores, and dots
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Replace multiple spaces/underscores with single ones
    filename = re.sub(r'[\s_]+', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' ._')
    
    # Ensure filename isn't empty
    if not filename:
        filename = "untitled"
    
    # Truncate if too long (leave room for extension)
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip(' ._')
    
    return filename


def create_output_filename(title: str, extension: str = "txt", 
                         output_dir: str = None) -> Path:
    """
    Create a full output path from a video title.
    
    Args:
        title: The video title
        extension: File extension (without dot)
        output_dir: Output directory (None for current directory)
    
    Returns:
        Path object for the output file
    """
    # Sanitize the title
    safe_filename = sanitize_filename(title)
    
    # Add extension
    filename = f"{safe_filename}.{extension}"
    
    # Create full path
    if output_dir:
        output_path = Path(output_dir) / filename
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(filename)
    
    # Handle duplicates by adding number
    if output_path.exists():
        base = output_path.stem
        ext = output_path.suffix
        counter = 1
        while output_path.exists():
            output_path = output_path.parent / f"{base}_{counter}{ext}"
            counter += 1
    
    return output_path


def create_structured_filename(
    metadata: Dict[str, Any],
    format_type: str = "transcript",
    extension: str = "txt"
) -> str:
    """
    Create a structured, machine-readable filename with metadata.
    
    Format: {date}_{platform}_{video_id}_{format}.{ext}
    Example: 20250623_youtube_dQw4w9WgXcQ_transcript.txt
    
    Args:
        metadata: Video metadata dict with title, url, platform, etc.
        format_type: Type of content (transcript, metadata, entities, etc.)
        extension: File extension
        
    Returns:
        Structured filename string
    """
    # Extract components
    date = datetime.now().strftime("%Y%m%d")
    
    # Get platform from URL
    url = metadata.get("url", "")
    platform = extract_platform_from_url(url)
    
    # Get video ID
    video_id = extract_video_id_from_url(url) or generate_short_id(metadata.get("title", ""))
    
    # Clean components for filename
    platform = sanitize_component(platform, 20)
    video_id = sanitize_component(video_id, 20)
    format_type = sanitize_component(format_type, 20)
    
    # Build filename
    filename = f"{date}_{platform}_{video_id}_{format_type}.{extension}"
    
    return filename


def extract_platform_from_url(url: str) -> str:
    """Extract platform name from URL."""
    if not url:
        return "unknown"
    
    # Common platforms
    patterns = {
        r"youtube\.com|youtu\.be": "youtube",
        r"vimeo\.com": "vimeo",
        r"tiktok\.com": "tiktok",
        r"twitter\.com|x\.com": "twitter",
        r"facebook\.com|fb\.com": "facebook",
        r"instagram\.com": "instagram",
        r"ted\.com": "ted",
        r"dailymotion\.com": "dailymotion",
        r"twitch\.tv": "twitch",
        r"soundcloud\.com": "soundcloud",
        r"reddit\.com": "reddit",
        r"bbc\.com|bbc\.co\.uk": "bbc",
    }
    
    for pattern, platform in patterns.items():
        if re.search(pattern, url, re.I):
            return platform
    
    # Try to extract domain name
    try:
        import urllib.parse
        domain = urllib.parse.urlparse(url).netloc
        domain = domain.replace("www.", "").split(".")[0]
        return domain[:20]  # Limit length
    except:
        return "unknown"


def extract_video_id_from_url(url: str) -> Optional[str]:
    """Extract video ID from common platforms."""
    if not url:
        return None
    
    # YouTube
    youtube_patterns = [
        r"(?:v=|/)([0-9A-Za-z_-]{11})(?:\?|&|$)",
        r"youtu\.be/([0-9A-Za-z_-]{11})"
    ]
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Vimeo
    vimeo_match = re.search(r"vimeo\.com/(\d+)", url)
    if vimeo_match:
        return vimeo_match.group(1)
    
    # TikTok
    tiktok_match = re.search(r"tiktok\.com/@[\w.-]+/video/(\d+)", url)
    if tiktok_match:
        return tiktok_match.group(1)
    
    # Twitter/X
    twitter_match = re.search(r"status/(\d+)", url)
    if twitter_match:
        return twitter_match.group(1)
    
    return None


def generate_short_id(text: str, length: int = 8) -> str:
    """Generate a short ID from text using hash."""
    if not text:
        text = str(datetime.now().timestamp())
    
    hash_obj = hashlib.md5(text.encode())
    return hash_obj.hexdigest()[:length]


def sanitize_component(text: str, max_length: int = 20) -> str:
    """Sanitize a component for use in structured filename."""
    if not text:
        return "unknown"
    
    # Keep only alphanumeric and basic punctuation
    text = re.sub(r'[^a-zA-Z0-9_-]', '', text)
    
    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.lower()


def create_output_structure(
    metadata: Dict[str, Any],
    base_dir: str = None
) -> Dict[str, Path]:
    """
    Create a complete output directory structure for a video.
    
    Creates:
    - {base_dir}/{date}_{platform}_{video_id}/
        - transcript.txt
        - transcript.json
        - transcript.srt
        - transcript.vtt
        - metadata.json
        - entities.json
        - manifest.json
    
    Returns:
        Dictionary mapping file types to their paths
    """
    # Create directory name
    date = datetime.now().strftime("%Y%m%d")
    platform = extract_platform_from_url(metadata.get("url", ""))
    video_id = extract_video_id_from_url(metadata.get("url", "")) or generate_short_id(metadata.get("title", ""))
    
    dir_name = f"{date}_{platform}_{video_id}"
    
    # Create base directory
    if base_dir:
        output_dir = Path(base_dir) / dir_name
    else:
        output_dir = Path(dir_name)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define file paths
    paths = {
        "transcript_txt": output_dir / "transcript.txt",
        "transcript_json": output_dir / "transcript.json",
        "transcript_srt": output_dir / "transcript.srt",
        "transcript_vtt": output_dir / "transcript.vtt",
        "metadata": output_dir / "metadata.json",
        "entities": output_dir / "entities.json",
        "manifest": output_dir / "manifest.json",
        "directory": output_dir
    }
    
    return paths 