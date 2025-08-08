#!/usr/bin/env python3
"""CLI Usage Examples - Command-line interface demonstration."""

import os
import subprocess
from pathlib import Path


def run_command(cmd: str, description: str = None):
    """Run a command and display output."""
    if description:
        print(f"\n {description}")
    print(f"\n$ {cmd}")
    print("-" * 60)
    
    # Note: In real usage, these would be actual commands
    # Here we're showing the expected output
    return True


def main():
    """Demonstrate ClipScribe CLI usage."""
    
    print(" ClipScribe CLI Usage Guide")
    print("=" * 60)
    print("\nClipScribe provides a powerful command-line interface")
    print("for video transcription and analysis.")
    
    # 1. Basic Commands
    print("\n\n BASIC COMMANDS")
    print("=" * 60)
    
    run_command(
        "clipscribe --version",
        "Check ClipScribe version"
    )
    print("ClipScribe v2.0.0")
    
    run_command(
        "clipscribe --help",
        "Show all available commands"
    )
    print("""Usage: clipscribe [OPTIONS] COMMAND [ARGS]...

  ClipScribe - AI-powered video transcription for 1800+ platforms

Options:
  --version  Show version
  --help     Show this message

Commands:
  transcribe  Transcribe a video from any supported platform
  platforms   List supported platforms
  config      Show configuration
  cost        Estimate transcription cost""")
    
    # 2. Transcription Examples
    print("\n\n TRANSCRIPTION EXAMPLES")
    print("=" * 60)
    
    run_command(
        'clipscribe transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ"',
        "Basic transcription (YouTube)"
    )
    print("""[15:23:45] Extracting video information...
[15:23:46] Downloading audio...
[15:23:48] Transcribing with Gemini 2.5 Flash...
[15:23:52]  Transcription complete!

Title: Rick Astley - Never Gonna Give You Up
Duration: 3:33 (213 seconds)
Cost: $0.0071
Output: ./Rick_Astley_-_Never_Gonna_Give_You_Up.txt""")
    
    run_command(
        'clipscribe transcribe "https://vimeo.com/123456789" --output-dir ./transcripts',
        "Transcribe from Vimeo with custom output directory"
    )
    
    run_command(
        'clipscribe transcribe "video.mp4" --format srt --format vtt',
        "Generate subtitles from local video file"
    )
    
    # 3. Output Format Options
    print("\n\n OUTPUT FORMAT OPTIONS")
    print("=" * 60)
    
    run_command(
        'clipscribe transcribe URL --format txt',
        "Plain text (default)"
    )
    
    run_command(
        'clipscribe transcribe URL --format srt',
        "SRT subtitles"
    )
    
    run_command(
        'clipscribe transcribe URL --format vtt',
        "WebVTT subtitles"
    )
    
    run_command(
        'clipscribe transcribe URL --format json',
        "JSON with full metadata"
    )
    
    run_command(
        'clipscribe transcribe URL --format txt --format srt --format json',
        "Multiple formats at once"
    )
    
    # 4. Advanced Options
    print("\n\n  ADVANCED OPTIONS")
    print("=" * 60)
    
    run_command(
        'clipscribe transcribe URL --no-save',
        "Display transcript without saving to file"
    )
    
    run_command(
        'clipscribe transcribe URL --quiet',
        "Suppress progress output"
    )
    
    run_command(
        'clipscribe transcribe URL --cookies cookies.txt',
        "Use cookies for authentication (private videos)"
    )
    
    run_command(
        'clipscribe transcribe URL --language es',
        "Specify expected language (improves accuracy)"
    )
    
    # 5. Batch Processing
    print("\n\n BATCH PROCESSING")
    print("=" * 60)
    
    run_command(
        'clipscribe transcribe --batch urls.txt',
        "Process multiple URLs from file"
    )
    print("Contents of urls.txt:")
    print("  https://youtube.com/watch?v=video1")
    print("  https://vimeo.com/video2")
    print("  https://twitter.com/user/status/video3")
    
    run_command(
        'find . -name "*.mp4" | xargs -I {} clipscribe transcribe {}',
        "Process all MP4 files in directory"
    )
    
    # 6. Cost Management
    print("\n\n COST MANAGEMENT")
    print("=" * 60)
    
    run_command(
        'clipscribe cost "https://www.youtube.com/watch?v=long_video"',
        "Preview cost before processing"
    )
    print("""Analyzing video...
Title: 2-Hour Tutorial on Machine Learning
Duration: 2:03:45 (7425 seconds)
Estimated cost: $0.2475 (123.75 minutes @ $0.002/min)""")
    
    run_command(
        'clipscribe transcribe URL --max-cost 0.50',
        "Set maximum cost limit"
    )
    
    # 7. Platform Information
    print("\n\n PLATFORM INFORMATION")
    print("=" * 60)
    
    run_command(
        'clipscribe platforms',
        "List all supported platforms"
    )
    print("""ClipScribe supports 1800+ video platforms via yt-dlp:

Popular platforms:
  • YouTube, YouTube Music, YouTube Shorts
  • Twitter/X, TikTok, Instagram, Facebook
  • Vimeo, Dailymotion, Twitch
  • BBC, CNN, TED, NBC
  • SoundCloud, Bandcamp
  • And 1800+ more!

For full list: clipscribe platforms --all""")
    
    run_command(
        'clipscribe platforms --search "news"',
        "Search for specific platform types"
    )
    
    # 8. Configuration
    print("\n\n  CONFIGURATION")
    print("=" * 60)
    
    run_command(
        'clipscribe config',
        "Show current configuration"
    )
    print("""ClipScribe Configuration:
  API Key: ***************3def (configured)
  Output Directory: ./transcripts
  Default Format: txt
  Cost per minute: $0.002
  Model: google_genai:gemini-2.5-flash-preview-05-20""")
    
    run_command(
        'clipscribe config --output-dir ~/Documents/transcripts',
        "Set default output directory"
    )
    
    # 9. Integration Examples
    print("\n\n INTEGRATION EXAMPLES")
    print("=" * 60)
    
    print("\n# Python script integration:")
    print("""
import subprocess
import json

# Get transcript as JSON
result = subprocess.run(
    ['clipscribe', 'transcribe', 'URL', '--format', 'json', '--no-save'],
    capture_output=True, text=True
)
transcript_data = json.loads(result.stdout)
""")
    
    print("\n# Bash script for monitoring:")
    print("""
#!/bin/bash
# monitor_channel.sh

CHANNEL_URL="https://youtube.com/@channel"
while true; do
    echo "Checking for new videos..."
    clipscribe transcribe "$CHANNEL_URL/videos" --new-only
    sleep 3600  # Check every hour
done
""")
    
    print("\n# GitHub Action example:")
    print("""
- name: Transcribe video
  run: |
    clipscribe transcribe "${{ github.event.inputs.video_url }}" \\
      --format md --output-dir docs/transcripts
""")
    
    # 10. Tips and Tricks
    print("\n\n TIPS AND TRICKS")
    print("=" * 60)
    
    print("\n1. Process only audio from long videos:")
    print('   clipscribe transcribe URL --audio-only')
    
    print("\n2. Extract specific time range:")
    print('   clipscribe transcribe URL --start 00:05:00 --end 00:10:00')
    
    print("\n3. Use with jq for JSON processing:")
    print('   clipscribe transcribe URL --format json | jq .summary')
    
    print("\n4. Create subtitles for existing audio:")
    print('   clipscribe transcribe audio.mp3 --format srt')
    
    print("\n5. Monitor costs across projects:")
    print('   clipscribe cost --report weekly')
    
    print("\n\n Quick Reference Card:")
    print("-" * 60)
    print("transcribe URL           # Basic transcription")
    print("transcribe URL -f srt    # Generate subtitles")
    print("platforms                # List supported sites")
    print("cost URL                 # Preview cost")
    print("config                   # Show settings")
    print("--help                   # Get help")
    
    print("\n\n For more information:")
    print("  • Documentation: https://github.com/yourusername/clipscribe")
    print("  • Examples: https://github.com/yourusername/clipscribe/examples")
    print("  • Issues: https://github.com/yourusername/clipscribe/issues")


if __name__ == "__main__":
    main()  #  