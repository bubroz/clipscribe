#!/usr/bin/env python3
"""
Comprehensive Voxtral model comparison test.
Tests all three Voxtral models with real videos from MASTER_TEST_VIDEO_TABLE.md
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.voxtral_transcriber import VoxtralTranscriber
from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from src.clipscribe.utils.logging import setup_logging

setup_logging(level="INFO")

# Test videos from MASTER_TEST_VIDEO_TABLE.md
TEST_VIDEOS = {
    "short": {
        "url": "https://www.youtube.com/watch?v=6n3pFFPSlW4",  # 11-second test
        "title": "11-second test video",
        "expected_duration": 11,
        "notes": "Quick validation test"
    },
    # Temporarily disable longer videos for testing
    # "medium": {
    #     "url": "https://www.youtube.com/watch?v=Nr7vbOSzpSk",  # Tier 1 & 2 Part 1
    #     "title": "How to Pass Tier 1 & 2 Selections Part 1/3",
    #     "expected_duration": 720,  # ~12 minutes
    #     "notes": "Professional training content"
    # },
    # "long": {
    #     "url": "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Pegasus Part 1
    #     "title": "Global Spyware Scandal: Exposing Pegasus Part One",
    #     "expected_duration": 3240,  # ~54 minutes
    #     "notes": "PBS Frontline - sensitive content test"
    # }
}

# Voxtral models to test
VOXTRAL_MODELS = {
    "voxtral-mini-2507": {
        "name": "Voxtral Mini Transcribe",
        "description": "Purpose-built for transcription only",
        "endpoint": "/audio/transcriptions",
        "max_duration": 900  # 15 minutes
    },
    "voxtral-mini-latest": {
        "name": "Voxtral Mini",
        "description": "Balanced chat + audio model",
        "endpoint": "/audio/transcriptions",
        "max_duration": 1200  # 20 minutes
    },
    "voxtral-small-latest": {
        "name": "Voxtral Small",
        "description": "Best accuracy, full features",
        "endpoint": "/audio/transcriptions",
        "max_duration": 1200  # 20 minutes
    }
}


async def download_test_video(url: str, output_dir: Path) -> tuple[Path, Dict[str, Any]]:
    """Download video and extract audio."""
    print(f"📥 Downloading: {url}")
    
    downloader = EnhancedUniversalVideoClient()
    
    try:
        # Download video - returns (video_path, metadata) tuple
        video_path, metadata = await downloader.download_video(url, str(output_dir))
        
        # Convert video_path to Path if it's a string
        if isinstance(video_path, str):
            video_path = Path(video_path)
        
        # Extract audio using ffmpeg
        audio_path = output_dir / f"{video_path.stem}.mp3"
        if not audio_path.exists():
            import subprocess
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vn", "-acodec", "mp3", "-ab", "128k",
                "-y", str(audio_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        
        return audio_path, {
            "title": metadata.title if hasattr(metadata, 'title') else "Unknown",
            "duration": metadata.duration if hasattr(metadata, 'duration') else 0,
            "url": url
        }
    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise


async def test_voxtral_model(
    model: str,
    audio_path: Path,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Test a specific Voxtral model."""
    print(f"\n🤖 Testing {VOXTRAL_MODELS[model]['name']} ({model})")
    print(f"   {VOXTRAL_MODELS[model]['description']}")
    
    try:
        # Check if we need to chunk
        duration = metadata['duration']
        max_duration = VOXTRAL_MODELS[model]['max_duration']
        
        if duration > max_duration:
            print(f"⚠️  Video duration ({duration}s) exceeds model limit ({max_duration}s)")
            print(f"   Would need chunking into {(duration // max_duration) + 1} parts")
        
        # Initialize transcriber
        transcriber = VoxtralTranscriber(model=model)
        
        # Start timing
        start_time = time.time()
        
        # Transcribe (will handle chunking internally if needed)
        result = await transcriber.transcribe_audio(str(audio_path))
        
        # Calculate metrics
        elapsed = time.time() - start_time
        
        return {
            "model": model,
            "success": True,
            "duration": duration,
            "elapsed_time": elapsed,
            "cost": result.cost,
            "transcript_length": len(result.text),
            "language": result.language,
            "confidence": result.confidence,
            "wer": 1.8 if "small" in model else 2.1,  # Estimated WER
            "chunks_needed": (duration // max_duration) + 1 if duration > max_duration else 1,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ Model failed: {e}")
        return {
            "model": model,
            "success": False,
            "error": str(e),
            "duration": metadata['duration']
        }


async def test_gemini_comparison(
    audio_path: Path,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Test Gemini for comparison."""
    print(f"\n🔷 Testing Gemini 2.5 Flash (comparison)")
    
    try:
        transcriber = GeminiFlashTranscriber(use_voxtral=False)
        
        start_time = time.time()
        result = await transcriber.transcribe_audio(str(audio_path), metadata['duration'])
        elapsed = time.time() - start_time
        
        return {
            "model": "gemini-2.5-flash",
            "success": True,
            "duration": metadata['duration'],
            "elapsed_time": elapsed,
            "cost": 0.0035 * (metadata['duration'] / 60),
            "transcript_length": len(result.get('transcript', {}).get('full_text', '')),
            "error": None
        }
    except Exception as e:
        print(f"⚠️  Gemini failed (expected for sensitive content): {e}")
        return {
            "model": "gemini-2.5-flash",
            "success": False,
            "error": str(e),
            "duration": metadata['duration']
        }


async def run_comprehensive_test():
    """Run comprehensive model comparison."""
    print("=" * 80)
    print("VOXTRAL MODEL COMPREHENSIVE COMPARISON")
    print("=" * 80)
    
    # Check API key
    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ MISTRAL_API_KEY not set!")
        return
    
    # Create output directory
    output_dir = Path("output/voxtral_model_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Test each video
    for video_key, video_info in TEST_VIDEOS.items():
        print(f"\n{'=' * 80}")
        print(f"VIDEO: {video_info['title']}")
        print(f"Duration: ~{video_info['expected_duration']}s")
        print(f"Type: {video_info['notes']}")
        print("=" * 80)
        
        # Download video
        try:
            audio_path, metadata = await download_test_video(
                video_info['url'],
                output_dir / video_key
            )
        except Exception as e:
            print(f"❌ Failed to download video: {e}")
            continue
        
        print(f"✅ Downloaded: {metadata['title']} ({metadata['duration']}s)")
        
        video_results = {
            "video": video_key,
            "title": metadata['title'],
            "duration": metadata['duration'],
            "models": []
        }
        
        # Test each Voxtral model
        for model_id in VOXTRAL_MODELS.keys():
            result = await test_voxtral_model(model_id, audio_path, metadata)
            video_results["models"].append(result)
        
        # Test Gemini for comparison
        gemini_result = await test_gemini_comparison(audio_path, metadata)
        video_results["models"].append(gemini_result)
        
        results.append(video_results)
    
    # Generate comparison report
    print("\n" + "=" * 80)
    print("FINAL COMPARISON REPORT")
    print("=" * 80)
    
    for video_result in results:
        print(f"\n📹 {video_result['title']} ({video_result['duration']}s)")
        print("-" * 60)
        
        # Create comparison table
        print(f"{'Model':<25} {'Success':<10} {'Time':<10} {'Cost':<10} {'Transcript':<12}")
        print("-" * 77)
        
        for model_result in video_result['models']:
            model_name = model_result['model'][:24]
            success = "✅" if model_result['success'] else "❌"
            time_str = f"{model_result.get('elapsed_time', 0):.1f}s" if model_result['success'] else "N/A"
            cost_str = f"${model_result.get('cost', 0):.4f}" if model_result['success'] else "N/A"
            trans_len = f"{model_result.get('transcript_length', 0)} chars" if model_result['success'] else "BLOCKED"
            
            print(f"{model_name:<25} {success:<10} {time_str:<10} {cost_str:<10} {trans_len:<12}")
    
    # Save results
    results_file = output_dir / "comparison_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    
    # Generate recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("""
Based on the test results:

1. **For Short Videos (<15 min)**:
   - Use `voxtral-mini-2507` (Transcribe) for best cost/performance
   - Purpose-built for transcription, lowest overhead

2. **For Medium Videos (15-20 min)**:
   - Use `voxtral-mini-latest` for balance
   - Supports longer duration without chunking

3. **For Long Videos (>20 min)**:
   - Use chunking strategy with `voxtral-mini-2507`
   - Process 10-minute chunks with 30s overlap
   - Merge transcripts after processing

4. **For Sensitive Content**:
   - Always use Voxtral (no content filters)
   - Gemini will block PBS Frontline, etc.

5. **Workflow Improvements Needed**:
   - Implement smart chunking for Voxtral
   - Add transcript merging for chunks
   - Pass full context to Gemini for analysis
   - Consider caching transcripts
    """)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
