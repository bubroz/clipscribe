"""
File system utilities for ClipScribe.
"""
import hashlib

def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: The path to the file.

    Returns:
        The SHA256 checksum as a hex digest.
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()
    except IOError:
        return "" 