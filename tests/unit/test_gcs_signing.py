"""Unit tests for GCS v4 signed URL generation using IAM SignBlob API."""

import base64
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock google.cloud.iam before importing the module
try:
    from clipscribe.utils import gcs_signing
except ImportError:
    pytest.skip("google-cloud-iam not installed", allow_module_level=True)


class TestGetServiceAccountEmail:
    """Tests for get_service_account_email function."""

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.default")
    def test_get_service_account_email_from_credentials(self, mock_default, mock_google):
        """Test extracting service account email from service account credentials."""
        mock_google.auth = Mock()
        mock_creds = Mock()
        mock_creds.service_account_email = "test@project.iam.gserviceaccount.com"
        mock_default.return_value = (mock_creds, "project-id")

        email = gcs_signing.get_service_account_email()
        assert email == "test@project.iam.gserviceaccount.com"

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.default")
    @patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_EMAIL": "env@project.iam.gserviceaccount.com"})
    def test_get_service_account_email_from_env(self, mock_default, mock_google):
        """Test getting service account email from environment variable."""
        # Clear cache first
        gcs_signing._service_account_email_cache = None
        mock_google.auth = Mock()
        mock_creds = Mock(spec=[])  # Empty spec so no attributes
        # Ensure no service_account_email or _service_account_email attributes
        if hasattr(mock_creds, "service_account_email"):
            delattr(mock_creds, "service_account_email")
        if hasattr(mock_creds, "_service_account_email"):
            delattr(mock_creds, "_service_account_email")
        mock_default.return_value = (mock_creds, "project-id")

        email = gcs_signing.get_service_account_email()
        assert email == "env@project.iam.gserviceaccount.com"

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.default")
    def test_get_service_account_email_cached(self, mock_default, mock_google):
        """Test that service account email is cached."""
        mock_google.auth = Mock()
        mock_creds = Mock()
        mock_creds.service_account_email = "test@project.iam.gserviceaccount.com"
        mock_default.return_value = (mock_creds, "project-id")

        # Clear cache first
        gcs_signing._service_account_email_cache = None

        # First call
        email1 = gcs_signing.get_service_account_email()
        # Second call should use cache
        email2 = gcs_signing.get_service_account_email()

        assert email1 == email2
        # Should only call default() once
        assert mock_default.call_count == 1

    @patch("builtins.__import__")
    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.default")
    def test_get_service_account_email_failure(self, mock_default, mock_google, mock_import):
        """Test error when service account email cannot be determined."""
        # Clear cache first
        gcs_signing._service_account_email_cache = None
        mock_google.auth = Mock()
        mock_creds = Mock(spec=[])  # Empty spec so no attributes
        # Ensure no service_account_email or _service_account_email attributes
        if hasattr(mock_creds, "service_account_email"):
            delattr(mock_creds, "service_account_email")
        if hasattr(mock_creds, "_service_account_email"):
            delattr(mock_creds, "_service_account_email")
        mock_default.return_value = (mock_creds, "project-id")

        # Mock httpx import to fail (simulate not installed or network issue)
        def import_side_effect(name, *args, **kwargs):
            if name == "httpx":
                raise ImportError("httpx not available")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect

        with patch.dict(os.environ, {}, clear=True):
            # Also need to mock urllib to fail
            with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
                with pytest.raises(RuntimeError, match="Could not determine service account email"):
                    gcs_signing.get_service_account_email()


class TestConstructCanonicalRequest:
    """Tests for _construct_canonical_request helper function."""

    def test_construct_canonical_request_basic(self):
        """Test canonical request construction for basic PUT request."""
        method = "PUT"
        resource = "/bucket/object"
        query_params = {"X-Goog-Algorithm": "GOOG4-RSA-SHA256", "X-Goog-Date": "20231127T120000Z"}
        headers = {"Content-Type": "audio/mpeg"}
        payload_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        canonical = gcs_signing._construct_canonical_request(
            method, resource, query_params, headers, payload_hash
        )

        # Should contain method, resource, query string, headers, signed headers, payload hash
        assert method in canonical
        assert resource in canonical
        assert "X-Goog-Algorithm" in canonical
        # Headers are lowercased in canonical request
        assert "content-type" in canonical.lower()
        assert payload_hash in canonical

    def test_construct_canonical_request_no_headers(self):
        """Test canonical request with no headers."""
        method = "GET"
        resource = "/bucket/object"
        query_params = {}
        headers = {}
        payload_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        canonical = gcs_signing._construct_canonical_request(
            method, resource, query_params, headers, payload_hash
        )

        # Should still be valid (empty headers section)
        assert canonical.count("\n") == 5  # 6 lines total
        assert method in canonical
        assert resource in canonical


class TestGetCredentialScope:
    """Tests for _get_credential_scope helper function."""

    def test_get_credential_scope_default_region(self):
        """Test credential scope with default region."""
        date = datetime(2023, 11, 27, 12, 0, 0, tzinfo=timezone.utc)

        with patch.dict(os.environ, {}, clear=True):
            scope = gcs_signing._get_credential_scope(date)

        assert "20231127" in scope
        assert "us-central1" in scope
        assert "storage" in scope
        assert "goog4_request" in scope

    def test_get_credential_scope_custom_region(self):
        """Test credential scope with custom region from env."""
        date = datetime(2023, 11, 27, 12, 0, 0, tzinfo=timezone.utc)

        with patch.dict(os.environ, {"GCS_SIGNED_URL_REGION": "europe-west1"}):
            scope = gcs_signing._get_credential_scope(date)

        assert "europe-west1" in scope


class TestSignBlobWithIam:
    """Tests for _sign_blob_with_iam helper function."""

    @patch("clipscribe.utils.gcs_signing.iam_credentials_v1")
    @patch("clipscribe.utils.gcs_signing.default")
    def test_sign_blob_with_iam_success(self, mock_default, mock_iam):
        """Test successful IAM SignBlob API call."""
        mock_creds = Mock()
        mock_default.return_value = (mock_creds, "test-project")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.signed_blob = base64.b64encode(b"signature_bytes").decode("utf-8")
        mock_client.sign_blob.return_value = mock_response
        mock_iam.IAMCredentialsClient.return_value = mock_client

        signature = gcs_signing._sign_blob_with_iam(
            "test@project.iam.gserviceaccount.com", b"data to sign"
        )

        assert signature == b"signature_bytes"
        mock_client.sign_blob.assert_called_once()
        # Verify credentials were passed to client
        mock_iam.IAMCredentialsClient.assert_called_once_with(credentials=mock_creds)

    @patch("clipscribe.utils.gcs_signing.iam_credentials_v1")
    @patch("clipscribe.utils.gcs_signing.default")
    def test_sign_blob_with_iam_failure(self, mock_default, mock_iam):
        """Test IAM SignBlob API failure."""
        mock_creds = Mock()
        mock_default.return_value = (mock_creds, "test-project")
        mock_client = MagicMock()
        mock_client.sign_blob.side_effect = Exception("Permission denied")
        mock_iam.IAMCredentialsClient.return_value = mock_client

        with pytest.raises(RuntimeError, match="IAM SignBlob API call failed"):
            gcs_signing._sign_blob_with_iam("test@project.iam.gserviceaccount.com", b"data")


class TestEncodeSignature:
    """Tests for _encode_signature helper function."""

    def test_encode_signature_basic(self):
        """Test URL-safe base64 encoding of signature."""
        signature = b"test_signature_bytes"
        encoded = gcs_signing._encode_signature(signature)

        # Should be URL-safe base64 (no padding)
        assert "=" not in encoded
        assert "+" not in encoded or "/" not in encoded  # URL-safe uses - and _

    def test_encode_signature_empty(self):
        """Test encoding empty signature."""
        encoded = gcs_signing._encode_signature(b"")
        assert isinstance(encoded, str)


class TestGenerateV4SignedUrlWithIam:
    """Tests for generate_v4_signed_url_with_iam main function."""

    @patch("clipscribe.utils.gcs_signing._generate_signed_url_with_storage_iam")
    def test_generate_v4_signed_url_uses_storage_iam_first(self, mock_storage_iam):
        """Test that storage IAM approach is tried first."""
        mock_storage_iam.return_value = (
            "https://storage.googleapis.com/test-bucket/uploads/file.mp3?signature=test"
        )

        url = gcs_signing.generate_v4_signed_url_with_iam(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="PUT",
            content_type="audio/mpeg",
            expiration_seconds=900,
        )

        # Should use storage IAM approach
        mock_storage_iam.assert_called_once_with(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="PUT",
            content_type="audio/mpeg",
            expiration_seconds=900,
        )
        assert url == "https://storage.googleapis.com/test-bucket/uploads/file.mp3?signature=test"

    @patch("clipscribe.utils.gcs_signing._generate_signed_url_with_storage_iam")
    @patch("clipscribe.utils.gcs_signing._generate_signed_url_manual_iam")
    def test_generate_v4_signed_url_falls_back_to_manual(self, mock_manual_iam, mock_storage_iam):
        """Test that manual IAM approach is used as fallback."""
        mock_storage_iam.side_effect = RuntimeError("Storage IAM failed")
        mock_manual_iam.return_value = (
            "https://storage.googleapis.com/test-bucket/uploads/file.mp3?X-Goog-Signature=test"
        )

        url = gcs_signing.generate_v4_signed_url_with_iam(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="PUT",
            content_type="audio/mpeg",
            expiration_seconds=900,
        )

        # Should fall back to manual IAM
        mock_storage_iam.assert_called_once()
        mock_manual_iam.assert_called_once_with(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="PUT",
            content_type="audio/mpeg",
            expiration_seconds=900,
        )
        assert "test-bucket" in url
        assert "uploads/file.mp3" in url

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.get_service_account_email")
    @patch("clipscribe.utils.gcs_signing._sign_blob_with_iam")
    def test_generate_v4_signed_url_manual_iam_basic(self, mock_sign, mock_get_email, mock_google):
        """Test manual IAM approach generating a basic signed URL."""
        mock_google.auth = Mock()
        mock_get_email.return_value = "test@project.iam.gserviceaccount.com"
        mock_sign.return_value = b"fake_signature_bytes"

        url = gcs_signing._generate_signed_url_manual_iam(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="PUT",
            content_type="audio/mpeg",
            expiration_seconds=900,
        )

        # Should contain bucket and object path
        assert "test-bucket" in url
        assert "uploads/file.mp3" in url
        # Should contain GCS v4 query parameters
        assert "X-Goog-Algorithm" in url
        assert "X-Goog-Credential" in url
        assert "X-Goog-Date" in url
        assert "X-Goog-Expires" in url
        assert "X-Goog-Signature" in url
        # Should be a valid HTTPS URL
        assert url.startswith("https://storage.googleapis.com/")

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.storage")
    @patch("clipscribe.utils.gcs_signing.default")
    @patch("clipscribe.utils.gcs_signing.auth_requests")
    @patch("clipscribe.utils.gcs_signing.get_service_account_email")
    def test_generate_signed_url_with_storage_iam(
        self, mock_get_email, mock_auth_requests, mock_default, mock_storage, mock_google
    ):
        """Test storage IAM approach generating a signed URL."""
        # Setup mocks
        mock_google.auth = Mock()
        mock_get_email.return_value = "test@project.iam.gserviceaccount.com"
        mock_creds = Mock()
        mock_creds.token = "test_access_token"
        mock_default.return_value = (mock_creds, "test-project")
        mock_request = Mock()
        mock_auth_requests.Request.return_value = mock_request

        # Mock storage client
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.generate_signed_url.return_value = (
            "https://storage.googleapis.com/test-bucket/uploads/file.mp3?signature=test"
        )
        mock_bucket.blob.return_value = mock_blob
        mock_client.bucket.return_value = mock_bucket
        mock_storage.Client.return_value = mock_client

        url = gcs_signing._generate_signed_url_with_storage_iam(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="PUT",
            content_type="audio/mpeg",
            expiration_seconds=900,
        )

        # Verify storage client was used
        mock_storage.Client.assert_called_once_with(credentials=mock_creds, project="test-project")
        mock_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.blob.assert_called_once_with("uploads/file.mp3")
        mock_blob.generate_signed_url.assert_called_once()
        call_kwargs = mock_blob.generate_signed_url.call_args[1]
        assert call_kwargs["version"] == "v4"
        assert call_kwargs["method"] == "PUT"
        assert call_kwargs["content_type"] == "audio/mpeg"
        assert call_kwargs["service_account_email"] == "test@project.iam.gserviceaccount.com"
        assert call_kwargs["access_token"] == "test_access_token"
        assert "test-bucket" in url
        assert "uploads/file.mp3" in url

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.get_service_account_email")
    @patch("clipscribe.utils.gcs_signing._sign_blob_with_iam")
    def test_generate_v4_signed_url_manual_no_content_type(
        self, mock_sign, mock_get_email, mock_google
    ):
        """Test manual IAM generating signed URL without content type."""
        mock_google.auth = Mock()
        mock_get_email.return_value = "test@project.iam.gserviceaccount.com"
        mock_sign.return_value = b"fake_signature_bytes"

        url = gcs_signing._generate_signed_url_manual_iam(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="PUT",
            content_type=None,
            expiration_seconds=900,
        )

        assert "test-bucket" in url
        assert "X-Goog-Signature" in url

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.get_service_account_email")
    @patch("clipscribe.utils.gcs_signing._sign_blob_with_iam")
    def test_generate_v4_signed_url_manual_different_method(
        self, mock_sign, mock_get_email, mock_google
    ):
        """Test manual IAM generating signed URL with GET method."""
        mock_google.auth = Mock()
        mock_get_email.return_value = "test@project.iam.gserviceaccount.com"
        mock_sign.return_value = b"fake_signature_bytes"

        url = gcs_signing._generate_signed_url_manual_iam(
            bucket_name="test-bucket",
            object_path="uploads/file.mp3",
            method="GET",
            content_type=None,
            expiration_seconds=3600,
        )

        assert "test-bucket" in url
        assert "X-Goog-Expires=3600" in url

    @patch("clipscribe.utils.gcs_signing.google")
    @patch("clipscribe.utils.gcs_signing.get_service_account_email")
    @patch("clipscribe.utils.gcs_signing._sign_blob_with_iam")
    def test_generate_v4_signed_url_manual_normalizes_path(
        self, mock_sign, mock_get_email, mock_google
    ):
        """Test that manual IAM normalizes object path (leading slash removed)."""
        mock_google.auth = Mock()
        mock_get_email.return_value = "test@project.iam.gserviceaccount.com"
        mock_sign.return_value = b"fake_signature_bytes"

        url = gcs_signing._generate_signed_url_manual_iam(
            bucket_name="test-bucket",
            object_path="/uploads/file.mp3",  # Leading slash
            method="PUT",
            content_type="audio/mpeg",
        )

        # Should not have double slashes
        assert "//uploads" not in url
        assert "/uploads/file.mp3" in url
