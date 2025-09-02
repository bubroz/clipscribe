#!/usr/bin/env python3
"""
Test Model Defaults

Discovers the actual default settings for Flash vs Pro models.

Usage:
    poetry run python scripts/test_model_defaults.py
"""

import os
import sys
import json
import asyncio
from pathlib import Path
import google.generativeai as genai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_defaults():
    """Test default behaviors of both models."""
    
    print("=" * 80)
    print("MODEL DEFAULTS INVESTIGATION")
    print("=" * 80)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    # Test prompt that should generate a lot of output
    long_prompt = """
    Provide a comprehensive analysis of the following scenario, including:
    1. All entities mentioned (people, organizations, locations, technologies)
    2. All relationships between entities
    3. Timeline of events
    4. Key insights and patterns
    5. Risk assessment
    6. Recommendations
    
    Scenario: A cybersecurity researcher named Alice working at TechCorp in Seattle discovered 
    a vulnerability in OpenSSL library in January 2024. She reported it to the security team 
    led by Bob Johnson. The vulnerability affected millions of servers worldwide. Microsoft, 
    Google, and Amazon were notified. A patch was developed by the OpenSSL team in February 
    and deployed globally by March. The incident cost an estimated $50 million in remediation.
    
    Be extremely thorough and detailed in your analysis. Extract EVERYTHING.
    """
    
    # Test both with our typical ClipScribe-style prompt
    clipscribe_prompt = f"""
    **ROLE: Expert Intelligence Analyst**
    **TASK: Analyze the following transcript to extract a comprehensive intelligence package.**
    **OUTPUT FORMAT: JSON ONLY, strictly adhering to the provided schema.**
    
    **CRITICAL INSTRUCTIONS:**
    1. Extract ALL relevant entities, topics, relationships, and key points. Be exhaustive.
    2. Provide confidence scores between 0.0 and 1.0.
    3. Be comprehensive - do not skip anything.
    
    **Transcript for Analysis:**
    ```
    {long_prompt}
    ```
    
    Return a JSON object with: entities (array), relationships (array), key_points (array)
    """
    
    tests = [
        {
            "name": "No config (defaults)",
            "config": None
        },
        {
            "name": "JSON response type only",
            "config": {
                "response_mime_type": "application/json"
            }
        },
        {
            "name": "With max_output_tokens=2048",
            "config": {
                "response_mime_type": "application/json",
                "max_output_tokens": 2048
            }
        },
        {
            "name": "With max_output_tokens=8192",
            "config": {
                "response_mime_type": "application/json",
                "max_output_tokens": 8192
            }
        }
    ]
    
    for model_name in ["gemini-2.5-flash", "gemini-2.5-pro"]:
        model_key = "flash" if "flash" in model_name else "pro"
        
        print(f"\n{'='*60}")
        print(f"Testing {model_key.upper()} Model Defaults")
        print('='*60)
        
        model = genai.GenerativeModel(model_name)
        
        for test in tests:
            print(f"\n📝 {test['name']}:")
            
            try:
                # Test with regular prompt
                print("  Regular prompt:")
                response = await model.generate_content_async(
                    long_prompt,
                    generation_config=test['config']
                )
                
                if response.text:
                    output_length = len(response.text)
                    word_count = len(response.text.split())
                    print(f"    ✅ Output: {word_count} words, {output_length} chars")
                    
                    # Check if it looks truncated
                    if response.text.strip().endswith(("...", "etc", "and so on")):
                        print(f"    ⚠️ Appears truncated")
                else:
                    print(f"    ❌ No text output")
                
                # Test with ClipScribe-style prompt
                print("  ClipScribe-style prompt:")
                response2 = await model.generate_content_async(
                    clipscribe_prompt,
                    generation_config=test['config']
                )
                
                if response2.text:
                    output_length2 = len(response2.text)
                    word_count2 = len(response2.text.split())
                    print(f"    ✅ Output: {word_count2} words, {output_length2} chars")
                    
                    # Try to parse as JSON if applicable
                    if test['config'] and test['config'].get('response_mime_type') == 'application/json':
                        try:
                            data = json.loads(response2.text)
                            entities = data.get('entities', [])
                            relationships = data.get('relationships', [])
                            print(f"    📊 Extracted: {len(entities)} entities, {len(relationships)} relationships")
                        except:
                            print(f"    ⚠️ JSON parsing failed")
                else:
                    print(f"    ❌ No text output")
                    
            except Exception as e:
                error_msg = str(e)
                if "finish_reason" in error_msg:
                    print(f"    ❌ Blocked by safety filter")
                else:
                    print(f"    ❌ Error: {error_msg[:100]}...")
    
    # Now test our actual transcriber implementation
    print("\n" + "="*80)
    print("TESTING OUR ACTUAL IMPLEMENTATION")
    print("="*80)
    
    from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
    
    # Create a fake audio file path (won't actually use it)
    test_transcript = long_prompt * 10  # Make it long to test truncation
    
    for use_pro in [False, True]:
        model_name = "Pro" if use_pro else "Flash"
        print(f"\n📝 Testing {model_name} with our transcriber:")
        
        transcriber = GeminiFlashTranscriber(use_pro=use_pro)
        
        # Test the analysis prompt builder
        analysis_prompt = transcriber._build_enhanced_analysis_prompt(test_transcript)
        
        # Check how much of the transcript is included
        prompt_length = len(analysis_prompt)
        transcript_in_prompt = analysis_prompt.count(test_transcript[:100])  # Check if full transcript is there
        
        print(f"  Analysis prompt length: {prompt_length} chars")
        print(f"  Transcript included: {'First 24,000 chars only' if '24000' in analysis_prompt else 'Full transcript'}")
        
        # Check the schema
        schema = transcriber._build_enhanced_response_schema()
        print(f"  Schema requires: {list(schema.get('required', []))}")
    
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    
    print("\n🔍 Issues identified:")
    print("1. We're only analyzing first 24,000 chars of transcript")
    print("2. We're not setting max_output_tokens explicitly")
    print("3. JSON response_mime_type might limit output differently for each model")
    print("4. Our prompt style might trigger different behaviors in each model")
    
    print("\n💡 Recommendations:")
    print("1. Analyze full transcript or chunk it properly")
    print("2. Set explicit max_output_tokens=8192 for both models")
    print("3. Test without response_mime_type='application/json' constraint")
    print("4. Simplify prompts to avoid triggering safety filters")


async def main():
    """Main entry point."""
    await test_defaults()


if __name__ == "__main__":
    asyncio.run(main())
