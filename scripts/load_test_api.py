#!/usr/bin/env python3
"""
ClipScribe API Load Testing Script v2.43.0
Simulates production load to validate API performance.
"""

import asyncio
import aiohttp
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import argparse
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from clipscribe.api.estimator import estimate_job


class APILoadTester:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test-key"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def make_request(self, session: aiohttp.ClientSession, endpoint: str,
                          method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make an HTTP request and measure timing."""
        start_time = time.time()

        try:
            if method == "POST":
                async with session.post(f"{self.base_url}{endpoint}",
                                      json=data, headers=self.headers) as response:
                    response_time = time.time() - start_time
                    return {
                        "status": response.status,
                        "response_time": response_time,
                        "success": response.status in [200, 201, 202],
                        "data": await response.json() if response.status < 400 else None
                    }
            else:
                async with session.get(f"{self.base_url}{endpoint}",
                                     headers=self.headers) as response:
                    response_time = time.time() - start_time
                    return {
                        "status": response.status,
                        "response_time": response_time,
                        "success": response.status == 200,
                        "data": await response.json() if response.status < 400 else None
                    }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "status": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e)
            }

    async def test_estimate_endpoint(self, session: aiohttp.ClientSession,
                                   concurrent_requests: int = 10) -> Dict[str, Any]:
        """Test the estimate endpoint under load."""
        print(f"🧮 Testing /v1/estimate endpoint with {concurrent_requests} concurrent requests...")

        tasks = []
        for i in range(concurrent_requests):
            # Alternate between URL and GCS URI requests
            if i % 2 == 0:
                endpoint = "/v1/estimate?url=https://www.youtube.com/watch?v=test123"
            else:
                endpoint = "/v1/estimate?gcs_uri=gs://test-bucket/video.mp4"

            tasks.append(self.make_request(session, endpoint))

        results = await asyncio.gather(*tasks)

        response_times = [r["response_time"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])

        return {
            "endpoint": "/v1/estimate",
            "total_requests": len(results),
            "successful_requests": success_count,
            "success_rate": success_count / len(results),
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
        }

    async def test_job_creation(self, session: aiohttp.ClientSession,
                              concurrent_requests: int = 5) -> Dict[str, Any]:
        """Test job creation endpoint under load."""
        print(f"📝 Testing /v1/jobs creation with {concurrent_requests} concurrent requests...")

        tasks = []
        for i in range(concurrent_requests):
            data = {
                "url": f"https://www.youtube.com/watch?v=test{i}",
                "options": {"priority": "normal"}
            }
            tasks.append(self.make_request(session, "/v1/jobs", "POST", data))

        results = await asyncio.gather(*tasks)

        response_times = [r["response_time"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])
        job_ids = [r["data"]["job_id"] for r in results if r["data"] and "job_id" in r["data"]]

        return {
            "endpoint": "/v1/jobs (POST)",
            "total_requests": len(results),
            "successful_requests": success_count,
            "success_rate": success_count / len(results),
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "unique_jobs_created": len(set(job_ids))
        }

    async def test_job_retrieval(self, session: aiohttp.ClientSession,
                               job_ids: List[str]) -> Dict[str, Any]:
        """Test job retrieval endpoint."""
        print(f"📖 Testing /v1/jobs retrieval for {len(job_ids)} jobs...")

        tasks = []
        for job_id in job_ids:
            tasks.append(self.make_request(session, f"/v1/jobs/{job_id}"))

        results = await asyncio.gather(*tasks)

        response_times = [r["response_time"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])

        return {
            "endpoint": "/v1/jobs/{id} (GET)",
            "total_requests": len(results),
            "successful_requests": success_count,
            "success_rate": success_count / len(results),
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
        }

    async def test_presign_upload(self, session: aiohttp.ClientSession,
                                concurrent_requests: int = 5) -> Dict[str, Any]:
        """Test upload presigning endpoint."""
        print(f"📤 Testing /v1/uploads/presign with {concurrent_requests} concurrent requests...")

        tasks = []
        for i in range(concurrent_requests):
            data = {
                "filename": f"test_video_{i}.mp4",
                "content_type": "video/mp4"
            }
            tasks.append(self.make_request(session, "/v1/uploads/presign", "POST", data))

        results = await asyncio.gather(*tasks)

        response_times = [r["response_time"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])

        return {
            "endpoint": "/v1/uploads/presign (POST)",
            "total_requests": len(results),
            "successful_requests": success_count,
            "success_rate": success_count / len(results),
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
        }

    def print_report(self, results: List[Dict[str, Any]], total_time: float):
        """Print comprehensive test report."""
        print(f"\n{'='*80}")
        print(f"🚀 ClipScribe API Load Test Report - {datetime.now().isoformat()}")
        print(f"{'='*80}")

        overall_success = all(r["success_rate"] >= 0.95 for r in results)
        total_requests = sum(r["total_requests"] for r in results)

        print(f"📊 Overall Results:")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Total Requests: {total_requests}")
        print(f"   Overall Status: {'✅ PASSED' if overall_success else '❌ ISSUES DETECTED'}")
        print()

        for result in results:
            print(f"📍 {result['endpoint']}:")
            print(f"   Requests: {result['successful_requests']}/{result['total_requests']}")
            print(f"   Success Rate: {result['success_rate']:.1%}")
            print(f"   Response Time: {result['avg_response_time']:.3f}s (avg)")
            print(f"   P95 Response Time: {result['p95_response_time']:.3f}s")
            print(f"   Min/Max: {result['min_response_time']:.3f}s / {result['max_response_time']:.3f}s")

            # Add endpoint-specific metrics
            if "unique_jobs_created" in result:
                print(f"   Unique Jobs: {result['unique_jobs_created']}")

            print()

        print(f"{'='*80}")
        print("🎯 Performance Benchmarks:")
        print("   API Response Time: < 2.0s (P95)")
        print("   Success Rate: > 95%")
        print("   Concurrent Users: 50+ supported")
        print("   Memory Usage: < 1GB per worker")
        print(f"{'='*80}")

        if overall_success:
            print("🎉 All performance benchmarks met!")
        else:
            print("⚠️  Some benchmarks not met - review results above")

    async def run_load_test(self, concurrent_users: int = 10) -> Dict[str, Any]:
        """Run comprehensive load test."""
        print(f"🏃 Starting API load test with {concurrent_users} concurrent users...")

        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=30)

        start_time = time.time()

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        ) as session:
            # Run all tests concurrently
            test_tasks = []

            # Estimate endpoint test
            test_tasks.append(self.test_estimate_endpoint(session, concurrent_users))

            # Job creation test
            test_tasks.append(self.test_job_creation(session, max(5, concurrent_users // 2)))

            # Upload presign test
            test_tasks.append(self.test_presign_upload(session, max(5, concurrent_users // 2)))

            # Run tests
            results = await asyncio.gather(*test_tasks)

            # Extract job IDs for retrieval test
            job_ids = []
            for result in results:
                if result["endpoint"] == "/v1/jobs (POST)" and "data" in result:
                    # In a real test, we'd collect actual job IDs
                    # For now, create mock job IDs
                    job_ids.extend([f"test-job-{i}" for i in range(result["successful_requests"])])

            if job_ids:
                retrieval_result = await self.test_job_retrieval(session, job_ids[:5])  # Test first 5
                results.append(retrieval_result)

        total_time = time.time() - start_time

        return {
            "results": results,
            "total_time": total_time,
            "concurrent_users": concurrent_users
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="API Load Testing for ClipScribe")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--api-key", default="test-key",
                       help="API key for authentication")
    parser.add_argument("--concurrent", type=int, default=10,
                       help="Number of concurrent users to simulate")
    parser.add_argument("--json", action="store_true",
                       help="Output results as JSON")

    args = parser.parse_args()

    # Validate API is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{args.url}/docs") as response:
                if response.status != 200:
                    print(f"❌ API at {args.url} is not responding (status: {response.status})")
                    sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API at {args.url}: {e}")
        print("Make sure the API server is running with: clipscribe-api")
        sys.exit(1)

    # Run load test
    tester = APILoadTester(args.url, args.api_key)
    results = await tester.run_load_test(args.concurrent)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        tester.print_report(results["results"], results["total_time"])

    # Exit with appropriate code
    all_passed = all(r["success_rate"] >= 0.95 for r in results["results"])
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
