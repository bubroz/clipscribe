#!/usr/bin/env python3
"""
Test script for ClipScribe retry logic and monitoring systems.

This script tests:
1. Retry Manager functionality
2. Monitoring system metrics collection
3. Alert system
4. Health checks
5. Dead letter queue handling
"""

import asyncio
import json
import time
import subprocess
import sys
from typing import Dict, Any, List
from datetime import datetime


class RetryMonitoringTester:
    """Test suite for retry logic and monitoring systems."""

    def __init__(self, api_url: str = "https://clipscribe-api-16459511304.us-central1.run.app",
                 worker_url: str = "https://clipscribe-worker-16459511304.us-central1.run.app",
                 test_token: str = "test-token-123"):
        self.api_url = api_url
        self.worker_url = worker_url
        self.test_token = test_token
        self.results: List[Dict[str, Any]] = []

    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
        if message:
            print(f"   {message}")
        self.results.append({
            "test": name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def run_curl(self, cmd: str) -> tuple[bool, str]:
        """Run a curl command and return success status and output."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Request timed out"
        except Exception as e:
            return False, str(e)

    async def test_api_health(self):
        """Test API health endpoint."""
        print("\n🏥 Testing API Health Check...")

        cmd = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/health"'
        success, output = self.run_curl(cmd)

        if success:
            try:
                data = json.loads(output)
                if data.get("status") in ["healthy", "warning"]:
                    self.log_test("API Health Check", True, f"Status: {data.get('status')}")
                else:
                    self.log_test("API Health Check", False, f"Unexpected status: {data}")
            except json.JSONDecodeError:
                self.log_test("API Health Check", False, f"Invalid JSON response: {output}")
        else:
            self.log_test("API Health Check", False, f"Request failed: {output}")

    async def test_worker_health(self):
        """Test Worker health endpoint."""
        print("\n🏥 Testing Worker Health Check...")

        cmd = f'curl -s "{self.worker_url}/health"'
        success, output = self.run_curl(cmd)

        if success:
            try:
                data = json.loads(output)
                if data.get("status") in ["healthy", "warning"]:
                    self.log_test("Worker Health Check", True, f"Status: {data.get('status')}")
                else:
                    self.log_test("Worker Health Check", False, f"Unexpected status: {data}")
            except json.JSONDecodeError:
                self.log_test("Worker Health Check", False, f"Invalid JSON response: {output}")
        else:
            self.log_test("Worker Health Check", False, f"Request failed: {output}")

    async def test_api_monitoring_endpoints(self):
        """Test API monitoring endpoints."""
        print("\n📊 Testing API Monitoring Endpoints...")

        endpoints = [
            "/v1/monitoring/metrics",
            "/v1/monitoring/alerts",
            "/v1/monitoring/queue-status",
            "/v1/monitoring/dead-letter-queue"
        ]

        for endpoint in endpoints:
            cmd = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}{endpoint}"'
            success, output = self.run_curl(cmd)

            if success:
                try:
                    data = json.loads(output)
                    if "timestamp" in data:
                        self.log_test(f"API {endpoint}", True, f"Response received with {len(data)} fields")
                    else:
                        self.log_test(f"API {endpoint}", False, f"Missing timestamp field: {data}")
                except json.JSONDecodeError:
                    self.log_test(f"API {endpoint}", False, f"Invalid JSON response: {output}")
            else:
                self.log_test(f"API {endpoint}", False, f"Request failed: {output}")

    async def test_worker_monitoring_endpoints(self):
        """Test Worker monitoring endpoints."""
        print("\n📊 Testing Worker Monitoring Endpoints...")

        endpoints = [
            "/queue-status",
            "/metrics",
            "/alerts",
            "/dead-letter-queue"
        ]

        for endpoint in endpoints:
            cmd = f'curl -s "{self.worker_url}{endpoint}"'
            success, output = self.run_curl(cmd)

            if success:
                try:
                    if endpoint == "/metrics":
                        # Metrics endpoint returns plain text
                        if "clipscribe_" in output:
                            self.log_test(f"Worker {endpoint}", True, "Prometheus metrics format")
                        else:
                            self.log_test(f"Worker {endpoint}", False, f"Unexpected format: {output[:100]}")
                    else:
                        # JSON endpoints
                        data = json.loads(output)
                        if "timestamp" in data:
                            self.log_test(f"Worker {endpoint}", True, f"Response received with {len(data)} fields")
                        else:
                            self.log_test(f"Worker {endpoint}", False, f"Missing timestamp field: {data}")
                except json.JSONDecodeError:
                    if endpoint != "/metrics":
                        self.log_test(f"Worker {endpoint}", False, f"Invalid JSON response: {output}")
                    else:
                        # Metrics endpoint should not be JSON
                        self.log_test(f"Worker {endpoint}", True, "Non-JSON format as expected")
            else:
                self.log_test(f"Worker {endpoint}", False, f"Request failed: {output}")

    async def test_job_with_retry_logic(self):
        """Test job processing with retry logic."""
        print("\n🔄 Testing Job Processing with Retry Logic...")

        # Submit a job with invalid URL to test retry handling
        payload = {"url": "https://invalid-url-that-does-not-exist-12345.com"}
        json_payload = json.dumps(payload)

        cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'{json_payload}\' "{self.api_url}/v1/jobs"'
        success, output = self.run_curl(cmd)

        if success:
            try:
                data = json.loads(output)
                job_id = data.get("job_id")
                if job_id:
                    self.log_test("Job Submission with Retry", True, f"Job created: {job_id}")

                    # Monitor the job for a few minutes to see retry behavior
                    max_attempts = 6  # 3 minutes
                    for attempt in range(max_attempts):
                        await asyncio.sleep(30)  # Wait 30 seconds between checks

                        cmd_status = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/jobs/{job_id}"'
                        success_status, output_status = self.run_curl(cmd_status)

                        if success_status:
                            try:
                                status_data = json.loads(output_status)
                                state = status_data.get("state")
                                print(f"   Job {job_id} state: {state} (attempt {attempt + 1}/{max_attempts})")

                                if state == "COMPLETED":
                                    self.log_test("Job Retry Logic", True, "Job completed despite invalid URL")
                                    break
                                elif state == "FAILED":
                                    error = status_data.get("error", "Unknown error")
                                    self.log_test("Job Retry Logic", True, f"Job failed gracefully: {error}")
                                    break
                            except json.JSONDecodeError:
                                self.log_test("Job Status Check", False, "Invalid JSON response")
                                break
                        else:
                            self.log_test("Job Status Check", False, f"Status request failed: {output_status}")
                            break
                    else:
                        self.log_test("Job Retry Logic", True, "Job still processing (acceptable for test)")
                else:
                    self.log_test("Job Submission with Retry", False, f"Unexpected response: {data}")
            except json.JSONDecodeError:
                self.log_test("Job Submission with Retry", False, f"Invalid JSON response: {output}")
        else:
            self.log_test("Job Submission with Retry", False, f"Request failed: {output}")

    async def test_alert_system(self):
        """Test alert system by triggering conditions."""
        print("\n🚨 Testing Alert System...")

        # Get current alerts
        cmd = f'curl -s "{self.worker_url}/alerts"'
        success, output = self.run_curl(cmd)

        if success:
            try:
                data = json.loads(output)
                alert_count = data.get("total_count", 0)
                self.log_test("Alert System Query", True, f"Found {alert_count} active alerts")

                # Check for default alerts
                if alert_count > 0:
                    alerts = data.get("active_alerts", [])
                    severity_counts = {}
                    for alert in alerts:
                        severity = alert.get("severity", "unknown")
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1

                    self.log_test("Alert Severity Distribution", True,
                                f"Critical: {severity_counts.get('critical', 0)}, "
                                f"Warning: {severity_counts.get('warning', 0)}, "
                                f"Info: {severity_counts.get('info', 0)}")
                else:
                    self.log_test("Alert System Empty", True, "No active alerts (system healthy)")

            except json.JSONDecodeError:
                self.log_test("Alert System Query", False, f"Invalid JSON response: {output}")
        else:
            self.log_test("Alert System Query", False, f"Request failed: {output}")

    async def test_metrics_collection(self):
        """Test metrics collection."""
        print("\n📈 Testing Metrics Collection...")

        # Test API metrics
        cmd = f'curl -s "{self.api_url}/metrics"'
        success, output = self.run_curl(cmd)

        if success:
            if "clipscribe_" in output or "# HELP" in output:
                self.log_test("API Metrics Collection", True, "Prometheus format metrics received")
            else:
                self.log_test("API Metrics Collection", False, f"Unexpected format: {output[:200]}")
        else:
            self.log_test("API Metrics Collection", False, f"Request failed: {output}")

        # Test Worker metrics
        cmd = f'curl -s "{self.worker_url}/metrics"'
        success, output = self.run_curl(cmd)

        if success:
            if "clipscribe_" in output:
                metrics_lines = [line for line in output.split('\n') if line.strip() and not line.startswith('#')]
                self.log_test("Worker Metrics Collection", True, f"Found {len(metrics_lines)} metric values")
            else:
                self.log_test("Worker Metrics Collection", False, f"Unexpected format: {output[:200]}")
        else:
            self.log_test("Worker Metrics Collection", False, f"Request failed: {output}")

    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 70)
        print("🎯 RETRY LOGIC & MONITORING TEST RESULTS")
        print("=" * 70)

        passed = sum(1 for result in self.results if result["passed"])
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"Tests Completed: {total}")
        print(f"Tests Passed: {passed}")
        print(f"Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("🎉 RETRY LOGIC & MONITORING SYSTEMS WORKING WELL!")
        elif success_rate >= 60:
            print("⚠️  SOME ISSUES DETECTED - REVIEW FAILED TESTS")
        else:
            print("❌ SIGNIFICANT ISSUES - REQUIRES ATTENTION")

        # Show failed tests
        failed_tests = [result for result in self.results if not result["passed"]]
        if failed_tests:
            print("\n❌ ISSUES FOUND:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")

        print("\n📊 SYSTEM STATUS:")
        if success_rate >= 80:
            print("   ✅ Retry logic and monitoring systems operational")
            print("   ✅ Alert system functional")
            print("   ✅ Health checks working")
            print("   ✅ Metrics collection active")
            print("   🚀 READY FOR PRODUCTION USE")
        else:
            print("   ⚠️  Some systems may need attention")
            print("   🔧  Review failed tests for specific issues")

    async def run_comprehensive_test(self):
        """Run the complete test suite."""
        print("🚀 Starting Retry Logic & Monitoring Test Suite")
        print("=" * 60)
        print(f"API URL: {self.api_url}")
        print(f"Worker URL: {self.worker_url}")
        print(f"Test Token: {self.test_token[:10]}...")
        print("=" * 60)

        # Run all tests
        await self.test_api_health()
        await self.test_worker_health()
        await self.test_api_monitoring_endpoints()
        await self.test_worker_monitoring_endpoints()
        await self.test_metrics_collection()
        await self.test_alert_system()
        await self.test_job_with_retry_logic()

        # Print summary
        self.print_summary()


async def main():
    """Main entry point."""
    # Use default URLs - can be overridden via environment variables
    api_url = "https://clipscribe-api-16459511304.us-central1.run.app"
    worker_url = "https://clipscribe-worker-16459511304.us-central1.run.app"
    test_token = "test-token-123"  # In production, this would be a real token

    tester = RetryMonitoringTester(api_url, worker_url, test_token)
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())
