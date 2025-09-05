#!/usr/bin/env python3
"""Debug what Grok-4 actually returns."""

import asyncio
import httpx
import json
import os

os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"


async def test_grok_extraction():
    """Test Grok extraction with a simple transcript."""
    
    api_key = os.environ["XAI_API_KEY"].strip('"').strip("'")
    
    # Simple test transcript
    transcript = """
    Jim Keller told me that modern culture is a form of mate suppression.
    Klaus Schwab founded the World Economic Forum.
    The WEF promotes degrowth and deindustrialization.
    Joe Biden and Zelensky are members of the WEF.
    """
    
    prompt = f"""
    Extract comprehensive intelligence from this transcript.
    
    1. ENTITIES: All people, organizations, places, concepts mentioned
    2. RELATIONSHIPS: Connections between entities (subject-predicate-object)
    3. TOPICS: Main themes discussed
    
    Transcript:
    {transcript}
    
    Respond in JSON with keys: entities, relationships, topics
    
    For relationships, use this exact format:
    {{"subject": "entity1", "predicate": "relation", "object": "entity2"}}
    """
    
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
                    {"role": "system", "content": "Extract entities and relationships."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
                "response_format": {"type": "json_object"}
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = json.loads(result["choices"][0]["message"]["content"])
            
            print("RAW GROK RESPONSE:")
            print(json.dumps(content, indent=2))
            
            print("\nRELATIONSHIPS STRUCTURE:")
            for r in content.get("relationships", []):
                print(f"  Keys: {r.keys()}")
                print(f"  Subject: '{r.get('subject', 'MISSING')}'")
                print(f"  Predicate: '{r.get('predicate', 'MISSING')}'")
                print(f"  Object: '{r.get('object', 'MISSING')}'")
                print()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(test_grok_extraction())
