"""
Knowledge graph cleaner - Gemini removed, functionality moved to HybridProcessor.

Instead of rigid rules, let's use AI to understand context and clean intelligently
"""

import json
import logging
from typing import Any, Dict, List

from google.generativeai.types import RequestOptions

from ..config.settings import Settings
from ..models import VideoIntelligence

logger = logging.getLogger(__name__)


class GraphCleaner:
    """Clean knowledge graphs - Gemini removed, functionality deprecated."""

    def __init__(self, model_name: str = "deprecated"):
        """Initialize the graph cleaner."""
        self.model_name = model_name
        self.settings = Settings()
        # self.request_timeout = self.settings.gemini_request_timeout  # Gemini removed

        # Gemini configuration removed
        # genai.configure(api_key=None)  # Uses GOOGLE_API_KEY env var
        # self.model = genai.GenerativeModel(model_name)
        self.model = None

    async def clean_knowledge_graph(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """Clean the knowledge graph by reviewing entities and relationships."""
        if not video_intel.knowledge_graph:
            return video_intel

        logger.info("Knowledge graph cleaning - Gemini removed, functionality deprecated")

        # Get video context
        video_context = (
            f"Video: {video_intel.metadata.title}\nTopic: {video_intel.summary[:200]}..."
        )

        # Clean entities
        cleaned_entities = await self._clean_entities(
            video_intel.entities, video_intel.knowledge_graph.get("nodes", []), video_context
        )

        # Clean relationships
        cleaned_relationships = await self._clean_relationships(
            video_intel.relationships, cleaned_entities, video_context
        )

        # Update the video intelligence
        video_intel.entities = cleaned_entities
        video_intel.relationships = cleaned_relationships

        # Rebuild knowledge graph with cleaned data
        video_intel = self._rebuild_knowledge_graph(video_intel)

        logger.info(
            f"Graph cleaned: {len(cleaned_entities)} entities, "
            f"{len(cleaned_relationships)} relationships "
        )

        return video_intel

    async def _clean_entities(
        self, entities: List[Any], nodes: List[Dict], context: str
    ) -> List[Any]:
        """Clean entities by removing noise and merging duplicates."""
        # Create entity list for review
        entity_list = []
        for entity in entities:
            entity_list.append(
                {"name": entity.name, "type": entity.type, "confidence": entity.confidence}
            )

        prompt = f"""
Review these entities extracted from a video and identify ONLY obvious issues.

{context}

Entities to review:
{json.dumps(entity_list, indent=2)}

Identify ONLY:
1. NOISE: Truly meaningless fragments or extraction errors
   Examples: "um", "uh", "the the", sentence fragments like "has directed that"
   DO NOT mark as noise: roles ("participant"), generic concepts ("country"), or any real words

2. DUPLICATES: Exact same entity with different spellings
   Examples: "U.S." and "United States", "Trump" and "Donald Trump"

3. MISTYPED: Obviously wrong type classification

Return a JSON object with these exact keys:
{{
    "noise": ["entity1", "entity2"],  // ONLY fragments and errors
    "duplicates": {{"variant": "primary", "US": "United States"}},  // Map variants
    "retype": {{"entity": "correct_type"}},  // Fix obvious type errors
    "keep_important": ["entity1", "entity2"]  // Entities that are definitely important
}}

CRITICAL RULES:
1. DEFAULT TO KEEPING EVERYTHING - Only remove if 100% certain it's garbage
2. Keep ALL real words, even if they seem generic
3. Keep ALL proper nouns, titles, concepts, ideas
4. ONLY remove: typos, fragments like "um", "uh", or obvious extraction errors
5. When you have ANY doubt, KEEP THE ENTITY

We want a RICH, COMPREHENSIVE graph. It's better to have too much data than too little.
Every entity might be important for understanding relationships.
"""

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options=RequestOptions(timeout=self.request_timeout),
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

    async def _clean_relationships(
        self, relationships: List[Any], entities: List[Any], context: str
    ) -> List[Any]:
        """Clean relationships by fixing malformed ones and removing noise."""
        # Get entity names for validation - handle both Entity and EnhancedEntity objects
        entity_names = set()
        for e in entities:
            # Handle both Entity (has .entity) and EnhancedEntity (has .entity)
            if hasattr(e, "name"):
                entity_names.add(e.name)
            elif hasattr(e, "entity"):
                entity_names.add(e.entity)

        # Create relationship list
        rel_list = []
        for rel in relationships:
            rel_list.append(
                {
                    "subject": rel.subject,
                    "predicate": rel.predicate,
                    "object": rel.object,
                    "confidence": rel.confidence,
                }
            )

        prompt = f"""
Review these relationships and fix ONLY clear errors. We want to keep as many relationships as possible.

{context}

Valid entities in the graph: {sorted(entity_names)}

Relationships to review (first 50 of {len(rel_list)}):
{json.dumps(rel_list[:50], indent=2)}

Fix ONLY these clear issues:
1. SWAPPED: When predicate and object are obviously swapped
   Example: subject="Israel", predicate="Iran", object="diplomatic relation"
   Fix to: subject="Israel", predicate="diplomatic relation", object="Iran"

2. COMPLETELY INVALID: Subject or object is gibberish or not an entity at all
   DO NOT remove relationships just because entities aren't in the list - they might be valid

3. IMPROVE VAGUE: If predicate is too generic, suggest specific replacement
   Examples: "related to" → "works at", "mentioned" → "criticized"
   But KEEP the relationship even with generic predicate if you can't improve it

Return JSON:
{{
    "fixed": [
        {{"index": 0, "subject": "Israel", "predicate": "diplomatic relation", "object": "Iran"}},
    ],
    "remove": [3, 4, 7],  // ONLY indices that are completely invalid
    "improved_predicates": {{"index": predicate}},  // Better predicates for vague ones
    "notes": "Brief explanation"
}}

CRITICAL: We want to keep 90%+ of relationships. Only remove if:
- The subject/predicate/object are completely gibberish (not real words)
- The relationship is logically impossible (e.g., "Monday | capital of | Blue")

Even generic relationships like "mentioned" or "related to" provide value!
It's better to have too many relationships than too few.
"""

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options=RequestOptions(timeout=self.request_timeout),
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

                # Always add the relationship - don't filter by entity existence
                # The entities might have been cleaned but the relationship is still valid
                cleaned_relationships.append(rel)

            # Add remaining relationships without entity filtering
            # They passed REBEL extraction so they're likely valid
            for rel in relationships[50:]:
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
            # Handle both Entity (has .entity) and EnhancedEntity (has .entity)
            entity_name = entity.name if hasattr(entity, "name") else entity.entity
            G.add_node(entity_name, type=entity.type, confidence=entity.confidence)

        # Add relationships as edges
        for rel in video_intel.relationships:
            G.add_edge(rel.subject, rel.object, predicate=rel.predicate, confidence=rel.confidence)

        # Convert to serializable format
        video_intel.knowledge_graph = {
            "nodes": [
                {
                    "id": node,
                    "type": data.get("type", "unknown"),
                    "confidence": data.get("confidence", 0.9),
                }
                for node, data in G.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "predicate": data.get("predicate", "related_to"),
                    "confidence": data.get("confidence", 0.9),
                }
                for u, v, data in G.edges(data=True)
            ],
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "cleaned": True,
        }

        return video_intel
