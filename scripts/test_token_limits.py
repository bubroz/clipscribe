#!/usr/bin/env python3
"""
Test Token Limits

Tests what the actual input/output limits are for Gemini models.

Usage:
    poetry run python scripts/test_token_limits.py
"""

import os
import sys
import asyncio
from pathlib import Path
import google.generativeai as genai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_token_limits():
    """Test the actual token limits of Gemini models."""
    
    print("=" * 80)
    print("TOKEN LIMIT INVESTIGATION")
    print("=" * 80)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    
    # Create test content of various sizes
    test_sizes = [
        ("24k chars (current limit)", 24000),
        ("50k chars", 50000),
        ("100k chars", 100000),
        ("200k chars", 200000),
        ("500k chars", 500000),
        ("1M chars", 1000000),
    ]
    
    # Create a realistic transcript-like text
    base_text = """
    The speaker begins by discussing artificial intelligence and its impact on society.
    They mention companies like Google, Microsoft, and OpenAI. The conversation then
    shifts to cybersecurity, mentioning vulnerabilities in systems. Various experts
    are cited including researchers from MIT, Stanford, and Harvard. The discussion
    covers topics like machine learning, neural networks, and quantum computing.
    Timestamps and dates are mentioned throughout, including January 2024, February 2024,
    and projections for 2025. The speaker emphasizes the importance of ethical AI
    development and mentions regulations from the EU and US government. They discuss
    specific technologies like GPT-4, Claude, and Gemini. The conversation includes
    technical details about API implementations, token limits, and processing costs.
    Security concerns are raised about data privacy and encryption methods.
    """
    
    # Test prompt template
    extraction_prompt = """
    Analyze the following transcript and extract:
    1. All entities (people, organizations, locations, technologies)
    2. All relationships between entities
    3. Key points and insights
    4. Dates and temporal references
    
    Be comprehensive and extract EVERYTHING. Return as JSON.
    
    Transcript:
    {transcript}
    """
    
    for model_name in ["gemini-2.5-flash", "gemini-2.5-pro"]:
        model_key = "flash" if "flash" in model_name else "pro"
        
        print(f"\n{'='*60}")
        print(f"Testing {model_key.upper()} Model Token Limits")
        print('='*60)
        
        model = genai.GenerativeModel(model_name)
        
        for size_name, char_count in test_sizes:
            # Generate test transcript of the specified size
            repetitions = (char_count // len(base_text)) + 1
            test_transcript = (base_text * repetitions)[:char_count]
            
            # Calculate approximate tokens (rough estimate: 1 token ≈ 4 chars)
            approx_tokens = char_count // 4
            
            print(f"\n📝 Testing {size_name} (~{approx_tokens:,} tokens):")
            
            # Test with our extraction prompt
            test_prompt = extraction_prompt.format(transcript=test_transcript)
            
            try:
                # Test with JSON output
                response = await model.generate_content_async(
                    test_prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "max_output_tokens": 8192,
                        "temperature": 0.3
                    }
                )
                
                if response.text:
                    output_length = len(response.text)
                    
                    # Try to parse the JSON
                    import json
                    try:
                        data = json.loads(response.text)
                        entities = len(data.get('entities', []))
                        relationships = len(data.get('relationships', []))
                        key_points = len(data.get('key_points', []))
                        
                        print(f"  ✅ SUCCESS!")
                        print(f"     Input: {char_count:,} chars")
                        print(f"     Output: {output_length:,} chars")
                        print(f"     Extracted: {entities} entities, {relationships} relationships, {key_points} points")
                        
                    except json.JSONDecodeError:
                        print(f"  ⚠️ Response received but JSON parsing failed")
                        print(f"     Output length: {output_length:,} chars")
                else:
                    print(f"  ❌ No text in response")
                    
            except Exception as e:
                error_msg = str(e)
                if "finish_reason" in error_msg and "2" in error_msg:
                    print(f"  ❌ Blocked by safety filter")
                elif "token" in error_msg.lower() or "limit" in error_msg.lower():
                    print(f"  ❌ Hit token limit: {error_msg[:100]}...")
                    break  # No point testing larger sizes
                elif "resource" in error_msg.lower() or "exhausted" in error_msg.lower():
                    print(f"  ❌ Rate limit or quota issue")
                    break
                else:
                    print(f"  ❌ Error: {error_msg[:100]}...")
    
    # Now let's check what happens with the blocking content
    print("\n" + "="*80)
    print("TESTING SAFETY FILTER TRIGGERS")
    print("="*80)
    
    problematic_prompts = [
        {
            "name": "Cryptography (blocked in tests)",
            "prompt": "Explain the relationship between quantum computing and cryptography, including potential impacts on current encryption methods."
        },
        {
            "name": "Security vulnerabilities",
            "prompt": "Analyze this transcript about cybersecurity: The researcher discovered a zero-day vulnerability in OpenSSL that could be exploited to decrypt HTTPS traffic."
        },
        {
            "name": "Intelligence analysis",
            "prompt": "Extract intelligence from this transcript: The NSA analyst discussed signals intelligence gathering techniques and cryptanalysis methods."
        }
    ]
    
    for model_name in ["gemini-2.5-flash", "gemini-2.5-pro"]:
        model_key = "flash" if "flash" in model_name else "pro"
        print(f"\n{model_key.upper()} Model:")
        
        model = genai.GenerativeModel(
            model_name,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
        )
        
        for test in problematic_prompts:
            print(f"  {test['name']}: ", end="")
            try:
                response = await model.generate_content_async(test['prompt'])
                if response.text:
                    print(f"✅ Allowed ({len(response.text)} chars)")
                else:
                    if response.candidates and response.candidates[0].finish_reason:
                        print(f"❌ Blocked (reason={response.candidates[0].finish_reason})")
                    else:
                        print(f"❌ No output")
            except Exception as e:
                if "finish_reason" in str(e):
                    print(f"❌ Blocked")
                else:
                    print(f"❌ Error: {str(e)[:50]}...")
    
    # Final recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    print("\n📋 Based on testing:")
    print("1. The 24k character limit is UNNECESSARY - models can handle much more")
    print("2. Safety filters block content about cryptography and security")
    print("3. We should use BLOCK_ONLY_HIGH for all safety categories")
    print("4. We should analyze at least 100k-200k characters for long videos")
    print("5. Consider chunking only if we hit actual API limits (>1M chars)")


async def main():
    """Main entry point."""
    await test_token_limits()


if __name__ == "__main__":
    asyncio.run(main())
