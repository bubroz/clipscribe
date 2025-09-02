#!/usr/bin/env python3
"""
Test Evidence & Quotes Fields in Extraction

Tests that the new evidence and quotes fields are properly included in entity
and relationship extraction results.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber


def test_evidence_quotes_schema():
    """Test that evidence/quotes fields are present in extraction results."""

    print("=" * 60)
    print("🧪 TESTING EVIDENCE & QUOTES SCHEMA")
    print("=" * 60)

    # Mock transcript for testing
    test_transcript = """
    John Smith from Microsoft announced today that their new AI partnership with OpenAI
    will revolutionize cloud computing. "This collaboration represents a major milestone
    in our shared mission to advance AI capabilities," said Smith during the press conference.
    The partnership was officially signed on March 15, 2024, and will focus on developing
    next-generation language models. Microsoft CEO Satya Nadella also commented that
    "OpenAI's technology combined with our cloud infrastructure will create unprecedented
    opportunities for innovation."
    """

    print("📝 Test Transcript:")
    print(test_transcript[:200] + "...")
    print()

    # Create transcriber instance
    transcriber = GeminiFlashTranscriber(use_pro=False)

    # Get the schema and prompt
    schema = transcriber._build_enhanced_response_schema()
    prompt = transcriber._build_enhanced_analysis_prompt(test_transcript)

    print("📋 Checking Schema Structure:")

    # Check entities schema
    entity_props = schema["properties"]["entities"]["items"]["properties"]
    required_entity_fields = schema["properties"]["entities"]["items"]["required"]

    print("🏷️  Entity Schema Fields:")
    for field, field_type in entity_props.items():
        required = " (required)" if field in required_entity_fields else ""
        if isinstance(field_type, dict) and "type" in field_type:
            print(f"   • {field}: {field_type['type']}{required}")
        else:
            print(f"   • {field}: {field_type}{required}")

    # Check if evidence and quotes are in entity schema
    has_evidence = "evidence" in entity_props
    has_quotes = "quotes" in entity_props

    print(f"\n✅ Entity has evidence field: {has_evidence}")
    print(f"✅ Entity has quotes field: {has_quotes}")

    # Check relationships schema
    rel_props = schema["properties"]["relationships"]["items"]["properties"]
    required_rel_fields = schema["properties"]["relationships"]["items"]["required"]

    print("\n🔗 Relationship Schema Fields:")
    for field, field_type in rel_props.items():
        required = " (required)" if field in required_rel_fields else ""
        if isinstance(field_type, dict) and "type" in field_type:
            print(f"   • {field}: {field_type['type']}{required}")
        else:
            print(f"   • {field}: {field_type}{required}")

    # Check if evidence and quotes are in relationship schema
    has_rel_evidence = "evidence" in rel_props
    has_rel_quotes = "quotes" in rel_props

    print(f"\n✅ Relationship has evidence field: {has_rel_evidence}")
    print(f"✅ Relationship has quotes field: {has_rel_quotes}")

    # Check prompt for evidence/quotes instructions
    evidence_instruction = "evidence" in prompt.lower()
    quotes_instruction = "quotes" in prompt.lower()

    print(f"\n📝 Prompt includes evidence instruction: {evidence_instruction}")
    print(f"📝 Prompt includes quotes instruction: {quotes_instruction}")

    print("\n" + "=" * 60)
    print("🎯 SCHEMA VALIDATION RESULTS")
    print("=" * 60)

    all_checks_pass = all([
        has_evidence,
        has_quotes,
        has_rel_evidence,
        has_rel_quotes,
        evidence_instruction,
        quotes_instruction
    ])

    if all_checks_pass:
        print("✅ ALL CHECKS PASSED!")
        print("🎉 Evidence & Quotes fields are properly implemented")
        print()
        print("📋 Summary:")
        print("   • Entity schema includes evidence and quotes fields")
        print("   • Relationship schema includes evidence and quotes fields")
        print("   • Prompt instructs AI to provide evidence and quotes")
        print("   • Ready for production use with evidence-based extraction")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("🔧 Issues found:")
        if not has_evidence:
            print("   • Entity missing evidence field")
        if not has_quotes:
            print("   • Entity missing quotes field")
        if not has_rel_evidence:
            print("   • Relationship missing evidence field")
        if not has_rel_quotes:
            print("   • Relationship missing quotes field")
        if not evidence_instruction:
            print("   • Prompt missing evidence instruction")
        if not quotes_instruction:
            print("   • Prompt missing quotes instruction")

    return all_checks_pass


if __name__ == "__main__":
    test_evidence_quotes_schema()
