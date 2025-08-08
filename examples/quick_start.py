#!/usr/bin/env python3
"""ClipScribe Quick Start - Simplest way to transcribe a video."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ClipScribe
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.utils.filename import create_output_filename


async def main():
    """Simple example of transcribing a video."""
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print(" Error: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print(" ClipScribe Quick Start Example")
    print("=" * 40)
    
    # Create video retriever
    retriever = VideoIntelligenceRetriever()
    
    # Video URL (works with 1800+ platforms!)
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"\n Processing: {video_url}")
    
    try:
        # Process the video - it's this simple!
        result = await retriever.process_url(video_url)
        
        if result:
            # Display results
            print(f"\n Success!")
            print(f" Title: {result.metadata.title}")
            print(f"⏱  Duration: {result.metadata.duration}s")
            print(f" Cost: ${result.processing_cost:.4f}")
            print(f"\n Transcript preview:")
            print(result.transcript.full_text[:300] + "...")
            
            # Save transcript to file with video title as filename
            output_file = create_output_filename(result.metadata.title, "txt")
            with open(output_file, "w", encoding='utf-8') as f:
                f.write(result.transcript.full_text)
            
            print(f"\n Files saved:")
            print(f"  • {output_file.name}")
        else:
            print(" Failed to process video")
        
    except Exception as e:
        print(f" Error: {e}")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())  #  