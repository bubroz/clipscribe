"""
Relationship Mapping Quality Testing for ClipScribe.

Tests relationship extraction accuracy and consistency to ensure zero critical
failures in core relationship mapping functionality.

Target Metrics:
- Zero critical failures in relationship mapping
- >90% accuracy for high-confidence relationships
- Consistent relationship extraction across similar contexts
- Proper relationship directionality and context

Part of Week 1-2 Core Excellence Implementation Plan.
"""

import pytest
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from unittest.mock import Mock, patch
import statistics

from clipscribe.extractors.advanced_hybrid_extractor import AdvancedHybridExtractor
from clipscribe.models import Relationship, Entity

logger = logging.getLogger(__name__)

class TestRelationshipMapping:
    """Test relationship mapping quality and consistency."""
    
    @pytest.fixture
    def relationship_test_cases(self):
        """Test cases for different relationship types."""
        return {
            "employment_relations": {
                "transcript": "Tim Cook is the CEO of Apple Inc. He announced that the company hired 50,000 new employees.",
                "expected_relationships": [
                    {"source": "Tim Cook", "target": "Apple Inc.", "type": "CEO_OF", "confidence_min": 0.9},
                    {"source": "Apple Inc.", "target": "employees", "type": "EMPLOYS", "confidence_min": 0.8}
                ],
                "critical_relationships": ["Tim Cook", "Apple Inc.", "CEO_OF"]
            },
            
            "organizational_hierarchy": {
                "transcript": "The Department of Defense announced that General Smith will report to Secretary Johnson on the new defense initiative.",
                "expected_relationships": [
                    {"source": "General Smith", "target": "Secretary Johnson", "type": "REPORTS_TO", "confidence_min": 0.85},
                    {"source": "Secretary Johnson", "target": "Department of Defense", "type": "WORKS_FOR", "confidence_min": 0.9}
                ],
                "critical_relationships": ["General Smith", "Secretary Johnson", "REPORTS_TO"]
            },
            
            "business_partnerships": {
                "transcript": "Microsoft partnered with OpenAI to integrate ChatGPT into their Office suite. Satya Nadella praised the collaboration.",
                "expected_relationships": [
                    {"source": "Microsoft", "target": "OpenAI", "type": "PARTNERS_WITH", "confidence_min": 0.9},
                    {"source": "Satya Nadella", "target": "Microsoft", "type": "CEO_OF", "confidence_min": 0.85},
                    {"source": "ChatGPT", "target": "Office suite", "type": "INTEGRATED_INTO", "confidence_min": 0.8}
                ],
                "critical_relationships": ["Microsoft", "OpenAI", "PARTNERS_WITH"]
            },
            
            "investment_relations": {
                "transcript": "Warren Buffett's Berkshire Hathaway invested $10 billion in Amazon stock, making them a major shareholder.",
                "expected_relationships": [
                    {"source": "Warren Buffett", "target": "Berkshire Hathaway", "type": "LEADS", "confidence_min": 0.9},
                    {"source": "Berkshire Hathaway", "target": "Amazon", "type": "INVESTS_IN", "confidence_min": 0.95},
                    {"source": "Berkshire Hathaway", "target": "Amazon", "type": "SHAREHOLDER_OF", "confidence_min": 0.9}
                ],
                "critical_relationships": ["Berkshire Hathaway", "Amazon", "INVESTS_IN"]
            },
            
            "conflict_relations": {
                "transcript": "The European Union imposed sanctions on Russia following the invasion of Ukraine. President Zelensky criticized the response.",
                "expected_relationships": [
                    {"source": "European Union", "target": "Russia", "type": "SANCTIONS", "confidence_min": 0.9},
                    {"source": "Russia", "target": "Ukraine", "type": "INVADED", "confidence_min": 0.95},
                    {"source": "President Zelensky", "target": "European Union", "type": "CRITICIZED", "confidence_min": 0.8}
                ],
                "critical_relationships": ["Russia", "Ukraine", "INVADED"]
            }
        }
    
    @pytest.fixture
    def relationship_consistency_tests(self):
        """Test relationship consistency across similar contexts."""
        return {
            "ceo_consistency": [
                "Tim Cook is the CEO of Apple.",
                "Apple's CEO Tim Cook announced new products.",
                "Tim Cook, who leads Apple as CEO, spoke today."
            ],
            "partnership_consistency": [
                "Microsoft partnered with OpenAI on AI development.",
                "The partnership between Microsoft and OpenAI continues to grow.",
                "OpenAI and Microsoft are working together on new AI tools."
            ],
            "employment_consistency": [
                "Sarah works at Google as a software engineer.",
                "Google employee Sarah developed the new algorithm.",
                "Sarah, a Google software engineer, presented her work."
            ]
        }
    
    @pytest.fixture
    def relationship_directionality_tests(self):
        """Test proper relationship directionality."""
        return {
            "acquisition": {
                "transcript": "Microsoft acquired LinkedIn for $26.2 billion in 2016.",
                "expected_direction": {"source": "Microsoft", "target": "LinkedIn", "type": "ACQUIRED"}
            },
            "reports_to": {
                "transcript": "The regional manager reports to the vice president.",
                "expected_direction": {"source": "regional manager", "target": "vice president", "type": "REPORTS_TO"}
            },
            "owns": {
                "transcript": "Amazon owns Whole Foods and AWS.",
                "expected_direction": [
                    {"source": "Amazon", "target": "Whole Foods", "type": "OWNS"},
                    {"source": "Amazon", "target": "AWS", "type": "OWNS"}
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_relationship_accuracy(self, relationship_test_cases):
        """Test relationship extraction accuracy across different scenarios."""
        extractor = AdvancedHybridExtractor()
        accuracy_results = {}
        
        for case_name, case_data in relationship_test_cases.items():
            transcript = case_data["transcript"]
            expected_relationships = case_data["expected_relationships"]
            critical_relationships = case_data["critical_relationships"]
            
            # Extract relationships
            entities = await extractor.extract_entities(transcript)
            relationships = await extractor.extract_relationships(transcript, entities)
            
            # Evaluate expected relationships
            found_relationships = []
            critical_found = []
            
            for expected in expected_relationships:
                source_name = expected["source"]
                target_name = expected["target"]
                rel_type = expected["type"]
                min_confidence = expected["confidence_min"]
                
                # Find matching relationships
                for rel in relationships:
                    if (source_name.lower() in rel.source.lower() and 
                        target_name.lower() in rel.target.lower() and
                        rel.confidence >= min_confidence):
                        
                        found_relationships.append({
                            "expected": expected,
                            "found": rel,
                            "confidence": rel.confidence
                        })
                        
                        # Check if this is a critical relationship
                        if all(term.lower() in f"{rel.source} {rel.target} {rel.type}".lower() 
                               for term in critical_relationships):
                            critical_found.append(rel)
                        break
            
            # Calculate metrics
            accuracy = len(found_relationships) / len(expected_relationships) if expected_relationships else 0
            critical_success = len(critical_found) > 0  # At least one critical relationship found
            
            accuracy_results[case_name] = {
                "accuracy": accuracy,
                "critical_success": critical_success,
                "found_count": len(found_relationships),
                "expected_count": len(expected_relationships),
                "total_relationships": len(relationships),
                "avg_confidence": statistics.mean([r.confidence for r in relationships]) if relationships else 0
            }
            
            logger.info(f"{case_name}: {accuracy:.2%} accuracy, critical_success: {critical_success}")
        
        # Validate relationship mapping performance
        successful_cases = sum(1 for r in accuracy_results.values() if r["accuracy"] >= 0.8)
        total_cases = len(accuracy_results)
        success_rate = (successful_cases / total_cases) * 100
        
        # Target: >90% of cases achieve >80% relationship accuracy
        assert success_rate >= 90.0, f"Relationship accuracy success rate {success_rate:.1f}% below 90% target"
        
        # Critical requirement: Zero critical failures
        critical_failures = sum(1 for r in accuracy_results.values() if not r["critical_success"])
        assert critical_failures == 0, f"Found {critical_failures} critical relationship mapping failures"
        
        # Overall accuracy target
        avg_accuracy = statistics.mean([r["accuracy"] for r in accuracy_results.values()])
        assert avg_accuracy >= 0.85, f"Average relationship accuracy {avg_accuracy:.2%} below 85% target"
        
        return accuracy_results
    
    @pytest.mark.asyncio
    async def test_relationship_consistency(self, relationship_consistency_tests):
        """Test relationship extraction consistency across similar contexts."""
        extractor = AdvancedHybridExtractor()
        consistency_results = {}
        
        for test_name, transcripts in relationship_consistency_tests.items():
            test_relationships = []
            
            for transcript in transcripts:
                entities = await extractor.extract_entities(transcript)
                relationships = await extractor.extract_relationships(transcript, entities)
                test_relationships.append(relationships)
            
            # Analyze consistency
            if test_relationships:
                # Find common relationship patterns
                all_rel_types = []
                all_confidences = []
                
                for rel_set in test_relationships:
                    for rel in rel_set:
                        all_rel_types.append(rel.type)
                        all_confidences.append(rel.confidence)
                
                # Calculate consistency metrics
                unique_types = set(all_rel_types)
                type_consistency = len(unique_types) <= 3  # Should have consistent relationship types
                
                confidence_std = statistics.stdev(all_confidences) if len(all_confidences) > 1 else 0
                confidence_consistency = confidence_std <= 0.2  # Confidence should be consistent
                
                consistency_results[test_name] = {
                    "type_consistency": type_consistency,
                    "confidence_consistency": confidence_consistency,
                    "unique_types": len(unique_types),
                    "confidence_std": confidence_std,
                    "avg_confidence": statistics.mean(all_confidences) if all_confidences else 0,
                    "total_relationships": len(all_rel_types)
                }
                
                logger.info(f"{test_name}: type_consistency: {type_consistency}, conf_std: {confidence_std:.3f}")
        
        # Validate consistency
        consistent_tests = sum(1 for r in consistency_results.values() 
                             if r["type_consistency"] and r["confidence_consistency"])
        total_tests = len(consistency_results)
        consistency_rate = (consistent_tests / total_tests) * 100
        
        # Target: >85% of consistency tests pass
        assert consistency_rate >= 85.0, f"Relationship consistency rate {consistency_rate:.1f}% below 85% target"
        
        return consistency_results
    
    @pytest.mark.asyncio
    async def test_relationship_directionality(self, relationship_directionality_tests):
        """Test proper relationship directionality."""
        extractor = AdvancedHybridExtractor()
        directionality_results = {}
        
        for test_name, test_data in relationship_directionality_tests.items():
            transcript = test_data["transcript"]
            
            entities = await extractor.extract_entities(transcript)
            relationships = await extractor.extract_relationships(transcript, entities)
            
            # Check directionality
            correct_directions = []
            
            if isinstance(test_data["expected_direction"], list):
                expected_directions = test_data["expected_direction"]
            else:
                expected_directions = [test_data["expected_direction"]]
            
            for expected in expected_directions:
                source = expected["source"]
                target = expected["target"]
                rel_type = expected["type"]
                
                for rel in relationships:
                    # Check if direction matches (source -> target)
                    if (source.lower() in rel.source.lower() and 
                        target.lower() in rel.target.lower()):
                        correct_directions.append({
                            "relationship": rel,
                            "expected": expected,
                            "correct": True
                        })
                        break
                else:
                    # Check if direction is reversed (wrong direction)
                    for rel in relationships:
                        if (target.lower() in rel.source.lower() and 
                            source.lower() in rel.target.lower()):
                            correct_directions.append({
                                "relationship": rel,
                                "expected": expected,
                                "correct": False,
                                "error": "reversed_direction"
                            })
                            break
            
            # Calculate directionality accuracy
            correct_count = sum(1 for cd in correct_directions if cd.get("correct", False))
            total_expected = len(expected_directions)
            directionality_accuracy = correct_count / total_expected if total_expected > 0 else 0
            
            directionality_results[test_name] = {
                "accuracy": directionality_accuracy,
                "correct_count": correct_count,
                "total_expected": total_expected,
                "total_found": len(relationships),
                "direction_errors": [cd for cd in correct_directions if not cd.get("correct", False)]
            }
            
            logger.info(f"{test_name}: {directionality_accuracy:.2%} directionality accuracy")
        
        # Validate directionality
        accurate_tests = sum(1 for r in directionality_results.values() if r["accuracy"] >= 0.9)
        total_tests = len(directionality_results)
        directionality_rate = (accurate_tests / total_tests) * 100
        
        # Target: >90% of directionality tests achieve >90% accuracy
        assert directionality_rate >= 90.0, f"Directionality accuracy rate {directionality_rate:.1f}% below 90% target"
        
        return directionality_results
    
    @pytest.mark.asyncio
    async def test_relationship_confidence_calibration(self):
        """Test that relationship confidence scores are well-calibrated."""
        extractor = AdvancedHybridExtractor()
        
        calibration_cases = [
            {
                "transcript": "Apple CEO Tim Cook announced the new iPhone at the company headquarters.",
                "expected_confidence": "high",  # Clear, direct relationship
                "min_confidence": 0.85
            },
            {
                "transcript": "Someone mentioned that some company might be working with another organization.",
                "expected_confidence": "low",   # Vague, uncertain relationship
                "max_confidence": 0.6
            },
            {
                "transcript": "Microsoft and OpenAI signed a multi-billion dollar partnership agreement.",
                "expected_confidence": "high",  # Clear business relationship
                "min_confidence": 0.9
            }
        ]
        
        calibration_results = []
        
        for case in calibration_cases:
            entities = await extractor.extract_entities(case["transcript"])
            relationships = await extractor.extract_relationships(case["transcript"], entities)
            
            if relationships:
                avg_confidence = statistics.mean([r.confidence for r in relationships])
                max_confidence = max([r.confidence for r in relationships])
                
                case_result = {
                    "expected_confidence": case["expected_confidence"],
                    "avg_confidence": avg_confidence,
                    "max_confidence": max_confidence,
                    "relationship_count": len(relationships)
                }
                
                # Check calibration
                if case["expected_confidence"] == "high":
                    meets_expectation = avg_confidence >= case.get("min_confidence", 0.8)
                else:  # low confidence expected
                    meets_expectation = avg_confidence <= case.get("max_confidence", 0.7)
                
                case_result["well_calibrated"] = meets_expectation
                calibration_results.append(case_result)
        
        # Validate confidence calibration
        well_calibrated = sum(1 for r in calibration_results if r["well_calibrated"])
        total_cases = len(calibration_results)
        calibration_rate = (well_calibrated / total_cases) * 100
        
        # Target: >85% of cases have well-calibrated confidence
        assert calibration_rate >= 85.0, f"Relationship confidence calibration rate {calibration_rate:.1f}% below 85% target"
        
        return calibration_results 