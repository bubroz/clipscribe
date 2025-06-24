#!/usr/bin/env python3
"""Output Formats Example - Export transcripts in various formats."""

import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from clipscribe.retrievers import UniversalVideoClient
from clipscribe.models import VideoIntelligence


async def demonstrate_output_formats():
    """Show all available output formats."""
    
    client = UniversalVideoClient()
    
    # Sample video
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("📹 Processing video for format demonstration...")
    
    # Process with all formats
    result = await client.transcribe_video(
        video_url,
        save_outputs=True,
        output_formats=['txt', 'srt', 'vtt', 'json', 'md']  # All formats
    )
    
    print("\n✅ Video processed! Demonstrating output formats:\n")
    
    # 1. Plain Text (.txt)
    print("1️⃣ Plain Text (.txt)")
    print("-" * 40)
    print("Simple text transcript, perfect for:")
    print("  • Reading and analysis")
    print("  • Copy/paste into documents")
    print("  • Full-text search")
    print("\nExample:")
    print(result.transcript.full_text[:200] + "...\n")
    
    # 2. SRT Subtitles (.srt)
    print("2️⃣ SRT Subtitles (.srt)")
    print("-" * 40)
    print("Standard subtitle format with timestamps:")
    print("  • Upload to YouTube")
    print("  • Use in video editors")
    print("  • Compatible with most players")
    print("\nExample:")
    print("1")
    print("00:00:00,000 --> 00:00:03,000")
    print("Hello, this is the first subtitle.")
    print("\n2")
    print("00:00:03,000 --> 00:00:06,000")
    print("And this is the second subtitle.\n")
    
    # 3. WebVTT (.vtt)
    print("3️⃣ WebVTT (.vtt)")
    print("-" * 40)
    print("Web-standard subtitle format:")
    print("  • HTML5 video players")
    print("  • Streaming platforms")
    print("  • Better styling options")
    print("\nExample:")
    print("WEBVTT")
    print("\n00:00:00.000 --> 00:00:03.000")
    print("Hello, this is the first subtitle.")
    print("\n00:00:03.000 --> 00:00:06.000")
    print("And this is the second subtitle.\n")
    
    # 4. JSON (.json)
    print("4️⃣ JSON (.json)")
    print("-" * 40)
    print("Structured data format with full metadata:")
    print("  • API integration")
    print("  • Database import")
    print("  • Custom processing")
    print("\nExample structure:")
    example_json = {
        "metadata": {
            "title": result.metadata.title,
            "duration": result.metadata.duration,
            "url": result.metadata.url
        },
        "transcript": {
            "full_text": "...",
            "segments": [
                {"start": 0.0, "end": 3.0, "text": "..."}
            ]
        },
        "processing": {
            "cost": result.processing_cost,
            "time": result.processing_time
        }
    }
    print(json.dumps(example_json, indent=2)[:300] + "...\n")
    
    # 5. Markdown (.md)
    print("5️⃣ Markdown (.md)")
    print("-" * 40)
    print("Formatted documentation:")
    print("  • GitHub/GitLab")
    print("  • Documentation sites")
    print("  • Note-taking apps")
    print("\nExample:")
    print(f"# {result.metadata.title}")
    print(f"\n**Duration:** {result.metadata.duration}s")
    print(f"**URL:** [{result.metadata.url}]({result.metadata.url})")
    print("\n## Transcript")
    print("The transcript content goes here...")
    
    return result


async def custom_format_examples(result: VideoIntelligence):
    """Show how to create custom output formats."""
    
    print("\n\n🎨 Custom Format Examples")
    print("=" * 50)
    
    # 1. CSV format for spreadsheets
    print("\n1️⃣ CSV Format (for Excel/Google Sheets):")
    print("-" * 40)
    print("timestamp,text")
    if result.transcript.segments:
        for seg in result.transcript.segments[:3]:
            print(f"{seg['start']},{seg['text']}")
    print("...")
    
    # 2. HTML format
    print("\n2️⃣ HTML Format (for web display):")
    print("-" * 40)
    html_output = f"""<!DOCTYPE html>
<html>
<head>
    <title>{result.metadata.title}</title>
</head>
<body>
    <h1>{result.metadata.title}</h1>
    <video controls width="640">
        <source src="{result.metadata.url}">
        <track src="subtitles.vtt" kind="subtitles" srclang="en" label="English">
    </video>
    <div id="transcript">
        <p>{result.transcript.full_text[:200]}...</p>
    </div>
</body>
</html>"""
    print(html_output)
    
    # 3. Chapter format
    print("\n3️⃣ YouTube Chapter Format:")
    print("-" * 40)
    print("00:00 Introduction")
    print("02:15 Main Topic")
    print("05:30 Examples")
    print("08:45 Conclusion")
    
    # 4. Summary format
    print("\n4️⃣ Executive Summary Format:")
    print("-" * 40)
    print(f"**Video:** {result.metadata.title}")
    print(f"**Length:** {result.metadata.duration // 60} minutes")
    print(f"**Key Points:**")
    print("• Main topic discussed...")
    print("• Important findings...")
    print("• Action items...")


async def save_custom_formats(result: VideoIntelligence, output_dir: str = "custom_outputs"):
    """Save transcripts in custom formats."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    base_name = result.metadata.title.lower().replace(' ', '_')[:50]
    
    # Save as CSV
    csv_path = output_path / f"{base_name}.csv"
    with open(csv_path, 'w') as f:
        f.write("start_time,end_time,text\n")
        for seg in result.transcript.segments:
            f.write(f"{seg['start']},{seg['end']},\"{seg['text']}\"\n")
    
    # Save as HTML
    html_path = output_path / f"{base_name}.html"
    with open(html_path, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{result.metadata.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .segment {{ margin: 10px 0; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{result.metadata.title}</h1>
    <div id="transcript">
""")
        for seg in result.transcript.segments:
            f.write(f'<div class="segment">')
            f.write(f'<span class="timestamp">[{seg["start"]:.1f}s]</span> ')
            f.write(f'{seg["text"]}</div>\n')
        f.write("</div></body></html>")
    
    print(f"\n💾 Custom formats saved to {output_dir}/")
    print(f"  • CSV: {csv_path.name}")
    print(f"  • HTML: {html_path.name}")


async def main():
    """Demonstrate all output format options."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print("📄 ClipScribe Output Formats Demo")
    print("=" * 50)
    
    # Show all standard formats
    result = await demonstrate_output_formats()
    
    # Show custom format examples
    await custom_format_examples(result)
    
    # Save custom formats
    await save_custom_formats(result)
    
    print("\n\n🎯 Format Selection Guide:")
    print("  • TXT: General purpose, human-readable")
    print("  • SRT/VTT: Video subtitles and captions")
    print("  • JSON: Programmatic access and APIs")
    print("  • MD: Documentation and notes")
    print("  • Custom: Tailored to your specific needs")


if __name__ == "__main__":
    asyncio.run(main())  # :-) 