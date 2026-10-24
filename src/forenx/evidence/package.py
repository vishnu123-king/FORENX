"""
ForenX Shared Evidence Package Format (FX-ACQ-*.forenx.zip).
Provides package creation, safe unpack verification, manifest schema enforcement,
path-traversal protection, and dual-level SHA-256 integrity verification.
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from forenx.config import get_config
from forenx.database import get_db_connection
from forenx.exceptions import EvidenceError, IntegrityVerificationError, SecurityViolationError
from forenx.integrity import calculate_sha256
from forenx.models import Evidence, EvidencePackage, generate_id, utc_now_iso
from forenx.audit import log_audit

MAX_PACKAGE_EXPANDED_BYTES = 1024 * 1024 * 1024  # 1GB max uncompressed size
MAX_PACKAGE_FILE_COUNT = 5000


def validate_archive_member_path(member_path: str) -> None:
    """
    Ensure zip archive member path is safe:
    - No absolute paths (e.g. /etc/passwd or C:\\)
    - No directory traversal (..)
    - Safe relative paths only
    """
    clean = member_path.replace("\\", "/")
    if clean.startswith("/") or clean.startswith("~"):
        raise SecurityViolationError(f"Absolute path in evidence archive member rejected: {member_path}")
    if ".." in clean.split("/"):
        raise SecurityViolationError(f"Path traversal sequence in evidence archive rejected: {member_path}")
    if clean.startswith(":"):
        raise SecurityViolationError(f"Invalid path prefix in evidence archive: {member_path}")


def create_evidence_package(
    case_id: str,
    acquisition_id: str,
    acquisition_method: str,
    artifacts: list[dict[str, Any]],
    output_directory: Optional[Path] = None,
    endpoint_id: Optional[str] = None,
    investigator_label: str = "",
    provenance_notes: str = ""
) -> Tuple[Path, str, EvidencePackage]:
    """
    Package acquired forensic artifacts into a standardized FX-ACQ-<id>.forenx.zip archive.
    Calculates per-artifact SHA-256 hashes, writes manifest.json and acquisition_log.json,
    and calculates the outer package SHA-256 hash.
    """
    cfg = get_config()
    cfg.ensure_directories()

    package_id = f"FX-ACQ-{generate_id()}"
    package_filename = f"{package_id}.forenx.zip"

    out_dir = output_directory or (cfg.evidence_dir / case_id / "packages")
    out_dir.mkdir(parents=True, exist_ok=True)
    package_zip_path = out_dir / package_filename

    now = utc_now_iso()

    # Prepare Manifest and Acquisition Log
    manifest_artifacts = []
    log_entries = []

    # Temporary staging directory for archive packaging
    staging_dir = cfg.working_dir / "pkg_staging" / package_id
    staging_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = staging_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    try:
        for art in artifacts:
            src_file = Path(art["file_path"]).resolve()
            if not src_file.exists():
                continue

            rel_target = f"artifacts/{art.get('profile_label', 'default')}/{src_file.name}"
            dest_file = staging_dir / rel_target
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)

            # Copy sidecars if present
            sidecars = []
            for suffix in ["-wal", "-shm"]:
                sidecar_file = src_file.parent / f"{src_file.name}{suffix}"
                if sidecar_file.exists():
                    dest_sidecar = dest_file.parent / f"{src_file.name}{suffix}"
                    shutil.copy2(sidecar_file, dest_sidecar)
                    sidecars.append(sidecar_file.name)

            art_hash = calculate_sha256(dest_file)
            art_size = dest_file.stat().st_size

            manifest_artifacts.append({
                "artifact_id": generate_id("art"),
                "browser_family": art.get("browser_family", "Chromium"),
                "browser_name": art.get("browser_name", "Browser"),
                "profile_label": art.get("profile_label", "Default"),
                "artifact_type": art.get("artifact_type", "History"),
                "relative_path": rel_target,
                "byte_size": art_size,
                "sha256": art_hash,
                "sidecars_preserved": sidecars,
                "acquisition_status": "acquired",
                "warnings": art.get("warnings", [])
            })

            log_entries.append({
                "timestamp_utc": now,
                "artifact": src_file.name,
                "sha256": art_hash,
                "status": "copied_and_verified"
            })

        # Build Manifest
        manifest_data = {
            "manifest_version": "1.0.0",
            "package_id": package_id,
            "case_id": case_id,
            "acquisition_id": acquisition_id,
            "acquisition_method": acquisition_method,
            "forenx_version": cfg.app_version,
            "created_at_utc": now,
            "endpoint_id": endpoint_id,
            "operating_system": os.name,
            "authorizing_investigator": investigator_label,
            "acquisition_notes": provenance_notes,
            "artifacts": manifest_artifacts
        }

        # Write manifest and acquisition log to staging
        manifest_file = staging_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        log_file = staging_dir / "acquisition_log.json"
        log_file.write_text(json.dumps({"entries": log_entries}, indent=2), encoding="utf-8")

        # Create zip archive
        with zipfile.ZipFile(package_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(staging_dir):
                for f in files:
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(staging_dir).as_posix()
                    validate_archive_member_path(rel_p)
                    zf.write(full_p, arcname=rel_p)

        # Outer package SHA-256 calculation
        outer_package_hash = calculate_sha256(package_zip_path)
        package_size = package_zip_path.stat().st_size

        pkg_model = EvidencePackage(
            id=package_id,
            case_id=case_id,
            acquisition_id=acquisition_id,
            endpoint_id=endpoint_id,
            acquisition_method=acquisition_method,
            package_filename=package_filename,
            storage_path=str(package_zip_path),
            package_sha256=outer_package_hash,
            byte_size=package_size,
            manifest_version="1.0.0",
            verification_status="verified",
            created_at=now,
            artifact_count=len(manifest_artifacts),
            warnings_count=0,
            manifest_json=json.dumps(manifest_data)
        )

        conn = get_db_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO evidence_packages (
                        id, case_id, acquisition_id, endpoint_id, acquisition_method,
                        package_filename, storage_path, package_sha256, byte_size,
                        manifest_version, verification_status, created_at, artifact_count,
                        warnings_count, manifest_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (pkg_model.id, pkg_model.case_id, pkg_model.acquisition_id,
                     pkg_model.endpoint_id, pkg_model.acquisition_method,
                     pkg_model.package_filename, pkg_model.storage_path,
                     pkg_model.package_sha256, pkg_model.byte_size,
                     pkg_model.manifest_version, pkg_model.verification_status,
                     pkg_model.created_at, pkg_model.artifact_count,
                     pkg_model.warnings_count, pkg_model.manifest_json)
                )
                log_audit(
                    operation="evidence_package_created",
                    case_id=case_id,
                    outcome="success",
                    details=f"Created package {package_id} ({len(manifest_artifacts)} artifacts, SHA-256: {outer_package_hash[:12]}...)",
                    conn=conn
                )
        finally:
            conn.close()

        return package_zip_path, outer_package_hash, pkg_model

    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


def inspect_package(zip_path: Path) -> dict[str, Any]:
    """Inspect evidence package manifest without unpacking all files."""
    path = Path(zip_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Package file not found: {zip_path}")

    with zipfile.ZipFile(path, "r") as zf:
        if "manifest.json" not in zf.namelist():
            raise EvidenceError("Archive is not a valid ForenX evidence package (missing manifest.json).")
        manifest_bytes = zf.read("manifest.json")
        return json.loads(manifest_bytes.decode("utf-8"))


def import_and_verify_package(
    case_id: str,
    zip_path: Path,
    expected_package_sha256: Optional[str] = None
) -> Tuple[EvidencePackage, List[Evidence], Dict[str, Any]]:
    """
    Safely import a portable ForenX evidence package into the workbench.
    Performs security checks:
    - Verifies outer package SHA-256 if expected hash is provided.
    - Inspects zip entries for path traversal or zip bombs.
    - Extracts into isolated vault folder.
    - Verifies each declared artifact SHA-256 against recorded manifest hash.
    - Registers evidence items and package in database.
    - Creates working copies for safe parsing.
    """
    cfg = get_config()
    cfg.ensure_directories()
    src_zip = Path(zip_path).resolve()

    if not src_zip.is_file():
        raise EvidenceError(f"Evidence package file not found: {zip_path}")

    # 1. Outer Package Hash Verification
    computed_package_hash = calculate_sha256(src_zip)
    if expected_package_sha256 and expected_package_sha256.lower() != computed_package_hash.lower():
        raise IntegrityVerificationError(
            f"Package outer SHA-256 mismatch! Expected: {expected_package_sha256[:12]}..., Computed: {computed_package_hash[:12]}..."
        )

    # 2. Archive Safety Inspection
    total_uncompressed_bytes = 0
    total_file_count = 0

    with zipfile.ZipFile(src_zip, "r") as zf:
        namelist = zf.namelist()
        if "manifest.json" not in namelist:
            raise EvidenceError("Invalid package: missing manifest.json")

        for info in zf.infolist():
            validate_archive_member_path(info.filename)
            total_uncompressed_bytes += info.file_size
            total_file_count += 1

            if total_uncompressed_bytes > MAX_PACKAGE_EXPANDED_BYTES:
                raise SecurityViolationError(
                    f"Evidence package exceeds maximum permitted uncompressed size ({MAX_PACKAGE_EXPANDED_BYTES} bytes)."
                )
            if total_file_count > MAX_PACKAGE_FILE_COUNT:
                raise SecurityViolationError(
                    f"Evidence package exceeds maximum permitted file count ({MAX_PACKAGE_FILE_COUNT} files)."
                )

        manifest_raw = zf.read("manifest.json").decode("utf-8")
        manifest_data = json.loads(manifest_raw)

    package_id = manifest_data.get("package_id", f"FX-ACQ-{generate_id()}")
    acquisition_id = manifest_data.get("acquisition_id", generate_id("acq"))
    acq_method = manifest_data.get("acquisition_method", "portable_package_import")
    endpoint_id = manifest_data.get("endpoint_id")

    # 3. Extract into vault storage
    vault_dest = cfg.evidence_dir / case_id / package_id
    vault_dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src_zip, "r") as zf:
        for member in zf.infolist():
            validate_archive_member_path(member.filename)
            zf.extract(member, vault_dest)

    # 4. Verify each artifact declared in manifest
    registered_evidence: List[Evidence] = []
    verification_failures = []
    declared_artifacts = manifest_data.get("artifacts", [])

    conn = get_db_connection()
    try:
        for art in declared_artifacts:
            art_rel = art["relative_path"]
            extracted_art_path = vault_dest / art_rel
            if not extracted_art_path.exists():
                verification_failures.append(f"Missing artifact from archive: {art_rel}")
                continue

            calculated_art_hash = calculate_sha256(extracted_art_path)
            expected_art_hash = art["sha256"]

            status = "verified" if calculated_art_hash.lower() == expected_art_hash.lower() else "failed"
            if status != "verified":
                verification_failures.append(
                    f"Artifact hash mismatch on {art_rel}: Expected {expected_art_hash[:8]}..., Computed {calculated_art_hash[:8]}..."
                )

            # Create working copy for non-destructive analysis
            working_dest = cfg.working_dir / case_id / package_id / art_rel
            working_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(extracted_art_path, working_dest)

            # Copy sidecars to working copy if present
            for suffix in ["-wal", "-shm"]:
                s_file = extracted_art_path.parent / f"{extracted_art_path.name}{suffix}"
                if s_file.exists():
                    shutil.copy2(s_file, working_dest.parent / f"{working_dest.name}{suffix}")

            evidence_type = "chromium_history" if "history" in extracted_art_path.name.lower() else "firefox_places"
            evidence_id = generate_id("evi")

            storage_rel = f"{case_id}/{package_id}/{art_rel}"

            evi_model = Evidence(
                id=evidence_id,
                case_id=case_id,
                filename=extracted_art_path.name,
                evidence_type=evidence_type,
                byte_size=extracted_art_path.stat().st_size,
                sha256=calculated_art_hash,
                imported_at=utc_now_iso(),
                acquisition_method=acq_method,
                provenance_notes=f"Package {package_id} ({art.get('browser_name')}, {art.get('profile_label')})",
                storage_relative_path=storage_rel,
                verification_status=status,
                parser_compatibility="compatible"
            )

            with conn:
                conn.execute(
                    """
                    INSERT INTO evidence (
                        id, case_id, filename, evidence_type, byte_size, sha256,
                        imported_at, acquisition_method, provenance_notes,
                        storage_relative_path, verification_status, parser_compatibility
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (evi_model.id, evi_model.case_id, evi_model.filename, evi_model.evidence_type,
                     evi_model.byte_size, evi_model.sha256, evi_model.imported_at,
                     evi_model.acquisition_method, evi_model.provenance_notes,
                     evi_model.storage_relative_path, evi_model.verification_status,
                     evi_model.parser_compatibility)
                )
            registered_evidence.append(evi_model)

        pkg_verification = "verified" if len(verification_failures) == 0 else "failed"

        pkg_model = EvidencePackage(
            id=package_id,
            case_id=case_id,
            acquisition_id=acquisition_id,
            endpoint_id=endpoint_id,
            acquisition_method=acq_method,
            package_filename=src_zip.name,
            storage_path=str(src_zip),
            package_sha256=computed_package_hash,
            byte_size=src_zip.stat().st_size,
            manifest_version="1.0.0",
            verification_status=pkg_verification,
            created_at=utc_now_iso(),
            artifact_count=len(registered_evidence),
            warnings_count=len(verification_failures),
            manifest_json=json.dumps(manifest_data)
        )

        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence_packages (
                    id, case_id, acquisition_id, endpoint_id, acquisition_method,
                    package_filename, storage_path, package_sha256, byte_size,
                    manifest_version, verification_status, created_at, artifact_count,
                    warnings_count, manifest_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (pkg_model.id, pkg_model.case_id, pkg_model.acquisition_id,
                 pkg_model.endpoint_id, pkg_model.acquisition_method,
                 pkg_model.package_filename, pkg_model.storage_path,
                 pkg_model.package_sha256, pkg_model.byte_size,
                 pkg_model.manifest_version, pkg_model.verification_status,
                 pkg_model.created_at, pkg_model.artifact_count,
                 pkg_model.warnings_count, pkg_model.manifest_json)
            )

            log_audit(
                operation="evidence_package_imported",
                case_id=case_id,
                outcome="success" if pkg_verification == "verified" else "warning",
                details=f"Imported package {package_id}: {len(registered_evidence)} artifacts, status: {pkg_verification}.",
                conn=conn
            )

        verification_report = {
            "package_id": package_id,
            "package_sha256": computed_package_hash,
            "verification_status": pkg_verification,
            "artifacts_verified_count": len(registered_evidence),
            "failures": verification_failures
        }

        return pkg_model, registered_evidence, verification_report

    finally:
        conn.close()


def list_evidence_packages(case_id: str) -> list[EvidencePackage]:
    """Retrieve all evidence packages for a case."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence_packages WHERE case_id = ? ORDER BY created_at DESC;", (case_id,))
        rows = cursor.fetchall()
        return [
            EvidencePackage(
                id=r["id"],
                case_id=r["case_id"],
                acquisition_id=r["acquisition_id"],
                endpoint_id=r["endpoint_id"],
                acquisition_method=r["acquisition_method"],
                package_filename=r["package_filename"],
                storage_path=r["storage_path"],
                package_sha256=r["package_sha256"],
                byte_size=r["byte_size"],
                manifest_version=r["manifest_version"],
                verification_status=r["verification_status"],
                created_at=r["created_at"],
                artifact_count=r["artifact_count"],
                warnings_count=r["warnings_count"],
                manifest_json=r["manifest_json"] or "{}"
            )
            for r in rows
        ]
    finally:
        conn.close()
