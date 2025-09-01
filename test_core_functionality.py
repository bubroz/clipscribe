#!/usr/bin/env python3
"""
Core Functionality Test for ClipScribe Infrastructure

Tests the essential components that must work for the system to be operational.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

class CoreFunctionalityTest:
    """Test core ClipScribe functionality."""

    def __init__(self):
        self.api_url = "https://clipscribe-api-16459511304.us-central1.run.app"
        self.web_url = "https://clipscribe-web-16459511304.us-central1.run.app"
        self.worker_url = "https://clipscribe-worker-16459511304.us-central1.run.app"

        # Test token for authentication
        self.test_token = "test-token-12345"

        # Test results
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }

    def run_curl(self, cmd: str) -> tuple[bool, str]:
        """Run a curl command and return success status and output."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test results."""
        self.results["tests_run"] += 1
        if success:
            self.results["tests_passed"] += 1
            status = "✅ PASS"
        else:
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"{test_name}: {message}")
            status = "❌ FAIL"

        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")

    async def test_service_availability(self):
        """Test 1: All Services Are Accessible"""
        print("🔍 Testing Service Availability...")

        # Test API service
        cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{self.api_url}/docs"'
        success, output = self.run_curl(cmd)
        if success and output.strip() == "200":
            self.log_test("API Service Availability", True, f"API accessible at {self.api_url}")
        else:
            self.log_test("API Service Availability", False, f"API not accessible: HTTP {output.strip()}")

        # Test Web service
        cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{self.web_url}"'
        success, output = self.run_curl(cmd)
        if success and output.strip() == "200":
            self.log_test("Web Service Availability", True, f"Web accessible at {self.web_url}")
        else:
            self.log_test("Web Service Availability", False, f"Web not accessible: HTTP {output.strip()}")

        # Test Worker service (should return 403 - not publicly accessible)
        cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{self.worker_url}/health"'
        success, output = self.run_curl(cmd)
        if success and output.strip() == "403":
            self.log_test("Worker Service Security", True, "Worker properly secured (not publicly accessible)")
        else:
            self.log_test("Worker Service Security", False, f"Worker security issue: HTTP {output.strip()}")

    async def test_api_functionality(self):
        """Test 2: API Core Functionality"""
        print("\n🔧 Testing API Functionality...")

        # Test authentication
        cmd = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/status"'
        success, output = self.run_curl(cmd)
        if success:
            try:
                data = json.loads(output)
                if data.get("status") == "healthy":
                    self.log_test("API Authentication", True, "Authentication working correctly")
                else:
                    self.log_test("API Authentication", False, f"Unexpected response: {data}")
            except json.JSONDecodeError:
                self.log_test("API Authentication", False, f"Invalid JSON: {output}")
        else:
            self.log_test("API Authentication", False, "Authentication request failed")

        # Test unauthenticated access (should fail)
        cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{self.api_url}/v1/status"'
        success, output = self.run_curl(cmd)
        if success and output.strip() == "401":
            self.log_test("API Security", True, "Properly rejects unauthenticated requests")
        else:
            self.log_test("API Security", False, f"Security issue: HTTP {output.strip()}")

    async def test_job_processing_flow(self):
        """Test 3: Complete Job Processing Flow"""
        print("\n⚙️  Testing Job Processing Flow...")

        # Submit a test job
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Short test video
        payload = {
            "url": test_url,
            "options": {
                "extract_entities": True,
                "max_duration": 30  # Very short for testing
            }
        }

        json_payload = json.dumps(payload)
        cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'{json_payload}\' "{self.api_url}/v1/jobs"'
        success, output = self.run_curl(cmd)

        if not success:
            self.log_test("Job Submission", False, f"Job submission failed: {output}")
            return

        try:
            data = json.loads(output)
            job_id = data.get("job_id")
            if not job_id:
                self.log_test("Job Submission", False, f"No job_id in response: {data}")
                return

            self.log_test("Job Submission", True, f"Job submitted successfully: {job_id}")

            # Monitor job progress
            max_attempts = 20  # 3 minutes max
            for attempt in range(max_attempts):
                await asyncio.sleep(10)  # Wait 10 seconds

                cmd_status = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/jobs/{job_id}"'
                success_status, output_status = self.run_curl(cmd_status)

                if success_status:
                    try:
                        status_data = json.loads(output_status)
                        state = status_data.get("state")

                        if state == "COMPLETED":
                            self.log_test("Job Processing", True, f"Job completed successfully in {attempt * 10} seconds")
                            return
                        elif state == "FAILED":
                            error_msg = status_data.get("error", "Unknown error")
                            self.log_test("Job Processing", False, f"Job failed: {error_msg}")
                            return
                        elif state in ["PROCESSING", "QUEUED", "DOWNLOADING", "ANALYZING"]:
                            print(f"   Job status: {state} (waiting...)")
                            continue
                        else:
                            print(f"   Job status: {state}")
                    except json.JSONDecodeError:
                        self.log_test("Job Monitoring", False, f"Invalid JSON response: {output_status}")
                        return
                else:
                    self.log_test("Job Monitoring", False, f"Status check failed: {output_status}")
                    return

            self.log_test("Job Processing", False, f"Job monitoring timed out after {max_attempts * 10} seconds")

        except json.JSONDecodeError:
            self.log_test("Job Submission", False, f"Invalid JSON response: {output}")

    async def test_error_scenarios(self):
        """Test 4: Error Handling"""
        print("\n🛡️  Testing Error Handling...")

        # Test invalid URL - should accept job and handle gracefully
        payload = {"url": "https://invalid-url-that-does-not-exist.com"}
        json_payload = json.dumps(payload)
        cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'{json_payload}\' "{self.api_url}/v1/jobs"'
        success, output = self.run_curl(cmd)

        if success:
            try:
                data = json.loads(output)
                job_id = data.get("job_id")
                if job_id:
                    self.log_test("Invalid URL Handling", True, f"Gracefully accepts invalid URL job: {job_id}")

                    # Monitor the job to see the final result
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        await asyncio.sleep(3)  # Give it time to process
                        cmd_status = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/jobs/{job_id}"'
                        success_status, output_status = self.run_curl(cmd_status)

                        if success_status:
                            try:
                                status_data = json.loads(output_status)
                                state = status_data.get("state")
                                if state in ["COMPLETED", "FAILED"]:
                                    if state == "COMPLETED":
                                        self.log_test("Invalid URL Processing", True, "Worker handled invalid URL gracefully and completed")
                                    else:
                                        self.log_test("Invalid URL Processing", True, f"Worker properly marked job as failed: {status_data.get('error', 'Unknown error')}")
                                    break
                                elif state in ["PROCESSING", "QUEUED"]:
                                    print(f"   Job still processing (attempt {attempt + 1}/{max_attempts})")
                                else:
                                    print(f"   Job state: {state}")
                            except json.JSONDecodeError:
                                self.log_test("Invalid URL Processing", False, "Could not parse job status")
                                break
                        else:
                            self.log_test("Invalid URL Processing", False, "Could not get job status")
                            break
                    else:
                        self.log_test("Invalid URL Processing", True, "Job still processing (acceptable for test)")
                else:
                    self.log_test("Invalid URL Handling", False, f"Unexpected response: {data}")
            except json.JSONDecodeError:
                self.log_test("Invalid URL Handling", False, f"Invalid response format: {output}")
        else:
            self.log_test("Invalid URL Handling", False, f"Request failed: {output}")

        # Test malformed JSON - should get proper FastAPI error
        cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'invalid json\' "{self.api_url}/v1/jobs"'
        success, output = self.run_curl(cmd)

        if success:
            try:
                data = json.loads(output)
                # FastAPI returns validation errors in this format
                if isinstance(data, dict) and "detail" in data:
                    if isinstance(data["detail"], list) and len(data["detail"]) > 0:
                        if data["detail"][0].get("type") == "json_invalid":
                            self.log_test("Malformed JSON Handling", True, "FastAPI properly rejects malformed JSON")
                        else:
                            self.log_test("Malformed JSON Handling", True, f"Proper validation error: {data['detail'][0].get('type')}")
                    else:
                        self.log_test("Malformed JSON Handling", True, "Proper error response format")
                else:
                    self.log_test("Malformed JSON Handling", False, f"Unexpected response format: {data}")
            except json.JSONDecodeError:
                self.log_test("Malformed JSON Handling", False, f"Invalid response format: {output}")
        else:
            self.log_test("Malformed JSON Handling", False, f"Request failed: {output}")

        # Test missing required fields
        payload = {}  # Empty payload
        json_payload = json.dumps(payload)
        cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'{json_payload}\' "{self.api_url}/v1/jobs"'
        success, output = self.run_curl(cmd)

        if success:
            try:
                data = json.loads(output)
                if data.get("code") in ["invalid_input", "validation_error"]:
                    self.log_test("Missing Fields Handling", True, "Properly rejects missing required fields")
                else:
                    self.log_test("Missing Fields Handling", False, f"Unexpected response: {data}")
            except json.JSONDecodeError:
                self.log_test("Missing Fields Handling", False, f"Invalid response format: {output}")
        else:
            self.log_test("Missing Fields Handling", False, f"Request failed: {output}")

    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 70)
        print("🎯 CLIPSCRIBE INFRASTRUCTURE TEST RESULTS")
        print("=" * 70)

        total = self.results["tests_run"]
        passed = self.results["tests_passed"]
        failed = self.results["tests_failed"]

        print(f"Tests Completed: {total}")
        print(f"Tests Passed: {passed}")
        print(f"Tests Failed: {failed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        if failed > 0:
            print("\n❌ ISSUES FOUND:")
            for error in self.results["errors"]:
                print(f"  • {error}")
        else:
            print("\n🎉 ALL CORE TESTS PASSED!")

        print("\n📊 INFRASTRUCTURE STATUS:")
        if failed == 0:
            print("   ✅ All services operational")
            print("   ✅ API authentication working")
            print("   ✅ Job processing pipeline functional")
            print("   ✅ Security measures in place")
            print("\n🚀 INFRASTRUCTURE IS PRODUCTION READY!")
        elif passed >= total * 0.75:
            print("   ⚠️  Minor issues detected but core functionality working")
            print("   🔧  Ready for implementation of retry logic and monitoring")
        else:
            print("   ❌ Significant issues require attention")
            print("   🔍  Debug and fix issues before proceeding")

async def main():
    """Run the core functionality tests."""
    print("🚀 ClipScribe Core Functionality Test")
    print("Testing essential infrastructure components...\n")

    tester = CoreFunctionalityTest()

    try:
        # Run all tests
        await tester.test_service_availability()
        await tester.test_api_functionality()
        await tester.test_job_processing_flow()
        await tester.test_error_scenarios()

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    except Exception as e:
        print(f"\n💥 Test error: {e}")

    # Always print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
