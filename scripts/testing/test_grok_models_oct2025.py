#!/usr/bin/env python3
"""
Test Grok model availability as of October 2025.
Verify which models work and which should we use.
"""

import httpx
import os
import json
from datetime import datetime

def test_grok_models():
    """Test all potential Grok models."""
    
    # Get API key from environment
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("❌ XAI_API_KEY not set in environment")
        print("Set it in .env.production or .env")
        return
    
    api_key = api_key.strip('"').strip("'")
    
    print("=" * 80)
    print("GROK MODEL AVAILABILITY TEST - October 2025")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Models to test (November 2025)
    models_to_test = [
        ("grok-4-1-fast-reasoning", "Grok 4 Fast (Reasoning) - PRODUCTION"),
        ("grok-4-1-fast-non-reasoning", "Grok 4 Fast (Non-Reasoning)"),
        ("grok-4-1-fast", "Grok 4 Fast (Alias for reasoning)"),
        ("grok-4-1-fast-reasoning-latest", "Grok 4 Fast Reasoning (Latest)"),
        ("grok-vision-beta", "Grok Vision Beta"),
    ]
    
    base_url = "https://api.x.ai/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    results = []
    
    print("\nTesting model availability...\n")
    
    for model_id, model_name in models_to_test:
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model_id,
                        "messages": [
                            {"role": "user", "content": "Extract entities from this: 'Joe Biden met with Elon Musk at the White House.'"}
                        ],
                        "max_tokens": 100,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    usage = result.get("usage", {})
                    
                    print(f"✅ {model_id:20} AVAILABLE")
                    print(f"   Name: {model_name}")
                    print(f"   Tokens: {usage.get('total_tokens', 'N/A')}")
                    
                    results.append({
                        "model": model_id,
                        "status": "available",
                        "name": model_name
                    })
                    
                elif response.status_code == 404 or "not found" in response.text.lower() or "deprecated" in response.text.lower():
                    print(f"❌ {model_id:20} NOT AVAILABLE / DEPRECATED")
                    print(f"   Response: {response.text[:100]}")
                    
                    results.append({
                        "model": model_id,
                        "status": "not_found",
                        "name": model_name,
                        "error": response.text[:200]
                    })
                    
                else:
                    print(f"⚠️  {model_id:20} ERROR: {response.status_code}")
                    print(f"   Response: {response.text[:150]}")
                    
                    results.append({
                        "model": model_id,
                        "status": "error",
                        "name": model_name,
                        "error": f"{response.status_code}: {response.text[:200]}"
                    })
                    
        except httpx.TimeoutException:
            print(f"⏱️  {model_id:20} TIMEOUT (took >15s)")
            results.append({
                "model": model_id,
                "status": "timeout",
                "name": model_name
            })
            
        except Exception as e:
            print(f"❌ {model_id:20} EXCEPTION: {str(e)[:100]}")
            results.append({
                "model": model_id,
                "status": "exception",
                "name": model_name,
                "error": str(e)[:200]
            })
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    available = [r for r in results if r["status"] == "available"]
    deprecated = [r for r in results if r["status"] == "not_found"]
    errors = [r for r in results if r["status"] not in ["available", "not_found"]]
    
    print(f"\n✅ Available models: {len(available)}")
    for r in available:
        print(f"   - {r['model']}")
    
    if deprecated:
        print(f"\n❌ Deprecated/Not Found: {len(deprecated)}")
        for r in deprecated:
            print(f"   - {r['model']}")
    
    if errors:
        print(f"\n⚠️  Errors: {len(errors)}")
        for r in errors:
            print(f"   - {r['model']}: {r['status']}")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if any(r["model"] == "grok-4-1-fast-reasoning" for r in available):
        print("\n✅ USE grok-4-1-fast-reasoning")
        print("   - Grok 4 Fast with reasoning is available")
        print("   - PRODUCTION MODEL")
        print("   - Superior quality (96% coverage validated)")
        print("   - Higher cost ($60/M vs $2/M) but worth it")
        
    elif any(r["model"] == "grok-4-1-fast-non-reasoning" for r in available):
        print("\n⚠️  FALLBACK: grok-4-1-fast-non-reasoning")
        print("   - Grok 4 Fast reasoning not available")
        print("   - Use non-reasoning variant")
        print("   - UPDATE local ClipScribe to match")
        
    else:
        print("\n❌ NO GROK 4 MODELS AVAILABLE")
        print("   - Contact xAI support")
        print("   - Check API key permissions")
        print("   - Cost-effective")
    else:
        print("\n❌ NO GROK MODELS AVAILABLE")
        print("   - Major issue, investigate API access")
    
    print("\n" + "=" * 80)
    
    # Save results
    output_file = "grok_model_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "available": len(available),
                "deprecated": len(deprecated),
                "errors": len(errors)
            }
        }, f, indent=2)
    
    print(f"\n📄 Results saved: {output_file}")

if __name__ == "__main__":
    test_grok_models()

