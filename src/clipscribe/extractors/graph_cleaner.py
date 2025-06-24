"""
Intelligent knowledge graph cleaner using Gemini.

Instead of rigid rules, let's use AI to understand context and clean intelligently :-)
"""

import json
import logging
from typing import Dict, List, Any, Set, Tuple
import asyncio

import google.generativeai as genai
from google.generativeai.types import RequestOptions

from ..config.settings import Settings
from ..models import VideoIntelligence

logger = logging.getLogger(__name__)


class GraphCleaner:
    """Clean knowledge graphs intelligently using Gemini."""
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """Initialize the graph cleaner."""
        self.model_name = model_name
        self.settings = Settings()
        self.request_timeout = self.settings.gemini_request_timeout
        
        # Configure Gemini
        genai.configure(api_key=None)  # Uses GOOGLE_API_KEY env var
        self.model = genai.GenerativeModel(model_name)
        
    async def clean_knowledge_graph(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """Clean the knowledge graph by reviewing entities and relationships."""
        if not video_intel.knowledge_graph:
            return video_intel
            
        logger.info("Cleaning knowledge graph with Gemini...")
        
        # Get video context
        video_context = f"Video: {video_intel.metadata.title}\nTopic: {video_intel.summary[:200]}..."
        
        # Clean entities
        cleaned_entities = await self._clean_entities(
            video_intel.entities, 
            video_intel.knowledge_graph.get('nodes', []),
            video_context
        )
        
        # Clean relationships
        cleaned_relationships = await self._clean_relationships(
            video_intel.relationships,
            cleaned_entities,
            video_context
        )
        
        # Update the video intelligence
        video_intel.entities = cleaned_entities
        video_intel.relationships = cleaned_relationships
        
        # Rebuild knowledge graph with cleaned data
        video_intel = self._rebuild_knowledge_graph(video_intel)
        
        logger.info(
            f"Graph cleaned: {len(cleaned_entities)} entities, "
            f"{len(cleaned_relationships)} relationships :-)"
        )
        
        return video_intel
        
    async def _clean_entities(self, entities: List[Any], nodes: List[Dict], context: str) -> List[Any]:
        """Clean entities by removing noise and merging duplicates."""
        # Create entity list for review
        entity_list = []
        for entity in entities:
            entity_list.append({
                "name": entity.name,
                "type": entity.type,
                "confidence": entity.confidence
            })
        
        prompt = f"""
Review these entities extracted from a video and identify issues.

{context}

Entities to review:
{json.dumps(entity_list, indent=2)}

Identify:
1. NOISE: Generic terms, extraction errors, or meaningless entities
   Examples: "country", "participant", "the President has directed", "sources and methods"
   
2. DUPLICATES: Different variations of the same entity
   Examples: "U.S." and "United States", "Trump" and "Donald Trump"
   
3. MISTYPED: Entities with wrong type classification

Return a JSON object with these exact keys:
{{
    "noise": ["entity1", "entity2"],  // Entities to remove
    "duplicates": {{"variant": "primary", "US": "United States"}},  // Map variants to primary
    "retype": {{"entity": "correct_type"}},  // Correct entity types
    "keep_important": ["entity1", "entity2"]  // Important entities to definitely keep
}}

Be conservative - only mark obvious noise. Keep all specific people, places, organizations, and events.
"""
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            
            result = json.loads(response.text)
            
            # Apply cleaning
            noise_set = set(result.get("noise", []))
            duplicate_map = result.get("duplicates", {})
            retype_map = result.get("retype", {})
            important_set = set(result.get("keep_important", []))
            
            cleaned_entities = []
            seen_names = set()
            
            for entity in entities:
                # Skip noise
                if entity.name in noise_set and entity.name not in important_set:
                    continue
                
                # Handle duplicates
                mapped_name = duplicate_map.get(entity.name, entity.name)
                if mapped_name in seen_names:
                    continue
                    
                # Update entity
                entity.name = mapped_name
                seen_names.add(mapped_name)
                
                # Retype if needed
                if entity.name in retype_map:
                    entity.type = retype_map[entity.name]
                
                cleaned_entities.append(entity)
                
            return cleaned_entities
            
        except Exception as e:
            logger.error(f"Entity cleaning failed: {e}")
            return entities  # Return original if cleaning fails
            
    async def _clean_relationships(self, relationships: List[Any], entities: List[Any], context: str) -> List[Any]:
        """Clean relationships by fixing malformed ones and removing noise."""
        # Get entity names for validation
        entity_names = {e.name for e in entities}
        
        # Create relationship list
        rel_list = []
        for rel in relationships:
            rel_list.append({
                "subject": rel.subject,
                "predicate": rel.predicate, 
                "object": rel.object,
                "confidence": rel.confidence
            })
        
        prompt = f"""
Review these relationships extracted from a video and fix issues.

{context}

Valid entities in the graph: {sorted(entity_names)}

Relationships to review:
{json.dumps(rel_list[:50], indent=2)}  // Showing first 50

Fix these issues:
1. SWAPPED: Predicates and objects are swapped (e.g., subject="Israel", predicate="Iran", object="diplomatic relation")
2. INVALID: Subject or object not in entity list
3. NONSENSE: Relationships that don't make logical sense
4. GENERIC: Overly vague predicates like "related to"

For SWAPPED relationships, return the corrected version.
For INVALID/NONSENSE, mark for removal.
For GENERIC, suggest a more specific predicate if possible.

Return JSON:
{{
    "fixed": [
        {{"index": 0, "subject": "Israel", "predicate": "diplomatic relation", "object": "Iran"}},
    ],
    "remove": [3, 4, 7],  // Indices to remove
    "notes": "Brief explanation of major fixes"
}}
"""
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options=RequestOptions(timeout=self.request_timeout)
            )
            
            result = json.loads(response.text)
            
            # Apply fixes
            fixed_map = {fix["index"]: fix for fix in result.get("fixed", [])}
            remove_set = set(result.get("remove", []))
            
            cleaned_relationships = []
            
            for i, rel in enumerate(relationships[:50]):  # Process first 50 that were reviewed
                if i in remove_set:
                    continue
                    
                if i in fixed_map:
                    fix = fixed_map[i]
                    rel.subject = fix["subject"]
                    rel.predicate = fix["predicate"] 
                    rel.object = fix["object"]
                
                # Validate entities exist
                if rel.subject in entity_names and rel.object in entity_names:
                    cleaned_relationships.append(rel)
                    
            # Add remaining relationships if they're valid
            for rel in relationships[50:]:
                if rel.subject in entity_names and rel.object in entity_names:
                    cleaned_relationships.append(rel)
                    
            return cleaned_relationships
            
        except Exception as e:
            logger.error(f"Relationship cleaning failed: {e}")
            # Basic fallback cleaning
            cleaned = []
            for rel in relationships:
                if rel.subject in entity_names and rel.object in entity_names:
                    cleaned.append(rel)
            return cleaned
            
    def _rebuild_knowledge_graph(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """Rebuild the knowledge graph with cleaned data."""
        import networkx as nx
        
        G = nx.DiGraph()
        
        # Add entities as nodes
        for entity in video_intel.entities:
            G.add_node(
                entity.name,
                type=entity.type,
                confidence=entity.confidence
            )
            
        # Add relationships as edges
        for rel in video_intel.relationships:
            G.add_edge(
                rel.subject,
                rel.object,
                predicate=rel.predicate,
                confidence=rel.confidence
            )
            
        # Convert to serializable format
        video_intel.knowledge_graph = {
            "nodes": [
                {
                    "id": node,
                    "type": data.get("type", "unknown"),
                    "confidence": data.get("confidence", 0.9)
                }
                for node, data in G.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "predicate": data.get("predicate", "related_to"),
                    "confidence": data.get("confidence", 0.9)
                }
                for u, v, data in G.edges(data=True)
            ],
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "cleaned": True
        }
        
        return video_intel 