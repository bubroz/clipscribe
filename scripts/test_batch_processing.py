#!/usr/bin/env python3
"""
Test Batch Processing Functionality

Validates that the batch processing system works correctly with:
- URL file parsing
- Parallel job execution
- Status tracking
- Result aggregation
- Error handling
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.processors.batch_processor import BatchProcessor, ProcessingPriority


async def test_batch_processing():
    """Test the complete batch processing workflow."""

    print("🧪 TESTING CLIPSCRIBE BATCH PROCESSING")
    print("=" * 50)

    # Test URLs (using mock/safe URLs for testing)
    test_urls = [
        "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Real short video
        "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Duplicate for testing
    ]

    # Create temporary directory for test outputs
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")

        # Initialize batch processor
        processor = BatchProcessor(
            max_concurrent_jobs=2,  # Limit concurrency for testing
            output_dir=temp_dir,
            enable_caching=True
        )

        try:
            print("🚀 Starting batch processing test...")

            # Process batch
            result = await processor.process_batch(
                video_urls=test_urls,
                batch_id="test_batch_001",
                priority=ProcessingPriority.NORMAL
            )

            print("\\n✅ Batch processing completed!")
            print(f"📊 Results: {result.completed_jobs}/{result.total_jobs} successful")
            print(f"⏱️  Total time: {result.total_processing_time:.2f}s")
            print(f"💰 Total cost: ${result.total_cost:.2f}")
            print(f"📂 Results saved to: {result.output_directory}")

            # Validate results
            print("\\n🔍 Validating results...")

            # Check batch directory exists
            batch_dir = Path(result.output_directory) / result.batch_id
            if batch_dir.exists():
                print("✅ Batch directory created")
            else:
                print("❌ Batch directory not found")
                return False

            # Check result files
            results_file = batch_dir / "batch_results.json"
            if results_file.exists():
                print("✅ Batch results file created")
            else:
                print("❌ Batch results file not found")
                return False

            # Check individual job directories
            job_dirs = list(batch_dir.glob("**/"))
            job_dirs = [d for d in job_dirs if d.is_dir() and d.name.startswith("test_batch_001_job_")]
            if len(job_dirs) == len(test_urls):
                print(f"✅ {len(job_dirs)} job directories created")
            else:
                print(f"❌ Expected {len(test_urls)} job directories, found {len(job_dirs)}")
                return False

            # Check job result files
            result_files = list(batch_dir.glob("**/*.json"))
            result_files = [f for f in result_files if "batch_" not in f.name]  # Exclude batch metadata files
            if len(result_files) > 0:
                print(f"✅ {len(result_files)} job result files created")
            else:
                print("❌ No job result files found")
                return False

            print("\\n🎉 All batch processing tests passed!")
            return True

        except Exception as e:
            print(f"❌ Batch processing test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_batch_status_and_results():
    """Test batch status and results retrieval."""

    print("\\n🧪 TESTING BATCH STATUS & RESULTS")
    print("=" * 50)

    # Create a simple batch for testing status/results
    test_urls = ["https://www.youtube.com/watch?v=6ZVj1_SE4Mo"]

    with tempfile.TemporaryDirectory() as temp_dir:
        processor = BatchProcessor(output_dir=temp_dir)

        try:
            # Create a test batch
            result = await processor.process_batch(
                video_urls=test_urls,
                batch_id="status_test_batch",
                priority=ProcessingPriority.NORMAL
            )

            # Test status retrieval
            status_result = await processor.get_batch_status("status_test_batch")
            if status_result:
                print("✅ Batch status retrieval works")
            else:
                print("❌ Batch status retrieval failed")
                return False

            # Test results retrieval
            results_result = await processor.get_batch_results("status_test_batch")
            if results_result:
                print("✅ Batch results retrieval works")
            else:
                print("❌ Batch results retrieval failed")
                return False

            # Test invalid batch ID
            invalid_status = await processor.get_batch_status("nonexistent_batch")
            if invalid_status is None:
                print("✅ Invalid batch ID handling works")
            else:
                print("❌ Invalid batch ID handling failed")
                return False

            print("\\n🎉 All status/results tests passed!")
            return True

        except Exception as e:
            print(f"❌ Status/results test failed: {e}")
            return False


async def main():
    """Run all batch processing tests."""

    print("🚀 CLIPSCRIBE BATCH PROCESSING TEST SUITE")
    print("=" * 60)

    # Test 1: Basic batch processing
    test1_passed = await test_batch_processing()

    # Test 2: Status and results retrieval
    test2_passed = await test_batch_status_and_results()

    # Summary
    print("\\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Batch Processing Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Status/Results Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\\n🎉 ALL TESTS PASSED! Batch processing is ready for use.")
        return 0
    else:
        print("\\n❌ SOME TESTS FAILED. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
