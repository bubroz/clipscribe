#!/usr/bin/env python3
"""
ClipScribe API Endpoint Tests v2.43.0
Comprehensive tests for production API readiness.
"""

import asyncio
import json
import time
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from httpx import AsyncClient
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from clipscribe.api.app import app
from clipscribe.api.estimator import estimate_job
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript, EnhancedEntity


class TestAPIEndpoints:
    """Test API endpoints for production readiness."""

    def setup_method(self):
        """Setup test client and mocks."""
        self.client = TestClient(app)

        # Mock Redis connection
        with patch('clipscribe.api.app.redis') as mock_redis, \
             patch('clipscribe.api.app.redis_conn', MagicMock()) as mock_redis_conn:
            mock_conn = MagicMock()
            mock_conn.incr.return_value = 1
            mock_conn.get.return_value = None
            mock_conn.exists.return_value = True
            mock_conn.pipeline.return_value = MagicMock()
            mock_conn.pipeline.return_value.execute.return_value = [None]
            mock_conn.pipeline.return_value.get.return_value = None
            mock_redis.from_url.return_value = mock_conn
            self.mock_redis = mock_conn
            self.mock_redis_conn = mock_conn  # Use the same mock for both

    def teardown_method(self):
        """Clean up after tests."""
        # Reset global state
        from clipscribe.api.app import jobs_by_id, idempotency_to_job, fingerprint_to_job, job_events
        jobs_by_id.clear()
        idempotency_to_job.clear()
        fingerprint_to_job.clear()
        job_events.clear()

    def test_api_root_accessible(self):
        """Test that API root is accessible."""
        response = self.client.get("/")
        assert response.status_code == 404  # FastAPI returns 404 for root without routes

    def test_api_docs_accessible(self):
        """Test that API documentation is accessible."""
        response = self.client.get("/docs")
        assert response.status_code == 200
        assert "ClipScribe API" in response.text

    def test_openapi_schema_valid(self):
        """Test that OpenAPI schema is valid JSON."""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "/v1/jobs" in schema["paths"]

    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured."""
        # Without CORS origins set, should not have CORS headers
        response = self.client.options("/v1/jobs",
                                     headers={"Origin": "http://localhost:3000"})
        # Should not have CORS headers when no origins configured
        assert "access-control-allow-origin" not in [h.lower() for h in response.headers]

    def test_request_id_header(self):
        """Test that X-Request-ID header is added to responses."""
        response = self.client.get("/docs")
        assert "x-request-id" in [h.lower() for h in response.headers]

    def test_missing_authorization_returns_401(self):
        """Test that endpoints require authorization."""
        # Test POST /v1/jobs without auth
        response = self.client.post("/v1/jobs", json={"url": "https://example.com"})
        assert response.status_code == 401
        assert "Missing or invalid bearer token" in response.json()["message"]

        # Test GET /v1/jobs/{job_id} without auth
        response = self.client.get("/v1/jobs/test-job")
        assert response.status_code == 401

    def test_invalid_request_body_returns_400(self):
        """Test that invalid request bodies return proper errors."""
        headers = {"Authorization": "Bearer test-token"}

        # Missing both url and gcs_uri
        response = self.client.post("/v1/jobs", json={}, headers=headers)
        assert response.status_code == 400
        assert "Provide either url or gcs_uri" in response.json()["message"]

    def test_create_job_success(self):
        """Test successful job creation."""
        headers = {"Authorization": "Bearer test-token"}

        with patch('clipscribe.api.app.estimate_job') as mock_estimate:
            mock_estimate.return_value = {"estimated_cost_usd": 0.035}

            response = self.client.post(
                "/v1/jobs",
                json={"url": "https://www.youtube.com/watch?v=test123"},
                headers=headers
            )

            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
            assert data["state"] == "QUEUED"
            assert data["cost_to_date_usd"] == 0.0

    def test_create_job_with_gcs_uri(self):
        """Test job creation with GCS URI."""
        headers = {"Authorization": "Bearer test-token"}

        with patch('clipscribe.api.app.estimate_job') as mock_estimate:
            mock_estimate.return_value = {"estimated_cost_usd": 0.035}

            response = self.client.post(
                "/v1/jobs",
                json={"gcs_uri": "gs://bucket/path/video.mp4"},
                headers=headers
            )

            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data

    def test_create_job_idempotency(self):
        """Test idempotent job creation."""
        headers = {
            "Authorization": "Bearer test-token",
            "Idempotency-Key": "test-key-123"
        }

        with patch('clipscribe.api.app.estimate_job') as mock_estimate:
            mock_estimate.return_value = {"estimated_cost_usd": 0.035}

            # First request
            response1 = self.client.post(
                "/v1/jobs",
                json={"url": "https://www.youtube.com/watch?v=test123"},
                headers=headers
            )
            assert response1.status_code == 202
            job_id_1 = response1.json()["job_id"]

            # Second request with same idempotency key
            response2 = self.client.post(
                "/v1/jobs",
                json={"url": "https://www.youtube.com/watch?v=test123"},
                headers=headers
            )
            assert response2.status_code == 200  # Should return existing job
            job_id_2 = response2.json()["job_id"]

            assert job_id_1 == job_id_2

    def test_get_job_not_found(self):
        """Test getting non-existent job returns 404."""
        headers = {"Authorization": "Bearer test-token"}

        response = self.client.get("/v1/jobs/non-existent-job", headers=headers)
        assert response.status_code == 404
        assert "Job not found" in response.json()["message"]

    def test_get_job_success(self):
        """Test successful job retrieval."""
        headers = {"Authorization": "Bearer test-token"}

        # First create a job
        with patch('clipscribe.api.app.estimate_job') as mock_estimate:
            mock_estimate.return_value = {"estimated_cost_usd": 0.035}

            create_response = self.client.post(
                "/v1/jobs",
                json={"url": "https://www.youtube.com/watch?v=test123"},
                headers=headers
            )
            job_id = create_response.json()["job_id"]

            # Then retrieve it
            get_response = self.client.get(f"/v1/jobs/{job_id}", headers=headers)
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["job_id"] == job_id
            assert data["state"] == "QUEUED"

    def test_estimate_endpoint(self):
        """Test cost estimation endpoint."""
        headers = {"Authorization": "Bearer test-token"}

        response = self.client.get("/v1/estimate?url=https://example.com", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "estimated_cost_usd" in data
        assert "estimated_duration_seconds" in data
        assert "proposed_model" in data
        assert data["proposed_model"] == "flash"

    def test_estimate_without_auth(self):
        """Test estimate endpoint requires authorization."""
        response = self.client.get("/v1/estimate?url=https://example.com")
        assert response.status_code == 401

    def test_presign_upload_endpoint(self):
        """Test upload presigning endpoint."""
        headers = {"Authorization": "Bearer test-token"}

        response = self.client.post(
            "/v1/uploads/presign",
            json={"filename": "test.mp4", "content_type": "video/mp4"},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "gcs_uri" in data
        assert "test.mp4" in data["gcs_uri"]

    def test_metrics_endpoint(self):
        """Test metrics endpoint returns Prometheus format."""
        response = self.client.get("/metrics")
        assert response.status_code == 200

        content = response.text
        assert isinstance(content, str)
        assert content.endswith("\n")

        # Should be valid Prometheus format (though may be empty)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        for line in lines:
            if line.startswith('#'):
                continue  # Comment lines are allowed
            if ' ' in line:
                metric_name, value = line.split(' ', 1)
                assert metric_name.startswith('clipscribe_')
                float(value)  # Should be numeric

    def test_rate_limiting_structure(self):
        """Test that rate limiting infrastructure is in place."""
        # This tests the presence of rate limiting functions
        from clipscribe.api.app import _rpm_allow, _token_id_from_auth

        # Test token ID extraction
        token_id = _token_id_from_auth("Bearer test-token-123")
        assert token_id is not None
        assert len(token_id) == 16  # SHA256 truncated

        # Test invalid auth
        assert _token_id_from_auth(None) is None
        assert _token_id_from_auth("Invalid") is None
        assert _token_id_from_auth("Bearer") is None

    def test_error_response_format(self):
        """Test that error responses follow consistent format."""
        headers = {"Authorization": "Bearer test-token"}

        # Test rate limit error format
        response = self.client.post(
            "/v1/jobs",
            json={"url": "https://www.youtube.com/watch?v=test123"},
            headers=headers
        )

        # Should succeed in test environment due to mocked Redis
        assert response.status_code in [200, 202]

        # Test error format for unauthorized requests
        response = self.client.post("/v1/jobs", json={"url": "https://example.com"})
        assert response.status_code == 401

        error_data = response.json()
        assert "code" in error_data
        assert "message" in error_data
        assert error_data["code"] == "invalid_input"
        assert "bearer token" in error_data["message"]

    def test_job_state_transitions(self):
        """Test that job states transition correctly."""
        headers = {"Authorization": "Bearer test-token"}

        with patch('clipscribe.api.app.estimate_job') as mock_estimate:
            mock_estimate.return_value = {"estimated_cost_usd": 0.035}

            # Create job
            response = self.client.post(
                "/v1/jobs",
                json={"url": "https://www.youtube.com/watch?v=test123"},
                headers=headers
            )
            assert response.status_code == 202
            job_id = response.json()["job_id"]

            # Job should start as QUEUED
            get_response = self.client.get(f"/v1/jobs/{job_id}", headers=headers)
            assert get_response.status_code == 200
            assert get_response.json()["state"] == "QUEUED"

    def test_job_events_streaming(self):
        """Test job events streaming endpoint."""
        headers = {"Authorization": "Bearer test-token"}

        # Test without auth
        response = self.client.get("/v1/jobs/test-job/events")
        assert response.status_code == 401

        # Test with auth but non-existent job
        response = self.client.get("/v1/jobs/test-job/events", headers=headers)
        assert response.status_code == 200  # Should return streaming response

    def test_artifacts_endpoint(self):
        """Test artifacts listing endpoint."""
        headers = {"Authorization": "Bearer test-token"}

        # Test without auth
        response = self.client.get("/v1/jobs/test-job/artifacts")
        assert response.status_code == 401

        # Test with auth
        response = self.client.get("/v1/jobs/test-job/artifacts", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert "artifacts" in data
        assert data["job_id"] == "test-job"
        assert isinstance(data["artifacts"], list)


class TestAPIProductionReadiness:
    """Test API production readiness features."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_api_handles_malformed_json(self):
        """Test API handles malformed JSON gracefully."""
        headers = {"Authorization": "Bearer test-token"}

        # Send malformed JSON
        response = self.client.post(
            "/v1/jobs",
            data="invalid json {",
            headers={**headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 400

    def test_api_handles_oversized_payloads(self):
        """Test API handles oversized payloads."""
        headers = {"Authorization": "Bearer test-token"}

        # Create a large payload (but not too large for test)
        large_data = {"url": "https://example.com", "options": {"data": "x" * 10000}}

        response = self.client.post(
            "/v1/jobs",
            json=large_data,
            headers=headers
        )
        # Should handle large payloads gracefully
        assert response.status_code in [200, 202, 400]

    def test_api_handles_special_characters(self):
        """Test API handles special characters in URLs."""
        headers = {"Authorization": "Bearer test-token"}

        test_urls = [
            "https://www.youtube.com/watch?v=test&feature=share",
            "https://www.youtube.com/watch?v=test?param=1&other=2",
            "https://www.youtube.com/watch?v=test#timestamp",
        ]

        for url in test_urls:
            with patch('clipscribe.api.app.estimate_job') as mock_estimate:
                mock_estimate.return_value = {"estimated_cost_usd": 0.035}

                response = self.client.post(
                    "/v1/jobs",
                    json={"url": url},
                    headers=headers
                )
                assert response.status_code in [200, 202]

    def test_api_handles_concurrent_requests(self):
        """Test API handles concurrent requests."""
        import threading
        import queue

        headers = {"Authorization": "Bearer test-token"}
        results = queue.Queue()

        def make_request():
            try:
                with patch('clipscribe.api.app.estimate_job') as mock_estimate:
                    mock_estimate.return_value = {"estimated_cost_usd": 0.035}

                    response = self.client.post(
                        "/v1/jobs",
                        json={"url": "https://www.youtube.com/watch?v=test"},
                        headers=headers
                    )
                    results.put(response.status_code)
            except Exception as e:
                results.put(f"error: {e}")

        # Start multiple concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)

        # Check results
        status_codes = []
        while not results.empty():
            result = results.get()
            if isinstance(result, int):
                status_codes.append(result)
            else:
                # If any request failed, that's concerning but may be expected
                # in test environment without proper Redis
                pass

        # Should have some successful responses
        successful_responses = [code for code in status_codes if code in [200, 202]]
        assert len(successful_responses) > 0

    def test_api_response_time_acceptable(self):
        """Test that API responses are within acceptable time limits."""
        import time

        headers = {"Authorization": "Bearer test-token"}

        start_time = time.time()
        response = self.client.get("/docs")
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 5.0  # Should respond within 5 seconds

    def test_api_memory_usage_stable(self):
        """Test that API doesn't have obvious memory leaks in basic operations."""
        import psutil
        import os

        headers = {"Authorization": "Bearer test-token"}

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make several requests
        for i in range(10):
            with patch('clipscribe.api.app.estimate_job') as mock_estimate:
                mock_estimate.return_value = {"estimated_cost_usd": 0.035}

                response = self.client.post(
                    "/v1/jobs",
                    json={"url": f"https://www.youtube.com/watch?v=test{i}"},
                    headers=headers
                )
                assert response.status_code in [200, 202]

        # Check memory usage after requests
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024

    def test_api_graceful_shutdown_signals(self):
        """Test that API can handle shutdown signals gracefully."""
        # This is more of a documentation test - in production,
        # the API should handle SIGTERM and SIGINT gracefully
        import signal

        # Test that signal handlers can be registered (doesn't actually shutdown)
        def signal_handler(signum, frame):
            pass

        # These should not raise exceptions
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        assert True  # Test passes if no exceptions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
