"""Stable ID generation utilities with versioned prefixes.

Provides consistent, portable identifiers using modern hash algorithms.
"""

from __future__ import annotations

import hashlib
from typing import Union


def _to_bytes(data: Union[str, bytes]) -> bytes:
    if isinstance(data, bytes):
        return data
    return str(data).encode("utf-8", errors="ignore")


def generate_stable_id(
    data: Union[str, bytes],
    *,
    algo: str = "sha256",
    length: int = 16,
    include_version_prefix: bool = True,
) -> str:
    """Generate a stable, versioned identifier.

    - algo: "sha256" (default) or "blake2b"
    - length: number of hex characters to keep from the digest
    - include_version_prefix: when True, return e.g. "sha256-16-<digest>"
    """
    raw = _to_bytes(data)

    if algo == "sha256":
        digest = hashlib.sha256(raw).hexdigest()
    elif algo == "blake2b":
        # Use digest_size to get the desired length efficiently when even
        # but still slice to enforce exact hex length
        ds = max(8, min(64, (length + 1) // 2))
        digest = hashlib.blake2b(raw, digest_size=ds).hexdigest()
    else:
        raise ValueError(f"Unsupported algo: {algo}")

    short = digest[:length]
    return f"{algo}-{length}-{short}" if include_version_prefix else short


def generate_unversioned_digest(
    data: Union[str, bytes], *, algo: str = "sha256", length: int = 16
) -> str:
    """Generate just the digest substring without any prefix."""
    return generate_stable_id(data, algo=algo, length=length, include_version_prefix=False)
