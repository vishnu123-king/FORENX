"""
Evidence acquisition and controlled handling for ForenX.
Preserves original evidence, verifies hashes before/after copy,
copies SQLite sidecars (WAL/SHM), and creates working analysis copies.
"""

import shutil
from pathlib import Path
from typing import Any

from forenx.audit import log_audit
from forenx.cases import get_case
from forenx.config import get_config
from forenx.database import get_db_connection
from forenx.exceptions import (
    EvidenceError,
    InconsistentEvidenceError,
    SecurityViolationError,
)
from forenx.integrity import calculate_sha256, verify_evidence_file
from forenx.models import Evidence, generate_id, utc_now_iso

KNOWN_SIDECAR_SUFFIXES = ["-wal", "-shm"]

def detect_evidence_type(filename: str, file_path: Path) -> str:
    """Detect whether evidence is Chromium History, Firefox places.sqlite, or unknown."""
    fname = filename.lower()
    if "history" in fname:
        return "chromium_history"
    if "places" in fname:
        return "firefox_places"
    if fname.endswith(".zip") or fname.endswith(".tar.gz"):
        return "artifact_package"
    return "unknown_browser_db"

def import_evidence(
    case_id: str,
    source_file_path: Path,
    acquisition_method: str = "controlled_local_copy",
    provenance_notes: str = ""
) -> Evidence:
    """
    Import an authorized browser evidence database into the case vault.
    Enforces size boundaries, path security, hashes before and after copying,
    preserves sidecars (-wal, -shm), creates a controlled working copy,
    and logs an audit record.
    """
    cfg = get_config()
    cfg.ensure_directories()

    # Verify case exists
    get_case(case_id)

    src_path = Path(source_file_path).resolve()
    if not src_path.exists() or not src_path.is_file():
        raise EvidenceError(f"Evidence source file does not exist or is not a regular file: {source_file_path}")

    # Bounded file size check
    file_size = src_path.stat().st_size
    if file_size > cfg.max_import_size_bytes:
        raise SecurityViolationError(
            f"Evidence file size ({file_size} bytes) exceeds maximum permitted threshold ({cfg.max_import_size_bytes} bytes)."
        )

    # Pre-copy SHA-256 hash calculation
    pre_copy_hash = calculate_sha256(src_path)

    evidence_id = generate_id("evi")
    case_vault_dir = cfg.evidence_dir / case_id / evidence_id
    case_vault_dir.mkdir(parents=True, exist_ok=True)

    dest_file = case_vault_dir / src_path.name
    shutil.copy2(src_path, dest_file)

    # Post-copy SHA-256 calculation of the vault copy
    post_copy_vault_hash = calculate_sha256(dest_file)

    # Also re-check source to ensure it was not modified during copy
    post_copy_src_hash = calculate_sha256(src_path)
    if pre_copy_hash != post_copy_src_hash:
        # Inconsistent source write detected during acquisition
        dest_file.unlink(missing_ok=True)
        raise InconsistentEvidenceError(
            f"Source evidence was concurrently modified during copy acquisition (Pre: {pre_copy_hash[:10]}, Post: {post_copy_src_hash[:10]})."
        )

    if post_copy_vault_hash != pre_copy_hash:
        dest_file.unlink(missing_ok=True)
        raise InconsistentEvidenceError(
            f"Vault copy byte hash mismatch (Source: {pre_copy_hash[:10]}, Vault: {post_copy_vault_hash[:10]})."
        )

    # Detect and preserve any SQLite sidecars (-wal, -shm) present alongside the source file
    src_parent = src_path.parent
    sidecars_found = []
    for suffix in KNOWN_SIDECAR_SUFFIXES:
        sidecar_candidate = src_parent / f"{src_path.name}{suffix}"
        if sidecar_candidate.exists() and sidecar_candidate.is_file():
            sidecar_dest = case_vault_dir / sidecar_candidate.name
            shutil.copy2(sidecar_candidate, sidecar_dest)
            sidecar_hash = calculate_sha256(sidecar_dest)
            sidecars_found.append(f"{sidecar_candidate.name} (SHA-256: {sidecar_hash[:8]}...)")

    # Create controlled working copy for non-destructive analysis
    working_case_dir = cfg.working_dir / case_id / evidence_id
    working_case_dir.mkdir(parents=True, exist_ok=True)
    working_db_file = working_case_dir / src_path.name
    shutil.copy2(dest_file, working_db_file)
    for s_file in case_vault_dir.glob(f"{src_path.name}*"):
        if s_file != dest_file:
            shutil.copy2(s_file, working_case_dir / s_file.name)

    rel_path = f"{case_id}/{evidence_id}/{src_path.name}"
    evidence_type = detect_evidence_type(src_path.name, src_path)

    now = utc_now_iso()
    sidecar_note = f" Sidecars preserved: {', '.join(sidecars_found)}." if sidecars_found else ""
    full_provenance = f"{provenance_notes.strip()}{sidecar_note}".strip()

    evidence = Evidence(
        id=evidence_id,
        case_id=case_id,
        filename=src_path.name,
        evidence_type=evidence_type,
        byte_size=file_size,
        sha256=post_copy_vault_hash,
        imported_at=now,
        acquisition_method=acquisition_method,
        provenance_notes=full_provenance,
        storage_relative_path=rel_path,
        verification_status="verified",
        parser_compatibility="compatible"
    )

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO evidence (
                    id, case_id, filename, evidence_type, byte_size, sha256,
                    imported_at, acquisition_method, provenance_notes,
                    storage_relative_path, verification_status, parser_compatibility
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (evidence.id, evidence.case_id, evidence.filename, evidence.evidence_type,
                 evidence.byte_size, evidence.sha256, evidence.imported_at,
                 evidence.acquisition_method, evidence.provenance_notes,
                 evidence.storage_relative_path, evidence.verification_status,
                 evidence.parser_compatibility)
            )
            log_audit(
                operation="evidence_imported",
                case_id=case_id,
                evidence_id=evidence.id,
                outcome="success",
                details=f"Imported evidence '{src_path.name}' ({file_size} bytes, SHA-256: {post_copy_vault_hash[:12]}...)",
                conn=conn
            )
        return evidence
    finally:
        conn.close()

def get_evidence(evidence_id: str) -> Evidence:
    """Retrieve evidence record by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE id = ?;", (evidence_id,))
        row = cursor.fetchone()
        if not row:
            raise EvidenceError(f"Evidence item with ID '{evidence_id}' was not found.")
        return Evidence(
            id=row["id"],
            case_id=row["case_id"],
            filename=row["filename"],
            evidence_type=row["evidence_type"],
            byte_size=row["byte_size"],
            sha256=row["sha256"],
            imported_at=row["imported_at"],
            acquisition_method=row["acquisition_method"],
            provenance_notes=row["provenance_notes"] or "",
            storage_relative_path=row["storage_relative_path"],
            verification_status=row["verification_status"],
            parser_compatibility=row["parser_compatibility"]
        )
    finally:
        conn.close()

def list_case_evidence(case_id: str) -> list[Evidence]:
    """List all evidence registered for a case."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE case_id = ? ORDER BY imported_at ASC;", (case_id,))
        rows = cursor.fetchall()
        return [
            Evidence(
                id=r["id"],
                case_id=r["case_id"],
                filename=r["filename"],
                evidence_type=r["evidence_type"],
                byte_size=r["byte_size"],
                sha256=r["sha256"],
                imported_at=r["imported_at"],
                acquisition_method=r["acquisition_method"],
                provenance_notes=r["provenance_notes"] or "",
                storage_relative_path=r["storage_relative_path"],
                verification_status=r["verification_status"],
                parser_compatibility=r["parser_compatibility"]
            )
            for r in rows
        ]
    finally:
        conn.close()

def verify_case_evidence_item(evidence_id: str) -> dict[str, Any]:
    """
    Re-hash stored evidence in the vault against its recorded SHA-256 hash.
    Updates the database verification status and logs an audit entry.
    """
    evidence = get_evidence(evidence_id)
    cfg = get_config()
    vault_file = cfg.evidence_dir / evidence.storage_relative_path

    is_match, status_code, details = verify_evidence_file(vault_file, evidence.sha256)

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE evidence SET verification_status = ? WHERE id = ?;",
                (status_code, evidence_id)
            )
            log_audit(
                operation="evidence_verified",
                case_id=evidence.case_id,
                evidence_id=evidence.id,
                outcome="success" if is_match else "failure",
                details=f"Verification status: {status_code}. Recorded: {evidence.sha256[:12]}..., Computed: {(details.get('calculated_sha256') or '')[:12]}...",
                conn=conn
            )
        details["status"] = status_code
        details["is_match"] = is_match
        details["evidence_id"] = evidence_id
        return details
    finally:
        conn.close()

def get_working_copy_path(evidence: Evidence) -> Path:
    """Return the absolute path to the working copy of the evidence database."""
    cfg = get_config()
    return cfg.working_dir / evidence.storage_relative_path
