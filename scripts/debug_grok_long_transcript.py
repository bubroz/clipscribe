#!/usr/bin/env python3
"""
Debug Grok-4 response with a longer, more complex transcript.
Following xAI API best practices.
"""

import asyncio
import httpx
import json
import os

os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"


async def test_grok_with_long_transcript():
    """Test Grok-4 with a longer transcript to understand response format."""
    
    api_key = os.environ["XAI_API_KEY"].strip('"').strip("'")
    
    # Longer, more complex test transcript
    transcript = """
    Jim Keller told me that modern culture is a form of mate suppression.
    Klaus Schwab founded the World Economic Forum.
    The WEF promotes degrowth and deindustrialization.
    Joe Biden and Zelensky are members of the WEF.
    
    The concept of Mouse Utopia was developed by John Calhoun in the 1960s.
    It demonstrated behavioral sink in overcrowded rat populations.
    This relates to modern urban environments and social dysfunction.
    
    Nietzsche wrote about the death of God and nihilism.
    He distinguished between life-affirming and life-denying philosophies.
    Christianity, in his view, was life-denying.
    
    The elites use various forms of social control.
    Media manipulation is one method.
    Educational indoctrination is another.
    Economic dependency creates compliance.
    
    Trump, despite being controversial, challenged the establishment.
    His policies differed from traditional Republican positions.
    The media reaction was unprecedented in its hostility.
    """ * 3  # Repeat to make it longer
    
    # Test different prompt formats based on xAI best practices
    prompts = [
        {
            "name": "Structured JSON Request",
            "prompt": f"""Extract entities and relationships from this transcript.

IMPORTANT: Return a JSON object with this EXACT structure:
{{
  "entities": [
    {{"name": "entity_name", "type": "entity_type", "confidence": 0.9}}
  ],
  "relationships": [
    {{"subject": "entity1", "predicate": "relation", "object": "entity2", "confidence": 0.9}}
  ],
  "topics": ["topic1", "topic2"]
}}

Transcript:
{transcript[:2000]}...

Ensure ALL relationships have non-empty subject and object fields."""
        },
        {
            "name": "Simple List Format",
            "prompt": f"""Extract from this transcript:
1. All entities (people, organizations, concepts)
2. All relationships between entities
3. Main topics

Transcript excerpt:
{transcript[:1000]}...

Return as JSON with entities, relationships, and topics."""
        }
    ]
    
    for test in prompts:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print("="*60)
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "grok-4-0709",
                        "messages": [
                            {
                                "role": "system", 
                                "content": "You are an expert at extracting structured information from text. Always return valid JSON."
                            },
                            {"role": "user", "content": test['prompt']}
                        ],
                        "temperature": 0.1,  # Low temperature for consistency
                        "max_tokens": 4000,
                        "response_format": {"type": "json_object"}  # Enforce JSON
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = json.loads(result["choices"][0]["message"]["content"])
                    
                    print(f"\n✅ Success! Response structure:")
                    
                    # Analyze entities
                    entities = content.get("entities", [])
                    print(f"\nEntities ({len(entities)} total):")
                    if entities:
                        first = entities[0]
                        print(f"  First entity type: {type(first)}")
                        if isinstance(first, dict):
                            print(f"  Keys: {first.keys()}")
                            print(f"  Example: {first}")
                        else:
                            print(f"  Example: {first}")
                    
                    # Analyze relationships
                    relationships = content.get("relationships", [])
                    print(f"\nRelationships ({len(relationships)} total):")
                    if relationships:
                        first_rel = relationships[0]
                        print(f"  First relationship type: {type(first_rel)}")
                        if isinstance(first_rel, dict):
                            print(f"  Keys: {first_rel.keys()}")
                            print(f"  Subject: '{first_rel.get('subject', 'MISSING')}'")
                            print(f"  Predicate: '{first_rel.get('predicate', 'MISSING')}'")
                            print(f"  Object: '{first_rel.get('object', 'MISSING')}'")
                            
                            # Check for empty values
                            empty_count = 0
                            for r in relationships:
                                if not r.get('subject') or not r.get('object'):
                                    empty_count += 1
                            if empty_count > 0:
                                print(f"  ⚠️ WARNING: {empty_count}/{len(relationships)} relationships have empty subject/object!")
                    
                    # Analyze topics
                    topics = content.get("topics", [])
                    print(f"\nTopics ({len(topics)} total):")
                    if topics:
                        print(f"  First topic type: {type(topics[0])}")
                        print(f"  Examples: {topics[:3]}")
                    
                    # Save for inspection
                    filename = f"grok_debug_{test['name'].replace(' ', '_').lower()}.json"
                    with open(filename, 'w') as f:
                        json.dump(content, f, indent=2)
                    print(f"\n💾 Saved full response to {filename}")
                    
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(response.text)
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🔍 Debugging Grok-4 Response Format with Long Transcripts")
    print("Following xAI API Best Practices")
    asyncio.run(test_grok_with_long_transcript())
