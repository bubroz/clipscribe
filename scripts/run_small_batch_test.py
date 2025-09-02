#!/usr/bin/env python3
"""
Small Batch Test Script for ClipScribe

Runs a minimal test batch to verify everything works before production deployment.
Tests both Flash and Pro models with diverse content types.

Usage:
    python scripts/run_small_batch_test.py
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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmallBatchTester:
    """Runs small batch tests before production deployment."""
    
    # Small, diverse test set
    SMALL_TEST_BATCH = [
        {
            "category": "news",
            "id": "short_news",
            "url": "https://www.youtube.com/watch?v=A-bdxIi7v04",  # PBS News Weekend ~26min
            "title": "PBS News Weekend (26 min)",
            "expected_duration": 26 * 60,
            "test_purpose": "Standard news extraction"
        },
        {
            "category": "defense",  
            "id": "tier_training",
            "url": "https://www.youtube.com/watch?v=Nr7vbOSzpSk",  # Tier 1&2 Part 1 ~31min
            "title": "Tier 1&2 Training (31 min)",
            "expected_duration": 31 * 60,
            "test_purpose": "Professional training content"
        },
        {
            "category": "intelligence",
            "id": "privacy",
            "url": "https://www.youtube.com/watch?v=V9VEvGSzzk0",  # Data Privacy ~18min
            "title": "Data Privacy Investigation (18 min)",
            "expected_duration": 18 * 60,
            "test_purpose": "OSINT/Privacy analysis"
        },
        {
            "category": "error_test",
            "id": "invalid_url",
            "url": "https://www.youtube.com/watch?v=INVALID_VIDEO_ID",
            "title": "Invalid URL Test",
            "expected_duration": 0,
            "test_purpose": "Error handling validation"
        }
    ]
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    async def run_test(self, video: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Run a single test."""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {video['title']}")
        logger.info(f"Model: {model.upper()}")
        logger.info(f"Purpose: {video['test_purpose']}")
        logger.info(f"URL: {video['url']}")
        
        result = {
            "video": video,
            "model": model,
            "start_time": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            # Import and initialize
            from src.clipscribe.api.job_worker import CloudRunJobWorker
            
            # Set model
            os.environ["USE_PRO_MODEL"] = "true" if model == "pro" else "false"
            
            # Create worker
            worker = CloudRunJobWorker()
            
            # Create job
            job_id = f"test_{model}_{video['id']}_{int(time.time())}"
            payload = {"url": video["url"], "options": {"model": model}}
            
            # Process
            start = time.time()
            job_result = await worker.process_job(job_id, payload)
            duration = time.time() - start
            
            # Analyze results
            if job_result["status"] == "completed":
                result["success"] = True
                result["processing_time"] = duration
                result["cost"] = job_result.get("cost_estimate", 0)
                
                # Extract metrics from artifacts
                if "artifacts" in job_result:
                    # This would need actual parsing of artifacts
                    result["entity_count"] = "Check artifacts"
                    result["relationship_count"] = "Check artifacts"
                
                logger.info(f"✅ SUCCESS in {duration:.1f}s - Cost: ${result['cost']:.4f}")
                
            elif video["id"] == "invalid_url":
                # Expected failure for error test
                result["success"] = True
                result["error_handled"] = True
                result["error_message"] = job_result.get("error", "Unknown")
                logger.info(f"✅ ERROR HANDLING WORKS: {result['error_message']}")
                
            else:
                result["error"] = job_result.get("error", "Processing failed")
                logger.error(f"❌ FAILED: {result['error']}")
                
        except Exception as e:
            result["error"] = str(e)
            
            if video["id"] == "invalid_url":
                result["success"] = True
                result["error_handled"] = True
                logger.info(f"✅ ERROR HANDLING WORKS: {e}")
            else:
                logger.error(f"❌ EXCEPTION: {e}")
        
        result["end_time"] = datetime.now().isoformat()
        return result
    
    async def run_small_batch(self):
        """Run the complete small batch test."""
        
        logger.info("\n" + "="*80)
        logger.info("🧪 CLIPSCRIBE SMALL BATCH TEST")
        logger.info("="*80)
        logger.info(f"Start Time: {self.start_time}")
        logger.info(f"Test Videos: {len(self.SMALL_TEST_BATCH)}")
        logger.info(f"Models: Flash & Pro")
        logger.info("="*80)
        
        # Test each video with both models
        for video in self.SMALL_TEST_BATCH:
            # Flash test
            flash_result = await self.run_test(video, "flash")
            self.results.append(flash_result)
            
            # Skip Pro test for error handling video
            if video["id"] != "invalid_url":
                # Pro test
                pro_result = await self.run_test(video, "pro")
                self.results.append(pro_result)
            
            # Brief pause between tests
            await asyncio.sleep(2)
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary."""
        
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        flash_results = [r for r in self.results if r["model"] == "flash"]
        pro_results = [r for r in self.results if r["model"] == "pro"]
        
        flash_success = sum(1 for r in flash_results if r["success"])
        pro_success = sum(1 for r in pro_results if r["success"])
        
        flash_cost = sum(r.get("cost", 0) for r in flash_results if r["success"])
        pro_cost = sum(r.get("cost", 0) for r in pro_results if r["success"])
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*80)
        
        logger.info(f"\n⏱️  Total Time: {total_duration:.1f} seconds")
        logger.info(f"📝 Total Tests: {len(self.results)}")
        
        logger.info(f"\n🔵 FLASH Model:")
        logger.info(f"   Success Rate: {flash_success}/{len(flash_results)} ({flash_success/len(flash_results)*100:.0f}%)")
        logger.info(f"   Total Cost: ${flash_cost:.4f}")
        
        logger.info(f"\n🟣 PRO Model:")
        logger.info(f"   Success Rate: {pro_success}/{len(pro_results)} ({pro_success/len(pro_results)*100:.0f}%)")
        logger.info(f"   Total Cost: ${pro_cost:.4f}")
        
        logger.info(f"\n💰 Cost Comparison:")
        if flash_cost > 0:
            logger.info(f"   Pro is {pro_cost/flash_cost:.1f}x more expensive than Flash")
        
        # Check for critical issues
        critical_issues = []
        
        # Check if basic extraction works
        content_tests = [r for r in self.results if r["video"]["id"] not in ["invalid_url"]]
        if not any(r["success"] for r in content_tests):
            critical_issues.append("❌ No successful content extraction")
        
        # Check if error handling works
        error_tests = [r for r in self.results if r["video"]["id"] == "invalid_url"]
        if not any(r.get("error_handled") for r in error_tests):
            critical_issues.append("❌ Error handling not working")
        
        # Final verdict
        logger.info("\n" + "="*80)
        if critical_issues:
            logger.error("🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                logger.error(f"   {issue}")
            logger.error("\n⛔ DO NOT DEPLOY TO PRODUCTION")
        else:
            logger.info("✅ ALL CRITICAL TESTS PASSED")
            logger.info("🚀 READY FOR PRODUCTION DEPLOYMENT")
        
        logger.info("="*80)
        
        # Save results
        output_file = Path(f"test_results/small_batch_{int(time.time())}.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"\n📁 Results saved to: {output_file}")


async def main():
    """Main entry point."""
    
    # Check for local environment
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("❌ GOOGLE_API_KEY not set")
        logger.error("Set environment variable: export GOOGLE_API_KEY=your_key")
        sys.exit(1)
    
    # Run tests
    tester = SmallBatchTester()
    await tester.run_small_batch()


if __name__ == "__main__":
    asyncio.run(main())
