#!/usr/bin/env python3
"""
Test Phase 2: Advanced Entity Normalization

Validates the cross-video entity normalization functionality.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.extractors.entity_normalizer import EntityNormalizer
from src.clipscribe.models import Entity


def create_test_entities():
    """Create test entities for validation."""
    # Video 1 entities
    video1_entities = [
        Entity(entity="John Smith", type="PERSON", confidence=0.8),
        Entity(entity="TechCorp", type="ORGANIZATION", confidence=0.9),
        Entity(entity="California", type="LOCATION", confidence=0.7),
        Entity(entity="CEO", type="PERSON", confidence=0.6),  # Will be deduplicated
    ]

    # Video 2 entities (overlapping with video 1)
    video2_entities = [
        Entity(entity="John Smith", type="PERSON", confidence=0.85),  # Same entity, higher confidence
        Entity(entity="Microsoft", type="ORGANIZATION", confidence=0.9),
        Entity(entity="California", type="LOCATION", confidence=0.75),  # Same location
        Entity(entity="CEO", type="PERSON", confidence=0.65),  # Same role
    ]

    # Video 3 entities (different content)
    video3_entities = [
        Entity(entity="Sarah Johnson", type="PERSON", confidence=0.8),
        Entity(entity="TechCorp", type="ORGANIZATION", confidence=0.85),  # Same org as video 1
        Entity(entity="New York", type="LOCATION", confidence=0.7),
    ]

    return {
        "video1": video1_entities,
        "video2": video2_entities,
        "video3": video3_entities
    }


def test_single_video_normalization():
    """Test single video entity normalization."""
    print("🧪 TESTING SINGLE VIDEO NORMALIZATION")
    print("=" * 50)

    test_entities = create_test_entities()
    normalizer = EntityNormalizer()

    # Test video 1
    result = normalizer.normalize_entities(test_entities["video1"])

    print(f"Input entities: {len(test_entities['video1'])}")
    print(f"Normalized entities: {len(result)}")

    # Check that entities were properly normalized
    entity_names = [e.entity for e in result]
    print(f"Entity names: {entity_names}")

    assert len(result) > 0, "Should have normalized entities"
    assert "John Smith" in entity_names, "Should preserve main entities"
    assert "TechCorp" in entity_names, "Should preserve organizations"

    print("✅ Single video normalization test passed")
    return True


def test_cross_video_normalization():
    """Test cross-video entity normalization."""
    print("\\n🧪 TESTING CROSS-VIDEO NORMALIZATION")
    print("=" * 50)

    test_entities = create_test_entities()
    normalizer = EntityNormalizer()

    # Test cross-video normalization
    result = normalizer.normalize_entities_across_videos(test_entities)

    print(f"Input videos: {len(test_entities)}")
    print(f"Total input entities: {sum(len(entities) for entities in test_entities.values())}")
    print(f"Result keys: {list(result.keys())}")

    # Check results structure
    assert 'cross_video_normalized' in result, "Should have cross_video_normalized"
    assert 'normalized_entities' in result['cross_video_normalized'], "Should have normalized_entities in cross_video_normalized"
    assert 'entity_networks' in result, "Should have entity_networks"
    assert 'insights' in result, "Should have insights"
    assert 'statistics' in result, "Should have statistics"

    stats = result['statistics']
    print(f"Normalized entities: {stats['cross_video_normalized_entities']}")
    print(f"Cross-video entities: {stats.get('multi_video_entities', 0)}")
    print(f"Deduplication ratio: {stats.get('deduplication_ratio', 0):.2f}")

    # Check insights
    insights = result['insights']
    if insights['cross_video_entities']:
        print("🏆 Cross-video entities found:")
        for entity in insights['cross_video_entities'][:3]:
            print(f"  • {entity['entity']} - {len(entity['videos'])} videos")

    print("✅ Cross-video normalization test passed")
    return True


def test_entity_confidence_boosting():
    """Test that entities get confidence boosts for cross-video appearance."""
    print("\\n🧪 TESTING CONFIDENCE BOOSTING")
    print("=" * 50)

    # Create entities that appear in multiple videos
    multi_video_entities = {
        "video1": [Entity(entity="John Smith", type="PERSON", confidence=0.8)],
        "video2": [Entity(entity="John Smith", type="PERSON", confidence=0.7)],
        "video3": [Entity(entity="John Smith", type="PERSON", confidence=0.75)],
    }

    normalizer = EntityNormalizer()
    result = normalizer.normalize_entities_across_videos(multi_video_entities)

    # Find the normalized John Smith entity
    john_smith = None
    print(f"Looking for John Smith in {len(result['confidence_boosted_entities'])} entities")
    for entity in result['confidence_boosted_entities']:
        print(f"  Checking entity: {getattr(entity, 'entity', 'NO_ENTITY')} confidence: {getattr(entity, 'confidence', 'NO_CONFIDENCE')}")
        if hasattr(entity, 'entity') and entity.entity == "John Smith":
            john_smith = entity
            break

    if not john_smith:
        # Try looking in cross_video_normalized
        for entity in result['cross_video_normalized']['normalized_entities']:
            print(f"  Checking cross-video entity: {getattr(entity, 'entity', 'NO_ENTITY')} confidence: {getattr(entity, 'confidence', 'NO_CONFIDENCE')}")
            if hasattr(entity, 'entity') and entity.entity == "John Smith":
                john_smith = entity
                break

    if john_smith:
        print(f"John Smith confidence: {john_smith.confidence}")

        # Check properties for cross-video metadata
        has_boost = False
        boost_value = 0
        source_videos = []
        mention_count = 0

        if hasattr(john_smith, 'properties') and john_smith.properties:
            boost_value = john_smith.properties.get('cross_video_boost', 0)
            source_videos = john_smith.properties.get('source_videos', [])
            mention_count = john_smith.properties.get('mention_count', 0)
            has_boost = boost_value > 0

        print(f"Cross-video boost applied: {has_boost}")
        print(f"Cross-video boost value: {boost_value}")
        print(f"Source videos: {source_videos}")
        print(f"Mention count: {mention_count}")

        # The important thing is that cross-video boost is applied
        if has_boost and len(source_videos) > 1:
            print("✅ Cross-video boost is properly applied")
            return True
        else:
            print("❌ Cross-video boost not applied or insufficient data")
            return False
        print("✅ Confidence boosting test passed")
        return True
    else:
        print("❌ Could not find John Smith entity")
        return False


def main():
    """Run all entity normalization tests."""
    print("🚀 CLIPSCRIBE PHASE 2: ENTITY NORMALIZATION TEST SUITE")
    print("=" * 60)

    tests = [
        test_single_video_normalization,
        test_cross_video_normalization,
        test_entity_confidence_boosting
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)

    # Summary
    print("\\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    test_names = [
        "Single Video Normalization",
        "Cross-Video Normalization",
        "Confidence Boosting"
    ]

    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {name}: {status}")

    passed_count = sum(results)
    total_count = len(results)

    print(f"\\nOverall: {passed_count}/{total_count} tests passed")

    if all(results):
        print("\\n🎉 ALL TESTS PASSED! Phase 2 entity normalization is working correctly.")
        return 0
    else:
        print("\\n⚠️  SOME TESTS FAILED. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
