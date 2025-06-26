#!/usr/bin/env python3
"""
ClipScribe Demo Script - Showcase features with REAL data
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test URLs for demo - PBS two-part video
DEMO_VIDEO_URLS = [
    "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Part 1
    "https://www.youtube.com/watch?v=xYMWTXIkANM"   # Part 2
]

async def run_demo():
    """Run the ClipScribe demo with REAL data - TWO-PART PBS VIDEO."""
    print("🚀 ClipScribe Demo - Two-Part PBS Video Intelligence")
    print("=" * 55)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found!")
        print("\n🔑 You need a FREE Google API key to run ClipScribe:")
        print("   1. Get FREE key: https://makersuite.google.com/app/apikey")
        print("   2. export GOOGLE_API_KEY='your_key_here'")
        print("   3. Run this demo again")
        print(f"\n🎬 This demo will process TWO PBS videos:")
        for i, url in enumerate(DEMO_VIDEO_URLS, 1):
            print(f"   Part {i}: {url}")
        return
    
    print("✅ Google API key detected!")
    print(f"🎬 Processing TWO-PART PBS video series:")
    for i, url in enumerate(DEMO_VIDEO_URLS, 1):
        print(f"   Part {i}: {url}")
    
    # Create output directory
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    print("\n📹 Running ClipScribe batch processing...")
    
    try:
        # Import ClipScribe after checking API key
        from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
        
        # Process both videos
        retriever = VideoIntelligenceRetriever()
        
        total_entities = 0
        total_relationships = 0
        
        for i, url in enumerate(DEMO_VIDEO_URLS, 1):
            print(f"\n🎬 Processing Part {i}/{len(DEMO_VIDEO_URLS)}: {url}")
            print("   ⏳ Downloading and transcribing...")
            print("   ⏳ Extracting entities and relationships...")
            print("   ⏳ Generating knowledge graph...")
            
            # Process each video and save all formats
            video_intelligence = await retriever.retrieve_and_process(
                url=url,
                output_dir=output_dir,
                save_formats=['json', 'csv', 'gexf', 'srt']
            )
            
            entities_count = len(video_intelligence.entities)
            relationships_count = len(video_intelligence.relationships)
            
            print(f"   ✅ Part {i} completed!")
            print(f"   📊 Found {entities_count} entities")
            print(f"   🔗 Found {relationships_count} relationships")
            
            total_entities += entities_count
            total_relationships += relationships_count
        
        print(f"\n🎉 All videos processed!")
        print(f"📊 Total entities across both parts: {total_entities}")
        print(f"🔗 Total relationships across both parts: {total_relationships}")
        
        # Run entity source analysis on the real data from both videos
        print("\n📈 Running Entity Source Analysis on TWO-PART data...")
        
        import subprocess
        result = subprocess.run([
            "python", str(Path.cwd() / "scripts" / "analyze_entity_sources.py"),
            "--output-dir", str(output_dir),
            "--create-visualizations",
            "--save-excel",
            "--save-csv",
            "--save-markdown"
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            print("✅ Batch entity source analysis completed!")
            print("📊 Interactive visualizations created for both videos!")
            print("📈 Cross-video comparison charts generated!")
        else:
            print(f"⚠️  Analysis output: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        print("💡 Make sure you have a valid Google API key and internet connection")
        return
    
    # Show what files were created
    print(f"\n📁 Real demo files created:")
    file_count = 0
    for file_path in output_dir.rglob("*"):
        if file_path.is_file() and file_count < 15:  # Limit output
            print(f"   📄 {file_path.relative_to(output_dir)}")
            file_count += 1
    
    if file_count >= 15:
        print("   ... and more files!")
    
    print("\n🎯 TWO-PART REAL Demo Features Showcased:")
    print("   • Batch processing of multiple videos")
    print("   • Real video transcription with Gemini (2 videos)")
    print("   • Cross-video entity extraction comparison")
    print("   • Multi-video relationship mapping")
    print("   • Batch performance analytics")
    print("   • Interactive Plotly visualizations across videos")
    print("   • Multi-format exports (JSON, CSV, GEXF, SRT)")
    print("   • Excel reports with cross-video analysis")
    print("   • Video comparison charts and insights")
    
    print(f"\n🔍 Next Steps:")
    print("   1. Check the REAL batch files in demo_output/")
    print("   2. Run: streamlit run app.py")
    print("   3. Upload the multi-video data to Streamlit")
    print("   4. Explore the video comparison features")
    print("   5. Try the research tab for more batch processing")
    
    print(f"\n🎉 TWO-PART Demo complete! You now have REAL batch ClipScribe data.")
    print(f"📺 Source videos:")
    for i, url in enumerate(DEMO_VIDEO_URLS, 1):
        print(f"   Part {i}: {url}")

def main():
    """Main entry point."""
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n⏹️  Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    main() 