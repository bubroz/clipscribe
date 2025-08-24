"""Unit tests for knowledge_graph_builder.py module."""
import pytest
from unittest.mock import patch, MagicMock
from clipscribe.retrievers.knowledge_graph_builder import KnowledgeGraphBuilder
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript, EnhancedEntity
from datetime import datetime


@pytest.fixture
def knowledge_graph_builder():
    """Create a KnowledgeGraphBuilder instance for testing."""
    return KnowledgeGraphBuilder()


@pytest.fixture
def mock_video_metadata():
    """Create mock video metadata."""
    return VideoMetadata(
        video_id="test_123",
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="test_channel",
        published_at=datetime.now(),
        duration=300,
        view_count=1000,
        description="Test description",
        tags=["test"]
    )


@pytest.fixture
def mock_transcript():
    """Create mock transcript."""
    return VideoTranscript(
        full_text="This is a test transcript.",
        segments=[{"text": "This is a test transcript.", "start": 0.0, "end": 5.0}],
    )


@pytest.fixture
def mock_entities():
    """Create mock entities for testing."""
    return [
        EnhancedEntity(
            name="John Doe",
            type="PERSON",
            mention_count=2,
            extraction_sources=["SpaCy"],
            canonical_form="John Doe",
            context_windows=[],
            aliases=["John", "Doe"],
            temporal_distribution=[],
        ),
        EnhancedEntity(
            name="Google",
            type="ORGANIZATION",
            mention_count=1,
            extraction_sources=["SpaCy"],
            canonical_form="Google",
            context_windows=[],
            aliases=["Alphabet"],
            temporal_distribution=[],
        ),
        EnhancedEntity(
            name="Machine Learning",
            type="CONCEPT",
            mention_count=3,
            extraction_sources=["GLiNER"],
            canonical_form="Machine Learning",
            context_windows=[],
            aliases=["ML", "AI"],
            temporal_distribution=[],
        )
    ]


@pytest.fixture
def mock_relationships():
    """Create mock relationships for testing."""
    return [
        {
            "subject": "John Doe",
            "predicate": "works_at",
            "object": "Google",
            "source": "REBEL",
            "evidence_chain": [
                {
                    "direct_quote": "John Doe works at Google",
                    "timestamp": "00:02:15",
                    "speaker": "Narrator",
                    "visual_context": "Company logo",
                    "context_window": "John Doe works at Google as a machine learning engineer",
                    "evidence_type": "spoken"
                }
            ],
            "supporting_mentions": 1,
            "contradictions": [],
            "visual_correlation": False,
            "properties": {}
        },
        {
            "subject": "Google",
            "predicate": "develops",
            "object": "Machine Learning",
            "source": "REBEL",
            "evidence_chain": [
                {
                    "direct_quote": "Google develops machine learning",
                    "timestamp": "00:05:30",
                    "speaker": "Narrator",
                    "visual_context": "Product demo",
                    "context_window": "Google develops advanced machine learning technologies",
                    "evidence_type": "spoken"
                }
            ],
            "supporting_mentions": 1,
            "contradictions": [],
            "visual_correlation": True,
            "properties": {}
        }
    ]


@pytest.fixture
def mock_video_intelligence(mock_video_metadata, mock_transcript, mock_entities, mock_relationships):
    """Create comprehensive mock VideoIntelligence object."""
    return VideoIntelligence(
        metadata=mock_video_metadata,
        transcript=mock_transcript,
        summary="Test summary",
        entities=mock_entities,
        relationships=mock_relationships,
        key_points=[
            {"text": "Key point 1", "importance": 0.8},
            {"text": "Key point 2", "importance": 0.9}
        ],
        topics=[
            {"name": "technology", "confidence": 0.9},
            {"name": "AI", "confidence": 0.8}
        ],
        processing_cost=0.15
    )


class TestKnowledgeGraphBuilder:
    """Test cases for KnowledgeGraphBuilder class."""

    def test_init_with_networkx_available(self, knowledge_graph_builder):
        """Test initialization when NetworkX is available."""
        assert knowledge_graph_builder is not None
        assert hasattr(knowledge_graph_builder, 'build_knowledge_graph')
        assert hasattr(knowledge_graph_builder, 'generate_gexf_content')

    @patch('clipscribe.retrievers.knowledge_graph_builder.HAS_NETWORKX', False)
    def test_init_without_networkx(self):
        """Test initialization when NetworkX is not available."""
        with pytest.raises(ImportError, match="NetworkX is required"):
            KnowledgeGraphBuilder()

    def test_build_knowledge_graph_success(self, knowledge_graph_builder, mock_video_intelligence):
        """Test successful knowledge graph building."""
        result = knowledge_graph_builder.build_knowledge_graph(mock_video_intelligence)

        assert result == mock_video_intelligence
        assert hasattr(result, 'knowledge_graph')
        assert result.knowledge_graph is not None

        # Verify graph structure
        kg = result.knowledge_graph
        assert "nodes" in kg
        assert "edges" in kg
        assert "node_count" in kg
        assert "edge_count" in kg

        # Verify node count (should have 3 entities)
        assert kg["node_count"] == 3

        # Verify edge count (should have 2 relationships)
        assert kg["edge_count"] == 2

    def test_build_knowledge_graph_empty_entities(self, knowledge_graph_builder, mock_video_metadata, mock_transcript):
        """Test knowledge graph building with no entities."""
        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            transcript=mock_transcript,
            summary="Test summary",
            entities=[],  # Empty entities
            relationships=[],
            key_points=[],
            topics=[]
        )

        result = knowledge_graph_builder.build_knowledge_graph(video_intel)

        assert result == video_intel
        assert hasattr(result, 'knowledge_graph')
        kg = result.knowledge_graph
        assert kg["node_count"] == 0
        assert kg["edge_count"] == 0

    def test_build_knowledge_graph_empty_relationships(self, knowledge_graph_builder, mock_video_metadata, mock_transcript, mock_entities):
        """Test knowledge graph building with entities but no relationships."""
        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            transcript=mock_transcript,
            summary="Test summary",
            entities=mock_entities,
            relationships=[],  # Empty relationships
            key_points=[],
            topics=[]
        )

        result = knowledge_graph_builder.build_knowledge_graph(video_intel)

        assert result == video_intel
        assert hasattr(result, 'knowledge_graph')
        kg = result.knowledge_graph
        assert kg["node_count"] == 3
        assert kg["edge_count"] == 0

    def test_build_knowledge_graph_node_attributes(self, knowledge_graph_builder, mock_video_intelligence):
        """Test that nodes have correct attributes in the knowledge graph."""
        result = knowledge_graph_builder.build_knowledge_graph(mock_video_intelligence)

        kg = result.knowledge_graph
        nodes = kg["nodes"]

        # Find John Doe node
        john_node = next(node for node in nodes if node["id"] == "John Doe")
        assert john_node["type"] == "PERSON"
        assert john_node["mention_count"] == 2
        assert "confidence" in john_node
        assert "extraction_sources" in john_node

        # Find Google node
        google_node = next(node for node in nodes if node["id"] == "Google")
        assert google_node["type"] == "ORGANIZATION"

        # Find Machine Learning node
        ml_node = next(node for node in nodes if node["id"] == "Machine Learning")
        assert ml_node["type"] == "CONCEPT"

    def test_build_knowledge_graph_edge_attributes(self, knowledge_graph_builder, mock_video_intelligence):
        """Test that edges have correct attributes in the knowledge graph."""
        result = knowledge_graph_builder.build_knowledge_graph(mock_video_intelligence)

        kg = result.knowledge_graph
        edges = kg["edges"]

        assert len(edges) == 2

        # Check first relationship (John Doe -> works_at -> Google)
        john_edge = next(edge for edge in edges if edge["source"] == "John Doe")
        assert john_edge["target"] == "Google"
        assert john_edge["predicate"] == "works_at"
        assert john_edge["confidence"] == 0.9
        assert john_edge["extraction_source"] == "REBEL"

        # Check second relationship (Google -> develops -> Machine Learning)
        google_edge = next(edge for edge in edges if edge["source"] == "Google")
        assert google_edge["target"] == "Machine Learning"
        assert google_edge["predicate"] == "develops"
        assert google_edge["confidence"] == 0.9

    def test_generate_gexf_content(self, knowledge_graph_builder, mock_video_intelligence):
        """Test GEXF content generation."""
        # First build the knowledge graph
        result = knowledge_graph_builder.build_knowledge_graph(mock_video_intelligence)
        kg = result.knowledge_graph

        gexf_content = knowledge_graph_builder.generate_gexf_content(kg)

        # Verify GEXF structure
        assert '<?xml version="1.0" encoding="UTF-8"?>' in gexf_content
        assert '<gexf' in gexf_content
        assert '<graph' in gexf_content
        assert '<nodes>' in gexf_content
        assert '<edges>' in gexf_content
        assert 'John Doe' in gexf_content
        assert 'Google' in gexf_content
        assert 'Machine Learning' in gexf_content
        assert 'works_at' in gexf_content
        assert 'develops' in gexf_content

    def test_generate_gexf_content_empty_graph(self, knowledge_graph_builder):
        """Test GEXF content generation with empty graph."""
        knowledge_graph = {
            "nodes": [],
            "edges": []
        }

        gexf_content = knowledge_graph_builder.generate_gexf_content(knowledge_graph)

        assert '<?xml version="1.0" encoding="UTF-8"?>' in gexf_content
        assert '<nodes>' in gexf_content
        assert '<edges>' in gexf_content
        # Should not contain any node content
        assert 'John Doe' not in gexf_content

    def test_generate_gexf_content_special_characters(self, knowledge_graph_builder):
        """Test GEXF content generation with special characters in names."""
        knowledge_graph = {
            "nodes": [
                {
                    "id": "John & Jane O'Connor",
                    "type": "PERSON",
                    "confidence": 0.9,
                    "mention_count": 1,
                    "occurrences": 1
                }
            ],
            "edges": []
        }

        gexf_content = knowledge_graph_builder.generate_gexf_content(knowledge_graph)

        # Special characters should be escaped
        assert 'John &amp; Jane O&apos;Connor' in gexf_content or 'John &amp; Jane O\'Connor' in gexf_content

    def test_build_knowledge_graph_with_large_dataset(self, knowledge_graph_builder, mock_video_metadata, mock_transcript):
        """Test knowledge graph building with many entities and relationships."""
        # Create 50 entities
        entities = []
        relationships = []

        for i in range(50):
            entities.append(EnhancedEntity(
                name=f"Entity{i}",
                type="PERSON" if i % 2 == 0 else "ORGANIZATION",
                mention_count=i + 1,
                extraction_sources=["SpaCy"],
                canonical_form=f"Entity{i}",
                context_windows=[],
                aliases=[],
                temporal_distribution=[],
            ))

            if i > 0:
                relationships.append({
                    "subject": f"Entity{i-1}",
                    "predicate": "related_to",
                    "object": f"Entity{i}",
                    "confidence": 0.7,
                    "extraction_source": "REBEL"
                })

        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            transcript=mock_transcript,
            summary="Large test summary",
            entities=entities,
            relationships=relationships,
            key_points=[],
            topics=[]
        )

        result = knowledge_graph_builder.build_knowledge_graph(video_intel)

        kg = result.knowledge_graph
        assert kg["node_count"] == 50
        assert kg["edge_count"] == 49

    def test_build_knowledge_graph_none_video_intelligence(self, knowledge_graph_builder):
        """Test handling of None video intelligence."""
        with pytest.raises(AttributeError):
            knowledge_graph_builder.build_knowledge_graph(None)

    def test_build_knowledge_graph_missing_attributes(self, knowledge_graph_builder, mock_video_metadata, mock_transcript):
        """Test handling of video intelligence with missing attributes."""
        # Create a mock object without entities attribute
        mock_video = MagicMock()
        mock_video.metadata = mock_video_metadata
        mock_video.transcript = mock_transcript
        del mock_video.entities  # Remove entities attribute

        with pytest.raises(AttributeError):
            knowledge_graph_builder.build_knowledge_graph(mock_video)

    def test_generate_gexf_content_with_missing_node_data(self, knowledge_graph_builder):
        """Test GEXF generation with missing node data."""
        knowledge_graph = {
            "nodes": [
                {
                    "id": "John Doe",
                    # Missing type, confidence, etc.
                }
            ],
            "edges": []
        }

        gexf_content = knowledge_graph_builder.generate_gexf_content(knowledge_graph)

        # Should handle missing data gracefully
        assert 'John Doe' in gexf_content
        assert 'unknown' in gexf_content  # Default type

    def test_generate_gexf_content_with_missing_edge_data(self, knowledge_graph_builder):
        """Test GEXF generation with missing edge data."""
        knowledge_graph = {
            "nodes": [
                {"id": "Node1", "type": "PERSON", "confidence": 0.9, "mention_count": 1, "occurrences": 1},
                {"id": "Node2", "type": "PERSON", "confidence": 0.9, "mention_count": 1, "occurrences": 1}
            ],
            "edges": [
                {
                    "source": "Node1",
                    "target": "Node2",
                    # Missing predicate and confidence
                }
            ]
        }

        gexf_content = knowledge_graph_builder.generate_gexf_content(knowledge_graph)

        # Should handle missing data gracefully
        assert 'Node1' in gexf_content
        assert 'Node2' in gexf_content
        assert 'related_to' in gexf_content  # Default predicate

    def test_build_knowledge_graph_relationship_only_entities(self, knowledge_graph_builder, mock_video_metadata, mock_transcript):
        """Test knowledge graph building with relationships but no direct entity connections."""
        entities = [
            EnhancedEntity(name="Entity1", type="PERSON", mention_count=1, extraction_sources=["SpaCy"], canonical_form="Entity1", context_windows=[], aliases=[], temporal_distribution=[]),
            EnhancedEntity(name="Entity2", type="PERSON", mention_count=1, extraction_sources=["SpaCy"], canonical_form="Entity2", context_windows=[], aliases=[], temporal_distribution=[]),
            EnhancedEntity(name="Entity3", type="ORGANIZATION", mention_count=1, extraction_sources=["SpaCy"], canonical_form="Entity3", context_windows=[], aliases=[], temporal_distribution=[])
        ]

        relationships = [
            {
                "subject": "Entity1",
                "predicate": "knows",
                "object": "Entity2",
                "confidence": 0.8,
                "extraction_source": "REBEL"
            },
            {
                "subject": "Entity2",
                "predicate": "works_at",
                "object": "Entity3",
                "confidence": 0.9,
                "extraction_source": "REBEL"
            }
        ]

        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            transcript=mock_transcript,
            summary="Test summary",
            entities=entities,
            relationships=relationships,
            key_points=[],
            topics=[]
        )

        result = knowledge_graph_builder.build_knowledge_graph(video_intel)

        kg = result.knowledge_graph
        assert kg["node_count"] == 3
        assert kg["edge_count"] == 2

        # Verify edges
        edges = kg["edges"]
        assert len(edges) == 2
        assert any(edge["source"] == "Entity1" and edge["target"] == "Entity2" for edge in edges)
        assert any(edge["source"] == "Entity2" and edge["target"] == "Entity3" for edge in edges)

    def test_build_knowledge_graph_complex_relationships(self, knowledge_graph_builder, mock_video_metadata, mock_transcript):
        """Test knowledge graph building with complex relationship patterns."""
        entities = [
            EnhancedEntity(name="CEO", type="PERSON", mention_count=1, extraction_sources=["SpaCy"], canonical_form="CEO", context_windows=[], aliases=[], temporal_distribution=[]),
            EnhancedEntity(name="Company", type="ORGANIZATION", mention_count=1, extraction_sources=["SpaCy"], canonical_form="Company", context_windows=[], aliases=[], temporal_distribution=[]),
            EnhancedEntity(name="Product", type="PRODUCT", mention_count=1, extraction_sources=["SpaCy"], canonical_form="Product", context_windows=[], aliases=[], temporal_distribution=[]),
            EnhancedEntity(name="Technology", type="CONCEPT", mention_count=1, extraction_sources=["GLiNER"], canonical_form="Technology", context_windows=[], aliases=[], temporal_distribution=[])
        ]

        relationships = [
            {
                "subject": "CEO",
                "predicate": "leads",
                "object": "Company",
                "confidence": 0.95,
                "extraction_source": "REBEL"
            },
            {
                "subject": "Company",
                "predicate": "develops",
                "object": "Product",
                "confidence": 0.88,
                "extraction_source": "REBEL"
            },
            {
                "subject": "Product",
                "predicate": "uses",
                "object": "Technology",
                "confidence": 0.92,
                "extraction_source": "REBEL"
            },
            {
                "subject": "CEO",
                "predicate": "champions",
                "object": "Technology",
                "confidence": 0.75,
                "extraction_source": "REBEL"
            }
        ]

        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            transcript=mock_transcript,
            summary="Complex relationships test",
            entities=entities,
            relationships=relationships,
            key_points=[],
            topics=[]
        )

        result = knowledge_graph_builder.build_knowledge_graph(video_intel)

        kg = result.knowledge_graph
        assert kg["node_count"] == 4
        assert kg["edge_count"] == 4

        # Verify complex relationship patterns
        edges = kg["edges"]
        assert len(edges) == 4

        # Check for expected relationships
        relationship_patterns = [
            ("CEO", "leads", "Company"),
            ("Company", "develops", "Product"),
            ("Product", "uses", "Technology"),
            ("CEO", "champions", "Technology")
        ]

        for source, predicate, target in relationship_patterns:
            assert any(
                edge["source"] == source and
                edge["predicate"] == predicate and
                edge["target"] == target
                for edge in edges
            ), f"Missing relationship: {source} -> {predicate} -> {target}"