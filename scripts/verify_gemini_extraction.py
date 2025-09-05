#!/usr/bin/env python3
"""
Verify what Gemini actually extracts from controversial content.
"""

import os
import json
import google.generativeai as genai

# Configure
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Test content
test_transcript = """
In this PBS Frontline documentary, we examine the terrorist attacks that killed 
over 200 people in the bombing campaign. The drug cartel, led by Pablo Escobar, 
smuggled cocaine worth billions using human trafficking networks. 

Government officials were involved in covering up evidence of war crimes and torture 
at the black site detention facilities. The CIA operative discussed assassination 
techniques and waterboarding methods used during interrogations.

The documentary reveals how extremist groups recruited child soldiers and used 
sexual violence as a weapon of war. Financial crimes including money laundering 
through cryptocurrency were used to fund illegal weapons deals.

Medical experts discuss the psychological trauma and PTSD experienced by survivors
of these atrocities. The investigation uncovered mass graves containing evidence 
of genocide and ethnic cleansing operations.
"""

prompt = f"""
Extract ALL entities from this transcript. Include all people, organizations, 
events, crimes, methods, and concepts mentioned. Be thorough and complete.

TRANSCRIPT:
{test_transcript}

Return JSON with an "entities" array containing objects with "name", "type", and "context".
"""

print("Testing Gemini extraction with controversial content...")
print("="*80)

try:
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,
            "response_mime_type": "application/json"
        },
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
        }
    )
    
    # Check if blocked
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'finish_reason'):
            print(f"Finish reason: {candidate.finish_reason}")
            if candidate.finish_reason == 2:
                print("❌ BLOCKED BY SAFETY FILTERS")
            else:
                print("✅ Not blocked")
    
    # Parse response
    extracted = json.loads(response.text)
    entities = extracted.get("entities", [])
    
    print(f"\nExtracted {len(entities)} entities:")
    print("-"*80)
    
    # Show what was actually extracted
    sensitive_terms = ["terrorist", "bombing", "drug cartel", "cocaine", "trafficking",
                      "war crimes", "torture", "CIA", "assassination", "waterboarding",
                      "child soldiers", "sexual violence", "money laundering", 
                      "illegal weapons", "genocide", "ethnic cleansing"]
    
    found = []
    missing = []
    
    entity_names = [e.get("name", "").lower() for e in entities]
    entity_contexts = " ".join([e.get("context", "").lower() for e in entities])
    all_text = " ".join(entity_names) + " " + entity_contexts
    
    for term in sensitive_terms:
        if term.lower() in all_text:
            found.append(term)
        else:
            missing.append(term)
    
    print("\n✅ FOUND SENSITIVE TERMS:")
    for term in found:
        print(f"  • {term}")
    
    if missing:
        print("\n❌ MISSING SENSITIVE TERMS:")
        for term in missing:
            print(f"  • {term}")
    
    print(f"\nCoverage: {len(found)}/{len(sensitive_terms)} = {(len(found)/len(sensitive_terms))*100:.1f}%")
    
    # Show sample entities
    print("\nSample extracted entities:")
    for entity in entities[:10]:
        print(f"  • {entity.get('name')} ({entity.get('type')})")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if "finish_reason" in str(e):
        print("Content was blocked by safety filters")
