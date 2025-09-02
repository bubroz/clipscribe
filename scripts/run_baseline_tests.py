#!/usr/bin/env python3
"""
Baseline Testing Script for ClipScribe

This script runs comprehensive baseline tests across multiple video categories
to evaluate extraction quality, performance, and cost for both Flash and Pro models.

Usage:
    python scripts/run_baseline_tests.py --category news --model both --limit 5
    python scripts/run_baseline_tests.py --all --model flash
    python scripts/run_baseline_tests.py --url "https://youtube.com/..." --model pro
"""

import os
import sys
import json
import time
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.api.job_worker import CloudRunJobWorker
from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Container for test results."""
    video_id: str
    url: str
    title: str
    category: str
    duration_seconds: int
    model: str
    processing_time: float
    cost: float
    entity_count: int
    relationship_count: int
    transcript_length: int
    confidence_avg: float
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class BaselineTester:
    """Runs baseline tests for ClipScribe."""
    
    # Test video library (from MASTER_TEST_VIDEO_TABLE.md)
    TEST_VIDEOS = {
        "news": [
            {
                "id": "HHkv6LbJklU",
                "url": "https://www.youtube.com/watch?v=HHkv6LbJklU",
                "title": "PBS News Hour full episode Aug 4 2025",
                "duration_minutes": 60
            },
            {
                "id": "lHikZov6oEQ",
                "url": "https://www.youtube.com/watch?v=lHikZov6oEQ",
                "title": "PBS News Hour full episode Aug 1 2025",
                "duration_minutes": 60
            },
            {
                "id": "A-bdxIi7v04",
                "url": "https://www.youtube.com/watch?v=A-bdxIi7v04",
                "title": "PBS News Weekend full episode Aug 2 2025",
                "duration_minutes": 26
            },
            {
                "id": "mdvGhRpH0JA",
                "url": "https://www.youtube.com/watch?v=mdvGhRpH0JA",
                "title": "PBS News Weekend full episode Aug 3 2025",
                "duration_minutes": 26
            },
            {
                "id": "7sWj6D2i4eU",
                "url": "https://www.youtube.com/watch?v=7sWj6D2i4eU",
                "title": "PBS News Hour live episode July 17 2025",
                "duration_minutes": 60
            }
        ],
        "intelligence": [
            {
                "id": "6ZVj1_SE4Mo",
                "url": "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",
                "title": "Global Spyware Scandal Exposing Pegasus Part One",
                "duration_minutes": 54
            },
            {
                "id": "xYMWTXIkANM",
                "url": "https://www.youtube.com/watch?v=xYMWTXIkANM",
                "title": "Global Spyware Scandal Exposing Pegasus Part Two",
                "duration_minutes": 54
            },
            {
                "id": "V9VEvGSzzk0",
                "url": "https://www.youtube.com/watch?v=V9VEvGSzzk0",
                "title": "Companies Selling Your Personal Data to the Cops",
                "duration_minutes": 18
            }
        ],
        "defense": [
            {
                "id": "Nr7vbOSzpSk",
                "url": "https://www.youtube.com/watch?v=Nr7vbOSzpSk",
                "title": "How to Pass Tier 1 & 2 Selections Part 1",
                "duration_minutes": 31
            },
            {
                "id": "tjFNZlZEJLY",
                "url": "https://www.youtube.com/watch?v=tjFNZlZEJLY",
                "title": "How to Pass Tier 1 & 2 Selections Part 2",
                "duration_minutes": 28
            },
            {
                "id": "7r-qOjUOjbs",
                "url": "https://www.youtube.com/watch?v=7r-qOjUOjbs",
                "title": "How To Pass Tier 1 & 2 Selections Part 3",
                "duration_minutes": 32
            }
        ],
        "technical": [
            {
                "id": "test_tech_1",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "title": "Technical Content Sample",
                "duration_minutes": 3
            }
        ]
    }
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TestResult] = []
        
        # Initialize worker for local testing
        self.flash_worker = None
        self.pro_worker = None
        
        logger.info(f"Test results will be saved to: {self.output_dir}")
    
    async def test_video(
        self, 
        video_info: Dict[str, Any], 
        category: str,
        model: str = "flash"
    ) -> TestResult:
        """Test a single video with the specified model."""
        
        logger.info(f"Testing {video_info['title']} with {model} model...")
        
        result = TestResult(
            video_id=video_info["id"],
            url=video_info["url"],
            title=video_info["title"],
            category=category,
            duration_seconds=video_info.get("duration_minutes", 0) * 60,
            model=model
        )
        
        start_time = time.time()
        
        try:
            # Initialize worker if needed
            if model == "pro" and not self.pro_worker:
                os.environ["USE_PRO_MODEL"] = "true"
                self.pro_worker = CloudRunJobWorker()
            elif model == "flash" and not self.flash_worker:
                os.environ["USE_PRO_MODEL"] = "false"
                self.flash_worker = CloudRunJobWorker()
            
            worker = self.pro_worker if model == "pro" else self.flash_worker
            
            # Create job payload
            job_id = f"test_{model}_{video_info['id']}_{int(time.time())}"
            payload = {
                "url": video_info["url"],
                "options": {
                    "model": model,
                    "test_mode": True
                }
            }
            
            # Process the job
            job_result = await worker.process_job(job_id, payload)
            
            # Extract metrics from result
            if job_result["status"] == "completed":
                # Parse the analysis from artifacts
                analysis = job_result.get("analysis", {})
                
                result.entity_count = len(analysis.get("entities", []))
                result.relationship_count = len(analysis.get("relationships", []))
                result.transcript_length = len(analysis.get("transcript", {}).get("text", ""))
                
                # Calculate average confidence
                entities = analysis.get("entities", [])
                if entities:
                    confidences = [e.get("confidence", 0) for e in entities]
                    result.confidence_avg = statistics.mean(confidences)
                else:
                    result.confidence_avg = 0.0
                
                result.cost = job_result.get("cost_estimate", 0)
                result.processing_time = time.time() - start_time
                
                logger.info(f"✅ Completed: {result.entity_count} entities, {result.relationship_count} relationships")
                
            else:
                result.error = job_result.get("error", "Unknown error")
                logger.error(f"❌ Failed: {result.error}")
        
        except Exception as e:
            result.error = str(e)
            result.processing_time = time.time() - start_time
            logger.error(f"❌ Exception: {e}")
        
        return result
    
    async def test_category(
        self, 
        category: str, 
        model: str = "both",
        limit: Optional[int] = None
    ) -> List[TestResult]:
        """Test all videos in a category."""
        
        if category not in self.TEST_VIDEOS:
            logger.error(f"Unknown category: {category}")
            return []
        
        videos = self.TEST_VIDEOS[category]
        if limit:
            videos = videos[:limit]
        
        logger.info(f"Testing {len(videos)} videos in category '{category}'")
        
        results = []
        for video in videos:
            if model == "both":
                # Test with both models
                flash_result = await self.test_video(video, category, "flash")
                results.append(flash_result)
                self.results.append(flash_result)
                
                pro_result = await self.test_video(video, category, "pro")
                results.append(pro_result)
                self.results.append(pro_result)
            else:
                # Test with single model
                result = await self.test_video(video, category, model)
                results.append(result)
                self.results.append(result)
            
            # Save intermediate results
            self.save_results()
        
        return results
    
    async def test_all_categories(
        self, 
        model: str = "both",
        limit_per_category: Optional[int] = None
    ) -> List[TestResult]:
        """Test all categories."""
        
        all_results = []
        for category in self.TEST_VIDEOS.keys():
            category_results = await self.test_category(category, model, limit_per_category)
            all_results.extend(category_results)
        
        return all_results
    
    async def test_single_url(self, url: str, model: str = "both") -> List[TestResult]:
        """Test a single URL."""
        
        video_info = {
            "id": url.split("/")[-1].split("?v=")[-1],
            "url": url,
            "title": "Custom URL Test",
            "duration_minutes": 0  # Will be determined during download
        }
        
        results = []
        if model == "both":
            flash_result = await self.test_video(video_info, "custom", "flash")
            results.append(flash_result)
            self.results.append(flash_result)
            
            pro_result = await self.test_video(video_info, "custom", "pro")
            results.append(pro_result)
            self.results.append(pro_result)
        else:
            result = await self.test_video(video_info, "custom", model)
            results.append(result)
            self.results.append(result)
        
        self.save_results()
        return results
    
    def save_results(self):
        """Save test results to JSON."""
        
        output_file = self.output_dir / "test_results.json"
        
        # Convert results to dicts
        results_data = [asdict(r) for r in self.results]
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Saved {len(self.results)} results to {output_file}")
    
    def generate_report(self):
        """Generate analysis report from results."""
        
        if not self.results:
            logger.warning("No results to analyze")
            return
        
        report_file = self.output_dir / "analysis_report.md"
        
        # Separate by model
        flash_results = [r for r in self.results if r.model == "flash"]
        pro_results = [r for r in self.results if r.model == "pro"]
        
        report = []
        report.append("# ClipScribe Baseline Test Report")
        report.append(f"\nGenerated: {datetime.now().isoformat()}")
        report.append(f"Total Tests: {len(self.results)}")
        
        # Model Comparison
        if flash_results and pro_results:
            report.append("\n## Model Comparison\n")
            report.append("| Metric | Flash | Pro | Difference |")
            report.append("|--------|-------|-----|------------|")
            
            # Calculate averages
            flash_entities = statistics.mean([r.entity_count for r in flash_results if not r.error])
            pro_entities = statistics.mean([r.entity_count for r in pro_results if not r.error])
            
            flash_rels = statistics.mean([r.relationship_count for r in flash_results if not r.error])
            pro_rels = statistics.mean([r.relationship_count for r in pro_results if not r.error])
            
            flash_cost = statistics.mean([r.cost for r in flash_results if not r.error])
            pro_cost = statistics.mean([r.cost for r in pro_results if not r.error])
            
            flash_time = statistics.mean([r.processing_time for r in flash_results if not r.error])
            pro_time = statistics.mean([r.processing_time for r in pro_results if not r.error])
            
            report.append(f"| Avg Entities | {flash_entities:.1f} | {pro_entities:.1f} | {(pro_entities/flash_entities - 1)*100:.1f}% |")
            report.append(f"| Avg Relationships | {flash_rels:.1f} | {pro_rels:.1f} | {(pro_rels/flash_rels - 1)*100:.1f}% |")
            report.append(f"| Avg Cost | ${flash_cost:.4f} | ${pro_cost:.4f} | {(pro_cost/flash_cost):.1f}x |")
            report.append(f"| Avg Time | {flash_time:.1f}s | {pro_time:.1f}s | {(pro_time/flash_time):.1f}x |")
        
        # Category Analysis
        report.append("\n## Results by Category\n")
        categories = set(r.category for r in self.results)
        
        for category in sorted(categories):
            cat_results = [r for r in self.results if r.category == category]
            report.append(f"\n### {category.title()}")
            report.append(f"Videos tested: {len(set(r.video_id for r in cat_results))}")
            
            # Success rate
            successful = [r for r in cat_results if not r.error]
            report.append(f"Success rate: {len(successful)}/{len(cat_results)} ({len(successful)/len(cat_results)*100:.1f}%)")
            
            if successful:
                avg_entities = statistics.mean([r.entity_count for r in successful])
                avg_relationships = statistics.mean([r.relationship_count for r in successful])
                report.append(f"Avg entities: {avg_entities:.1f}")
                report.append(f"Avg relationships: {avg_relationships:.1f}")
        
        # Errors
        errors = [r for r in self.results if r.error]
        if errors:
            report.append("\n## Errors\n")
            for error in errors:
                report.append(f"- {error.title} ({error.model}): {error.error}")
        
        # Cost Analysis
        report.append("\n## Cost Analysis\n")
        total_cost = sum(r.cost for r in self.results if not r.error)
        report.append(f"Total cost: ${total_cost:.2f}")
        
        if flash_results:
            flash_total = sum(r.cost for r in flash_results if not r.error)
            report.append(f"Flash total: ${flash_total:.2f}")
        
        if pro_results:
            pro_total = sum(r.cost for r in pro_results if not r.error)
            report.append(f"Pro total: ${pro_total:.2f}")
        
        # Write report
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))
        
        logger.info(f"Report saved to {report_file}")
        print("\n" + "\n".join(report))


async def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(description="Run ClipScribe baseline tests")
    parser.add_argument(
        "--category",
        choices=["news", "intelligence", "defense", "technical", "all"],
        help="Video category to test"
    )
    parser.add_argument(
        "--model",
        choices=["flash", "pro", "both"],
        default="both",
        help="Model to test with"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of videos per category"
    )
    parser.add_argument(
        "--url",
        help="Test a single URL"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = BaselineTester(output_dir=args.output_dir)
    
    # Run tests
    if args.url:
        await tester.test_single_url(args.url, args.model)
    elif args.category == "all":
        await tester.test_all_categories(args.model, args.limit)
    elif args.category:
        await tester.test_category(args.category, args.model, args.limit)
    else:
        parser.print_help()
        return
    
    # Generate report
    tester.generate_report()
    
    logger.info("Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
