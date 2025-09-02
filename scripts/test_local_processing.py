#!/usr/bin/env python3
"""
Local Processing Test for ClipScribe

Tests video processing locally using the actual ClipScribe modules.
Validates output structure, formatting, and content quality.

Usage:
    poetry run python scripts/test_local_processing.py
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import tempfile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalProcessingTester:
    """Tests ClipScribe processing locally with output validation."""
    
    # Small test set with diverse content
    TEST_VIDEOS = [
        {
            "id": "short_news",
            "url": "https://www.youtube.com/watch?v=A-bdxIi7v04",
            "title": "PBS News Weekend",
            "expected_duration": 26 * 60,
            "category": "news"
        },
        {
            "id": "defense_training", 
            "url": "https://www.youtube.com/watch?v=Nr7vbOSzpSk",
            "title": "Tier 1&2 Training",
            "expected_duration": 31 * 60,
            "category": "defense"
        }
    ]
    
    def __init__(self):
        self.results = []
        self.output_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Test outputs will be saved to: {self.output_dir}")
    
    async def test_video_processing(self, video: Dict[str, Any], use_pro: bool = False) -> Dict[str, Any]:
        """Test processing a single video."""
        
        model = "pro" if use_pro else "flash"
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {video['title']} with {model.upper()} model")
        logger.info(f"URL: {video['url']}")
        
        result = {
            "video": video,
            "model": model,
            "start_time": datetime.now().isoformat(),
            "success": False,
            "validation": {}
        }
        
        try:
            # Import ClipScribe modules
            from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
            from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
            from src.clipscribe.models import VideoIntelligence
            
            # 1. Download video
            logger.info("📥 Downloading video...")
            client = EnhancedUniversalVideoClient()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path, metadata = await client.download_audio(video["url"], output_dir=tmpdir)
                
                # Validate download
                if not Path(audio_path).exists():
                    raise Exception("Download failed - no audio file")
                
                duration = int(getattr(metadata, "duration", 0) or 0)
                logger.info(f"✅ Downloaded: {Path(audio_path).stat().st_size / 1024 / 1024:.1f} MB, Duration: {duration}s")
                
                # 2. Transcribe with Gemini
                logger.info(f"🎙️ Transcribing with Gemini {model.upper()}...")
                transcriber = GeminiFlashTranscriber(use_pro=use_pro)
                
                start_time = time.time()
                transcript_data = await transcriber.transcribe_audio(audio_path, duration)
                transcription_time = time.time() - start_time
                
                logger.info(f"✅ Transcribed in {transcription_time:.1f}s")
                
                # 3. Extract entities and relationships
                logger.info("🔍 Extracting entities and relationships...")
                
                # Process transcript
                transcript_text = transcript_data.get("transcript", "")
                if not transcript_text:
                    raise Exception("No transcript generated")
                
                entities = transcript_data.get("entities", [])
                relationships = transcript_data.get("relationships", [])
                
                logger.info(f"✅ Extracted: {len(entities)} entities, {len(relationships)} relationships")
                
                # 4. Create simplified data structure for validation
                video_data = {
                    "url": video["url"],
                    "title": metadata.title,
                    "transcript": transcript_text,
                    "entities": entities,
                    "relationships": relationships,
                    "processing_timestamp": datetime.now().isoformat()
                }
                
                # 5. Validate output structure and content
                validation = self.validate_output(video_data, transcript_data)
                result["validation"] = validation
                
                # 6. Save outputs for manual inspection
                output_path = self.output_dir / f"{video['id']}_{model}.json"
                output_data = {
                    "metadata": {
                        "url": video["url"],
                        "title": metadata.title,
                        "duration": duration,
                        "model": model,
                        "processing_time": transcription_time
                    },
                    "transcript": transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text,
                    "entities": entities[:10],  # First 10 for inspection
                    "relationships": relationships[:10],  # First 10 for inspection
                    "validation": validation
                }
                
                with open(output_path, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                logger.info(f"💾 Saved output to: {output_path}")
                
                # Calculate cost
                cost = duration / 60 * (0.02 if use_pro else 0.0035)
                
                # Update result
                result["success"] = True
                result["entity_count"] = len(entities)
                result["relationship_count"] = len(relationships)
                result["transcript_length"] = len(transcript_text)
                result["processing_time"] = transcription_time
                result["cost"] = cost
                
                # Log validation summary
                self.log_validation_summary(validation)
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            result["error"] = str(e)
        
        result["end_time"] = datetime.now().isoformat()
        return result
    
    def validate_output(self, video_data, transcript_data) -> Dict[str, Any]:
        """Validate output structure, formatting, and content quality."""
        
        validation = {
            "structure": {},
            "formatting": {},
            "content_quality": {},
            "issues": []
        }
        
        # 1. Structure Validation
        validation["structure"]["has_transcript"] = bool(video_data["transcript"])
        validation["structure"]["has_entities"] = len(video_data["entities"]) > 0
        validation["structure"]["has_relationships"] = len(video_data["relationships"]) > 0
        
        # Check entity structure
        if video_data["entities"]:
            sample_entity = video_data["entities"][0]
            validation["structure"]["entity_fields"] = {
                "has_name": "name" in sample_entity,
                "has_type": "type" in sample_entity,
                "has_confidence": "confidence" in sample_entity,
                "has_evidence": "evidence" in sample_entity or "quote" in sample_entity
            }
            
            # Check for missing required fields
            for field, present in validation["structure"]["entity_fields"].items():
                if not present:
                    validation["issues"].append(f"Entity missing {field}")
        
        # Check relationship structure
        if video_data["relationships"]:
            sample_rel = video_data["relationships"][0]
            validation["structure"]["relationship_fields"] = {
                "has_source": "source" in sample_rel or "subject" in sample_rel,
                "has_target": "target" in sample_rel or "object" in sample_rel,
                "has_type": "type" in sample_rel or "relationship" in sample_rel,
                "has_evidence": "evidence" in sample_rel or "quote" in sample_rel
            }
            
            # Check for missing required fields
            for field, present in validation["structure"]["relationship_fields"].items():
                if not present:
                    validation["issues"].append(f"Relationship missing {field}")
        
        # 2. Formatting Validation
        validation["formatting"]["transcript_has_punctuation"] = any(
            c in video_data["transcript"] for c in ['.', '!', '?']
        )
        validation["formatting"]["transcript_has_capitalization"] = (
            video_data["transcript"] != video_data["transcript"].lower()
        )
        
        # Check entity name formatting
        if video_data["entities"]:
            entity_names = [e.get("name", "") for e in video_data["entities"]]
            validation["formatting"]["entities_capitalized"] = sum(
                1 for name in entity_names if name and name[0].isupper()
            ) / len(entity_names) > 0.5
        
        # 3. Content Quality Validation
        transcript_words = len(video_data["transcript"].split())
        duration_minutes = transcript_data.get("duration", 0) / 60 if transcript_data.get("duration") else 1
        
        validation["content_quality"]["words_per_minute"] = transcript_words / max(duration_minutes, 1)
        validation["content_quality"]["entity_density"] = len(video_data["entities"]) / max(duration_minutes, 1)
        validation["content_quality"]["relationship_density"] = len(video_data["relationships"]) / max(duration_minutes, 1)
        
        # Quality thresholds
        if validation["content_quality"]["words_per_minute"] < 50:
            validation["issues"].append("Very low word count - possible transcription issue")
        
        if validation["content_quality"]["entity_density"] < 1:
            validation["issues"].append("Low entity density - extraction may be incomplete")
        
        if validation["content_quality"]["relationship_density"] < 0.5:
            validation["issues"].append("Low relationship density - extraction may be incomplete")
        
        # Check for duplicate entities
        entity_names = [e.get("name", "").lower() for e in video_data["entities"]]
        unique_entities = len(set(entity_names))
        validation["content_quality"]["duplicate_entity_ratio"] = 1 - (unique_entities / len(entity_names)) if entity_names else 0
        
        if validation["content_quality"]["duplicate_entity_ratio"] > 0.3:
            validation["issues"].append("High duplicate entity ratio - needs deduplication")
        
        # Check confidence scores
        if video_data["entities"]:
            confidences = [e.get("confidence", 0) for e in video_data["entities"] if "confidence" in e]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                validation["content_quality"]["avg_confidence"] = avg_confidence
                
                if avg_confidence < 0.5:
                    validation["issues"].append("Low average confidence - quality concern")
        
        # Overall quality score
        quality_score = 0
        if validation["structure"]["has_transcript"]: quality_score += 20
        if validation["structure"]["has_entities"]: quality_score += 20
        if validation["structure"]["has_relationships"]: quality_score += 20
        if validation["formatting"]["transcript_has_punctuation"]: quality_score += 10
        if validation["formatting"]["transcript_has_capitalization"]: quality_score += 10
        if validation["content_quality"].get("entity_density", 0) > 2: quality_score += 10
        if validation["content_quality"].get("relationship_density", 0) > 1: quality_score += 10
        
        validation["overall_quality_score"] = quality_score
        
        return validation
    
    def log_validation_summary(self, validation: Dict[str, Any]):
        """Log a summary of validation results."""
        
        logger.info("\n📊 Output Validation Summary:")
        
        # Structure
        logger.info("  Structure:")
        for key, value in validation["structure"].items():
            if isinstance(value, dict):
                logger.info(f"    {key}:")
                for subkey, subvalue in value.items():
                    status = "✅" if subvalue else "❌"
                    logger.info(f"      {status} {subkey}")
            else:
                status = "✅" if value else "❌"
                logger.info(f"    {status} {key}")
        
        # Content Quality
        logger.info("  Content Quality:")
        for key, value in validation["content_quality"].items():
            if isinstance(value, (int, float)):
                logger.info(f"    {key}: {value:.2f}")
        
        # Issues
        if validation["issues"]:
            logger.info("  ⚠️ Issues Found:")
            for issue in validation["issues"]:
                logger.info(f"    - {issue}")
        
        # Overall Score
        score = validation["overall_quality_score"]
        grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
        logger.info(f"  📈 Overall Quality Score: {score}/100 (Grade: {grade})")
    
    async def run_tests(self):
        """Run all tests."""
        
        logger.info("\n" + "="*80)
        logger.info("🧪 CLIPSCRIBE LOCAL PROCESSING TEST")
        logger.info("="*80)
        
        for video in self.TEST_VIDEOS:
            # Test with Flash
            flash_result = await self.test_video_processing(video, use_pro=False)
            self.results.append(flash_result)
            
            # Test with Pro
            pro_result = await self.test_video_processing(video, use_pro=True)
            self.results.append(pro_result)
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report."""
        
        logger.info("\n" + "="*80)
        logger.info("📊 FINAL TEST REPORT")
        logger.info("="*80)
        
        # Separate by model
        flash_results = [r for r in self.results if r["model"] == "flash"]
        pro_results = [r for r in self.results if r["model"] == "pro"]
        
        # Success rates
        flash_success = sum(1 for r in flash_results if r["success"])
        pro_success = sum(1 for r in pro_results if r["success"])
        
        logger.info(f"\n🔵 FLASH Model:")
        logger.info(f"  Success Rate: {flash_success}/{len(flash_results)}")
        
        if flash_success > 0:
            flash_successful = [r for r in flash_results if r["success"]]
            avg_entities = sum(r["entity_count"] for r in flash_successful) / len(flash_successful)
            avg_relationships = sum(r["relationship_count"] for r in flash_successful) / len(flash_successful)
            avg_quality = sum(r["validation"]["overall_quality_score"] for r in flash_successful) / len(flash_successful)
            total_cost = sum(r["cost"] for r in flash_successful)
            
            logger.info(f"  Avg Entities: {avg_entities:.1f}")
            logger.info(f"  Avg Relationships: {avg_relationships:.1f}")
            logger.info(f"  Avg Quality Score: {avg_quality:.1f}/100")
            logger.info(f"  Total Cost: ${total_cost:.4f}")
        
        logger.info(f"\n🟣 PRO Model:")
        logger.info(f"  Success Rate: {pro_success}/{len(pro_results)}")
        
        if pro_success > 0:
            pro_successful = [r for r in pro_results if r["success"]]
            avg_entities = sum(r["entity_count"] for r in pro_successful) / len(pro_successful)
            avg_relationships = sum(r["relationship_count"] for r in pro_successful) / len(pro_successful)
            avg_quality = sum(r["validation"]["overall_quality_score"] for r in pro_successful) / len(pro_successful)
            total_cost = sum(r["cost"] for r in pro_successful)
            
            logger.info(f"  Avg Entities: {avg_entities:.1f}")
            logger.info(f"  Avg Relationships: {avg_relationships:.1f}")
            logger.info(f"  Avg Quality Score: {avg_quality:.1f}/100")
            logger.info(f"  Total Cost: ${total_cost:.4f}")
        
        # Common issues
        all_issues = []
        for r in self.results:
            if r["success"] and "validation" in r:
                all_issues.extend(r["validation"].get("issues", []))
        
        if all_issues:
            logger.info("\n⚠️ Common Issues Across All Tests:")
            from collections import Counter
            issue_counts = Counter(all_issues)
            for issue, count in issue_counts.most_common(5):
                logger.info(f"  - {issue} (occurred {count} times)")
        
        # Save full report
        report_path = self.output_dir / "test_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"\n📁 Full report saved to: {report_path}")
        logger.info(f"📂 All outputs in: {self.output_dir}")
        
        # Final verdict
        total_success = flash_success + pro_success
        total_tests = len(self.results)
        
        logger.info("\n" + "="*80)
        if total_success == 0:
            logger.error("❌ ALL TESTS FAILED - DO NOT DEPLOY")
        elif total_success < total_tests / 2:
            logger.warning("⚠️ PARTIAL SUCCESS - REVIEW ISSUES BEFORE DEPLOYING")
        else:
            logger.info("✅ TESTS PASSED - READY FOR DEPLOYMENT")
            logger.info("📋 Review output quality in test_results folder before proceeding")
        logger.info("="*80)


async def main():
    """Main entry point."""
    
    # Check environment
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    tester = LocalProcessingTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
