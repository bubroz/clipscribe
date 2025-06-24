#!/usr/bin/env python3
"""
Dynamic Extraction Demo - Shows the real power of GLiNER and REBEL

This demonstrates:
1. GLiNER can find ANY entity type you describe (not just from a dictionary)
2. REBEL extracts semantic relationships between entities
3. Together they build rich knowledge graphs
"""

import asyncio
from typing import List, Optional
import sys

from clipscribe.extractors.gliner_extractor import GLiNERExtractor
from clipscribe.extractors.rebel_extractor import REBELExtractor


async def demo_dynamic_gliner():
    """Show how GLiNER can find any entity type dynamically."""
    
    # Example transcript about a cooking show
    cooking_text = """
    Today on MasterChef, Gordon Ramsay demonstrates how to make perfect risotto.
    You'll need arborio rice, white wine, parmesan cheese, and chicken stock.
    The key technique is constant stirring and gradual addition of liquid.
    This classic Italian dish takes about 25 minutes to prepare.
    """
    
    # Example transcript about a tech tutorial
    tech_text = """
    In this tutorial, we'll build a REST API using FastAPI and PostgreSQL.
    We'll deploy it on AWS Lambda using Docker containers.
    The authentication will use JWT tokens with refresh token rotation.
    Our frontend will be built with React and TypeScript.
    """
    
    gliner = GLiNERExtractor()
    
    print("\n=== Dynamic Entity Extraction with GLiNER ===\n")
    
    # For cooking content - ask for cooking-specific entities
    print("1. Cooking Video - Looking for culinary entities:")
    cooking_labels = [
        "chef", "dish", "ingredient", "cooking_technique", "cuisine_type",
        "cooking_time", "kitchen_tool", "flavor", "meal_course"
    ]
    
    cooking_entities = gliner.extract_entities(cooking_text, cooking_labels)
    for e in cooking_entities:
        print(f"   - {e.text} ({e.label})")
    
    # For tech content - ask for tech-specific entities  
    print("\n2. Tech Tutorial - Looking for technical entities:")
    tech_labels = [
        "programming_framework", "database", "cloud_service", "authentication_method",
        "programming_language", "api_type", "deployment_tool", "frontend_technology"
    ]
    
    tech_entities = gliner.extract_entities(tech_text, tech_labels)
    for e in tech_entities:
        print(f"   - {e.text} ({e.label})")
    
    # Show zero-shot capability - ask for abstract concepts
    print("\n3. Abstract Concepts - GLiNER understands context:")
    abstract_labels = [
        "learning_objective", "difficulty_level", "time_requirement", 
        "prerequisite", "end_result", "key_concept"
    ]
    
    abstract_entities = gliner.extract_entities(tech_text, abstract_labels)
    for e in abstract_entities:
        print(f"   - {e.text} ({e.label})")


async def demo_rebel_relationships():
    """Show how REBEL extracts semantic relationships."""
    
    # Text with clear relationships
    text = """
    Elon Musk founded SpaceX in 2002. SpaceX manufactures the Falcon 9 rocket.
    The company is headquartered in Hawthorne, California.
    Falcon 9 has launched over 200 missions successfully.
    SpaceX competes with Blue Origin, which was founded by Jeff Bezos.
    """
    
    rebel = REBELExtractor()
    
    print("\n\n=== Relationship Extraction with REBEL ===\n")
    
    relationships = rebel.extract_relations(text)
    
    print("Extracted Knowledge Graph Triples:")
    for rel in relationships:
        print(f"   ({rel.subject}) --[{rel.predicate}]--> ({rel.object})")
    
    # Show how this builds a graph
    print("\n\nThese relationships form a knowledge graph:")
    print("   - Nodes: Elon Musk, SpaceX, Falcon 9, Blue Origin, Jeff Bezos, etc.")
    print("   - Edges: founded, manufactures, headquartered in, competes with")
    print("   - This enables graph queries like 'What did Elon Musk found?'")


def show_complementary_nature():
    """Explain how GLiNER and REBEL complement each other."""
    
    print("\n\n=== Why GLiNER + REBEL is Powerful ===\n")
    
    print("GLiNER finds the NODES (entities):")
    print("- Flexible: Can find any entity type you describe")
    print("- Context-aware: Understands 'Apple' as company vs fruit")
    print("- Zero-shot: No training needed for new domains")
    
    print("\nREBEL finds the EDGES (relationships):")
    print("- Semantic: Understands 'founded', 'located in', 'works for'")
    print("- Directional: Knows subject vs object")
    print("- Contextual: Extracts implied relationships")
    
    print("\nTogether they build KNOWLEDGE GRAPHS:")
    print("- Entities become nodes")
    print("- Relationships become edges")
    print("- Enables complex queries and reasoning")
    
    print("\n\n=== Better Implementation Ideas ===\n")
    
    print("1. Dynamic Entity Detection:")
    print("   - Let users specify what they're looking for")
    print("   - 'Find all cooking terms' or 'Find all people and their roles'")
    
    print("\n2. Adaptive Extraction:")
    print("   - First pass: detect video domain")
    print("   - Second pass: use domain-specific labels")
    
    print("\n3. Query-Driven Extraction:")
    print("   - User asks: 'What tools are mentioned?'")
    print("   - GLiNER searches specifically for tools")
    
    print("\n4. Relationship Patterns:")
    print("   - Look for specific relationship types")
    print("   - 'Who works where?', 'What causes what?'")


async def improved_extraction_pipeline(text: str, user_query: Optional[str] = None):
    """Show how we could improve the extraction based on user needs."""
    
    print("\n\n=== Improved Extraction Pipeline ===\n")
    
    if user_query:
        print(f"User Query: '{user_query}'")
        
        # Parse user query to determine what to look for
        if "who" in user_query.lower():
            labels = ["person", "role", "title", "profession"]
        elif "what tools" in user_query.lower():
            labels = ["software", "hardware", "tool", "framework", "library"]
        elif "when" in user_query.lower():
            labels = ["date", "time", "duration", "deadline", "schedule"]
        else:
            labels = None  # Use defaults
            
        print(f"Dynamically selected labels: {labels}")
    
    # This would be integrated into the main pipeline
    print("\nThis approach makes ClipScribe adaptive to user needs!")


async def main():
    """Run all demos."""
    
    print("ClipScribe Entity Extraction - Understanding the Tools\n")
    print("=" * 60)
    
    # Show dynamic GLiNER
    await demo_dynamic_gliner()
    
    # Show REBEL relationships
    await demo_rebel_relationships()
    
    # Explain complementary nature
    show_complementary_nature()
    
    # Show improved pipeline concept
    await improved_extraction_pipeline(
        "Example text here",
        "What tools and frameworks are mentioned?"
    )
    
    print("\n\nKey Takeaways:")
    print("1. You DON'T need infinite dictionaries - GLiNER understands context")
    print("2. REBEL builds semantic graphs, not just keyword matching")
    print("3. Together they enable rich, queryable knowledge extraction")
    print("4. We can make extraction adaptive to user needs")


if __name__ == "__main__":
    asyncio.run(main()) 