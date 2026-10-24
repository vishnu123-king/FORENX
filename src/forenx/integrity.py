"""
Cryptographic integrity verification for ForenX.
Computes and verifies SHA-256 hashes of forensic evidence items.
"""

import hashlib
from pathlib import Path
from typing import Any

CHUNK_SIZE = 64 * 1024  # 64KB streaming buffer

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 digest of a file in streaming chunks.
    Raises FileNotFoundError if file does not exist.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Target file for hashing does not exist: {file_path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_evidence_file(file_path: Path, recorded_sha256: str) -> tuple[bool, str, dict[str, Any]]:
    """
    Verify a physical file against its recorded SHA-256 hash.
    Returns:
        (is_match, status_code, details_dict)
        status_code: 'verified', 'failed', 'missing', 'unreadable'
    """
    path = Path(file_path)
    if not path.exists():
        return False, "missing", {
            "error": f"File does not exist at path: {file_path}",
            "recorded_sha256": recorded_sha256,
            "calculated_sha256": None
        }

    try:
        calculated = calculate_sha256(path)
        is_match = (calculated.lower() == recorded_sha256.lower())
        status = "verified" if is_match else "failed"
        return is_match, status, {
            "recorded_sha256": recorded_sha256,
            "calculated_sha256": calculated,
            "byte_size": path.stat().st_size,
            "match": is_match
        }
    except Exception as e:
        return False, "unreadable", {
            "error": str(e),
            "recorded_sha256": recorded_sha256,
            "calculated_sha256": None
        }
