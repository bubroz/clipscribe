#!/usr/bin/env python3
"""
Comprehensive Infrastructure Test Suite for ClipScribe

This script tests the entire ClipScribe infrastructure including:
- API service health and connectivity
- Worker service communication
- Job submission and processing flow
- Error handling and edge cases
- Performance and scaling
"""

import asyncio
import json
import time
import hashlib
import subprocess
import sys
from typing import Dict, Any, Optional
from datetime import datetime

class ClipScribeInfrastructureTest:
    """Comprehensive test suite for ClipScribe infrastructure."""

    def __init__(self):
        self.api_url = "https://clipscribe-api-16459511304.us-central1.run.app"
        self.web_url = "https://clipscribe-web-16459511304.us-central1.run.app"
        self.worker_url = "https://clipscribe-worker-16459511304.us-central1.run.app"

        # Test token for authentication
        self.test_token = "test-token-12345"
        self.token_id = hashlib.sha256(self.test_token.encode("utf-8")).hexdigest()[:16]
        self.headers = {"Authorization": f"Bearer {self.test_token}"}

        # Test results
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }

    def run_curl(self, cmd: str, silent: bool = True) -> tuple[bool, str]:
        """Run a curl command and return success status and output."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout if silent else result.stdout + result.stderr
            return result.returncode == 0, output
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

    async def test_api_service_accessibility(self):
        """Test 1: API Service Accessibility"""
        try:
            cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{self.api_url}/docs"'
            success, output = self.run_curl(cmd)

            if success and output.strip() == "200":
                # Check if swagger is in the response
                cmd_content = f'curl -s "{self.api_url}/docs"'
                success_content, content = self.run_curl(cmd_content)
                if success_content and "swagger" in content.lower():
                    self.log_test("API Service Accessibility", True, "API docs accessible")
                    return True
                else:
                    self.log_test("API Service Accessibility", False, "Swagger UI not found in response")
                    return False
            else:
                self.log_test("API Service Accessibility", False, f"HTTP {output.strip()}")
                return False
        except Exception as e:
            self.log_test("API Service Accessibility", False, str(e))
            return False

    async def test_web_service_accessibility(self):
        """Test 2: Web Service Accessibility"""
        try:
            cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{self.web_url}"'
            success, output = self.run_curl(cmd)

            if success and output.strip() == "200":
                # Check if clipscribe is in the response
                cmd_content = f'curl -s "{self.web_url}"'
                success_content, content = self.run_curl(cmd_content)
                if success_content and "clipscribe" in content.lower():
                    self.log_test("Web Service Accessibility", True, "Web interface accessible")
                    return True
                else:
                    self.log_test("Web Service Accessibility", False, "ClipScribe content not found")
                    return False
            else:
                self.log_test("Web Service Accessibility", False, f"HTTP {output.strip()}")
                return False
        except Exception as e:
            self.log_test("Web Service Accessibility", False, str(e))
            return False

    async def test_api_authentication(self):
        """Test 3: API Authentication"""
        try:
            # Test without authentication
            cmd = f'curl -s -o /dev/null -w "%{{http_code}}" "{self.api_url}/v1/status"'
            success, output = self.run_curl(cmd)

            if success and output.strip() == "401":
                self.log_test("API Authentication (no auth)", True, "Properly rejects unauthenticated requests")
            else:
                self.log_test("API Authentication (no auth)", False, f"Unexpected response: {output.strip()}")
                return False

            # Test with authentication
            cmd_auth = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/status"'
            success_auth, output_auth = self.run_curl(cmd_auth)

            if success_auth:
                try:
                    data = json.loads(output_auth)
                    if data.get("status") == "healthy":
                        self.log_test("API Authentication (with auth)", True, "Authentication successful")
                        return True
                    else:
                        self.log_test("API Authentication (with auth)", False, f"Unexpected response data: {data}")
                        return False
                except json.JSONDecodeError:
                    self.log_test("API Authentication (with auth)", False, f"Invalid JSON response: {output_auth}")
                    return False
            else:
                self.log_test("API Authentication (with auth)", False, "Authentication request failed")
                return False
        except Exception as e:
            self.log_test("API Authentication", False, str(e))
            return False

    async def test_job_submission(self):
        """Test 4: Job Submission"""
        try:
            # Test data
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley video (short test)

            payload = {
                "url": test_url,
                "options": {
                    "extract_entities": True,
                    "extract_relationships": True,
                    "max_duration": 60  # Limit to 60 seconds for testing
                }
            }

            # Create JSON payload
            json_payload = json.dumps(payload)

            cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'{json_payload}\' "{self.api_url}/v1/jobs"'
            success, output = self.run_curl(cmd)

            if success:
                try:
                    data = json.loads(output)
                    if "job_id" in data:
                        job_id = data["job_id"]
                        self.log_test("Job Submission", True, f"Job submitted successfully: {job_id}")
                        return job_id
                    else:
                        self.log_test("Job Submission", False, f"Missing job_id in response: {data}")
                        return None
                except json.JSONDecodeError:
                    self.log_test("Job Submission", False, f"Invalid JSON response: {output}")
                    return None
            else:
                self.log_test("Job Submission", False, f"Request failed: {output}")
                return None
        except Exception as e:
            self.log_test("Job Submission", False, str(e))
            return None

    async def test_job_monitoring(self, job_id: str):
        """Test 5: Job Monitoring"""
        try:
            max_attempts = 30  # Wait up to 5 minutes
            for attempt in range(max_attempts):
                cmd = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/jobs/{job_id}"'
                success, output = self.run_curl(cmd)

                if success:
                    try:
                        data = json.loads(output)
                        state = data.get("state")

                        if state == "COMPLETED":
                            self.log_test("Job Monitoring", True, f"Job completed successfully in {attempt * 10} seconds")
                            return True
                        elif state == "FAILED":
                            self.log_test("Job Monitoring", False, f"Job failed: {data.get('error', 'Unknown error')}")
                            return False
                        elif state in ["PROCESSING", "QUEUED"]:
                            print(f"   Job status: {state} (attempt {attempt + 1}/{max_attempts})")
                            await asyncio.sleep(10)  # Wait 10 seconds
                            continue
                        else:
                            print(f"   Job status: {state}")
                            await asyncio.sleep(10)
                            continue
                    except json.JSONDecodeError:
                        self.log_test("Job Monitoring", False, f"Invalid JSON response: {output}")
                        return False
                else:
                    self.log_test("Job Monitoring", False, f"Failed to get job status: {output}")
                    return False

            self.log_test("Job Monitoring", False, f"Job monitoring timed out after {max_attempts * 10} seconds")
            return False

        except Exception as e:
            self.log_test("Job Monitoring", False, str(e))
            return False

    async def test_error_handling(self):
        """Test 6: Error Handling"""
        try:
            # Test malformed JSON - should get proper error
            cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'invalid json\' "{self.api_url}/v1/jobs"'
            success, output = self.run_curl(cmd)

            if success:
                try:
                    data = json.loads(output)
                    if data.get("code") in ["invalid_input", "validation_error"]:
                        self.log_test("Malformed JSON Handling", True, "Properly rejects malformed JSON")
                    else:
                        self.log_test("Malformed JSON Handling", False, f"Unexpected response: {data}")
                except json.JSONDecodeError:
                    self.log_test("Malformed JSON Handling", False, f"Invalid response format: {output}")
            else:
                self.log_test("Malformed JSON Handling", False, f"Request failed: {output}")

            # Test missing authorization header
            cmd = f'curl -s -X POST -H "Content-Type: application/json" -d \'{{"url": "https://example.com"}}\' "{self.api_url}/v1/jobs"'
            success, output = self.run_curl(cmd)

            if success:
                try:
                    data = json.loads(output)
                    if data.get("code") in ["unauthorized", "invalid_input"] or "token" in str(data).lower():
                        self.log_test("Authorization Handling", True, "Properly rejects missing auth")
                    else:
                        self.log_test("Authorization Handling", False, f"Unexpected response: {data}")
                except json.JSONDecodeError:
                    self.log_test("Authorization Handling", False, f"Invalid response format: {output}")
            else:
                self.log_test("Authorization Handling", False, f"Request failed: {output}")

            # Test invalid job ID
            cmd = f'curl -s -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/jobs/invalid-job-id"'
            success, output = self.run_curl(cmd)

            if success:
                try:
                    data = json.loads(output)
                    if data.get("code") in ["not_found", "invalid_input"]:
                        self.log_test("Invalid Job ID Handling", True, "Properly handles invalid job IDs")
                    else:
                        self.log_test("Invalid Job ID Handling", False, f"Unexpected response: {data}")
                except json.JSONDecodeError:
                    self.log_test("Invalid Job ID Handling", False, f"Invalid response format: {output}")
            else:
                self.log_test("Invalid Job ID Handling", False, f"Request failed: {output}")

            return True

        except Exception as e:
            self.log_test("Error Handling", False, str(e))
            return False

    async def test_rate_limiting(self):
        """Test 7: Rate Limiting"""
        try:
            # Submit multiple jobs quickly to test rate limiting
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            jobs_submitted = 0

            for i in range(3):  # Try to submit 3 jobs quickly (not too aggressive)
                payload = {"url": test_url}
                json_payload = json.dumps(payload)
                cmd = f'curl -s -X POST -H "Content-Type: application/json" -H "Authorization: Bearer {self.test_token}" -d \'{json_payload}\' "{self.api_url}/v1/jobs"'
                success, output = self.run_curl(cmd)

                if success:
                    try:
                        data = json.loads(output)
                        if data.get("job_id"):
                            jobs_submitted += 1
                            print(f"   Request {i + 1}: Job created successfully")
                        else:
                            print(f"   Request {i + 1}: Unexpected response")
                    except json.JSONDecodeError:
                        print(f"   Request {i + 1}: Invalid JSON response")
                else:
                    print(f"   Request {i + 1}: Request failed")

                # Small delay to avoid overwhelming
                await asyncio.sleep(0.5)

            if jobs_submitted > 0:
                self.log_test("Rate Limiting", True, f"Successfully submitted {jobs_submitted} jobs (no rate limiting detected)")
            else:
                self.log_test("Rate Limiting", False, "All requests failed")

            return True

        except Exception as e:
            self.log_test("Rate Limiting", False, str(e))
            return False

    async def test_admin_endpoints(self):
        """Test 8: Admin Endpoints"""
        try:
            # Test pause endpoint
            cmd = f'curl -s -X POST -H "Authorization: Bearer {self.test_token}" "{self.api_url}/v1/admin/pause"'
            success, output = self.run_curl(cmd)

            if success:
                try:
                    data = json.loads(output)
                    if data.get("code") in ["unauthorized", "forbidden"]:
                        self.log_test("Admin Endpoints", True, "Admin endpoints properly secured")
                    else:
                        self.log_test("Admin Endpoints", False, f"Admin endpoints not secured: {data}")
                except json.JSONDecodeError:
                    self.log_test("Admin Endpoints", False, f"Invalid response format: {output}")
            else:
                self.log_test("Admin Endpoints", False, f"Request failed: {output}")

            return True

        except Exception as e:
            self.log_test("Admin Endpoints", False, str(e))
            return False

    async def run_comprehensive_test(self):
        """Run the complete test suite."""
        print("🚀 Starting ClipScribe Infrastructure Test Suite")
        print("=" * 60)

        # Test 1: Service Accessibility
        await self.test_api_service_accessibility()
        await self.test_web_service_accessibility()

        # Test 2: Authentication
        auth_success = await self.test_api_authentication()
        if not auth_success:
            print("⚠️  Authentication failed, skipping remaining tests")
            return

        # Test 3: Error Handling
        await self.test_error_handling()

        # Test 4: Rate Limiting
        await self.test_rate_limiting()

        # Test 5: Admin Endpoints
        await self.test_admin_endpoints()

        # Test 6: Job Submission (the main functionality)
        print("\n📋 Testing Job Submission and Processing Flow")
        print("-" * 40)

        job_id = await self.test_job_submission()
        if job_id:
            await self.test_job_monitoring(job_id)

        # Print results
        self.print_results()

    def print_results(self):
        """Print comprehensive test results."""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        total = self.results["tests_run"]
        passed = self.results["tests_passed"]
        failed = self.results["tests_failed"]

        print(f"Tests Run: {total}")
        print(f"Tests Passed: {passed}")
        print(f"Tests Failed: {failed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for error in self.results["errors"]:
                print(f"  • {error}")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Infrastructure is healthy.")
        elif passed >= total * 0.8:
            print(f"\n⚠️  MOST TESTS PASSED ({passed}/{total}). Minor issues detected.")
        else:
            print(f"\n❌ SIGNIFICANT ISSUES DETECTED ({failed}/{total} tests failed).")


async def main():
    """Main test execution."""
    tester = ClipScribeInfrastructureTest()

    try:
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        tester.print_results()
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        tester.print_results()


if __name__ == "__main__":
    asyncio.run(main())
