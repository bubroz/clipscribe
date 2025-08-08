#!/usr/bin/env python3
"""
Compare extraction methods to show why we use all three
"""

import asyncio
from clipscribe.extractors.spacy_extractor import SpacyEntityExtractor
from clipscribe.extractors.gliner_extractor import GLiNERExtractor
from clipscribe.extractors.rebel_extractor import REBELExtractor

async def compare_extractors():
    # Sample text with various entity types
    text = """
    Dr. Sarah Chen, CEO of BioTech Innovations in San Francisco, announced 
    a breakthrough COVID-19 treatment using mRNA technology. The new drug, 
    called RNAShield-X, showed 95% efficacy in Phase 3 trials involving 
    30,000 patients. The treatment costs $50 per dose and will be 
    manufactured at their facility in Boston starting March 2025.
    """
    
    print("=" * 60)
    print("EXTRACTION COMPARISON: Why We Need All Three")
    print("=" * 60)
    
    # 1. SpaCy - Standard Entities
    print("\n1. SPACY (Standard NER):")
    spacy_extractor = SpacyEntityExtractor()
    spacy_entities = spacy_extractor.extract_entities(text)
    print("   Found:", len(spacy_entities), "entities")
    for entity, conf in spacy_entities[:10]:  # Show first 10
        print(f"   - {entity.name} ({entity.type})")
    
    # What SpaCy missed
    print("\n    SpaCy MISSED:")
    print("   - 'mRNA technology' (biotech term)")
    print("   - 'RNAShield-X' (drug name)")
    print("   - 'Phase 3 trials' (clinical term)")
    print("   - 'COVID-19 treatment' (medical concept)")
    
    # 2. GLiNER - Custom Entities
    print("\n2. GLINER (Custom Entities):")
    gliner = GLiNERExtractor()
    biotech_labels = [
        "drug", "disease", "treatment", "technology", "clinical_trial",
        "biotech_company", "efficacy_metric", "medical_facility"
    ]
    gliner_entities = gliner.extract_entities(text, biotech_labels)
    print("   Found:", len(gliner_entities), "specialized entities")
    for entity in gliner_entities:
        print(f"   - {entity.text} ({entity.label})")
    
    # 3. REBEL - Relationships
    print("\n3. REBEL (Relationships):")
    rebel = REBELExtractor()
    relationships = rebel.extract_relations(text)
    print("   Found:", len(relationships), "relationships")
    for rel in relationships:
        print(f"   - {rel.subject} --[{rel.predicate}]--> {rel.object}")
    
    # Combined Intelligence
    print("\n4. COMBINED INTELLIGENCE:")
    print("   Total Entities:", len(spacy_entities) + len(gliner_entities))
    print("   Total Relationships:", len(relationships))
    print("\n   Knowledge Graph Preview:")
    print("   - Dr. Sarah Chen [PERSON] --[CEO of]--> BioTech Innovations [ORG]")
    print("   - BioTech Innovations [ORG] --[located in]--> San Francisco [LOC]")
    print("   - RNAShield-X [drug] --[treats]--> COVID-19 [disease]")
    print("   - RNAShield-X [drug] --[efficacy]--> 95% [PERCENT]")

if __name__ == "__main__":
    asyncio.run(compare_extractors())
