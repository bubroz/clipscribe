#!/usr/bin/env python3
"""
Fast mock-based testing for Voxtral-Grok pipeline.
Tests the complete workflow without real API calls or video downloads.
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2
from src.clipscribe.core_data import CoreData
from src.clipscribe.validators.output_validator import OutputValidator


def create_mock_transcript():
    """Create realistic mock transcript data."""
    return {
        "transcript": """
        This is a test transcript for the Tier 1 and Tier 2 Selections training video.
        The instructor discusses the fundamental differences between Tier 1 and Tier 2 operations.
        Key concepts include operational security, selection criteria, and tactical implementation.
        The training covers both theoretical frameworks and practical applications.
        """,
        "language": "en",
        "confidence_score": 0.94,
        "processing_cost": 0.035,
        "word_timestamps": [
            {"word": "This", "start": 0.0, "end": 0.5},
            {"word": "is", "start": 0.5, "end": 0.8},
            {"word": "a", "start": 0.8, "end": 1.0},
            {"word": "test", "start": 1.0, "end": 1.5}
        ]
    }


def create_mock_entities():
    """Create realistic mock entity data."""
    return [
        {
            "name": "Tier 1 Operations",
            "type": "CONCEPT",
            "confidence": 0.92,
            "mentions": 15,
            "evidence": [
                {
                    "quote": "Tier 1 operations require the highest level of security clearance",
                    "timestamp": 120.5,
                    "context": "The instructor explains the classification system"
                }
            ]
        },
        {
            "name": "Selection Criteria",
            "type": "PROCESS",
            "confidence": 0.88,
            "mentions": 12,
            "evidence": [
                {
                    "quote": "Candidates must demonstrate exceptional analytical capabilities",
                    "timestamp": 245.2,
                    "context": "Discussion of evaluation standards"
                }
            ]
        },
        {
            "name": "Operational Security",
            "type": "CONCEPT",
            "confidence": 0.95,
            "mentions": 8,
            "evidence": [
                {
                    "quote": "OPSEC protocols are non-negotiable in Tier 1 environments",
                    "timestamp": 180.7,
                    "context": "Security briefing section"
                }
            ]
        }
    ]


def create_mock_relationships():
    """Create realistic mock relationship data."""
    return [
        {
            "source": "Tier 1 Operations",
            "target": "Selection Criteria",
            "relationship_type": "REQUIRES",
            "confidence": 0.89,
            "evidence": [
                {
                    "quote": "Tier 1 positions require candidates to meet stringent selection criteria",
                    "timestamp": 156.3,
                    "context": "Explanation of qualification requirements"
                }
            ]
        },
        {
            "source": "Selection Criteria",
            "target": "Operational Security",
            "relationship_type": "INCLUDES",
            "confidence": 0.91,
            "evidence": [
                {
                    "quote": "Security clearance is a fundamental component of the selection process",
                    "timestamp": 203.8,
                    "context": "Security requirements discussion"
                }
            ]
        }
    ]


def create_mock_metadata():
    """Create realistic mock video metadata."""
    return {
        "video_id": "test_123",
        "title": "How to Pass Tier 1 & 2 Selections Part 1/3: Difference Between Tier 1 & 2",
        "channel": "Professional Training Channel",
        "channel_id": "pro_training_123",
        "duration": 720,  # 12 minutes
        "url": "https://www.youtube.com/watch?v=test123",
        "description": "Comprehensive training on Tier 1 and Tier 2 selection processes",
        "upload_date": "2025-09-30",
        "view_count": 15420,
        "like_count": 892
    }


async def test_mock_pipeline():
    """Test the complete pipeline with mocked dependencies."""
    
    print("=" * 80)
    print("TESTING VOXTRAL-GROK PIPELINE (MOCKED - FAST TEST)")
    print("=" * 80)
    
    # Mock the external dependencies
    with patch('src.clipscribe.retrievers.video_retriever_v2.EnhancedUniversalVideoClient') as mock_client, \
         patch('src.clipscribe.retrievers.video_retriever_v2.HybridProcessor') as mock_processor:
        
        # Setup mock video client
        mock_client_instance = AsyncMock()
        mock_client_instance.download_video.return_value = (
            create_mock_metadata(),
            "/tmp/test_video.mp4"
        )
        mock_client.return_value = mock_client_instance
        
        # Setup mock processor
        mock_processor_instance = AsyncMock()
        mock_processor_instance.process_video.return_value = {
            "transcript": create_mock_transcript(),
            "entities": create_mock_entities(),
            "relationships": create_mock_relationships(),
            "topics": ["Professional Training", "Security Operations", "Selection Process"],
            "processing_cost": 0.035,
            "processing_time": 45.2
        }
        mock_processor.return_value = mock_processor_instance
        
        # Initialize retriever
        print("\n1. Initializing VideoIntelligenceRetrieverV2...")
        retriever = VideoIntelligenceRetrieverV2(
            output_dir="output/test_mock",
            use_cache=False
        )
        print("   ✅ Retriever initialized")
        
        # Process video
        print("\n2. Processing test video...")
        test_url = "https://www.youtube.com/watch?v=test123"
        
        try:
            result = await retriever.process_url(test_url)
            print("   ✅ Video processed successfully")
            
            # Validate result
            print("\n3. Validating output...")
            if result and hasattr(result, 'entities'):
                print(f"   ✅ Found {len(result.entities)} entities")
                print(f"   ✅ Found {len(result.relationships)} relationships")
                print(f"   ✅ Processing cost: ${result.processing_cost:.3f}")
                print(f"   ✅ Processing time: {result.processing_time:.1f}s")
                
                # Test output validation
                validator = OutputValidator()
                validation_result = validator.validate_output("output/test_mock")
                
                if validation_result.is_valid:
                    print("   ✅ Output validation passed")
                else:
                    print(f"   ⚠️  Output validation warnings: {len(validation_result.warnings)}")
                    for warning in validation_result.warnings[:3]:  # Show first 3
                        print(f"      - {warning}")
                
                return True
            else:
                print("   ❌ Invalid result structure")
                return False
                
        except Exception as e:
            print(f"   ❌ Processing failed: {e}")
            return False


async def test_core_data_validation():
    """Test CoreData model validation."""
    
    print("\n4. Testing CoreData model validation...")
    
    try:
        # Create test data
        core_data = CoreData(
            video_id="test_123",
            title="Test Video",
            transcript=create_mock_transcript()["transcript"],
            entities=create_mock_entities(),
            relationships=create_mock_relationships(),
            metadata=create_mock_metadata()
        )
        
        # Validate the model
        core_data.validate()
        print("   ✅ CoreData validation passed")
        
        # Test derived outputs
        facts = core_data.generate_facts()
        print(f"   ✅ Generated {len(facts)} facts")
        
        knowledge_graph = core_data.generate_knowledge_graph()
        print(f"   ✅ Generated knowledge graph with {len(knowledge_graph.nodes)} nodes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CoreData validation failed: {e}")
        return False


async def main():
    """Run all mock tests."""
    print("Starting fast mock-based testing...")
    
    success = True
    
    # Test pipeline
    if not await test_mock_pipeline():
        success = False
    
    # Test CoreData
    if not await test_core_data_validation():
        success = False
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL MOCK TESTS PASSED - PIPELINE LOGIC WORKING!")
        print("💡 Ready for real API testing in separate terminal")
    else:
        print("❌ MOCK TESTS FAILED - CHECK ERRORS ABOVE")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
