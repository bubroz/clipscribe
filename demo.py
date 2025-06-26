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

# Test URL for demo
DEMO_VIDEO_URL = "https://www.youtube.com/watch?v=xbQzIzx1dhw"

async def run_demo():
    """Run the ClipScribe demo with REAL data."""
    print("🚀 ClipScribe Demo - Video Intelligence with REAL Data")
    print("=" * 55)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found!")
        print("\n🔑 You need a FREE Google API key to run ClipScribe:")
        print("   1. Get FREE key: https://makersuite.google.com/app/apikey")
        print("   2. export GOOGLE_API_KEY='your_key_here'")
        print("   3. Run this demo again")
        print(f"\n🎬 This demo will process: {DEMO_VIDEO_URL}")
        return
    
    print("✅ Google API key detected!")
    print(f"🎬 Processing real PBS video: {DEMO_VIDEO_URL}")
    
    # Create output directory
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    print("\n📹 Running ClipScribe transcription...")
    
    try:
        # Import ClipScribe after checking API key
        from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
        
        # Process the real video
        retriever = VideoIntelligenceRetriever()
        
        print("   ⏳ Downloading and transcribing video...")
        print("   ⏳ Extracting entities and relationships...")
        print("   ⏳ Generating knowledge graph...")
        
        # Process the video and save all formats
        video_intelligence = await retriever.retrieve_and_process(
            url=DEMO_VIDEO_URL,
            output_dir=output_dir,
            save_formats=['json', 'csv', 'gexf', 'srt']
        )
        
        print(f"✅ Video processing completed!")
        print(f"📊 Found {len(video_intelligence.entities)} entities")
        print(f"🔗 Found {len(video_intelligence.relationships)} relationships")
        
        # Run entity source analysis on the real data
        print("\n📈 Running Entity Source Analysis on real data...")
        
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
            print("✅ Entity source analysis completed!")
            print("📊 Interactive visualizations created!")
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
    
    print("\n🎯 REAL Demo Features Showcased:")
    print("   • Real video transcription with Gemini")
    print("   • Actual entity extraction (SpaCy, GLiNER, REBEL)")
    print("   • Real relationship mapping")
    print("   • Live performance analytics")
    print("   • Interactive Plotly visualizations")
    print("   • Multi-format exports (JSON, CSV, GEXF, SRT)")
    print("   • Excel reports with real data")
    
    print(f"\n🔍 Next Steps:")
    print("   1. Check the REAL files in demo_output/")
    print("   2. Run: streamlit run app.py")
    print("   3. Upload the real data files to Streamlit")
    print("   4. Try the research tab with more PBS videos")
    
    print(f"\n🎉 Demo complete! You now have REAL ClipScribe output data.")
    print(f"📺 Source video: {DEMO_VIDEO_URL}")

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