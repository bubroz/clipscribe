#!/usr/bin/env python3
"""
Multi-Video Test for ClipScribe

Tests multiple videos with both Flash and Pro models to identify patterns.

Usage:
    poetry run python scripts/test_multi_video.py
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


TEST_VIDEOS = [
    {
        "id": "news_short",
        "url": "https://www.youtube.com/watch?v=A-bdxIi7v04",
        "title": "PBS News Weekend (26 min)",
        "category": "news"
    },
    {
        "id": "defense_training",
        "url": "https://www.youtube.com/watch?v=Nr7vbOSzpSk", 
        "title": "Tier 1&2 Training (31 min)",
        "category": "defense"
    },
    {
        "id": "privacy_tech",
        "url": "https://www.youtube.com/watch?v=V9VEvGSzzk0",
        "title": "Data Privacy Investigation (94 min)",
        "category": "tech"
    }
]


async def test_video(video: Dict[str, Any], use_pro: bool) -> Dict[str, Any]:
    """Test a single video with specified model."""
    
    model = "pro" if use_pro else "flash"
    print(f"\n{'='*60}")
    print(f"Testing: {video['title']}")
    print(f"Model: {model.upper()}")
    print(f"URL: {video['url']}")
    
    result = {
        "video_id": video["id"],
        "title": video["title"],
        "category": video["category"],
        "model": model,
        "success": False
    }
    
    try:
        from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
        from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
        
        # Download
        print("📥 Downloading...")
        client = EnhancedUniversalVideoClient()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path, metadata = await client.download_audio(video["url"], output_dir=tmpdir)
            
            duration = int(getattr(metadata, "duration", 0) or 0)
            print(f"✅ Downloaded: {duration}s ({duration/60:.1f} min)")
            
            # Transcribe
            print(f"🎙️ Transcribing with {model.upper()}...")
            transcriber = GeminiFlashTranscriber(use_pro=use_pro)
            
            output = await transcriber.transcribe_audio(audio_path, duration)
            
            # Collect metrics
            result.update({
                "success": True,
                "duration": duration,
                "transcript_length": len(output.get("transcript", "")),
                "word_count": len(output.get("transcript", "").split()),
                "entities": len(output.get("entities", [])),
                "relationships": len(output.get("relationships", [])),
                "key_points": len(output.get("key_points", [])),
                "dates": len(output.get("dates", [])),
                "cost": output.get("processing_cost", 0),
                "cost_per_minute": output.get("processing_cost", 0) / (duration / 60) if duration > 0 else 0
            })
            
            print(f"✅ Complete: {result['entities']} entities, {result['relationships']} relationships, ${result['cost']:.4f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        result["error"] = str(e)
    
    return result


async def main():
    """Run tests on all videos with both models."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    print("="*80)
    print("CLIPSCRIBE MULTI-VIDEO TEST")
    print("="*80)
    print(f"Testing {len(TEST_VIDEOS)} videos with Flash and Pro models")
    
    results = []
    
    # Test each video with both models
    for video in TEST_VIDEOS:
        for use_pro in [False, True]:
            result = await test_video(video, use_pro)
            results.append(result)
    
    # Save results
    output_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "multi_video_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    # Group by video
    for video in TEST_VIDEOS:
        print(f"\n📹 {video['title']} ({video['category']})")
        
        flash_result = next((r for r in results if r["video_id"] == video["id"] and r["model"] == "flash"), None)
        pro_result = next((r for r in results if r["video_id"] == video["id"] and r["model"] == "pro"), None)
        
        if flash_result and flash_result.get("success") and pro_result and pro_result.get("success"):
            print(f"\n  Flash Model:")
            print(f"    Words: {flash_result['word_count']:,}")
            print(f"    Entities: {flash_result['entities']}")
            print(f"    Relationships: {flash_result['relationships']}")
            print(f"    Cost: ${flash_result['cost']:.4f} (${flash_result['cost_per_minute']:.4f}/min)")
            
            print(f"\n  Pro Model:")
            print(f"    Words: {pro_result['word_count']:,}")
            print(f"    Entities: {pro_result['entities']}")
            print(f"    Relationships: {pro_result['relationships']}")
            print(f"    Cost: ${pro_result['cost']:.4f} (${pro_result['cost_per_minute']:.4f}/min)")
            
            print(f"\n  Pro vs Flash:")
            word_diff = (pro_result['word_count'] - flash_result['word_count']) / max(flash_result['word_count'], 1) * 100
            entity_diff = (pro_result['entities'] - flash_result['entities']) / max(flash_result['entities'], 1) * 100
            rel_diff = (pro_result['relationships'] - flash_result['relationships']) / max(flash_result['relationships'], 1) * 100
            cost_diff = (pro_result['cost'] - flash_result['cost']) / flash_result['cost'] * 100
            
            print(f"    Words: {word_diff:+.1f}%")
            print(f"    Entities: {entity_diff:+.1f}%")
            print(f"    Relationships: {rel_diff:+.1f}%")
            print(f"    Cost: {cost_diff:+.1f}%")
        else:
            if flash_result and not flash_result.get("success"):
                print(f"  Flash: ❌ {flash_result.get('error', 'Unknown error')}")
            if pro_result and not pro_result.get("success"):
                print(f"  Pro: ❌ {pro_result.get('error', 'Unknown error')}")
    
    # Overall summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    flash_results = [r for r in results if r["model"] == "flash" and r.get("success")]
    pro_results = [r for r in results if r["model"] == "pro" and r.get("success")]
    
    if flash_results and pro_results:
        avg_flash_entities = sum(r["entities"] for r in flash_results) / len(flash_results)
        avg_pro_entities = sum(r["entities"] for r in pro_results) / len(pro_results)
        
        avg_flash_rels = sum(r["relationships"] for r in flash_results) / len(flash_results)
        avg_pro_rels = sum(r["relationships"] for r in pro_results) / len(pro_results)
        
        avg_flash_cost = sum(r["cost_per_minute"] for r in flash_results) / len(flash_results)
        avg_pro_cost = sum(r["cost_per_minute"] for r in pro_results) / len(pro_results)
        
        print(f"\nAverage Performance:")
        print(f"  Flash: {avg_flash_entities:.1f} entities, {avg_flash_rels:.1f} relationships, ${avg_flash_cost:.4f}/min")
        print(f"  Pro: {avg_pro_entities:.1f} entities, {avg_pro_rels:.1f} relationships, ${avg_pro_cost:.4f}/min")
        
        print(f"\n📊 Conclusion:")
        entity_improvement = (avg_pro_entities - avg_flash_entities) / avg_flash_entities
        rel_improvement = (avg_pro_rels - avg_flash_rels) / avg_flash_rels
        cost_increase = (avg_pro_cost - avg_flash_cost) / avg_flash_cost
        
        if entity_improvement > 0.2 and rel_improvement > 0.2:
            print("  ✅ Pro model provides significant quality improvement")
        elif entity_improvement < -0.1 or rel_improvement < -0.1:
            print("  ⚠️ Pro model underperforms Flash - needs investigation")
        else:
            print("  💡 Flash model is sufficient for most use cases")
        
        print(f"\n  Quality change: {entity_improvement*100:+.1f}% entities, {rel_improvement*100:+.1f}% relationships")
        print(f"  Cost change: {cost_increase*100:+.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
