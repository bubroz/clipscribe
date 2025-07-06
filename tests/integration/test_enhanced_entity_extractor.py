"""Test enhanced entity extractor integration."""

import pytest
from unittest.mock import Mock
from clipscribe.models import Entity, EnhancedEntity, VideoTranscript
from clipscribe.extractors.enhanced_entity_extractor import EnhancedEntityExtractor


@pytest.mark.asyncio
async def test_enhanced_entity_extraction_unit():
    """
    Unit test to verify that the EnhancedEntityExtractor correctly processes
    entities and returns EnhancedEntity objects with populated metadata.
    """
    # Create mock entities (simulating output from SpaCy/GLiNER)
    mock_entities = [
        Entity(entity="Joe Biden", type="PERSON", confidence=0.9, source="spacy"),
        Entity(entity="President Biden", type="PERSON", confidence=0.8, source="gliner"),
        Entity(entity="Biden", type="PERSON", confidence=0.7, source="spacy"),
        Entity(entity="NSO Group", type="ORG", confidence=0.95, source="gliner"),
        Entity(entity="Israel", type="GPE", confidence=0.9, source="spacy"),
        Entity(entity="Pegasus", type="MISC", confidence=0.85, source="gliner"),
        Entity(entity="Pegasus spyware", type="MISC", confidence=0.9, source="spacy"),
    ]
    
    # Create mock transcript segments
    mock_segments = [
        {
            "text": "President Biden announced new sanctions against NSO Group, the Israeli company behind Pegasus spyware.",
            "timestamp": "00:01:30",
            "speaker": "Narrator"
        },
        {
            "text": "Biden emphasized that this surveillance technology threatens human rights globally.",
            "timestamp": "00:02:15", 
            "speaker": "Narrator"
        },
        {
            "text": "The Pegasus spyware has been used to target journalists and activists in multiple countries.",
            "timestamp": "00:03:45",
            "speaker": "Expert"
        }
    ]
    
    # Initialize the enhanced entity extractor
    extractor = EnhancedEntityExtractor()
    
    # Process entities with enhancement
    enhanced_entities = extractor.enhance_entities(
        entities=mock_entities,
        transcript_segments=mock_segments,
        visual_data=None
    )
    
    # --- Assertions ---
    
    # 1. Check that entities were processed
    assert enhanced_entities, "No enhanced entities were returned."
    assert len(enhanced_entities) > 0, "Enhanced entities list is empty."
    
    # 2. Verify all returned entities are EnhancedEntity objects
    for entity in enhanced_entities:
        assert isinstance(entity, EnhancedEntity), f"Entity {entity.entity} is not an EnhancedEntity object."
    
    # 3. Check that similar entities were merged (Biden variations)
    biden_entities = [e for e in enhanced_entities if "biden" in e.entity.lower()]
    assert len(biden_entities) == 1, f"Expected 1 Biden entity after merging, got {len(biden_entities)}"
    
    biden_entity = biden_entities[0]
    assert biden_entity.canonical_form in ["Joe Biden", "President Biden"], "Biden canonical form not set correctly"
    assert biden_entity.mention_count >= 3, f"Biden should have 3+ mentions, got {biden_entity.mention_count}"
    assert len(biden_entity.aliases) >= 1, "Biden should have aliases"
    
    # 4. Check Pegasus entities were merged
    pegasus_entities = [e for e in enhanced_entities if "pegasus" in e.entity.lower()]
    assert len(pegasus_entities) == 1, f"Expected 1 Pegasus entity after merging, got {len(pegasus_entities)}"
    
    pegasus_entity = pegasus_entities[0]
    assert pegasus_entity.mention_count >= 2, f"Pegasus should have 2+ mentions, got {pegasus_entity.mention_count}"
    
    # 5. Verify confidence scores are calculated
    for entity in enhanced_entities:
        assert entity.confidence is not None, f"Entity {entity.entity} missing confidence score"
        assert 0.0 <= entity.confidence <= 1.0, f"Entity {entity.entity} confidence out of range: {entity.confidence}"
    
    # 6. Verify source attribution
    for entity in enhanced_entities:
        assert entity.extraction_sources, f"Entity {entity.entity} missing extraction sources"
        assert len(entity.extraction_sources) > 0, f"Entity {entity.entity} has empty extraction sources"
        
        # Check source confidence mapping
        assert entity.source_confidence, f"Entity {entity.entity} missing source confidence"
        for source in entity.extraction_sources:
            assert source in entity.source_confidence, f"Source {source} missing from confidence mapping"
    
    # 7. Verify context windows were extracted
    entities_with_context = [e for e in enhanced_entities if len(e.context_windows) > 0]
    assert len(entities_with_context) > 0, "No entities have context windows"
    
    # Check context window structure
    for entity in entities_with_context:
        for context in entity.context_windows:
            assert context.text, "Context window missing text"
            assert context.timestamp, "Context window missing timestamp"
            assert context.confidence > 0, "Context window missing confidence"
    
    # 8. Verify temporal distribution
    entities_with_temporal = [e for e in enhanced_entities if len(e.temporal_distribution) > 0]
    assert len(entities_with_temporal) > 0, "No entities have temporal distribution"
    
    # 9. Check specific entity properties
    nso_entities = [e for e in enhanced_entities if "nso" in e.entity.lower()]
    if nso_entities:
        nso_entity = nso_entities[0]
        assert nso_entity.type == "ORG", f"NSO Group should be ORG, got {nso_entity.type}"
        assert nso_entity.confidence > 0.7, f"NSO Group should have reasonable confidence, got {nso_entity.confidence}"
    
    print(f"✅ Successfully processed {len(enhanced_entities)} enhanced entities:")
    for entity in enhanced_entities:
        print(f"  - {entity.canonical_form} ({entity.type}): {entity.mention_count} mentions, confidence={entity.confidence:.3f}")
        print(f"    Sources: {entity.extraction_sources}")
        print(f"    Aliases: {entity.aliases}")
        print(f"    Context windows: {len(entity.context_windows)}")
        print(f"    Temporal mentions: {len(entity.temporal_distribution)}")
        print()


def test_enhanced_entity_extractor_initialization():
    """Test that EnhancedEntityExtractor initializes correctly."""
    extractor = EnhancedEntityExtractor()
    
    # Check that type confidence modifiers are set
    assert extractor.type_confidence_modifiers is not None
    assert "PERSON" in extractor.type_confidence_modifiers
    assert "ORG" in extractor.type_confidence_modifiers
    
    # Check high quality sources
    assert extractor.high_quality_sources is not None
    assert "spacy" in extractor.high_quality_sources
    assert "gliner" in extractor.high_quality_sources
    
    # Check title patterns
    assert extractor.title_patterns is not None
    assert len(extractor.title_patterns) > 0


def test_canonical_form_normalization():
    """Test that canonical form normalization works correctly."""
    extractor = EnhancedEntityExtractor()
    
    # Test title removal
    assert extractor._get_canonical_form("President Biden") == "Biden"
    assert extractor._get_canonical_form("Dr. Smith") == "Smith"
    assert extractor._get_canonical_form("CEO Johnson") == "Johnson"
    
    # Test whitespace normalization
    assert extractor._get_canonical_form("  Joe   Biden  ") == "Joe Biden"
    
    # Test no change needed
    assert extractor._get_canonical_form("NSO Group") == "NSO Group"


def test_entity_similarity_detection():
    """Test that entity similarity detection works correctly."""
    extractor = EnhancedEntityExtractor()
    
    # Test exact match
    assert extractor._are_entities_similar("Biden", "biden")
    
    # Test substring match
    assert extractor._are_entities_similar("Biden", "Joe Biden")
    assert extractor._are_entities_similar("NSO", "NSO Group")
    
    # Test abbreviation (simple cases that the implementation handles)
    assert extractor._are_abbreviations("USA", "United States America")
    assert extractor._are_abbreviations("AI", "Artificial Intelligence")
    
    # Test no match
    assert not extractor._are_entities_similar("Biden", "Trump")
    assert not extractor._are_entities_similar("Apple", "Microsoft") 