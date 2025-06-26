#!/usr/bin/env python3
"""
ClipScribe Demo Script - Showcase features with sample data
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clipscribe.models import VideoIntelligence, Entity, Relationship
from clipscribe.utils.performance import PerformanceMonitor

def create_sample_data() -> Dict[str, Any]:
    """Create realistic sample data for demo purposes."""
    return {
        "video_id": "demo_pbs_news",
        "title": "PBS NewsHour: Climate Change Impact on Global Economy",
        "url": "https://www.youtube.com/watch?v=demo_video",
        "platform": "youtube",
        "duration": 1800,  # 30 minutes
        "transcript": [
            {
                "start": 0.0,
                "end": 5.2,
                "text": "Good evening, I'm Judy Woodruff with the PBS NewsHour."
            },
            {
                "start": 5.2,
                "end": 12.8,
                "text": "Tonight, we examine how climate change is reshaping the global economy with Dr. Sarah Chen from MIT."
            },
            {
                "start": 12.8,
                "end": 20.1,
                "text": "Dr. Chen, your recent research shows significant economic impacts from rising sea levels."
            },
            {
                "start": 20.1,
                "end": 28.5,
                "text": "That's right, Judy. Our analysis of coastal cities shows potential GDP losses of up to 15% by 2050."
            }
        ],
        "summary": "PBS NewsHour examines the economic impacts of climate change, featuring an interview with Dr. Sarah Chen from MIT discussing research on coastal city vulnerabilities and GDP projections.",
        "key_points": [
            "Climate change is significantly impacting the global economy",
            "Coastal cities face potential GDP losses of up to 15% by 2050",
            "MIT research provides new insights into economic vulnerabilities",
            "Rising sea levels are a major economic concern"
        ],
        "entities": [
            {
                "text": "Judy Woodruff",
                "label": "PERSON",
                "confidence": 0.98,
                "source": "spacy",
                "context": "PBS NewsHour host and journalist"
            },
            {
                "text": "Dr. Sarah Chen",
                "label": "PERSON", 
                "confidence": 0.95,
                "source": "gliner",
                "context": "MIT researcher studying climate economics"
            },
            {
                "text": "MIT",
                "label": "ORG",
                "confidence": 0.92,
                "source": "spacy",
                "context": "Massachusetts Institute of Technology"
            },
            {
                "text": "PBS NewsHour",
                "label": "ORG",
                "confidence": 0.96,
                "source": "rebel",
                "context": "Public television news program"
            },
            {
                "text": "climate change",
                "label": "CONCEPT",
                "confidence": 0.88,
                "source": "gliner",
                "context": "Long-term shifts in global climate patterns"
            },
            {
                "text": "GDP",
                "label": "CONCEPT",
                "confidence": 0.85,
                "source": "spacy",
                "context": "Gross Domestic Product economic measure"
            }
        ],
        "relationships": [
            {
                "source": "Judy Woodruff",
                "target": "PBS NewsHour",
                "relation": "hosts",
                "confidence": 0.95,
                "context": "Judy Woodruff is the host of PBS NewsHour"
            },
            {
                "source": "Dr. Sarah Chen",
                "target": "MIT",
                "relation": "affiliated_with",
                "confidence": 0.92,
                "context": "Dr. Sarah Chen conducts research at MIT"
            },
            {
                "source": "climate change",
                "target": "GDP",
                "relation": "impacts",
                "confidence": 0.89,
                "context": "Climate change impacts GDP through economic losses"
            }
        ],
        "processing_metadata": {
            "extraction_methods": {
                "spacy": {"entities_found": 3, "confidence_avg": 0.91},
                "gliner": {"entities_found": 2, "confidence_avg": 0.92},
                "rebel": {"entities_found": 1, "confidence_avg": 0.96}
            },
            "processing_time": 45.2,
            "api_cost": 0.12,
            "timestamp": datetime.now().isoformat()
        }
    }

def create_entity_sources_data() -> Dict[str, Any]:
    """Create entity sources data for analysis demo."""
    return {
        "video_url": "https://www.youtube.com/watch?v=demo_video",
        "title": "PBS NewsHour: Climate Change Impact on Global Economy",
        "summary": "PBS NewsHour examines the economic impacts of climate change, featuring an interview with Dr. Sarah Chen from MIT discussing research on coastal city vulnerabilities and GDP projections.",
        "all_entities": [
            {"text": "Judy Woodruff", "type": "PERSON", "confidence": 0.98, "source": "spacy"},
            {"text": "Dr. Sarah Chen", "type": "PERSON", "confidence": 0.95, "source": "gliner"},
            {"text": "MIT", "type": "ORG", "confidence": 0.92, "source": "spacy"},
            {"text": "PBS NewsHour", "type": "ORG", "confidence": 0.96, "source": "rebel"},
            {"text": "climate change", "type": "CONCEPT", "confidence": 0.88, "source": "gliner"},
            {"text": "GDP", "type": "CONCEPT", "confidence": 0.85, "source": "spacy"}
        ]
    }

def run_demo():
    """Run the ClipScribe demo."""
    print("🚀 ClipScribe Demo - Video Intelligence Showcase")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    print("📊 Creating sample video intelligence data...")
    
    # Create sample data
    sample_data = create_sample_data()
    entity_sources_data = create_entity_sources_data()
    
    # Create a video subdirectory structure that the analyzer expects
    video_dir = output_dir / "demo_pbs_news"
    video_dir.mkdir(exist_ok=True)
    
    # Save sample files in the expected structure
    with open(video_dir / "video_intelligence.json", "w") as f:
        json.dump(sample_data, f, indent=2)
        
    with open(video_dir / "entity_sources.json", "w") as f:
        json.dump(entity_sources_data, f, indent=2)
    
    print(f"✅ Sample data created in {output_dir}/")
    
    # Demonstrate entity source analysis
    print("\n📈 Running Entity Source Analysis...")
    
    try:
        # Import and run the analyzer
        import subprocess
        # Change to the demo output directory so the analyzer can find the files
        result = subprocess.run([
            "python", str(Path.cwd() / "scripts" / "analyze_entity_sources.py"),
            "--output-dir", "analysis",
            "--create-visualizations",
            "--save-excel",
            "--save-csv",
            "--save-markdown"
        ], capture_output=True, text=True, cwd=output_dir)
        
        if result.returncode == 0:
            print("✅ Entity source analysis completed!")
            print(f"📊 Results saved to {output_dir / 'analysis'}/")
        else:
            print(f"⚠️  Analysis script output: {result.stderr}")
            
    except Exception as e:
        print(f"⚠️  Could not run analysis script: {e}")
    
    # Show what files were created
    print(f"\n📁 Demo files created:")
    for file_path in output_dir.rglob("*"):
        if file_path.is_file():
            print(f"   📄 {file_path.relative_to(output_dir)}")
    
    print("\n🎯 Demo Features Showcased:")
    print("   • Video intelligence extraction")
    print("   • Entity source tracking (SpaCy, GLiNER, REBEL)")
    print("   • Relationship mapping")
    print("   • Performance analytics")
    print("   • Multi-format exports")
    
    print(f"\n🔍 Next Steps:")
    print("   1. Check the files in demo_output/")
    print("   2. Run: streamlit run app.py")
    print("   3. Upload demo files to the Streamlit interface")
    print("   4. Get a Google API key for live video processing")
    
    # Check if API key is available
    if os.getenv("GOOGLE_API_KEY"):
        print("\n✅ Google API key detected!")
        print("   Try: poetry run clipscribe transcribe 'https://www.youtube.com/watch?v=UjDpW_SOrlw'")
    else:
        print("\n💡 To process real videos:")
        print("   1. Get API key: https://makersuite.google.com/app/apikey")
        print("   2. export GOOGLE_API_KEY='your_key_here'")
        print("   3. poetry run clipscribe transcribe 'VIDEO_URL'")

if __name__ == "__main__":
    run_demo() 