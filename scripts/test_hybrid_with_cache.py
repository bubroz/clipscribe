#!/usr/bin/env python3
"""
Hybrid Model Strategy Test Using Cached Data

Tests Pro for analytical tasks using already extracted data.

Usage:
    poetry run python scripts/test_hybrid_with_cache.py
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_analytical_capabilities():
    """Test Pro's analytical capabilities vs Flash."""
    
    print("=" * 80)
    print("ANALYTICAL CAPABILITIES TEST")
    print("=" * 80)
    print("Testing: Pro for analysis vs Flash for extraction")
    print()
    
    import google.generativeai as genai
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Use sample data from our previous tests
    sample_transcript = """
    Hugh Mingola was born in Cam Ranh, Vietnam and started hacking at age 14-15 by stealing 
    internet dial-up accounts. This led to a $5,000 fine that his father paid. He moved to 
    Ho Chi Minh City where he discovered the dark web and learned advanced hacking techniques 
    including SQL injection. He became an administrator on Vietnamese hacking forums.
    
    At 17, he began financially motivated cybercrime, partnering with another hacker to exploit 
    e-commerce websites for credit card details. They developed a money laundering scheme called 
    "chip dumping" using online poker sites, earning thousands of USD daily. He sold over 
    100,000 stolen credit cards on the dark web at prices as low as 50 cents.
    
    Hugh moved to New Zealand to study computer science but resumed hacking due to financial 
    pressures. He used stolen cards to buy thousands of Ticketmaster concert tickets and resell 
    them, leading to a police investigation. He fled back to Vietnam to evade arrest.
    
    Around 2009, other hackers convinced Hugh to switch from credit card theft to stealing US 
    identities, claiming it was safer from law enforcement. He began targeting US data brokers 
    like LocatePlus, MicroBilt, and Court Ventures to acquire identity information.
    
    The US government charged Hugh with causing $60 million in damage through CFAA violations, 
    though the actual crimes were committed by others using the data he provided. He was not 
    charged with the actual identity theft or fraud, but with violating terms of service.
    """
    
    sample_entities = [
        {"name": "Hugh Mingola", "type": "Person", "confidence": 1.0},
        {"name": "Cam Ranh", "type": "Location", "confidence": 0.9},
        {"name": "Vietnam", "type": "Location", "confidence": 1.0},
        {"name": "Ho Chi Minh City", "type": "Location", "confidence": 1.0},
        {"name": "New Zealand", "type": "Location", "confidence": 1.0},
        {"name": "Ticketmaster", "type": "Organization", "confidence": 0.95},
        {"name": "LocatePlus", "type": "Organization", "confidence": 0.95},
        {"name": "MicroBilt", "type": "Organization", "confidence": 0.95},
        {"name": "Court Ventures", "type": "Organization", "confidence": 0.95},
        {"name": "US Secret Service", "type": "Organization", "confidence": 0.9},
        {"name": "SQL injection", "type": "Technology", "confidence": 0.9},
        {"name": "dark web", "type": "Concept", "confidence": 0.85},
        {"name": "chip dumping", "type": "Technique", "confidence": 0.85},
        {"name": "CFAA", "type": "Law", "confidence": 0.95}
    ]
    
    sample_relationships = [
        {"subject": "Hugh Mingola", "predicate": "born in", "object": "Cam Ranh"},
        {"subject": "Hugh Mingola", "predicate": "moved to", "object": "Ho Chi Minh City"},
        {"subject": "Hugh Mingola", "predicate": "fled to", "object": "Vietnam"},
        {"subject": "Hugh Mingola", "predicate": "studied in", "object": "New Zealand"},
        {"subject": "Hugh Mingola", "predicate": "targeted", "object": "LocatePlus"},
        {"subject": "Hugh Mingola", "predicate": "used", "object": "SQL injection"},
        {"subject": "Hugh Mingola", "predicate": "sold on", "object": "dark web"},
        {"subject": "US government", "predicate": "charged", "object": "Hugh Mingola"},
        {"subject": "Hugh Mingola", "predicate": "caused damage of", "object": "$60 million"}
    ]
    
    # Define analytical tasks
    analytical_tasks = [
        {
            "name": "Executive Intelligence Brief",
            "prompt": f"""
            Create an executive intelligence brief from this information.
            
            Transcript Summary:
            {sample_transcript}
            
            Key Entities: {json.dumps(sample_entities, indent=2)}
            Relationships: {json.dumps(sample_relationships, indent=2)}
            
            Provide:
            1. Executive Summary (2-3 sentences)
            2. Key Intelligence Findings (3-5 bullet points)
            3. Threat Assessment (Low/Medium/High with justification)
            4. Network Analysis (key connections and patterns)
            5. Recommended Actions (2-3 strategic recommendations)
            
            Format as a professional intelligence brief.
            """
        },
        {
            "name": "Temporal Analysis",
            "prompt": f"""
            Analyze the temporal progression and timeline from this narrative.
            
            Content: {sample_transcript}
            
            Create:
            1. Chronological timeline of key events
            2. Age/time-based progression analysis
            3. Escalation patterns over time
            4. Critical turning points
            5. Future trajectory assessment
            """
        },
        {
            "name": "Pattern Recognition",
            "prompt": f"""
            Identify patterns, methods, and techniques from this intelligence.
            
            Entities: {json.dumps(sample_entities)}
            Relationships: {json.dumps(sample_relationships)}
            
            Extract:
            1. Behavioral patterns
            2. Technical methods used
            3. Geographic patterns
            4. Financial patterns
            5. Social engineering techniques
            6. Escalation indicators
            """
        },
        {
            "name": "Risk Assessment",
            "prompt": f"""
            Perform a comprehensive risk assessment.
            
            Context: {sample_transcript[:1000]}
            
            Assess:
            1. Primary risks identified
            2. Vulnerability indicators
            3. Threat actor capabilities
            4. Impact assessment
            5. Likelihood ratings
            6. Mitigation strategies
            
            Use standard risk matrix (Impact vs Likelihood).
            """
        }
    ]
    
    # Test with both models
    results = {
        "flash": {},
        "pro": {}
    }
    
    output_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for model_name in ["gemini-2.5-flash", "gemini-2.5-pro"]:
        model_key = "flash" if "flash" in model_name else "pro"
        
        print(f"\n{'='*60}")
        print(f"Testing {model_key.upper()} Model for Analysis")
        print('='*60)
        
        model = genai.GenerativeModel(model_name)
        
        for task in analytical_tasks:
            print(f"\n📝 {task['name']}...")
            
            try:
                # Configure generation
                config = {
                    "temperature": 0.3 if model_key == "pro" else 0.2,
                    "max_output_tokens": 2048,
                    "top_p": 0.9
                }
                
                response = await model.generate_content_async(
                    task['prompt'],
                    generation_config=config
                )
                
                result_text = response.text
                
                # Quality metrics
                word_count = len(result_text.split())
                has_structure = any(marker in result_text for marker in ["1.", "•", "-", "##"])
                has_analysis = any(term in result_text.lower() for term in 
                                 ["analysis", "assessment", "risk", "pattern", "finding"])
                completeness = min(word_count / 200, 1.0)  # Expect at least 200 words
                
                quality_score = (
                    completeness * 0.4 +
                    (1.0 if has_structure else 0) * 0.3 +
                    (1.0 if has_analysis else 0) * 0.3
                )
                
                print(f"   ✅ Generated {word_count} words")
                print(f"   Structure: {'Yes' if has_structure else 'No'}")
                print(f"   Analysis depth: {'Yes' if has_analysis else 'No'}")
                print(f"   Quality score: {quality_score:.2f}/1.0")
                
                # Save output
                task_file = output_dir / f"{model_key}_{task['name'].lower().replace(' ', '_')}.txt"
                with open(task_file, 'w') as f:
                    f.write(f"Model: {model_name}\n")
                    f.write(f"Task: {task['name']}\n")
                    f.write(f"Quality Score: {quality_score:.2f}\n")
                    f.write(f"Word Count: {word_count}\n")
                    f.write("\n" + "="*60 + "\n\n")
                    f.write(result_text)
                
                # Show preview
                preview_lines = result_text.split('\n')[:5]
                print(f"   Preview:\n     " + "\n     ".join(preview_lines))
                
                results[model_key][task['name']] = {
                    "word_count": word_count,
                    "quality_score": quality_score,
                    "has_structure": has_structure,
                    "has_analysis": has_analysis
                }
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[model_key][task['name']] = {"error": str(e)}
    
    # COMPARISON
    print("\n" + "="*80)
    print("MODEL COMPARISON FOR ANALYTICAL TASKS")
    print("="*80)
    
    # Calculate averages
    for model_key in ["flash", "pro"]:
        successful = [v for v in results[model_key].values() if "quality_score" in v]
        
        if successful:
            avg_quality = sum(v["quality_score"] for v in successful) / len(successful)
            avg_words = sum(v["word_count"] for v in successful) / len(successful)
            
            print(f"\n{model_key.upper()} Model:")
            print(f"  Average quality score: {avg_quality:.2f}/1.0")
            print(f"  Average word count: {avg_words:.0f}")
            print(f"  Success rate: {len(successful)}/{len(analytical_tasks)}")
            
            print(f"\n  Task Performance:")
            for task_name, result in results[model_key].items():
                if "quality_score" in result:
                    print(f"    {task_name}: {result['quality_score']:.2f} ({result['word_count']} words)")
    
    # Direct comparison
    print("\n" + "="*60)
    print("HEAD-TO-HEAD COMPARISON")
    print("="*60)
    
    for task in analytical_tasks:
        task_name = task['name']
        flash_result = results['flash'].get(task_name, {})
        pro_result = results['pro'].get(task_name, {})
        
        if "quality_score" in flash_result and "quality_score" in pro_result:
            flash_score = flash_result['quality_score']
            pro_score = pro_result['quality_score']
            
            diff = pro_score - flash_score
            winner = "Pro" if diff > 0.1 else ("Flash" if diff < -0.1 else "Tie")
            
            print(f"\n{task_name}:")
            print(f"  Flash: {flash_score:.2f}")
            print(f"  Pro: {pro_score:.2f}")
            print(f"  Winner: {winner} ({diff:+.2f})")
    
    # FINAL RECOMMENDATION
    print("\n" + "="*80)
    print("HYBRID STRATEGY RECOMMENDATION")
    print("="*80)
    
    flash_avg = sum(v.get("quality_score", 0) for v in results['flash'].values()) / len(analytical_tasks)
    pro_avg = sum(v.get("quality_score", 0) for v in results['pro'].values()) / len(analytical_tasks)
    
    print("\n📊 Based on analytical task testing:")
    
    if pro_avg > flash_avg + 0.15:
        print("\n✅ CONFIRMED: Use hybrid approach")
        print("   • Flash for extraction (entities, relationships)")
        print("   • Pro for analysis (briefs, assessments, reports)")
        print(f"   • Pro shows {(pro_avg - flash_avg)/flash_avg*100:.0f}% better analytical quality")
    elif flash_avg > pro_avg + 0.05:
        print("\n⚠️ SURPRISING: Flash performs better at analysis too!")
        print("   • Use Flash for both extraction AND analysis")
        print(f"   • Flash shows {(flash_avg - pro_avg)/pro_avg*100:.0f}% better quality")
        print("   • Pro model may have issues - needs investigation")
    else:
        print("\n🤝 NEUTRAL: Similar analytical performance")
        print("   • Use Flash for everything (cost-effective)")
        print("   • Reserve Pro for special high-stakes analysis")
        print(f"   • Quality difference: {abs(pro_avg - flash_avg)*100:.0f}%")
    
    print("\n💰 Cost Implications:")
    print(f"   Flash: ~$0.002/1k tokens (5x cheaper)")
    print(f"   Pro: ~$0.01/1k tokens")
    print(f"   Recommendation: Default to Flash unless Pro shows clear value")
    
    # Save complete analysis
    analysis_file = output_dir / "analytical_comparison.json"
    with open(analysis_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "averages": {
                "flash": flash_avg,
                "pro": pro_avg
            },
            "recommendation": "Hybrid" if pro_avg > flash_avg + 0.15 else "Flash-only"
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_dir}")
    
    return results


async def main():
    """Main entry point."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    await test_analytical_capabilities()


if __name__ == "__main__":
    asyncio.run(main())
