"""
Test Entity Quality Improvements for ClipScribe.

This test validates the comprehensive entity quality enhancement system:
- Dynamic confidence calculation (replaces hardcoded 0.85)
- Language filtering (removes non-English noise)
- False positive detection and removal
- Source attribution correction
- Enhanced SpaCy and REBEL confidence scoring

Ensures the quality improvements work as expected :-)
"""

import pytest
import asyncio
from typing import List

from src.clipscribe.models import Entity, VideoIntelligence, VideoMetadata, VideoTranscript
from src.clipscribe.extractors.entity_quality_filter import EntityQualityFilter, QualityMetrics
from src.clipscribe.extractors.spacy_extractor import SpacyEntityExtractor
from src.clipscribe.extractors.rebel_extractor import REBELExtractor


class TestEntityQualityImprovements:
    """Test comprehensive entity quality improvements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quality_filter = EntityQualityFilter(
            min_confidence_threshold=0.6,
            language_confidence_threshold=0.8
        )
        
        # Sample video intelligence for testing
        self.sample_video_intel = VideoIntelligence(
            video_url="https://youtube.com/watch?v=test",
            title="Test Video",
            metadata=VideoMetadata(
                video_id="test123",
                duration=300,
                view_count=1000
            ),
            transcript=VideoTranscript(
                full_text="John Smith works at Microsoft Corporation. He announced a new product launch.",
                segments=[]
            ),
            entities=[],
            relationships=[]
        )
    
    def test_false_positive_removal(self):
        """Test that obvious false positives are removed."""
        # Create entities with false positives
        test_entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.85, properties={"source": "SpaCy"}),
            Entity(name="Microsoft", type="ORGANIZATION", confidence=0.85, properties={"source": "SpaCy"}),
            # False positives
            Entity(name="uh", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="a", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="!!!", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="", type="LOCATION", confidence=0.85, properties={"source": "GLiNER"}),
        ]
        
        # Apply false positive removal
        filtered = self.quality_filter._remove_false_positives(
            test_entities, 
            QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0.0, {}, 0.0)
        )
        
        # Should keep only valid entities
        assert len(filtered) == 2
        valid_names = {entity.name for entity in filtered}
        assert "John Smith" in valid_names
        assert "Microsoft" in valid_names
        assert "uh" not in valid_names
        assert "a" not in valid_names
    
    def test_language_filtering(self):
        """Test that non-English entities are filtered out."""
        # Create entities with mixed languages
        test_entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.85, properties={"source": "SpaCy"}),
            Entity(name="Microsoft", type="ORGANIZATION", confidence=0.85, properties={"source": "SpaCy"}),
            # Non-English entities
            Entity(name="Afirmar Categóricamente Que", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="Lo Cruzamos", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="Bien Été Ciblé Par Le Client", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="C'Est De Lui Écrire", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
        ]
        
        # Apply language filtering
        metrics = QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0.0, {}, 0.0)
        filtered = self.quality_filter._filter_non_english_entities(test_entities, metrics)
        
        # Should keep only English entities
        assert len(filtered) == 2
        valid_names = {entity.name for entity in filtered}
        assert "John Smith" in valid_names
        assert "Microsoft" in valid_names
        assert metrics.language_filtered == 4
    
    def test_language_score_calculation(self):
        """Test language scoring accuracy."""
        # Test English entities
        assert self.quality_filter._calculate_language_score("John Smith") >= 0.8
        assert self.quality_filter._calculate_language_score("Microsoft Corporation") >= 0.8
        assert self.quality_filter._calculate_language_score("United States") >= 0.8
        
        # Test non-English entities
        assert self.quality_filter._calculate_language_score("Afirmar Categóricamente Que") < 0.8
        assert self.quality_filter._calculate_language_score("Lo Cruzamos") < 0.8
        assert self.quality_filter._calculate_language_score("C'Est De Lui Écrire") < 0.8
        
        # Test mixed/unclear cases
        assert self.quality_filter._calculate_language_score("José García") >= 0.5  # Name with accent
        assert self.quality_filter._calculate_language_score("ACME Corp") >= 0.8   # Acronym
    
    @pytest.mark.asyncio
    async def test_dynamic_confidence_calculation(self):
        """Test that dynamic confidence improves over hardcoded values."""
        # Create entities with hardcoded confidence
        test_entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.85, properties={"source": "SpaCy"}),
            Entity(name="Microsoft Corporation", type="ORGANIZATION", confidence=0.85, properties={"source": "SpaCy"}),
            Entity(name="x", type="PERSON", confidence=0.85, properties={"source": "SpaCy"}),  # Poor quality
        ]
        
        context_text = "John Smith is the CEO of Microsoft Corporation. John Smith announced new initiatives."
        
        # Apply dynamic confidence calculation
        metrics = QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0.0, {}, 0.0)
        enhanced = await self.quality_filter._calculate_dynamic_confidence(
            test_entities, context_text, metrics
        )
        
        # Check confidence improvements
        enhanced_by_name = {entity.name: entity for entity in enhanced}
        
        # High-quality entities should have higher confidence
        assert enhanced_by_name["John Smith"].confidence > 0.85
        assert enhanced_by_name["Microsoft Corporation"].confidence > 0.85
        
        # Poor-quality entities should have lower confidence
        assert enhanced_by_name["x"].confidence < 0.85
        
        # Should track confidence improvements
        assert metrics.confidence_improved >= 1
    
    def test_source_attribution_correction(self):
        """Test that source attribution is corrected."""
        # Create entities with "Unknown" sources
        test_entities = [
            Entity(name="John Smith", type="PERSON", confidence=0.85, properties={"source": "Unknown"}),
            Entity(name="Microsoft", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="TestEntity", type="LOCATION", confidence=0.85, properties={}),  # No properties
        ]
        
        # Apply source correction
        metrics = QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0.0, {}, 0.0)
        corrected = self.quality_filter._correct_source_attribution(test_entities, metrics)
        
        # Check source corrections
        corrected_by_name = {entity.name: entity for entity in corrected}
        
        # Unknown sources should be corrected
        assert corrected_by_name["John Smith"].properties["source"] != "Unknown"
        assert corrected_by_name["TestEntity"].properties["source"] != "Unknown"
        
        # Good sources should remain unchanged
        assert corrected_by_name["Microsoft"].properties["source"] == "GLiNER"
        
        # Should track corrections
        assert metrics.source_corrections >= 1
    
    @pytest.mark.asyncio
    async def test_comprehensive_quality_enhancement(self):
        """Test the complete quality enhancement pipeline."""
        # Create a realistic mix of good and bad entities
        test_entities = [
            # Good entities
            Entity(name="John Smith", type="PERSON", confidence=0.85, properties={"source": "SpaCy"}),
            Entity(name="Microsoft Corporation", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="Washington", type="LOCATION", confidence=0.85, properties={"source": "SpaCy"}),
            
            # False positives
            Entity(name="uh", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="a", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
            
            # Non-English
            Entity(name="Lo Cruzamos", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
            Entity(name="Bien Été", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
            
            # Unknown sources
            Entity(name="Amazon", type="ORGANIZATION", confidence=0.85, properties={"source": "Unknown"}),
        ]
        
        # Apply comprehensive enhancement
        enhanced_entities, metrics = await self.quality_filter.filter_and_enhance_entities(
            test_entities, self.sample_video_intel
        )
        
        # Validate results
        assert len(enhanced_entities) == 4  # Should keep 4 good entities (John, Microsoft, Washington, Amazon)
        assert metrics.false_positives_removed == 2  # uh, a
        assert metrics.language_filtered == 2  # Lo Cruzamos, Bien Été
        assert metrics.source_corrections >= 1  # Amazon
        assert metrics.final_quality_score > 0.7  # Should have good quality score
        assert metrics.language_purity_score > 0.8  # Should be mostly English
        
        # Check specific entities survived
        entity_names = {entity.name for entity in enhanced_entities}
        assert "John Smith" in entity_names
        assert "Microsoft Corporation" in entity_names
        assert "Washington" in entity_names
        assert "Amazon" in entity_names
        
        # False positives should be removed
        assert "uh" not in entity_names
        assert "a" not in entity_names
        assert "Lo Cruzamos" not in entity_names
        assert "Bien Été" not in entity_names
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        # Create entities with varying quality
        test_entities = [
            Entity(name="High Quality", type="PERSON", confidence=0.95, properties={"source": "SpaCy"}),
            Entity(name="Medium Quality", type="ORGANIZATION", confidence=0.75, properties={"source": "GLiNER"}),
            Entity(name="Low Quality", type="LOCATION", confidence=0.55, properties={"source": "SpaCy"}),
        ]
        
        # Calculate metrics
        overall_quality = self.quality_filter._calculate_overall_quality_score(test_entities)
        confidence_dist = self.quality_filter._calculate_confidence_distribution(test_entities)
        language_purity = self.quality_filter._calculate_language_purity(test_entities)
        
        # Validate metrics
        assert 0.7 < overall_quality < 0.9  # Should be decent quality
        assert confidence_dist["very_high"] == 1  # One high confidence entity
        assert confidence_dist["medium"] == 1     # One medium confidence entity
        assert confidence_dist["low"] == 1        # One low confidence entity
        assert language_purity > 0.9             # All English entities
    
    def test_spacy_dynamic_confidence(self):
        """Test SpaCy dynamic confidence calculation."""
        # This test would require SpaCy to be loaded, so we'll test the concept
        if SpacyEntityExtractor:
            extractor = SpacyEntityExtractor()
            
            # Test that confidence calculation method exists
            assert hasattr(extractor, '_calculate_spacy_confidence')
            
            # The actual test would require loading SpaCy model
            # For now, just verify the method signature exists
    
    def test_rebel_dynamic_confidence(self):
        """Test REBEL dynamic confidence calculation."""
        # Test REBEL confidence calculation
        extractor = REBELExtractor()
        
        # Test high-quality relationship
        high_quality_triplet = {
            'subject': 'John Smith',
            'predicate': 'CEO of',
            'object': 'Microsoft Corporation'
        }
        
        confidence_high = extractor._calculate_rebel_confidence(
            high_quality_triplet, 
            "John Smith is the CEO of Microsoft Corporation"
        )
        
        # Test low-quality relationship
        low_quality_triplet = {
            'subject': 'x',
            'predicate': 'mentioned',
            'object': 'y'
        }
        
        confidence_low = extractor._calculate_rebel_confidence(
            low_quality_triplet,
            "Some random text"
        )
        
        # High-quality should have higher confidence
        assert confidence_high > confidence_low
        assert confidence_high > 0.8
        assert confidence_low < 0.7


# Integration test for real-world usage
@pytest.mark.asyncio
async def test_real_world_entity_quality_improvement():
    """Test entity quality improvement with realistic data."""
    
    # Create realistic problematic entities (like those found in actual output)
    problematic_entities = [
        # Good entities
        Entity(name="Jamal Khashoggi", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
        Entity(name="NSO Group", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
        Entity(name="Saudi Arabia", type="LOCATION", confidence=0.85, properties={"source": "SpaCy"}),
        
        # Actual problematic entities from real output
        Entity(name="Afirmar Categóricamente Que", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
        Entity(name="Lo Cruzamos", type="PERSON", confidence=0.85, properties={"source": "GLiNER"}),
        Entity(name="Bien", type="LOCATION", confidence=0.85, properties={"source": "GLiNER"}),
        Entity(name="C'Est De Lui Écrire", type="ORGANIZATION", confidence=0.85, properties={"source": "GLiNER"}),
        Entity(name="Bueno", type="PERSON", confidence=0.85, properties={"source": "Unknown"}),
        Entity(name="Casa", type="ORGANIZATION", confidence=0.85, properties={"source": "Unknown"}),
    ]
    
    # Create realistic video intelligence
    video_intel = VideoIntelligence(
        video_url="https://youtube.com/watch?v=test",
        title="Pegasus Spyware Investigation",
        metadata=VideoMetadata(video_id="test", duration=1800, view_count=50000),
        transcript=VideoTranscript(
            full_text="Jamal Khashoggi was murdered by Saudi agents. NSO Group developed Pegasus spyware used to target journalists and activists around the world.",
            segments=[]
        ),
        entities=[],
        relationships=[]
    )
    
    # Apply quality enhancement
    quality_filter = EntityQualityFilter()
    enhanced_entities, metrics = await quality_filter.filter_and_enhance_entities(
        problematic_entities, video_intel
    )
    
    # Validate real-world improvement
    enhanced_names = {entity.name for entity in enhanced_entities}
    
    # Should keep legitimate entities
    assert "Jamal Khashoggi" in enhanced_names
    assert "NSO Group" in enhanced_names
    assert "Saudi Arabia" in enhanced_names
    
    # Should remove Spanish/French false positives
    assert "Afirmar Categóricamente Que" not in enhanced_names
    assert "Lo Cruzamos" not in enhanced_names
    assert "C'Est De Lui Écrire" not in enhanced_names
    
    # Should show significant improvement
    assert metrics.language_filtered >= 4  # Multiple non-English entities filtered
    assert metrics.source_corrections >= 2  # Unknown sources corrected
    assert metrics.final_quality_score > 0.8  # High final quality
    assert metrics.language_purity_score > 0.9  # Very high English purity
    
    # Should significantly reduce entity count while keeping quality
    improvement_ratio = len(enhanced_entities) / len(problematic_entities)
    assert 0.3 <= improvement_ratio <= 0.6  # 30-60% retention is realistic for noisy input
    
    print(f"✅ Real-world test passed!")
    print(f"   📊 Entities: {len(problematic_entities)} → {len(enhanced_entities)} ({improvement_ratio:.1%} retained)")
    print(f"   🎯 Quality score: {metrics.final_quality_score:.3f}")
    print(f"   🌍 Language purity: {metrics.language_purity_score:.3f}")
    print(f"   🚫 False positives removed: {metrics.false_positives_removed}")
    print(f"   🌐 Non-English filtered: {metrics.language_filtered}") 