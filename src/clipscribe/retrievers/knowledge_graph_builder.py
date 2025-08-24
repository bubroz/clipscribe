"""Knowledge Graph Builder Module - Handles knowledge graph construction."""

import logging
from typing import List, Dict, Any, Optional

from ..models import VideoIntelligence

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not available. Knowledge graph building disabled.")


class KnowledgeGraphBuilder:
    """Handles construction of knowledge graphs from entities and relationships."""

    def __init__(self):
        """Initialize the knowledge graph builder."""
        if not HAS_NETWORKX:
            raise ImportError("NetworkX is required for knowledge graph building")

    def build_knowledge_graph(self, video_intel: VideoIntelligence) -> VideoIntelligence:
        """
        Build knowledge graph from entities and relationships.

        Args:
            video_intel: VideoIntelligence object with entities and relationships

        Returns:
            VideoIntelligence object with knowledge_graph populated
        """
        if not video_intel.entities:
            logger.debug("No entities to build knowledge graph from")
            video_intel.knowledge_graph = {
                "nodes": [],
                "edges": [],
                "node_count": 0,
                "edge_count": 0,
            }
            return video_intel

        G = nx.DiGraph()

        # Add entities as nodes
        for entity in video_intel.entities:
            # Handle both Entity and EnhancedEntity objects
            entity_name = getattr(entity, "name", str(entity))
            entity_type = getattr(entity, "type", "unknown")
            entity_confidence = getattr(entity, "confidence", 0.9)
            mention_count = getattr(entity, "mention_count", 1)
            occurrences = getattr(entity, "occurrences", 1)
            extraction_sources = getattr(entity, "extraction_sources", [])
            canonical_form = getattr(entity, "canonical_form", entity_name)

            G.add_node(
                entity_name,
                type=entity_type,
                confidence=entity_confidence,
                mention_count=mention_count,
                occurrences=occurrences,
                extraction_sources=extraction_sources,
                canonical_form=canonical_form
            )

        # Add relationships as edges
        if hasattr(video_intel, "relationships") and video_intel.relationships:
            for rel in video_intel.relationships:
                subject = getattr(rel, "subject", rel.get("subject") if isinstance(rel, dict) else None)
                obj = getattr(rel, "object", rel.get("object") if isinstance(rel, dict) else None)
                predicate = getattr(
                    rel, "predicate", rel.get("predicate") if isinstance(rel, dict) else "related_to"
                )
                confidence = getattr(
                    rel, "confidence", rel.get("confidence", 0.9) if isinstance(rel, dict) else 0.9
                )
                source = getattr(rel, "source", rel.get("source", "unknown") if isinstance(rel, dict) else "unknown")

                if subject and obj:
                    G.add_edge(subject, obj, predicate=predicate, confidence=confidence, source=source)

        # Convert to serializable format
        video_intel.knowledge_graph = {
            "nodes": [
                {
                    "id": node,
                    "type": data.get("type", "unknown"),
                    "confidence": data.get("confidence", 0.9),
                    "mention_count": data.get("mention_count", 1),
                    "occurrences": data.get("occurrences", 1),
                    "extraction_sources": data.get("extraction_sources", []),
                    "canonical_form": data.get("canonical_form", node),
                }
                for node, data in G.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "predicate": data.get("predicate", "related_to"),
                    "confidence": data.get("confidence", 0.9),
                    "extraction_source": data.get("source", "unknown"),
                }
                for u, v, data in G.edges(data=True)
            ],
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
        }

        logger.info(
            f"Built knowledge graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
        )
        return video_intel

    def generate_gexf_content(self, knowledge_graph: Dict[str, Any]) -> str:
        """
        Generate GEXF content from knowledge graph for Gephi visualization.

        Args:
            knowledge_graph: Knowledge graph dictionary

        Returns:
            GEXF XML string
        """
        from xml.sax.saxutils import escape
        import hashlib
        from datetime import datetime

        def stable_node_id(label: str) -> str:
            # Use SHA-256 truncated for stable node IDs (12 hex chars)
            h = hashlib.sha256(label.encode("utf-8")).hexdigest()
            return f"n_{h[:12]}"

        label_to_id = {}

        gexf_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        gexf_content += '<gexf xmlns="http://www.gexf.net/1.3" xmlns:viz="http://www.gexf.net/1.3/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://gexf.net/1.3 http://gexf.net/1.3/gexf.xsd" version="1.3">\n'
        gexf_content += '  <meta lastmodifieddate="' + datetime.now().strftime("%Y-%m-%d") + '">\n'
        gexf_content += "    <creator>ClipScribe</creator>\n"
        gexf_content += '    <description>Knowledge graph extracted from video content</description>\n'
        gexf_content += "  </meta>\n"
        gexf_content += '  <graph mode="static" defaultedgetype="directed" idtype="string">\n'
        gexf_content += '    <attributes class="node">\n'
        gexf_content += '      <attribute id="0" title="Type" type="string"/>\n'
        gexf_content += '      <attribute id="1" title="Confidence" type="double"/>\n'
        gexf_content += '      <attribute id="2" title="MentionCount" type="integer"/>\n'
        gexf_content += '      <attribute id="3" title="Occurrences" type="integer"/>\n'
        gexf_content += '      <attribute id="4" title="Name" type="string"/>\n'
        gexf_content += "    </attributes>\n"
        gexf_content += '    <attributes class="edge">\n'
        gexf_content += '      <attribute id="0" title="Predicate" type="string"/>\n'
        gexf_content += '      <attribute id="1" title="Confidence" type="double"/>\n'
        gexf_content += "    </attributes>\n"
        gexf_content += "    <nodes>\n"

        # Color map for entity types
        color_map = {
            "PERSON": (255, 107, 107),  # Red
            "ORGANIZATION": (78, 205, 196),  # Teal
            "LOCATION": (69, 183, 209),  # Blue
            "EVENT": (247, 220, 111),  # Yellow
            "CONCEPT": (187, 143, 206),  # Purple
            "TECHNOLOGY": (82, 190, 128),  # Green
            "DATE": (243, 156, 18),  # Orange
            "MONEY": (133, 193, 226),  # Light Blue
            "unknown": (149, 165, 166),  # Gray
        }

        # Add nodes with attributes
        for node in knowledge_graph.get("nodes", []):
            label = escape(str(node.get("id", "unknown")))
            node_id = stable_node_id(label)
            label_to_id[label] = node_id
            node_type = node.get("type", "unknown")
            confidence = node.get("confidence", 0.9)
            mention_count = (
                int(node.get("mention_count", 0))
                if isinstance(node.get("mention_count", 0), (int, float))
                else 0
            )
            occurrences = (
                int(node.get("occurrences", 0))
                if isinstance(node.get("occurrences", 0), (int, float))
                else 0
            )

            # Get color for node type
            r, g, b = color_map.get(node_type, color_map["unknown"])

            gexf_content += f'      <node id="{node_id}" label="{label}">\n'
            gexf_content += "        <attvalues>\n"
            gexf_content += f'          <attvalue for="0" value="{escape(node_type)}"/>\n'
            gexf_content += f'          <attvalue for="1" value="{confidence}"/>\n'
            gexf_content += f'          <attvalue for="2" value="{mention_count}"/>\n'
            gexf_content += f'          <attvalue for="3" value="{occurrences}"/>\n'
            gexf_content += f'          <attvalue for="4" value="{label}"/>\n'
            gexf_content += "        </attvalues>\n"
            gexf_content += f'        <viz:color r="{r}" g="{g}" b="{b}" a="1.0"/>\n'
            gexf_content += f'        <viz:size value="{20 + (confidence * 30)}"/>\n'
            gexf_content += "      </node>\n"

        gexf_content += "    </nodes>\n"
        gexf_content += "    <edges>\n"

        # Add edges with attributes
        for i, edge in enumerate(knowledge_graph.get("edges", [])):
            source_label = escape(str(edge["source"]))
            target_label = escape(str(edge["target"]))
            source = label_to_id.get(source_label, stable_node_id(source_label))
            target = label_to_id.get(target_label, stable_node_id(target_label))
            predicate = escape(str(edge.get("predicate", "related_to")))
            confidence = edge.get("confidence", 0.9)

            gexf_content += f'      <edge id="{i}" source="{source}" target="{target}" weight="{confidence}" label="{predicate}" kind="{predicate}">\n'
            gexf_content += "        <attvalues>\n"
            gexf_content += f'          <attvalue for="0" value="{predicate}"/>\n'
            gexf_content += f'          <attvalue for="1" value="{confidence}"/>\n'
            gexf_content += "        </attvalues>\n"
            gexf_content += "      </edge>\n"

        gexf_content += "    </edges>\n"
        gexf_content += "  </graph>\n"
        gexf_content += "</gexf>\n"

        return gexf_content
