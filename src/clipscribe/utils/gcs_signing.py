"""GCS v4 Signed URL generation using IAM SignBlob API.

This module provides functionality to generate Google Cloud Storage v4 signed URLs
without requiring service account private keys. It uses Google Cloud Storage's built-in
IAM signing support, which automatically triggers server-side signing via IAM API when
service_account_email and access_token are provided.

This is necessary because Cloud Run's default service account uses Compute Engine
credentials (token-based) that don't include a private key, making traditional
blob.generate_signed_url() calls fail.

The primary approach uses google-cloud-storage's built-in IAM signing, with a manual
IAM SignBlob implementation as a fallback.
"""

import base64
import hashlib
import logging
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import google.auth
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    from google.auth.transport import requests as auth_requests
    from google.cloud import iam_credentials_v1, storage
except ImportError:
    google = None  # type: ignore
    default = None  # type: ignore
    DefaultCredentialsError = Exception  # type: ignore
    auth_requests = None  # type: ignore
    iam_credentials_v1 = None  # type: ignore
    storage = None  # type: ignore

logger = logging.getLogger(__name__)

# Cache for service account email (doesn't change during runtime)
_service_account_email_cache: Optional[str] = None


def get_service_account_email() -> str:
    """Get the service account email from default credentials.

    Works with both service account credentials and Compute Engine credentials.
    For Compute Engine credentials, extracts the service account email from the
    credentials object.

    Returns:
        Service account email address.

    Raises:
        RuntimeError: If credentials cannot be obtained or service account email
            cannot be determined.
    """
    global _service_account_email_cache

    # Return cached value if available
    if _service_account_email_cache:
        return _service_account_email_cache

    # PRIORITY: Check environment variable FIRST (most reliable for Cloud Run)
    # This avoids issues where credentials return "default" instead of actual email
    env_email = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")
    if env_email:
        logger.debug(f"Using service account from GOOGLE_SERVICE_ACCOUNT_EMAIL: {env_email}")
        _service_account_email_cache = env_email
        return env_email

    if google is None:
        raise RuntimeError(
            "google-cloud-iam is not installed. Install with: poetry install -E enterprise"
        )

    try:
        # Request credentials with cloud-platform scope for IAM API access
        credentials, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    except DefaultCredentialsError as e:
        raise RuntimeError(
            f"Failed to get default credentials: {e}. "
            "Ensure GOOGLE_APPLICATION_CREDENTIALS is set or running on GCP."
        ) from e

    # Try to get service account email from credentials
    service_account_email: Optional[str] = None

    # For service account credentials (has service_account_email attribute)
    # Skip if it's "default" (common on Cloud Run when not properly configured)
    if hasattr(credentials, "service_account_email") and credentials.service_account_email:
        if credentials.service_account_email != "default":
            service_account_email = credentials.service_account_email
    # For Compute Engine credentials (Cloud Run default)
    # Try to get from internal attribute (varies by credential type)
    if (
        not service_account_email
        and hasattr(credentials, "_service_account_email")
        and credentials._service_account_email
    ):
        if credentials._service_account_email != "default":
            service_account_email = credentials._service_account_email

    # Last resort: try to query metadata server for Compute Engine (Cloud Run)
    if not service_account_email:
        try:
            # Use httpx (already in dependencies) or fallback to urllib
            try:
                import httpx

                # Query metadata server for service account email
                metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
                response = httpx.get(
                    metadata_url, headers={"Metadata-Flavor": "Google"}, timeout=2.0
                )
                if response.status_code == 200:
                    service_account_email = response.text.strip()
            except ImportError:
                # Fallback to urllib if httpx not available
                from urllib.request import Request, urlopen

                metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
                req = Request(metadata_url, headers={"Metadata-Flavor": "Google"})
                with urlopen(req, timeout=2) as response:
                    service_account_email = response.read().decode("utf-8").strip()
        except Exception:
            # Metadata server query failed (not on GCP or network issue)
            # Continue to error with helpful message
            pass

    if not service_account_email:
        raise RuntimeError(
            "Could not determine service account email from credentials. "
            "Set GOOGLE_SERVICE_ACCOUNT_EMAIL environment variable, or ensure "
            "credentials include service account email. On Cloud Run, the service "
            "account email is typically PROJECT_NUMBER-compute@developer.gserviceaccount.com"
        )

    # Cache the result
    _service_account_email_cache = service_account_email
    logger.debug(f"Service account email: {service_account_email}")

    return service_account_email


def _construct_canonical_request(
    method: str,
    resource: str,
    query_params: dict[str, str],
    headers: dict[str, str],
    payload_hash: str,
) -> str:
    """Construct the canonical request string for GCS v4 signed URLs.

    Args:
        method: HTTP method (e.g., "PUT", "GET").
        resource: Resource path (e.g., "/bucket/object").
        query_params: Query parameters (excluding signature-related params).
        headers: Headers to include in signature.
        payload_hash: SHA256 hash of payload (empty string hash for PUT).

    Returns:
        Canonical request string.
    """
    # Sort query parameters
    sorted_params = sorted(query_params.items())
    query_string = "&".join(f"{k}={v}" for k, v in sorted_params)

    # Sort and format headers
    sorted_headers = sorted(headers.items())
    canonical_headers = "\n".join(f"{k.lower()}:{v}" for k, v in sorted_headers)
    signed_headers = ";".join(k.lower() for k, _ in sorted_headers)

    # Construct canonical request
    canonical_request = (
        f"{method}\n"
        f"{resource}\n"
        f"{query_string}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    return canonical_request


def _get_credential_scope(date: datetime) -> str:
    """Get the credential scope string for GCS v4 signed URLs.

    Args:
        date: Date/time for the signature.

    Returns:
        Credential scope string (e.g., "20231127/us-central1/storage/goog4_request").
    """
    date_str = date.strftime("%Y%m%d")
    # GCS uses "auto" region for signed URLs, but we'll use "us-central1" as default
    # This can be overridden via environment variable if needed
    region = os.getenv("GCS_SIGNED_URL_REGION", "us-central1")
    return f"{date_str}/{region}/storage/goog4_request"


def _sign_blob_with_iam(service_account_email: str, blob_to_sign: bytes) -> bytes:
    """Sign a blob using the IAM Credentials API SignBlob method.

    Args:
        service_account_email: Service account email to sign with.
        blob_to_sign: Bytes to sign.

    Returns:
        Signed blob (signature bytes).

    Raises:
        RuntimeError: If IAM API call fails.
    """
    if iam_credentials_v1 is None:
        raise RuntimeError(
            "google-cloud-iam is not installed. Install with: poetry install -E enterprise"
        )

    try:
        # Get credentials with explicit scopes for IAM API
        credentials, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

        # Create IAM client with explicit credentials
        # This ensures the client uses the right credentials with proper scopes
        client = iam_credentials_v1.IAMCredentialsClient(credentials=credentials)

        # Format: projects/-/serviceAccounts/{email}
        # Using '-' for project_id tells IAM to infer it from the service account email
        name = f"projects/-/serviceAccounts/{service_account_email}"

        request = iam_credentials_v1.SignBlobRequest(
            name=name,
            payload=blob_to_sign,
        )

        response = client.sign_blob(request=request)
        # Response contains signed_blob which is base64-encoded
        signature = base64.b64decode(response.signed_blob)

        logger.debug(f"Successfully signed blob using IAM API for {service_account_email}")
        return signature
    except Exception as e:
        logger.error(
            f"Failed to sign blob with IAM API for {service_account_email}: {e}",
            exc_info=True,
        )
        raise RuntimeError(
            f"IAM SignBlob API call failed: {e}. "
            "Ensure the service account has roles/iam.serviceAccountTokenCreator "
            "permission on itself, and that the calling credentials have "
            "roles/iam.serviceAccountTokenCreator permission."
        ) from e


def _encode_signature(signature: bytes) -> str:
    """Encode signature as URL-safe base64.

    Args:
        signature: Signature bytes.

    Returns:
        URL-safe base64-encoded signature string.
    """
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


def generate_v4_signed_url_with_iam(
    bucket_name: str,
    object_path: str,
    method: str = "PUT",
    content_type: Optional[str] = None,
    expiration_seconds: int = 900,
) -> str:
    """Generate a GCS v4 signed URL using IAM SignBlob API.

    This function uses Google Cloud Storage's built-in IAM signing support, which
    automatically triggers server-side signing via IAM API when service_account_email
    and access_token are provided. This is the recommended approach for Cloud Run.

    Falls back to manual IAM SignBlob implementation if storage library approach fails.

    Args:
        bucket_name: GCS bucket name.
        object_path: Object path within bucket (e.g., "uploads/file.mp3").
        method: HTTP method (default: "PUT").
        content_type: Content type header (optional).
        expiration_seconds: URL expiration time in seconds (default: 900 = 15 minutes).

    Returns:
        Signed URL string.

    Raises:
        RuntimeError: If signing fails or credentials cannot be obtained.
    """
    # Try the recommended approach first: google-cloud-storage's built-in IAM signing
    try:
        return _generate_signed_url_with_storage_iam(
            bucket_name=bucket_name,
            object_path=object_path,
            method=method,
            content_type=content_type,
            expiration_seconds=expiration_seconds,
        )
    except Exception as e:
        logger.warning(
            f"Storage IAM signing failed, falling back to manual IAM SignBlob: {e}",
            exc_info=True,
        )
        # Fall back to manual IAM SignBlob implementation
        return _generate_signed_url_manual_iam(
            bucket_name=bucket_name,
            object_path=object_path,
            method=method,
            content_type=content_type,
            expiration_seconds=expiration_seconds,
        )


def _generate_signed_url_with_storage_iam(
    bucket_name: str,
    object_path: str,
    method: str = "PUT",
    content_type: Optional[str] = None,
    expiration_seconds: int = 900,
) -> str:
    """Generate signed URL using google-cloud-storage's built-in IAM signing.

    This is the recommended approach for Cloud Run as it uses the storage library's
    native IAM signing support, which automatically handles server-side signing.

    Args:
        bucket_name: GCS bucket name.
        object_path: Object path within bucket.
        method: HTTP method.
        content_type: Content type header (optional).
        expiration_seconds: URL expiration time in seconds.

    Returns:
        Signed URL string.

    Raises:
        RuntimeError: If signing fails or dependencies are missing.
    """
    if storage is None:
        raise RuntimeError(
            "google-cloud-storage is not installed. Install with: poetry install -E enterprise"
        )

    if google is None or default is None:
        raise RuntimeError(
            "google-auth is not installed. Install with: poetry install -E enterprise"
        )

    logger.debug(f"Using storage library IAM signing for gs://{bucket_name}/{object_path}")

    # Get credentials with explicit scopes for IAM API access
    try:
        credentials, project = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    except DefaultCredentialsError as e:
        raise RuntimeError(
            f"Failed to get default credentials: {e}. "
            "Ensure GOOGLE_APPLICATION_CREDENTIALS is set or running on GCP."
        ) from e

    # Refresh credentials to ensure we have a valid access token
    if auth_requests is None:
        raise RuntimeError("google-auth transport is not available")
    auth_request = auth_requests.Request()
    try:
        credentials.refresh(auth_request)
    except Exception as e:
        logger.warning(f"Credential refresh failed, continuing with existing token: {e}")

    # Get service account email
    service_account_email = get_service_account_email()
    logger.debug(f"Using service account: {service_account_email}")

    # Normalize object path (remove leading slash if present)
    object_path = object_path.lstrip("/")

    # Create storage client with credentials
    client = storage.Client(credentials=credentials, project=project)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)

    # Generate signed URL using IAM (server-side signing)
    # When service_account_email and access_token are provided, the storage library
    # automatically uses IAM SignBlob API instead of local signing
    try:
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration_seconds),
            method=method,
            content_type=content_type,
            service_account_email=service_account_email,
            access_token=credentials.token,
        )
        logger.debug(
            f"Successfully generated signed URL for gs://{bucket_name}/{object_path} "
            f"(expires in {expiration_seconds}s)"
        )
        return url
    except Exception as e:
        logger.error(
            f"Storage library IAM signing failed for {service_account_email}: {e}",
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to generate signed URL using storage library IAM signing: {e}. "
            "Ensure the service account has roles/iam.serviceAccountTokenCreator "
            "permission on itself."
        ) from e


def _generate_signed_url_manual_iam(
    bucket_name: str,
    object_path: str,
    method: str = "PUT",
    content_type: Optional[str] = None,
    expiration_seconds: int = 900,
) -> str:
    """Generate signed URL using manual IAM SignBlob implementation (fallback).

    This is the fallback approach that manually constructs the signed URL and uses
    IAM SignBlob API directly.

    Args:
        bucket_name: GCS bucket name.
        object_path: Object path within bucket.
        method: HTTP method.
        content_type: Content type header (optional).
        expiration_seconds: URL expiration time in seconds.

    Returns:
        Signed URL string.

    Raises:
        RuntimeError: If signing fails or credentials cannot be obtained.
    """
    if google is None:
        raise RuntimeError(
            "google-cloud-iam is not installed. Install with: poetry install -E enterprise"
        )

    logger.debug(f"Using manual IAM SignBlob for gs://{bucket_name}/{object_path}")

    # Get service account email
    service_account_email = get_service_account_email()

    # Normalize object path (remove leading slash if present)
    object_path = object_path.lstrip("/")

    # Get current time and expiration time
    now = datetime.now(timezone.utc)
    expiration_time = now + timedelta(seconds=expiration_seconds)  # noqa: F841

    # Format dates for URL
    date_str = now.strftime("%Y%m%d")  # noqa: F841
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    # Get credential scope
    credential_scope = _get_credential_scope(now)

    # Construct credential string
    credential = f"{service_account_email}/{credential_scope}"

    # Prepare query parameters (excluding signature)
    query_params: dict[str, str] = {
        "X-Goog-Algorithm": "GOOG4-RSA-SHA256",
        "X-Goog-Credential": credential,
        "X-Goog-Date": timestamp,
        "X-Goog-Expires": str(expiration_seconds),
    }

    # Prepare headers
    headers: dict[str, str] = {}
    if content_type:
        headers["Content-Type"] = content_type

    # Calculate payload hash (empty string hash for PUT requests)
    payload_hash = hashlib.sha256(b"").hexdigest()

    # Construct canonical request
    resource = f"/{bucket_name}/{object_path}"
    canonical_request = _construct_canonical_request(
        method=method,
        resource=resource,
        query_params=query_params,
        headers=headers,
        payload_hash=payload_hash,
    )

    # Hash the canonical request
    canonical_request_hash = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()

    # Construct string to sign
    string_to_sign = (
        f"GOOG4-RSA-SHA256\n" f"{timestamp}\n" f"{credential_scope}\n" f"{canonical_request_hash}"
    )

    # Sign the string using IAM API
    signature_bytes = _sign_blob_with_iam(service_account_email, string_to_sign.encode("utf-8"))

    # Encode signature
    signature = _encode_signature(signature_bytes)

    # Add signature to query parameters
    query_params["X-Goog-Signature"] = signature

    # Add signed headers to query parameters
    if headers:
        signed_headers = ";".join(k.lower() for k in sorted(headers.keys()))
        query_params["X-Goog-SignedHeaders"] = signed_headers

    # Construct final URL
    query_string = "&".join(
        f"{k}={urllib.parse.quote(v, safe='')}" for k, v in sorted(query_params.items())
    )
    url = f"https://storage.googleapis.com/{bucket_name}/{object_path}?{query_string}"

    logger.debug(
        f"Generated signed URL (manual IAM) for gs://{bucket_name}/{object_path} "
        f"(expires in {expiration_seconds}s)"
    )

    return url
