"""
Entity Extraction Accuracy Testing for ClipScribe.

Tests entity extraction accuracy across different content domains and speaker patterns
to ensure <2% false positive rate and >90% accuracy.

Part of Week 1-2 Core Excellence Implementation Plan.
"""

import pytest
import asyncio
import logging
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import statistics

from clipscribe.extractors.advanced_hybrid_extractor import AdvancedHybridExtractor
from clipscribe.models import Entity

logger = logging.getLogger(__name__)

class TestEntityExtractionAccuracy:
    """Test entity extraction accuracy across various scenarios."""
    
    @pytest.fixture
    def test_content_domains(self):
        """Test content covering different domains."""
        return {
            "political_news": {
                "transcript": "President Biden met with Speaker McCarthy at the White House to discuss debt ceiling negotiations.",
                "expected_entities": {"PERSON": ["Biden", "McCarthy"], "ORGANIZATION": ["White House"]},
                "target_accuracy": 0.92
            },
            "tech_interview": {
                "transcript": "Elon Musk announced Twitter will use OpenAI's GPT-4 technology costing $2.5 million monthly.",
                "expected_entities": {"PERSON": ["Elon Musk"], "ORGANIZATION": ["Twitter", "OpenAI"], "MONEY": ["$2.5 million"]},
                "target_accuracy": 0.88
            },
            "business_earnings": {
                "transcript": "Apple reported Q4 revenue of $117.2 billion, beating expectations. CEO Tim Cook highlighted iPhone sales.",
                "expected_entities": {"ORGANIZATION": ["Apple"], "PERSON": ["Tim Cook"], "MONEY": ["$117.2 billion"], "PRODUCT": ["iPhone"]},
                "target_accuracy": 0.95
            }
        }
    
    @pytest.fixture  
    def speaker_patterns(self):
        """Different speaker patterns and styles."""
        return {
            "formal": {"transcript": "Distinguished colleagues, I present our quarterly findings regarding market performance.", "target_accuracy": 0.90},
            "casual": {"transcript": "So basically, this new app has millions of downloads and they're gonna IPO next year.", "target_accuracy": 0.85},
            "technical": {"transcript": "The API uses REST with OAuth 2.0 authentication deployed on Kubernetes clusters.", "target_accuracy": 0.88}
        }
    
    @pytest.fixture
    def false_positive_scenarios(self):
        """Scenarios to test false positive detection."""
        return {
            "common_words": {
                "transcript": "I need to apple for a job at the white house down the street.",
                "should_not_extract": ["apple", "white house"],
                "context": "common_words_as_entities"
            },
            "fictional": {
                "transcript": "In Star Wars, Luke Skywalker fights the Empire on Tatooine.",
                "should_not_extract_as_real": ["Luke Skywalker", "Empire", "Tatooine"],
                "context": "fictional_entities"
            }
        }
    
    @pytest.mark.asyncio
    async def test_domain_accuracy(self, test_content_domains):
        """Test entity extraction accuracy across content domains."""
        extractor = AdvancedHybridExtractor()
        domain_results = {}
        
        for domain_name, domain_data in test_content_domains.items():
            entities = await extractor.extract_entities(domain_data["transcript"])
            
            # Calculate accuracy metrics
            extracted_names = {e.type: [e.name.lower() for e in entities if e.type == e.type] for e in entities}
            expected = domain_data["expected_entities"]
            
            correct_total = 0
            expected_total = 0
            
            for entity_type, expected_names in expected.items():
                extracted = extracted_names.get(entity_type, [])
                expected_lower = [name.lower() for name in expected_names]
                correct = len(set(extracted).intersection(set(expected_lower)))
                
                correct_total += correct
                expected_total += len(expected_names)
            
            accuracy = correct_total / expected_total if expected_total > 0 else 0
            meets_target = accuracy >= domain_data["target_accuracy"]
            
            domain_results[domain_name] = {
                "accuracy": accuracy,
                "target": domain_data["target_accuracy"],
                "meets_target": meets_target,
                "entity_count": len(entities)
            }
            
            logger.info(f"{domain_name}: {accuracy:.2%} accuracy (target: {domain_data['target_accuracy']:.2%})")
        
        # Validate performance
        successful = sum(1 for r in domain_results.values() if r["meets_target"])
        success_rate = (successful / len(domain_results)) * 100
        
        assert success_rate >= 90.0, f"Domain accuracy success rate {success_rate:.1f}% below 90% target"
        
        avg_accuracy = statistics.mean([r["accuracy"] for r in domain_results.values()])
        assert avg_accuracy >= 0.85, f"Average accuracy {avg_accuracy:.2%} below 85% minimum"
    
    @pytest.mark.asyncio 
    async def test_speaker_robustness(self, speaker_patterns):
        """Test robustness across speaker patterns."""
        extractor = AdvancedHybridExtractor()
        pattern_results = {}
        
        for pattern_name, pattern_data in speaker_patterns.items():
            entities = await extractor.extract_entities(pattern_data["transcript"])
            
            avg_confidence = statistics.mean([e.confidence for e in entities]) if entities else 0
            meets_target = avg_confidence >= pattern_data["target_accuracy"]
            
            pattern_results[pattern_name] = {
                "avg_confidence": avg_confidence,
                "target": pattern_data["target_accuracy"],
                "meets_target": meets_target,
                "entity_count": len(entities)
            }
        
        successful = sum(1 for r in pattern_results.values() if r["meets_target"])
        robustness_rate = (successful / len(pattern_results)) * 100
        
        assert robustness_rate >= 85.0, f"Speaker robustness {robustness_rate:.1f}% below 85% target"
    
    @pytest.mark.asyncio
    async def test_false_positive_detection(self, false_positive_scenarios):
        """Test false positive detection capabilities."""
        extractor = AdvancedHybridExtractor()
        fp_results = {}
        
        for scenario_name, scenario_data in false_positive_scenarios.items():
            entities = await extractor.extract_entities(scenario_data["transcript"])
            
            false_positives = []
            if "should_not_extract" in scenario_data:
                for should_not in scenario_data["should_not_extract"]:
                    for entity in entities:
                        if should_not.lower() in entity.name.lower():
                            false_positives.append(entity.name)
            
            fp_rate = len(false_positives) / len(entities) if entities else 0
            meets_target = fp_rate <= 0.02  # <2% target
            
            fp_results[scenario_name] = {
                "false_positive_rate": fp_rate,
                "meets_target": meets_target,
                "total_entities": len(entities),
                "false_positives": false_positives
            }
        
        successful = sum(1 for r in fp_results.values() if r["meets_target"])
        fp_success_rate = (successful / len(fp_results)) * 100
        
        assert fp_success_rate >= 95.0, f"False positive success rate {fp_success_rate:.1f}% below 95% target"
        
        # Overall false positive rate
        total_entities = sum(r["total_entities"] for r in fp_results.values())
        total_fps = sum(len(r["false_positives"]) for r in fp_results.values())
        overall_fp_rate = total_fps / total_entities if total_entities > 0 else 0
        
        assert overall_fp_rate < 0.02, f"Overall false positive rate {overall_fp_rate:.2%} exceeds 2% target" 