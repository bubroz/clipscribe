#!/usr/bin/env python3
"""Structured Output Demo - Machine-readable output with multiple formats."""

import asyncio
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import json

# Load environment variables
load_dotenv()

# Import ClipScribe
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever


async def main():
    """Demonstrate structured, machine-readable output."""
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print("🏗️  ClipScribe Structured Output Demo")
    print("=" * 50)
    print("\nThis demo shows how ClipScribe creates machine-readable")
    print("output with multiple formats for Chimera integration.\n")
    
    # Create video retriever
    retriever = VideoIntelligenceRetriever()
    
    # Get video URL from command line or use default
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"📹 Processing: {video_url}")
    
    try:
        # Process the video
        result = await retriever.process_url(video_url)
        
        if result:
            # Display initial results
            print(f"\n✅ Processing Complete!")
            print(f"📝 Title: {result.metadata.title}")
            print(f"⏱️  Duration: {result.metadata.duration}s")
            print(f"💰 Cost: ${result.processing_cost:.4f}")
            
            # Save all formats with structured output
            print(f"\n💾 Saving structured output...")
            paths = retriever.save_all_formats(result, output_dir="structured_output")
            
            # Show what was created
            print(f"\n📁 Created directory: {paths['directory']}")
            print(f"\nFiles created:")
            
            # List all files with descriptions
            file_info = [
                ("transcript.txt", "Plain text transcript"),
                ("transcript.json", "Full data with analysis"),
                ("transcript.srt", "Subtitle file (SRT format)"),
                ("transcript.vtt", "Web subtitle file (WebVTT)"),
                ("metadata.json", "Video metadata & statistics"),
                ("entities.json", "Extracted entities for knowledge graph"),
                ("manifest.json", "File index with checksums"),
                ("chimera_format.json", "Chimera-compatible format")
            ]
            
            for filename, description in file_info:
                file_path = paths['directory'] / filename
                if file_path.exists():
                    size = file_path.stat().st_size
                    print(f"  • {filename:<20} - {description:<35} ({size:,} bytes)")
            
            # Show manifest content
            print(f"\n📋 Manifest Preview:")
            with open(paths['manifest'], 'r') as f:
                manifest = json.load(f)
                print(f"  Version: {manifest['version']}")
                print(f"  Platform: {manifest['video']['platform']}")
                print(f"  Files: {len(manifest['files'])}")
            
            # Show directory structure
            print(f"\n🗂️  Directory Structure:")
            print(f"structured_output/")
            print(f"└── {paths['directory'].name}/")
            for filename, _ in file_info:
                print(f"    ├── {filename}")
            
            # Show naming convention
            print(f"\n🏷️  Machine-Readable Naming:")
            print(f"  Pattern: {{date}}_{{platform}}_{{video_id}}/")
            print(f"  Example: {paths['directory'].name}/")
            print(f"  - Date: {paths['directory'].name.split('_')[0]}")
            print(f"  - Platform: {paths['directory'].name.split('_')[1]}")
            print(f"  - Video ID: {paths['directory'].name.split('_')[2]}")
            
            # Show how to read the data
            print(f"\n📖 Reading the Data (Python example):")
            print("""
# Load the manifest
with open('manifest.json', 'r') as f:
    manifest = json.load(f)
    
# Load full transcript data
with open('transcript.json', 'r') as f:
    data = json.load(f)
    transcript = data['transcript']['full_text']
    entities = data['analysis']['entities']
    
# Load entities for knowledge graph
with open('entities.json', 'r') as f:
    entities = json.load(f)
    for entity in entities['entities']:
        print(f"{entity['name']} ({entity['type']})")
""")
            
            # Show Chimera integration
            print(f"\n🔗 Chimera Integration:")
            print("  The chimera_format.json file contains data in the exact")
            print("  format expected by Chimera Researcher for video intelligence.")
            print("  Fields include: title, href, body, source, metadata")
            
        else:
            print("❌ Failed to process video")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())  # :-) 