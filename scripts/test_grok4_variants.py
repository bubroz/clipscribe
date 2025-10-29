#!/usr/bin/env python3
"""
Test Grok-4 model variants to find the best for entity extraction.
"""

import httpx
import os
import json
from datetime import datetime

def test_grok4_variants():
    """Test different Grok-4 model variants."""
    
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("❌ XAI_API_KEY not set")
        return
    
    api_key = api_key.strip('"').strip("'")
    
    print("=" * 80)
    print("GROK-4 MODEL VARIANTS TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test different Grok-4 variants based on xAI docs
    models_to_test = [
        "grok-4-0709",           # Original Grok-4 (what we use in local)
        "grok-4-fast",           # Potential fast variant
        "grok-4-fast-reasoning", # User mentioned this
        "grok-4-reasoning",      # Potential reasoning variant
        "grok-4-latest",         # Potential latest
    ]
    
    base_url = "https://api.x.ai/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test prompt
    test_prompt = """Extract entities from this transcript:
    
    "President Biden met with Elon Musk at the White House to discuss Tesla's new factory in Texas. 
    They agreed on a $50 billion investment plan for clean energy infrastructure."
    
    Return JSON with entities and their types."""
    
    results = []
    
    print("\nTesting model variants...\n")
    
    for model_id in models_to_test:
        try:
            with httpx.Client(timeout=20) as client:
                response = client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": "Extract entities. Return JSON."},
                            {"role": "user", "content": test_prompt}
                        ],
                        "max_tokens": 500,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    usage = result.get("usage", {})
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    print(f"✅ {model_id:25} AVAILABLE")
                    print(f"   Tokens: {usage.get('total_tokens', 'N/A')} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")
                    print(f"   Response length: {len(content)} chars")
                    
                    # Try to parse response
                    try:
                        parsed = json.loads(content)
                        entity_count = len(parsed.get('entities', []))
                        print(f"   Entities extracted: {entity_count}")
                    except:
                        print(f"   Response: {content[:100]}...")
                    
                    results.append({
                        "model": model_id,
                        "status": "available",
                        "tokens": usage.get('total_tokens', 0)
                    })
                    
                elif response.status_code == 404 or "not found" in response.text.lower() or "deprecated" in response.text.lower():
                    print(f"❌ {model_id:25} NOT AVAILABLE")
                    print(f"   Response: {response.text[:150]}")
                    
                    results.append({
                        "model": model_id,
                        "status": "not_found",
                        "error": response.text[:200]
                    })
                    
                else:
                    print(f"⚠️  {model_id:25} ERROR: {response.status_code}")
                    print(f"   Response: {response.text[:150]}")
                    
                    results.append({
                        "model": model_id,
                        "status": "error",
                        "error": f"{response.status_code}: {response.text[:200]}"
                    })
                    
        except Exception as e:
            print(f"❌ {model_id:25} EXCEPTION: {str(e)[:100]}")
            results.append({
                "model": model_id,
                "status": "exception",
                "error": str(e)[:200]
            })
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY & RECOMMENDATION")
    print("=" * 80)
    
    available = [r for r in results if r["status"] == "available"]
    
    print(f"\n✅ Available Grok-4 variants: {len(available)}")
    for r in available:
        print(f"   - {r['model']}")
    
    if len(available) > 1:
        print("\n💡 RECOMMENDATION:")
        print("   Test quality/speed of each variant to choose best")
        print("   Likely: grok-4-fast-reasoning if available (optimized for our use case)")
    elif len(available) == 1:
        print(f"\n💡 RECOMMENDATION: Use {available[0]['model']}")
    else:
        print("\n❌ NO GROK-4 VARIANTS AVAILABLE")
    
    # Save results
    with open("grok4_variants_test_results.json", 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Results saved: grok4_variants_test_results.json")

if __name__ == "__main__":
    test_grok4_variants()
