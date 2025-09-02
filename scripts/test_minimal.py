#!/usr/bin/env python3
"""
Minimal Test Script for ClipScribe

A clean, dependency-minimal test to verify core functionality.
Tests both Flash and Pro models on a single video.

Usage:
    poetry run python scripts/test_minimal.py
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_single_video():
    """Test one video with both models."""
    
    # Test video - short for speed
    test_url = "https://www.youtube.com/watch?v=V9VEvGSzzk0"  # 18 min privacy video
    
    print("=" * 80)
    print("CLIPSCRIBE MINIMAL TEST")
    print("=" * 80)
    print(f"Test URL: {test_url}")
    print()
    
    results = {}
    
    # Test both models
    for use_pro in [False, True]:
        model = "pro" if use_pro else "flash"
        print(f"\n{'='*40}")
        print(f"Testing with {model.upper()} model")
        print('='*40)
        
        try:
            # Import only what we need
            from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
            from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
            
            # 1. Download
            print("📥 Downloading video...")
            client = EnhancedUniversalVideoClient()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path, metadata = await client.download_audio(test_url, output_dir=tmpdir)
                
                duration = int(getattr(metadata, "duration", 0) or 0)
                title = getattr(metadata, "title", "Unknown")
                
                print(f"✅ Downloaded: {title}")
                print(f"   Duration: {duration}s ({duration/60:.1f} minutes)")
                
                # 2. Transcribe
                print(f"\n🎙️ Transcribing with Gemini {model.upper()}...")
                transcriber = GeminiFlashTranscriber(use_pro=use_pro)
                
                result = await transcriber.transcribe_audio(audio_path, duration)
                
                # 3. Analyze results
                print("\n📊 Results:")
                print(f"   Transcript length: {len(result.get('transcript', ''))} chars")
                print(f"   Entities found: {len(result.get('entities', []))}")
                print(f"   Relationships found: {len(result.get('relationships', []))}")
                print(f"   Key points: {len(result.get('key_points', []))}")
                print(f"   Dates extracted: {len(result.get('dates', []))}")
                print(f"   Processing cost: ${result.get('processing_cost', 0):.4f}")
                
                # Sample entities
                entities = result.get('entities', [])
                if entities:
                    print("\n   Sample entities:")
                    for i, entity in enumerate(entities[:3]):
                        name = entity.get('name', 'Unknown')
                        etype = entity.get('type', 'Unknown')
                        conf = entity.get('confidence', 0)
                        print(f"     {i+1}. {name} ({etype}) - conf: {conf:.2f}")
                
                # Sample relationships
                relationships = result.get('relationships', [])
                if relationships:
                    print("\n   Sample relationships:")
                    for i, rel in enumerate(relationships[:3]):
                        subj = rel.get('subject') or rel.get('source', 'Unknown')
                        pred = rel.get('predicate') or rel.get('type', 'Unknown')
                        obj = rel.get('object') or rel.get('target', 'Unknown')
                        print(f"     {i+1}. {subj} --[{pred}]--> {obj}")
                
                # Quality metrics
                print("\n📈 Quality Metrics:")
                if duration > 0:
                    entities_per_min = len(entities) / (duration / 60)
                    rels_per_min = len(relationships) / (duration / 60)
                    cost_per_min = result.get('processing_cost', 0) / (duration / 60)
                    
                    print(f"   Entities/minute: {entities_per_min:.1f}")
                    print(f"   Relationships/minute: {rels_per_min:.1f}")
                    print(f"   Cost/minute: ${cost_per_min:.4f}")
                
                # Save output
                output_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / f"{model}_output.json"
                with open(output_file, 'w') as f:
                    json.dump({
                        "metadata": {
                            "url": test_url,
                            "title": title,
                            "duration": duration,
                            "model": model,
                            "timestamp": datetime.now().isoformat()
                        },
                        "results": result
                    }, f, indent=2)
                
                print(f"\n💾 Output saved to: {output_file}")
                
                results[model] = {
                    "success": True,
                    "entities": len(entities),
                    "relationships": len(relationships),
                    "cost": result.get('processing_cost', 0)
                }
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results[model] = {
                "success": False,
                "error": str(e)
            }
    
    # Compare models
    print("\n" + "="*80)
    print("MODEL COMPARISON")
    print("="*80)
    
    if all(r.get("success") for r in results.values()):
        flash = results["flash"]
        pro = results["pro"]
        
        print(f"\nFlash Model:")
        print(f"  Entities: {flash['entities']}")
        print(f"  Relationships: {flash['relationships']}")
        print(f"  Cost: ${flash['cost']:.4f}")
        
        print(f"\nPro Model:")
        print(f"  Entities: {pro['entities']}")
        print(f"  Relationships: {pro['relationships']}")
        print(f"  Cost: ${pro['cost']:.4f}")
        
        print(f"\nDifferences:")
        print(f"  Entity difference: {pro['entities'] - flash['entities']:+d} ({(pro['entities'] - flash['entities'])/flash['entities']*100:+.1f}%)")
        print(f"  Relationship difference: {pro['relationships'] - flash['relationships']:+d} ({(pro['relationships'] - flash['relationships'])/max(flash['relationships'], 1)*100:+.1f}%)")
        print(f"  Cost difference: ${pro['cost'] - flash['cost']:+.4f} ({(pro['cost'] - flash['cost'])/flash['cost']*100:+.1f}%)")
        
        # Recommendation
        entity_improvement = (pro['entities'] - flash['entities']) / max(flash['entities'], 1)
        cost_increase = (pro['cost'] - flash['cost']) / flash['cost']
        
        print(f"\n📊 Recommendation:")
        if entity_improvement > 0.2 and cost_increase < 5:
            print("  ✅ Pro model provides significant improvement for reasonable cost")
        elif entity_improvement < 0.1:
            print("  💡 Flash model is sufficient - minimal quality difference")
        else:
            print(f"  ⚖️ Pro provides {entity_improvement*100:.0f}% more entities at {cost_increase*100:.0f}% higher cost")
    else:
        print("\n❌ One or both models failed - check errors above")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


async def main():
    """Main entry point."""
    
    # Check environment
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        print("Please run: source .env")
        sys.exit(1)
    
    print("Starting minimal test...\n")
    await test_single_video()


if __name__ == "__main__":
    asyncio.run(main())
