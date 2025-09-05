#!/usr/bin/env python3
"""
Test which Grok models are actually available via x.ai API.
This is Gate 1 of our circuit breaker approach.
"""

import asyncio
import os
import httpx
import json
from datetime import datetime

async def test_grok_models():
    """Test all potential Grok models via x.ai API."""
    
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("❌ XAI_API_KEY not set")
        return
    
    # Remove quotes if present
    api_key = api_key.strip('"').strip("'")
    
    print("="*80)
    print("GROK MODEL AVAILABILITY TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    # Models to test (based on research)
    models_to_test = [
        "grok-2-latest",      # Confirmed in previous test
        "grok-2-1212",        # December 2024 release
        "grok-2",             # Base model
        "grok-4",             # Potential Grok-4
        "grok-4-latest",      # Potential latest
        "grok-beta",          # Beta version
    ]
    
    base_url = "https://api.x.ai/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    available_models = []
    
    print("\n🔍 Testing model availability...\n")
    
    async with httpx.AsyncClient(timeout=30) as client:
        # First, try to list models if endpoint exists
        try:
            response = await client.get(f"{base_url}/models", headers=headers)
            if response.status_code == 200:
                models_data = response.json()
                print("✅ Found models endpoint:")
                print(json.dumps(models_data, indent=2))
                print("\n" + "-"*80 + "\n")
        except:
            print("ℹ️  No /models endpoint available\n")
        
        # Test each model with a simple prompt
        for model in models_to_test:
            print(f"Testing {model}...")
            
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "Say 'Hello' and nothing else"}
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        
                        # Extract model info
                        model_used = result.get("model", model) if isinstance(result, dict) else model
                        usage = result.get("usage", {}) if isinstance(result, dict) else {}
                        
                        print(f"  ✅ {model} AVAILABLE")
                        print(f"     Model ID: {model_used}")
                        print(f"     Input cost: ${usage.get('prompt_tokens', 0) * 0.000003:.6f}")
                    except Exception as e:
                        print(f"  ✅ {model} returned 200 but parsing failed: {e}")
                        print(f"     Response: {response.text[:200]}")
                    
                    available_models.append({
                        "requested": model,
                        "actual": model_used,
                        "working": True
                    })
                    
                elif response.status_code == 404:
                    print(f"  ❌ {model} - Model not found")
                    
                elif response.status_code == 400:
                    try:
                        error = response.json()
                        if isinstance(error, dict):
                            print(f"  ❌ {model} - Bad request: {error.get('error', {}).get('message', 'Unknown')}")
                        else:
                            print(f"  ❌ {model} - Bad request: {error}")
                    except:
                        print(f"  ❌ {model} - Bad request: {response.text}")
                    
                else:
                    print(f"  ❌ {model} - HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {model} - Error: {e}")
            
            print()
    
    # Test advanced features
    if available_models:
        print("\n" + "="*80)
        print("TESTING ADVANCED FEATURES")
        print("="*80)
        
        # Use first available model
        test_model = available_models[0]["actual"]
        print(f"\nUsing {test_model} for feature tests...\n")
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Test 1: JSON mode
            print("1. Testing JSON response format...")
            data = {
                "model": test_model,
                "messages": [
                    {"role": "user", "content": 'Return JSON: {"status": "working"}'}
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 50
            }
            
            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                if response.status_code == 200:
                    print("   ✅ JSON mode supported")
                else:
                    print("   ❌ JSON mode not supported")
            except:
                print("   ❌ JSON mode failed")
            
            # Test 2: Web search
            print("\n2. Testing web search capability...")
            data = {
                "model": test_model,
                "messages": [
                    {"role": "user", "content": "Search the web for: latest news today"}
                ],
                "tools": [{"type": "web_search"}],
                "max_tokens": 100
            }
            
            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                if response.status_code == 200:
                    result = response.json()
                    if "tool_calls" in str(result) or "search" in str(result).lower():
                        print("   ✅ Web search available")
                    else:
                        print("   ⚠️  Web search may not be available via API")
                else:
                    print("   ❌ Web search not supported")
            except:
                print("   ❌ Web search test failed")
            
            # Test 3: Context window
            print("\n3. Testing context window size...")
            
            # Create a long prompt (approx 10k tokens)
            long_text = "The quick brown fox jumps over the lazy dog. " * 1000
            
            data = {
                "model": test_model,
                "messages": [
                    {"role": "user", "content": f"Summarize this in 5 words: {long_text}"}
                ],
                "max_tokens": 20
            }
            
            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                if response.status_code == 200:
                    print("   ✅ Handles 10k+ token inputs")
                else:
                    print("   ⚠️  May have context limitations")
            except:
                print("   ❌ Large context test failed")
    
    # Summary
    print("\n" + "="*80)
    print("GATE 1 ASSESSMENT: Model Availability")
    print("="*80)
    
    if available_models:
        print(f"\n✅ GATE 1 PASSED: {len(available_models)} model(s) available")
        print("\nAvailable models:")
        for m in available_models:
            print(f"  • {m['actual']}")
        
        print("\n📊 Pricing (estimated):")
        print("  • Input: $3.00 per million tokens")
        print("  • Output: $15.00 per million tokens")
        print("  • Cost per minute of video: ~$0.004")
        
        print("\n🎯 RECOMMENDATION: Proceed to Gate 2 (Quality Testing)")
        
    else:
        print("\n❌ GATE 1 FAILED: No Grok models accessible")
        print("\n🔄 FALLBACK OPTIONS:")
        print("  1. Check API key permissions")
        print("  2. Consider Mixtral via Mistral API")
        print("  3. Explore OpenRouter for access")


if __name__ == "__main__":
    asyncio.run(test_grok_models())
