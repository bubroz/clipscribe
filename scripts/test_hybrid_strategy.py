#!/usr/bin/env python3
"""
Hybrid Model Strategy Test

Tests the hypothesis that:
- Flash is better for extraction (entities, relationships)
- Pro is better for analysis (summaries, insights, reports)

Usage:
    poetry run python scripts/test_hybrid_strategy.py
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_hybrid_approach():
    """Test Flash for extraction, Pro for analysis."""
    
    # Test video
    test_url = "https://www.youtube.com/watch?v=V9VEvGSzzk0"  # 94 min privacy video
    
    print("=" * 80)
    print("HYBRID MODEL STRATEGY TEST")
    print("=" * 80)
    print("Hypothesis: Flash for extraction, Pro for analysis")
    print(f"Test URL: {test_url}")
    print()
    
    from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
    from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
    import google.generativeai as genai
    
    # Download video once
    print("📥 Downloading video...")
    client = EnhancedUniversalVideoClient()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path, metadata = await client.download_audio(test_url, output_dir=tmpdir)
        
        duration = int(getattr(metadata, "duration", 0) or 0)
        title = getattr(metadata, "title", "Unknown")
        
        print(f"✅ Downloaded: {title}")
        print(f"   Duration: {duration}s ({duration/60:.1f} minutes)")
        
        # STEP 1: Use FLASH for extraction (the grunt work)
        print("\n" + "="*60)
        print("STEP 1: FLASH for Extraction (Grunt Work)")
        print("="*60)
        
        flash_transcriber = GeminiFlashTranscriber(use_pro=False)
        
        print("\n🎙️ Transcribing with FLASH...")
        flash_result = await flash_transcriber.transcribe_audio(audio_path, duration)
        
        transcript = flash_result.get("transcript", "")
        entities = flash_result.get("entities", [])
        relationships = flash_result.get("relationships", [])
        flash_cost = flash_result.get("processing_cost", 0)
        
        print(f"\n📊 Flash Extraction Results:")
        print(f"   Transcript: {len(transcript)} chars")
        print(f"   Entities: {len(entities)}")
        print(f"   Relationships: {len(relationships)}")
        print(f"   Cost: ${flash_cost:.4f}")
        
        # Save Flash results
        output_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        flash_file = output_dir / "flash_extraction.json"
        with open(flash_file, 'w') as f:
            json.dump({
                "transcript_length": len(transcript),
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "cost": flash_cost,
                "entities": entities[:10],  # Sample
                "relationships": relationships[:10]  # Sample
            }, f, indent=2)
        
        # STEP 2: Use PRO for analysis (the thinking work)
        print("\n" + "="*60)
        print("STEP 2: PRO for Analysis (Intelligence Work)")
        print("="*60)
        
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        pro_model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Test different analytical tasks
        analytical_tasks = [
            {
                "name": "Executive Summary",
                "prompt": f"""
                Based on this transcript and extracted intelligence, create an executive summary.
                
                Transcript (first 10000 chars):
                {transcript[:10000]}
                
                Key Entities Found ({len(entities)} total):
                {json.dumps(entities[:20], indent=2)}
                
                Key Relationships ({len(relationships)} total):
                {json.dumps(relationships[:15], indent=2)}
                
                Create a 3-5 paragraph executive summary that:
                1. Identifies the main themes and topics
                2. Highlights key players and their roles
                3. Summarizes critical relationships and connections
                4. Provides actionable intelligence insights
                5. Identifies potential risks or opportunities
                """
            },
            {
                "name": "Threat Assessment",
                "prompt": f"""
                Analyze this content for potential security/privacy threats.
                
                Context: {title}
                Key Entities: {json.dumps([e.get('name') for e in entities[:30]])}
                
                Provide a threat assessment including:
                1. Privacy risks identified
                2. Security vulnerabilities mentioned
                3. Threat actors or techniques discussed
                4. Mitigation recommendations
                5. Risk level assessment (Low/Medium/High)
                
                Format as structured analysis.
                """
            },
            {
                "name": "Network Analysis", 
                "prompt": f"""
                Analyze the relationship network from this content.
                
                Entities: {json.dumps(entities[:25], indent=2)}
                Relationships: {json.dumps(relationships[:20], indent=2)}
                
                Provide:
                1. Key network clusters/groups
                2. Central figures (hub nodes)
                3. Information flow patterns
                4. Hidden connections or implications
                5. Strategic insights from the network structure
                """
            },
            {
                "name": "Timeline Construction",
                "prompt": f"""
                From this transcript, construct a chronological timeline of events.
                
                Transcript excerpt: {transcript[:8000]}
                
                Create a structured timeline with:
                1. Date/timeframe
                2. Event description
                3. Key actors involved
                4. Significance/impact
                
                Focus on the most important 10-15 events.
                """
            }
        ]
        
        pro_results = {}
        total_pro_cost = 0
        
        for task in analytical_tasks:
            print(f"\n📝 Testing Pro: {task['name']}...")
            
            try:
                # Estimate cost (Pro: ~$0.01 per 1000 chars input, $0.02 per 1000 chars output)
                input_chars = len(task['prompt'])
                estimated_cost = (input_chars / 1000) * 0.01 + 2.0 * 0.02  # Assume 2k output
                
                response = await pro_model.generate_content_async(
                    task['prompt'],
                    generation_config={
                        "temperature": 0.3,  # More focused for analysis
                        "max_output_tokens": 2048
                    }
                )
                
                result_text = response.text
                quality_score = len(result_text) / 100  # Simple quality metric
                
                print(f"   ✅ Generated: {len(result_text)} chars")
                print(f"   Estimated cost: ${estimated_cost:.4f}")
                print(f"   Quality score: {quality_score:.1f}")
                
                # Save sample
                task_file = output_dir / f"pro_{task['name'].lower().replace(' ', '_')}.txt"
                with open(task_file, 'w') as f:
                    f.write(result_text)
                
                # Show preview
                preview = result_text[:300] + "..." if len(result_text) > 300 else result_text
                print(f"   Preview: {preview}")
                
                pro_results[task['name']] = {
                    "success": True,
                    "length": len(result_text),
                    "cost": estimated_cost,
                    "quality": quality_score
                }
                
                total_pro_cost += estimated_cost
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                pro_results[task['name']] = {
                    "success": False,
                    "error": str(e)
                }
        
        # STEP 3: Compare with Flash doing the same analytical tasks
        print("\n" + "="*60)
        print("STEP 3: FLASH for Analysis (Comparison)")
        print("="*60)
        
        flash_model = genai.GenerativeModel("gemini-2.5-flash")
        flash_analysis_results = {}
        total_flash_analysis_cost = 0
        
        # Test just the executive summary with Flash for comparison
        test_task = analytical_tasks[0]  # Executive Summary
        
        print(f"\n📝 Testing Flash: {test_task['name']}...")
        
        try:
            estimated_cost = (len(test_task['prompt']) / 1000) * 0.002 + 2.0 * 0.004
            
            response = await flash_model.generate_content_async(
                test_task['prompt'],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 2048
                }
            )
            
            result_text = response.text
            quality_score = len(result_text) / 100
            
            print(f"   ✅ Generated: {len(result_text)} chars")
            print(f"   Estimated cost: ${estimated_cost:.4f}")
            print(f"   Quality score: {quality_score:.1f}")
            
            # Save for comparison
            flash_summary_file = output_dir / "flash_executive_summary.txt"
            with open(flash_summary_file, 'w') as f:
                f.write(result_text)
            
            preview = result_text[:300] + "..." if len(result_text) > 300 else result_text
            print(f"   Preview: {preview}")
            
            flash_analysis_results["Executive Summary"] = {
                "length": len(result_text),
                "cost": estimated_cost,
                "quality": quality_score
            }
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # ANALYSIS
        print("\n" + "="*80)
        print("ANALYSIS: HYBRID MODEL STRATEGY")
        print("="*80)
        
        print("\n📊 Extraction Performance (Grunt Work):")
        print(f"  Flash: {len(entities)} entities, {len(relationships)} relationships")
        print(f"  Cost: ${flash_cost:.4f}")
        print(f"  Speed: Fast, reliable")
        
        print("\n📊 Analysis Performance (Intelligence Work):")
        
        successful_pro = [k for k, v in pro_results.items() if v.get("success")]
        if successful_pro:
            avg_pro_quality = sum(v["quality"] for v in pro_results.values() if v.get("success")) / len(successful_pro)
            avg_pro_length = sum(v["length"] for v in pro_results.values() if v.get("success")) / len(successful_pro)
            
            print(f"\n  Pro Model Analytics:")
            for task_name in successful_pro:
                result = pro_results[task_name]
                print(f"    {task_name}: {result['length']} chars, quality: {result['quality']:.1f}")
            
            print(f"\n  Pro Average:")
            print(f"    Output length: {avg_pro_length:.0f} chars")
            print(f"    Quality score: {avg_pro_quality:.1f}")
            print(f"    Total cost: ${total_pro_cost:.4f}")
        
        if flash_analysis_results:
            print(f"\n  Flash Model Analytics:")
            for task_name, result in flash_analysis_results.items():
                print(f"    {task_name}: {result['length']} chars, quality: {result['quality']:.1f}")
                print(f"    Cost: ${result['cost']:.4f}")
        
        # RECOMMENDATION
        print("\n" + "="*80)
        print("RECOMMENDATION")
        print("="*80)
        
        print("\n🎯 Hybrid Strategy Assessment:")
        
        # Calculate value proposition
        flash_extraction_value = len(entities) / flash_cost if flash_cost > 0 else 0
        
        print(f"\n1. Extraction (Grunt Work):")
        print(f"   ✅ Use FLASH - Better performance at lower cost")
        print(f"   Value: {flash_extraction_value:.0f} entities per dollar")
        
        print(f"\n2. Analysis (Intelligence Work):")
        if successful_pro and flash_analysis_results:
            pro_summary = pro_results.get("Executive Summary", {})
            flash_summary = flash_analysis_results.get("Executive Summary", {})
            
            if pro_summary.get("success") and flash_summary:
                quality_diff = (pro_summary.get("quality", 0) - flash_summary.get("quality", 0)) / flash_summary.get("quality", 1) * 100
                cost_diff = (pro_summary.get("cost", 0) - flash_summary.get("cost", 0)) / flash_summary.get("cost", 1) * 100
                
                if quality_diff > 20:
                    print(f"   ✅ Use PRO - {quality_diff:.0f}% better quality for complex analysis")
                elif cost_diff > 200:
                    print(f"   💡 Use FLASH - Similar quality at {cost_diff:.0f}% lower cost")
                else:
                    print(f"   ⚖️ Either works - Pro is {quality_diff:.0f}% better at {cost_diff:.0f}% higher cost")
        
        print(f"\n3. Optimal Pipeline:")
        print(f"   Step 1: Flash extracts entities/relationships (${flash_cost:.4f})")
        print(f"   Step 2: Pro analyzes and generates reports (${total_pro_cost:.4f})")
        print(f"   Total cost: ${flash_cost + total_pro_cost:.4f}")
        
        print(f"\n4. Use Case Recommendations:")
        print(f"   • Bulk processing: Flash only")
        print(f"   • Executive briefings: Flash extraction → Pro analysis")
        print(f"   • Real-time monitoring: Flash only")
        print(f"   • Strategic analysis: Flash extraction → Pro synthesis")
        print(f"   • Cost-sensitive: Flash for everything")
        
        # Save complete analysis
        analysis_file = output_dir / "hybrid_strategy_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                "test_video": {
                    "url": test_url,
                    "title": title,
                    "duration": duration
                },
                "extraction_performance": {
                    "model": "flash",
                    "entities": len(entities),
                    "relationships": len(relationships),
                    "cost": flash_cost,
                    "value": flash_extraction_value
                },
                "analysis_performance": {
                    "pro_results": pro_results,
                    "flash_comparison": flash_analysis_results,
                    "total_pro_cost": total_pro_cost
                },
                "recommendation": "Use Flash for extraction, Pro for complex analysis when quality matters"
            }, f, indent=2)
        
        print(f"\n💾 Full results saved to: {output_dir}")


async def main():
    """Main entry point."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    await test_hybrid_approach()


if __name__ == "__main__":
    asyncio.run(main())
