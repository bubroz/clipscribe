#!/usr/bin/env python3
"""
Test Safety Settings with Modified Prompts

Tests whether our BLOCK_NONE safety settings work with modified, less sensitive prompts.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber


async def test_simple_analysis():
    """Test with a simple, non-sensitive transcript."""

    print("🧪 TESTING SAFETY SETTINGS WITH SIMPLE CONTENT")
    print("=" * 60)

    # Simple, non-sensitive test transcript
    simple_transcript = """
    John Smith is the CEO of TechCorp, a software company based in San Francisco.
    The company was founded in 2015 and has grown to employ over 500 people.
    Their main product is a cloud-based project management tool called TaskFlow.
    """

    print(f"Test transcript: {simple_transcript[:100]}...")

    try:
        transcriber = GeminiFlashTranscriber()

        # Create a simple analysis prompt
        analysis_prompt = f"""
        Analyze this transcript and extract:
        - Summary
        - Key entities (people, organizations, products)
        - Relationships between them

        Transcript: {simple_transcript}
        """

        print("\\n📤 Sending analysis request...")

        # Get model and make request
        from src.clipscribe.retrievers.gemini_pool import TaskType
        model = transcriber.pool.get_model(TaskType.ENTITIES)

        response = await transcriber._retry_generate_content(
            model,
            [analysis_prompt],
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "entities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "max_output_tokens": 8192,
                "temperature": 0.1
            }
        )

        print("✅ Analysis successful!")
        print(f"Response: {response.text[:500]}...")

        return True

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


async def test_pegasus_with_modified_prompt():
    """Test with Pegasus content using the modified, less sensitive prompt."""

    print("\\n🧪 TESTING PEGASUS CONTENT WITH MODIFIED PROMPT")
    print("=" * 60)

    # Short Pegasus-related transcript (much shorter than the full video)
    pegasus_transcript = """
    A global investigation exposed the misuse of Pegasus spyware.
    Pegasus was developed by NSO Group, an Israeli cybersecurity company.
    The spyware was used to target journalists and human rights activists.
    The investigation was led by Forbidden Stories and involved 17 news organizations.
    """

    print(f"Pegasus test transcript: {pegasus_transcript[:100]}...")

    try:
        transcriber = GeminiFlashTranscriber()

        # Use the modified analysis prompt
        analysis_prompt = transcriber._build_enhanced_analysis_prompt(pegasus_transcript)
        response_schema = transcriber._build_enhanced_response_schema()

        print("\\n📤 Sending Pegasus analysis request with modified prompt...")

        # Get model and make request
        from src.clipscribe.retrievers.gemini_pool import TaskType
        model = transcriber.pool.get_model(TaskType.ENTITIES)

        response = await transcriber._retry_generate_content(
            model,
            [analysis_prompt],
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
                "max_output_tokens": 8192,
                "temperature": 0.1
            }
        )

        print("✅ Pegasus analysis successful!")
        print(f"Response length: {len(response.text)} characters")
        print(f"Response preview: {response.text[:500]}...")

        return True

    except Exception as e:
        print(f"❌ Pegasus analysis failed: {e}")
        return False


async def main():
    """Run safety settings tests."""

    print("🔒 CLIPSCRIBE SAFETY SETTINGS TEST SUITE")
    print("=" * 60)

    # Test 1: Simple content
    test1_passed = await test_simple_analysis()

    # Test 2: Pegasus content with modified prompt
    test2_passed = await test_pegasus_with_modified_prompt()

    # Summary
    print("\\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Simple Analysis Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Pegasus Analysis Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\\n🎉 ALL TESTS PASSED! Safety settings are working correctly.")
        return 0
    else:
        print("\\n⚠️  SOME TESTS FAILED. Safety settings may need further adjustment.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
