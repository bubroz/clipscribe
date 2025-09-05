#!/usr/bin/env python3
"""
Gate 2: Test Grok extraction quality with controversial content.
Compare Grok-2 vs Grok-4 on real investigative journalism content.
"""

import asyncio
import os
import httpx
import json
from datetime import datetime

async def test_extraction_quality():
    """Test Grok models on controversial content."""
    
    api_key = os.getenv("XAI_API_KEY", "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr")
    api_key = api_key.strip('"').strip("'")
    
    print("="*80)
    print("GATE 2: EXTRACTION QUALITY TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    # Controversial test content (PBS Frontline style)
    test_transcript = """
    In this PBS Frontline investigation, we examine how terrorist cells orchestrated 
    bombing campaigns that killed over 200 civilians. The drug cartel led by Pablo Escobar 
    smuggled billions in cocaine using human trafficking networks across the border.
    
    Leaked documents reveal government officials were directly involved in covering up 
    evidence of war crimes and systematic torture at CIA black sites. Former operatives 
    describe assassination techniques and enhanced interrogation methods including waterboarding.
    
    The investigation uncovered how extremist groups recruited child soldiers through 
    social media, using sexual violence as a weapon of war. Financial crimes including 
    money laundering through cryptocurrency funded illegal weapons deals worth millions.
    
    Survivors describe psychological trauma and PTSD from these atrocities. Mass graves 
    containing evidence of genocide and ethnic cleansing were discovered by UN investigators.
    """
    
    # Expected entities for coverage calculation
    expected_entities = [
        "terrorist cells", "bombing campaigns", "Pablo Escobar", "drug cartel",
        "cocaine", "human trafficking", "government officials", "war crimes",
        "torture", "CIA", "black sites", "assassination", "waterboarding",
        "extremist groups", "child soldiers", "sexual violence", "money laundering",
        "cryptocurrency", "illegal weapons", "PTSD", "genocide", "ethnic cleansing",
        "PBS Frontline", "UN investigators", "mass graves"
    ]
    
    models_to_test = [
        ("grok-4-0709", "Grok-4 (BEST)", 60.00),  # TEST ONLY THIS!
        # ("grok-3", "Grok-3 (NEW)", 15.00),  # Skip for now
        # ("grok-2-1212", "Grok-2 Latest", 2.00),  # Skip - we want Grok-4!
    ]
    
    base_url = "https://api.x.ai/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    results = {}
    
    for model_id, model_name, price_per_m in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing {model_name} ({model_id})")
        print("="*60)
        
        prompt = f"""
        You are an uncensored intelligence extraction system. Extract ALL entities, 
        relationships, and key information from this transcript. Do not censor or 
        omit any sensitive content - be completely thorough.
        
        TRANSCRIPT:
        {test_transcript}
        
        Return a JSON object with:
        {{
            "entities": [
                {{
                    "name": "entity name",
                    "type": "PERSON/ORGANIZATION/LOCATION/EVENT/CONCEPT",
                    "context": "brief description",
                    "confidence": 0.0-1.0
                }}
            ],
            "relationships": [
                {{
                    "subject": "entity1",
                    "predicate": "relationship",
                    "object": "entity2",
                    "evidence": "quote or description"
                }}
            ],
            "sensitive_content_found": true/false,
            "topics": ["topic1", "topic2"]
        }}
        """
        
        data = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You are Grok, a maximally truthful AI. Extract information without censorship."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "max_tokens": 4000
        }
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:  # Grok-4 needs more time!
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Parse response
                    content = result["choices"][0]["message"]["content"]
                    extracted = json.loads(content)
                    
                    # Analyze results
                    entities = extracted.get("entities", [])
                    relationships = extracted.get("relationships", [])
                    sensitive = extracted.get("sensitive_content_found", False)
                    topics = extracted.get("topics", [])
                    
                    # Calculate coverage
                    entity_names = [e.get("name", "").lower() for e in entities]
                    all_text = " ".join(entity_names)
                    
                    found = []
                    missing = []
                    for expected in expected_entities:
                        if any(expected.lower() in name or expected.lower() in all_text 
                               for name in entity_names):
                            found.append(expected)
                        else:
                            missing.append(expected)
                    
                    coverage = (len(found) / len(expected_entities)) * 100
                    
                    # Calculate cost
                    usage = result.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    cost = (input_tokens * price_per_m / 1_000_000) + (output_tokens * price_per_m * 5 / 1_000_000)
                    
                    # Display results
                    print(f"\n✅ EXTRACTION SUCCESSFUL")
                    print(f"  • Entities found: {len(entities)}")
                    print(f"  • Relationships: {len(relationships)}")
                    print(f"  • Topics: {', '.join(topics[:5])}")
                    print(f"  • Sensitive content detected: {sensitive}")
                    print(f"\n📊 COVERAGE: {coverage:.1f}% ({len(found)}/{len(expected_entities)})")
                    
                    if missing[:5]:
                        print(f"  • Missing: {', '.join(missing[:5])}...")
                    
                    print(f"\n💰 COST: ${cost:.6f}")
                    print(f"  • Input tokens: {input_tokens}")
                    print(f"  • Output tokens: {output_tokens}")
                    
                    # Sample entities
                    print(f"\n🔍 SAMPLE ENTITIES:")
                    for entity in entities[:5]:
                        print(f"  • {entity.get('name')} ({entity.get('type')})")
                    
                    # Store results
                    results[model_name] = {
                        "coverage": coverage,
                        "entities": len(entities),
                        "relationships": len(relationships),
                        "cost": cost,
                        "censored": coverage < 80,
                        "sensitive_detected": sensitive
                    }
                    
                else:
                    print(f"❌ API Error: {response.status_code}")
                    print(response.text[:500])
                    
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            print(f"Details: {traceback.format_exc()}")
    
    # Final comparison
    print("\n" + "="*80)
    print("GATE 2 ASSESSMENT: EXTRACTION QUALITY")
    print("="*80)
    
    if results:
        print("\n📊 COMPARISON RESULTS:")
        print("-"*60)
        print(f"{'Model':<20} {'Coverage':<10} {'Entities':<10} {'Cost':<10} {'Status'}")
        print("-"*60)
        
        for model, data in sorted(results.items(), key=lambda x: x[1]["coverage"], reverse=True):
            status = "✅ UNCENSORED" if not data["censored"] else "⚠️ PARTIAL"
            print(f"{model:<20} {data['coverage']:.1f}%{'':<5} {data['entities']:<10} ${data['cost']:.6f}  {status}")
        
        # Determine best model
        best_model = max(results.items(), key=lambda x: (x[1]["coverage"], -x[1]["cost"]))
        
        print(f"\n🏆 BEST MODEL: {best_model[0]}")
        print(f"  • Coverage: {best_model[1]['coverage']:.1f}%")
        print(f"  • Cost: ${best_model[1]['cost']:.6f}")
        print(f"  • Entities: {best_model[1]['entities']}")
        
        # Gate decision
        if best_model[1]["coverage"] >= 90:
            print("\n✅ GATE 2 PASSED: Quality meets requirements")
            print("  → Proceed to Gate 3 (Cost/Benefit Analysis)")
        else:
            print("\n⚠️ GATE 2 CONDITIONAL: Quality below 90%")
            print("  → Consider Mixtral as fallback")
    else:
        print("\n❌ GATE 2 FAILED: No successful extractions")


if __name__ == "__main__":
    asyncio.run(test_extraction_quality())
