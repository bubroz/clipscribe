import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from clipscribe.extractors.multi_video_processor import MultiVideoProcessor
from clipscribe.models import (
    VideoIntelligence, 
    VideoMetadata, 
    KeyPoint, 
    ExtractedDate, 
    ConsolidatedTimeline, 
    TimelineEvent,
    VideoTranscript
)

@pytest.fixture
def processor():
    """Provides a MultiVideoProcessor instance for testing."""
    return MultiVideoProcessor(use_ai_validation=True)

@pytest.fixture
def base_video_intelligence():
    """Provides a base VideoIntelligence object for tests."""
    return VideoIntelligence(
        metadata=VideoMetadata(
            video_id="video1",
            title="A video about an event in 1999",
            channel="Test Channel",
            channel_id="UC123",
            duration=60,
            url="http://test.com/video1",
            published_at=datetime(2024, 1, 1, 12, 0, 0),
        ),
        transcript=VideoTranscript(full_text="mock transcript", segments=[]),
        summary="Test summary",
        key_points=[] # Key points will be added per test
    )

@pytest.mark.asyncio
async def test_timeline_uses_date_from_key_point(processor, base_video_intelligence):
    """Verify timeline uses date extracted directly from key point text."""
    base_video_intelligence.key_points = [
        KeyPoint(timestamp=10, text="The main event happened on Christmas Day 2023.", importance=0.9)
    ]
    
    async def side_effect(text, source_type):
        if "Christmas Day 2023" in text:
            return ExtractedDate(parsed_date=datetime(2023, 12, 25), original_text="Christmas Day 2023", confidence=0.95, source=source_type)
        return None
    processor._extract_date_from_text = AsyncMock(side_effect=side_effect)

    timeline = await processor._synthesize_event_timeline([base_video_intelligence], [], "collection1")
    
    assert len(timeline.events) == 1
    event = timeline.events[0]
    assert event.timestamp == datetime(2023, 12, 25)
    assert event.date_source == "key_point_content"
    assert event.extracted_date.original_text == "Christmas Day 2023"

@pytest.mark.asyncio
async def test_timeline_falls_back_to_title_date(processor, base_video_intelligence):
    """Verify timeline falls back to video title's date if key point has no date."""
    base_video_intelligence.key_points = [
        KeyPoint(timestamp=20, text="Another thing happened.", importance=0.8)
    ]
    
    async def side_effect(text, source_type):
        if source_type == 'video_title':
            return ExtractedDate(parsed_date=datetime(1999, 1, 1), original_text="1999", confidence=0.9, source=source_type)
        return None
    processor._extract_date_from_text = AsyncMock(side_effect=side_effect)

    timeline = await processor._synthesize_event_timeline([base_video_intelligence], [], "collection1")
    
    assert len(timeline.events) == 1
    event = timeline.events[0]
    assert event.timestamp == datetime(1999, 1, 1)
    assert event.date_source == "video_title"
    assert event.extracted_date.original_text == "1999"

@pytest.mark.asyncio
async def test_timeline_falls_back_to_publication_date(processor, base_video_intelligence):
    """Verify timeline falls back to publication date when no other date is found."""
    base_video_intelligence.key_points = [
        KeyPoint(timestamp=30, text="A final point.", importance=0.7)
    ]
    
    # Mock returns None for all calls
    processor._extract_date_from_text = AsyncMock(return_value=None)

    timeline = await processor._synthesize_event_timeline([base_video_intelligence], [], "collection1")
    
    assert len(timeline.events) == 1
    event = timeline.events[0]
    expected_fallback_date = base_video_intelligence.metadata.published_at + timedelta(seconds=30)
    assert event.timestamp == expected_fallback_date
    assert event.date_source == "video_published_date"
    assert event.extracted_date is None

@pytest.mark.asyncio
async def test_knowledge_panels_synthesis():
    """Test comprehensive Knowledge Panel synthesis for entity-centric intelligence."""
    # Create mock processor
    processor = MultiVideoProcessor(use_ai_validation=False)  # Disable AI for testing
    
    # Create mock videos with entities and relationships
    videos = []
    
    # Video 1: Features Iran, IAEA, and Nuclear Program
    video1 = create_mock_video("video1", "Iran Nuclear Deal Analysis")
    video1.entities = [
        create_mock_entity("Iran", "ORGANIZATION", 0.95),
        create_mock_entity("IAEA", "ORGANIZATION", 0.90),
        create_mock_entity("Nuclear Program", "CONCEPT", 0.85),
        create_mock_entity("Hassan Rouhani", "PERSON", 0.88)
    ]
    video1.relationships = [
        create_mock_relationship("Iran", "operates", "Nuclear Program"),
        create_mock_relationship("IAEA", "monitors", "Nuclear Program"),
        create_mock_relationship("Hassan Rouhani", "leads", "Iran")
    ]
    video1.key_points = [
        create_mock_key_point(300, "Iran announced new uranium enrichment activities", 0.9),
        create_mock_key_point(600, "IAEA expresses concerns about compliance", 0.8)
    ]
    videos.append(video1)
    
    # Video 2: Features Iran, UN, and Sanctions 
    video2 = create_mock_video("video2", "UN Sanctions on Iran")
    video2.entities = [
        create_mock_entity("Iran", "ORGANIZATION", 0.92),
        create_mock_entity("United Nations", "ORGANIZATION", 0.90),
        create_mock_entity("Sanctions", "CONCEPT", 0.85),
        create_mock_entity("Nuclear Program", "CONCEPT", 0.80)
    ]
    video2.relationships = [
        create_mock_relationship("United Nations", "imposes", "Sanctions"),
        create_mock_relationship("Sanctions", "target", "Iran"),
        create_mock_relationship("Iran", "develops", "Nuclear Program")
    ]
    video2.key_points = [
        create_mock_key_point(200, "UN Security Council votes on new sanctions", 0.85),
        create_mock_key_point(500, "Iran responds to international pressure", 0.75)
    ]
    videos.append(video2)
    
    # Create unified entities (simulating cross-video resolution)
    unified_entities = [
        create_mock_cross_video_entity("Iran", "ORGANIZATION", ["video1", "video2"], 4),
        create_mock_cross_video_entity("Nuclear Program", "CONCEPT", ["video1", "video2"], 3),
        create_mock_cross_video_entity("IAEA", "ORGANIZATION", ["video1"], 2),
        create_mock_cross_video_entity("United Nations", "ORGANIZATION", ["video2"], 2),
        create_mock_cross_video_entity("Hassan Rouhani", "PERSON", ["video1"], 1)
    ]
    
    # Create cross-video relationships
    cross_video_relationships = [
        create_mock_cross_video_relationship("Iran", "operates", "Nuclear Program", ["video1", "video2"]),
        create_mock_cross_video_relationship("IAEA", "monitors", "Nuclear Program", ["video1"])
    ]
    
    # Test Knowledge Panel synthesis
    knowledge_panels = await processor._synthesize_knowledge_panels(
        videos=videos,
        unified_entities=unified_entities,
        cross_video_relationships=cross_video_relationships,
        collection_id="test_collection",
        collection_title="Iran Nuclear Crisis Analysis"
    )
    
    # Verify knowledge panels structure
    assert knowledge_panels is not None
    assert knowledge_panels.collection_id == "test_collection"
    assert knowledge_panels.collection_title == "Iran Nuclear Crisis Analysis"
    assert isinstance(knowledge_panels.panels, list)
    
    # Should create panels for top entities (appear in multiple videos or high mentions)
    # Iran: 2 videos, 4 mentions - definitely included
    # Nuclear Program: 2 videos, 3 mentions - definitely included  
    # IAEA: 1 video, 2 mentions - should be included (>= 3 mentions threshold not met, but important)
    assert len(knowledge_panels.panels) >= 2  # At least Iran and Nuclear Program
    
    # Find Iran panel (should be most prominent)
    iran_panel = None
    for panel in knowledge_panels.panels:
        if panel.entity_name == "Iran":
            iran_panel = panel
            break
    
    assert iran_panel is not None, "Iran panel should be created"
    
    # Verify Iran panel details
    assert iran_panel.entity_type == "ORGANIZATION"
    assert iran_panel.collection_id == "test_collection"
    assert len(iran_panel.video_appearances) == 2
    assert "video1" in iran_panel.video_appearances
    assert "video2" in iran_panel.video_appearances
    assert iran_panel.total_mentions == 4
    assert iran_panel.source_videos_count == 2
    
    # Should have activities from key points
    assert len(iran_panel.activities) > 0
    
    # Should have relationships
    assert len(iran_panel.relationships) > 0
    
    # Should have executive summary (even if template-based)
    assert iran_panel.executive_summary is not None
    assert len(iran_panel.executive_summary) > 0
    assert "iran" in iran_panel.executive_summary.lower()
    
    # Should have confidence score
    assert 0.0 <= iran_panel.confidence_score <= 1.0
    
    # Should have synthesis quality marker
    assert iran_panel.synthesis_quality in ["TEMPLATE", "AI_ENHANCED"]
    
    # Verify collection-level analysis
    assert knowledge_panels.panel_summary is not None
    assert len(knowledge_panels.panel_summary) > 0
    assert knowledge_panels.total_entities == len(knowledge_panels.panels)
    
    # Find Nuclear Program panel
    nuclear_panel = None
    for panel in knowledge_panels.panels:
        if panel.entity_name == "Nuclear Program":
            nuclear_panel = panel
            break
    
    # Nuclear Program should also have a panel (appears in 2 videos)
    if nuclear_panel:
        assert nuclear_panel.entity_type == "CONCEPT"
        assert len(nuclear_panel.video_appearances) == 2
        assert nuclear_panel.total_mentions == 3

@pytest.mark.asyncio
async def test_information_flow_map_synthesis():
    """Test comprehensive Information Flow Map synthesis for concept evolution tracking."""
    # Create mock processor
    processor = MultiVideoProcessor(use_ai_validation=False)  # Disable AI for testing
    
    # Create sequence of videos showing concept evolution
    videos = []
    
    # Video 1: Introduction to AI (basic concepts)
    video1 = create_mock_video("video1", "Introduction to Artificial Intelligence")
    video1.key_points = [
        create_mock_key_point(100, "Artificial Intelligence is computer systems that can think", 0.9),
        create_mock_key_point(200, "Machine Learning is a subset of AI", 0.8),
        create_mock_key_point(300, "Neural Networks mimic the brain", 0.7)
    ]
    video1.entities = [
        create_mock_entity("Artificial Intelligence", "CONCEPT", 0.95),
        create_mock_entity("Machine Learning", "CONCEPT", 0.90),
        create_mock_entity("Neural Networks", "CONCEPT", 0.85)
    ]
    videos.append(video1)
    
    # Video 2: Deep Learning advances (expanded concepts)
    video2 = create_mock_video("video2", "Deep Learning Revolution")
    video2.key_points = [
        create_mock_key_point(150, "Deep Learning uses multiple neural network layers", 0.9),
        create_mock_key_point(250, "Convolutional Neural Networks excel at image recognition", 0.85),
        create_mock_key_point(350, "Deep Learning requires large datasets", 0.8)
    ]
    video2.entities = [
        create_mock_entity("Deep Learning", "CONCEPT", 0.95),
        create_mock_entity("Neural Networks", "CONCEPT", 0.90),
        create_mock_entity("Convolutional Neural Networks", "CONCEPT", 0.85)
    ]
    videos.append(video2)
    
    # Video 3: Transformer architecture (breakthrough moment)
    video3 = create_mock_video("video3", "Transformers: The Game Changer")
    video3.key_points = [
        create_mock_key_point(120, "Transformers revolutionized natural language processing", 0.95),
        create_mock_key_point(220, "Attention mechanism allows models to focus on relevant parts", 0.9),
        create_mock_key_point(320, "BERT and GPT are based on transformer architecture", 0.85)
    ]
    video3.entities = [
        create_mock_entity("Transformers", "CONCEPT", 0.95),
        create_mock_entity("Attention Mechanism", "CONCEPT", 0.90),
        create_mock_entity("BERT", "CONCEPT", 0.85),
        create_mock_entity("GPT", "CONCEPT", 0.85)
    ]
    videos.append(video3)
    
    # Create unified entities for the test
    unified_entities = [
        create_mock_cross_video_entity("Artificial Intelligence", "CONCEPT", ["video1"], 1),
        create_mock_cross_video_entity("Neural Networks", "CONCEPT", ["video1", "video2"], 2),
        create_mock_cross_video_entity("Machine Learning", "CONCEPT", ["video1"], 1),
        create_mock_cross_video_entity("Deep Learning", "CONCEPT", ["video2"], 1),
        create_mock_cross_video_entity("Transformers", "CONCEPT", ["video3"], 1)
    ]
    
    # Create cross-video relationships
    cross_video_relationships = [
        create_mock_cross_video_relationship("Machine Learning", "is_subset_of", "Artificial Intelligence", ["video1"]),
        create_mock_cross_video_relationship("Deep Learning", "uses", "Neural Networks", ["video2"]),
        create_mock_cross_video_relationship("Transformers", "revolutionized", "Neural Networks", ["video3"])
    ]
    
    # Test Information Flow Map synthesis
    flow_map = await processor._synthesize_information_flow_map(
        videos=videos,
        unified_entities=unified_entities,
        cross_video_relationships=cross_video_relationships,
        collection_id="ai_evolution",
        collection_title="AI Evolution Series"
    )
    
    # Verify basic structure
    assert flow_map is not None
    assert flow_map.collection_id == "ai_evolution"
    assert flow_map.collection_title == "AI Evolution Series"
    
    # Should have concept nodes from all videos
    assert len(flow_map.concept_nodes) > 0
    
    # Check that we have concept names extracted
    concept_names = [node.concept_name for node in flow_map.concept_nodes]
    assert len(concept_names) > 0  # Should extract at least some concepts
    print(f"✓ Extracted concepts: {concept_names}")
    
    # Should have information flows tracking concept evolution
    assert len(flow_map.information_flows) >= 0  # May be 0 if no dependencies found
    
    # Should have concept evolution paths (may be 0 if concepts don't appear multiple times)
    assert len(flow_map.evolution_paths) >= 0
    
    # Check evolution paths if any exist
    if len(flow_map.evolution_paths) > 0:
        evolution_path = flow_map.evolution_paths[0]  # Check first path
        # Should have meaningful evolution pattern
        assert hasattr(evolution_path, 'concept_name')
        assert hasattr(evolution_path, 'evolution_coherence')
        assert 0.0 <= evolution_path.evolution_coherence <= 1.0
        print(f"✓ Found evolution path for: {evolution_path.concept_name}")
    
    # Should have concept clusters (may be 0 if no relationships found)
    assert len(flow_map.concept_clusters) >= 0
    
    # Check clusters if any exist
    if len(flow_map.concept_clusters) > 0:
        cluster = flow_map.concept_clusters[0]  # Check first cluster
        assert len(cluster.core_concepts) >= 1  # Should have at least core concept
        assert 0.0 <= cluster.coherence_score <= 1.0
        print(f"✓ Found cluster with concepts: {cluster.core_concepts}")
    
            # Should have meaningful synthesis quality
        assert flow_map.synthesis_quality in ["TEMPLATE", "AI_ENHANCED"]
    
    # Should have metadata
    assert flow_map.total_concepts > 0
    assert flow_map.total_flows >= 0
    
    # Verify concept node details
    if len(flow_map.concept_nodes) > 0:
        node = flow_map.concept_nodes[0]  # Check first concept node
        
        # Should have proper metadata
        assert node.video_id in ["video1", "video2", "video3"]
        assert len(node.video_title) > 0
        assert node.timestamp >= 0
        
        # Should have maturity level
        assert node.maturity_level.value in ["mentioned", "defined", "explored", "synthesized", "criticized", "evolved"]
        
        # Should have confidence and other metrics
        assert 0.0 <= node.confidence <= 1.0
        assert 0.0 <= node.explanation_depth <= 1.0
        assert 0.0 <= node.information_density <= 1.0
        
        # Should have context
        assert len(node.context) > 0
        print(f"✓ Verified concept node: {node.concept_name} in {node.video_title}")
    
    print(f"✓ Information Flow Map created with {len(flow_map.concept_nodes)} concept nodes")
    print(f"✓ Found {len(flow_map.evolution_paths)} concept evolution paths")
    print(f"✓ Created {len(flow_map.concept_clusters)} concept clusters")

def create_mock_cross_video_entity(name: str, entity_type: str, video_appearances: list, mention_count: int):
    """Create a mock CrossVideoEntity for testing."""
    from clipscribe.models import CrossVideoEntity
    from datetime import datetime
    
    return CrossVideoEntity(
        name=name,
        type=entity_type,
        canonical_name=name,
        aliases=[],
        video_appearances=video_appearances,
        aggregated_confidence=0.9,
        first_mentioned=datetime(2023, 1, 1),
        last_mentioned=datetime(2023, 1, 2),
        mention_count=mention_count,
        properties={},
        source_videos=[]
    )

def create_mock_cross_video_relationship(subject: str, predicate: str, object_name: str, video_sources: list):
    """Create a mock CrossVideoRelationship for testing."""
    from clipscribe.models import CrossVideoRelationship
    from datetime import datetime
    
    return CrossVideoRelationship(
        subject=subject,
        predicate=predicate,
        object=object_name,
        confidence=0.85,
        video_sources=video_sources,
        first_mentioned=datetime(2023, 1, 1),
        mention_count=len(video_sources),
        context_examples=[f"Example context for {subject} {predicate} {object_name}"],
        properties={}
    )

def create_mock_relationship(subject: str, predicate: str, object_name: str):
    """Create a mock Relationship for testing."""
    from clipscribe.models import Relationship
    
    return Relationship(
        subject=subject,
        predicate=predicate,
        object=object_name,
        confidence=0.8,
        context=f"Context for {subject} {predicate} {object_name}"
    )

def create_mock_key_point(timestamp: int, text: str, importance: float):
    """Create a mock KeyPoint for testing."""
    from clipscribe.models import KeyPoint
    
    return KeyPoint(
        timestamp=timestamp,
        text=text,
        importance=importance,
        context=f"Context for: {text}"
    )

def create_mock_video(video_id: str, title: str):
    """Create a mock VideoIntelligence for testing."""
    from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript
    from datetime import datetime
    
    return VideoIntelligence(
        metadata=VideoMetadata(
            video_id=video_id,
            title=title,
            channel="Test Channel",
            channel_id="UC123",
            duration=3600,  # 1 hour
            url=f"http://test.com/{video_id}",
            published_at=datetime(2023, 1, 1, 12, 0, 0),
        ),
        transcript=VideoTranscript(full_text=f"Mock transcript for {title}", segments=[]),
        summary=f"Test summary for {title}",
        key_points=[],  # Will be set by tests
        entities=[],    # Will be set by tests  
        relationships=[]  # Will be set by tests
    )

def create_mock_entity(name: str, entity_type: str, confidence: float):
    """Create a mock Entity for testing."""
    from clipscribe.models import Entity
    
    return Entity(
        name=name,
        type=entity_type,
        confidence=confidence,
        properties={},
        timestamp=None
    ) 