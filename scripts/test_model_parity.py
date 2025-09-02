#!/usr/bin/env python3
"""
Model Parity Test

Tests Flash vs Pro with IDENTICAL settings to understand performance differences.
Checks if the issue is in our code or the models themselves.

Usage:
    poetry run python scripts/test_model_parity.py
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
import google.generativeai as genai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_model_parity():
    """Test both models with identical configuration."""
    
    print("=" * 80)
    print("MODEL PARITY TEST")
    print("=" * 80)
    print("Testing Flash vs Pro with IDENTICAL settings")
    print()
    
    # Configure API
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    # Define identical test prompts
    test_prompts = [
        {
            "name": "Simple Analysis",
            "prompt": "Analyze the following text and extract key points:\n\nArtificial intelligence is transforming industries worldwide. Machine learning models are becoming more sophisticated. Natural language processing enables better human-computer interaction."
        },
        {
            "name": "Entity Extraction",
            "prompt": """Extract entities from this text. Return as JSON with 'entities' array.

            Text: Microsoft announced that CEO Satya Nadella will meet with OpenAI's Sam Altman in San Francisco next Tuesday to discuss the $10 billion investment in artificial intelligence research."""
        },
        {
            "name": "Complex Reasoning",
            "prompt": "Explain the relationship between quantum computing and cryptography, including potential impacts on current encryption methods. Provide a detailed analysis."
        }
    ]
    
    # Test with different safety settings
    safety_configs = [
        {
            "name": "Default (None)",
            "settings": None
        },
        {
            "name": "Minimal Blocking",
            "settings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
        }
    ]
    
    # Test with different generation configs
    generation_configs = [
        {
            "name": "Default",
            "config": {
                "temperature": 0.3,
                "max_output_tokens": 2048
            }
        },
        {
            "name": "Low Temperature",
            "config": {
                "temperature": 0.1,
                "max_output_tokens": 2048,
                "top_p": 0.95,
                "top_k": 40
            }
        },
        {
            "name": "High Output",
            "config": {
                "temperature": 0.3,
                "max_output_tokens": 8192  # Pro might support more
            }
        }
    ]
    
    results = {}
    
    # Test each model
    for model_name in ["gemini-2.5-flash", "gemini-2.5-pro"]:
        model_key = "flash" if "flash" in model_name else "pro"
        results[model_key] = {}
        
        print(f"\n{'='*60}")
        print(f"Testing {model_key.upper()} Model")
        print('='*60)
        
        # Test with each safety config
        for safety_config in safety_configs:
            print(f"\nSafety: {safety_config['name']}")
            
            # Create model with safety settings
            if safety_config['settings']:
                model = genai.GenerativeModel(
                    model_name,
                    safety_settings=safety_config['settings']
                )
            else:
                model = genai.GenerativeModel(model_name)
            
            # Test with each generation config
            for gen_config in generation_configs:
                print(f"  Generation Config: {gen_config['name']}")
                
                config_results = []
                
                # Test each prompt
                for test_prompt in test_prompts:
                    try:
                        response = await model.generate_content_async(
                            test_prompt['prompt'],
                            generation_config=gen_config['config']
                        )
                        
                        # Check for blocked content
                        if response.candidates and response.candidates[0].finish_reason:
                            finish_reason = response.candidates[0].finish_reason
                            if finish_reason != 1:  # 1 = STOP (normal completion)
                                print(f"    ❌ {test_prompt['name']}: Blocked (reason={finish_reason})")
                                config_results.append({
                                    "prompt": test_prompt['name'],
                                    "blocked": True,
                                    "reason": finish_reason
                                })
                                continue
                        
                        result_text = response.text
                        word_count = len(result_text.split())
                        char_count = len(result_text)
                        
                        print(f"    ✅ {test_prompt['name']}: {word_count} words, {char_count} chars")
                        
                        config_results.append({
                            "prompt": test_prompt['name'],
                            "blocked": False,
                            "word_count": word_count,
                            "char_count": char_count,
                            "preview": result_text[:100]
                        })
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"    ❌ {test_prompt['name']}: Error - {error_msg[:50]}...")
                        config_results.append({
                            "prompt": test_prompt['name'],
                            "error": error_msg
                        })
                
                # Store results
                config_key = f"{safety_config['name']}_{gen_config['name']}"
                results[model_key][config_key] = config_results
    
    # Compare results
    print("\n" + "="*80)
    print("COMPARISON ANALYSIS")
    print("="*80)
    
    # Find configurations where Pro fails but Flash succeeds
    print("\n🔍 Configurations where Pro fails but Flash succeeds:")
    for config_key in results.get('flash', {}).keys():
        flash_results = results['flash'].get(config_key, [])
        pro_results = results.get('pro', {}).get(config_key, [])
        
        if flash_results and pro_results:
            flash_success = sum(1 for r in flash_results if not r.get('blocked') and not r.get('error'))
            pro_success = sum(1 for r in pro_results if not r.get('blocked') and not r.get('error'))
            
            if flash_success > pro_success:
                print(f"\n  Config: {config_key}")
                print(f"    Flash: {flash_success}/3 succeeded")
                print(f"    Pro: {pro_success}/3 succeeded")
                
                # Show which prompts failed for Pro
                for i, prompt in enumerate(test_prompts):
                    flash_r = flash_results[i] if i < len(flash_results) else {}
                    pro_r = pro_results[i] if i < len(pro_results) else {}
                    
                    if flash_r.get('word_count') and not pro_r.get('word_count'):
                        print(f"      {prompt['name']}: Pro failed (reason: {pro_r.get('reason', pro_r.get('error', 'unknown'))})")
    
    # Compare output lengths
    print("\n📊 Average output length comparison:")
    for model_key in ['flash', 'pro']:
        total_words = 0
        count = 0
        
        for config_results in results.get(model_key, {}).values():
            for result in config_results:
                if result.get('word_count'):
                    total_words += result['word_count']
                    count += 1
        
        if count > 0:
            avg_words = total_words / count
            print(f"  {model_key.upper()}: {avg_words:.0f} words average")
    
    # Check for systematic differences
    print("\n🔎 Systematic differences detected:")
    
    # Check if Pro consistently blocks more
    flash_blocks = sum(1 for config in results.get('flash', {}).values() 
                      for r in config if r.get('blocked'))
    pro_blocks = sum(1 for config in results.get('pro', {}).values() 
                     for r in config if r.get('blocked'))
    
    if pro_blocks > flash_blocks:
        print(f"  ⚠️ Pro blocks more content: {pro_blocks} vs Flash: {flash_blocks}")
    
    # Check if Pro consistently outputs less
    flash_avg_chars = []
    pro_avg_chars = []
    
    for config_key in results.get('flash', {}).keys():
        flash_chars = [r.get('char_count', 0) for r in results['flash'].get(config_key, []) if r.get('char_count')]
        pro_chars = [r.get('char_count', 0) for r in results.get('pro', {}).get(config_key, []) if r.get('char_count')]
        
        if flash_chars:
            flash_avg_chars.append(sum(flash_chars) / len(flash_chars))
        if pro_chars:
            pro_avg_chars.append(sum(pro_chars) / len(pro_chars))
    
    if flash_avg_chars and pro_avg_chars:
        flash_overall = sum(flash_avg_chars) / len(flash_avg_chars)
        pro_overall = sum(pro_avg_chars) / len(pro_avg_chars)
        
        if pro_overall < flash_overall * 0.5:
            print(f"  ⚠️ Pro outputs significantly less: {pro_overall:.0f} chars vs Flash: {flash_overall:.0f} chars")
    
    # Save detailed results
    output_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "model_parity_test.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "analysis": {
                "pro_blocks_more": pro_blocks > flash_blocks,
                "pro_outputs_less": pro_overall < flash_overall * 0.5 if flash_avg_chars and pro_avg_chars else None,
                "flash_success_rate": sum(1 for config in results.get('flash', {}).values() 
                                        for r in config if not r.get('blocked') and not r.get('error')),
                "pro_success_rate": sum(1 for config in results.get('pro', {}).values() 
                                      for r in config if not r.get('blocked') and not r.get('error'))
            }
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Final diagnosis
    print("\n" + "="*80)
    print("DIAGNOSIS")
    print("="*80)
    
    if pro_blocks > flash_blocks * 1.5:
        print("\n🔴 PRIMARY ISSUE: Pro has more aggressive safety filters")
        print("   Pro is blocking content that Flash allows through")
        print("   SOLUTION: Use more permissive safety settings for Pro")
    
    if pro_avg_chars and flash_avg_chars and pro_overall < flash_overall * 0.5:
        print("\n🔴 PRIMARY ISSUE: Pro generates much shorter outputs")
        print("   This could be due to different default max_output_tokens")
        print("   SOLUTION: Explicitly set higher max_output_tokens for Pro")
    
    flash_total = sum(1 for config in results.get('flash', {}).values() for r in config if not r.get('error'))
    pro_total = sum(1 for config in results.get('pro', {}).values() for r in config if not r.get('error'))
    
    if pro_total < flash_total * 0.8:
        print("\n🔴 PRIMARY ISSUE: Pro has higher error rate")
        print("   Pro is failing more often than Flash")
        print("   This could indicate API issues or quota problems")
    
    print("\n📋 Recommendations:")
    print("1. Set explicit max_output_tokens=8192 for Pro")
    print("2. Use BLOCK_ONLY_HIGH for all safety categories with Pro")
    print("3. Consider if your API key has different quotas for Pro")
    print("4. Test with Vertex AI to see if behavior differs")
    print("5. Monitor Google's status page for Pro model issues")


async def main():
    """Main entry point."""
    await test_model_parity()


if __name__ == "__main__":
    asyncio.run(main())
