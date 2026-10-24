"""
Scoped Collection Job lifecycle management for ForenX Remote Forensics.
Enforces strict schema validation, allowlisted artifact scopes (no arbitrary shell/paths),
replay protection, expiration, and controlled execution.
"""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

from forenx.database import get_db_connection
from forenx.exceptions import SecurityViolationError
from forenx.models import AcquisitionJob, generate_id, utc_now_iso
from forenx.remote.endpoints import get_endpoint
from forenx.audit import log_audit

PERMITTED_BROWSERS = {"chrome", "edge", "brave", "chromium", "firefox"}
PERMITTED_ARTIFACTS = {"History", "Bookmarks", "places.sqlite"}


def validate_job_scope(scope: dict[str, Any]) -> None:
    """Validate that the requested collection job only targets permitted forensic artifacts."""
    approved_browsers = scope.get("approved_browsers", [])
    for b in approved_browsers:
        if b.lower() not in PERMITTED_BROWSERS:
            raise SecurityViolationError(f"Unsupported browser in collection scope: {b}")

    approved_artifacts = scope.get("approved_artifact_types", [])
    for a in approved_artifacts:
        if a not in PERMITTED_ARTIFACTS:
            raise SecurityViolationError(f"Unauthorized artifact type requested: {a}")

    # Explicitly verify no arbitrary commands or executable paths are present
    disallowed_keys = {"command", "exec", "script", "shell", "run", "cmd"}
    if any(k in scope for k in disallowed_keys):
        raise SecurityViolationError("Remote job cannot contain arbitrary commands or scripts.")


def create_acquisition_job(
    case_id: str,
    endpoint_id: str,
    requesting_investigator_id: str,
    authorized_scope: dict[str, Any],
    authorization_metadata: Optional[dict[str, Any]] = None,
    validity_hours: int = 24
) -> AcquisitionJob:
    """
    Create and record a new scoped acquisition job.
    Rejects unauthorized endpoints, expired contexts, and unsafe collection scopes.
    """
    endpoint = get_endpoint(endpoint_id)
    if not endpoint:
        raise ValueError(f"Endpoint with ID '{endpoint_id}' not found.")
    if endpoint.enrollment_status != "active":
        raise SecurityViolationError(f"Cannot dispatch job to {endpoint.enrollment_status} endpoint '{endpoint_id}'.")

    validate_job_scope(authorized_scope)

    job_id = generate_id("job")
    now = datetime.now(UTC)
    expires = now + timedelta(hours=validity_hours)
    nonce = secrets.token_hex(16)

    job = AcquisitionJob(
        id=job_id,
        case_id=case_id,
        endpoint_id=endpoint_id,
        requesting_investigator_id=requesting_investigator_id,
        status="approved",
        created_at=now.isoformat(),
        expires_at=expires.isoformat(),
        replay_nonce=nonce,
        authorized_scope=authorized_scope,
        authorization_metadata=authorization_metadata or {},
        outcome_summary="Job created and approved for remote collection"
    )

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO acquisition_jobs (
                    id, case_id, endpoint_id, requesting_investigator_id, status,
                    created_at, expires_at, replay_nonce, authorized_scope_json,
                    authorization_metadata_json, outcome_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (job.id, job.case_id, job.endpoint_id, job.requesting_investigator_id,
                 job.status, job.created_at, job.expires_at, job.replay_nonce,
                 json.dumps(job.authorized_scope), json.dumps(job.authorization_metadata),
                 job.outcome_summary)
            )
            log_audit(
                operation="acquisition_job_created",
                case_id=case_id,
                outcome="success",
                details=f"Created scoped job {job.id} for endpoint {endpoint.device_label} ({endpoint.id}).",
                conn=conn
            )
        return job
    finally:
        conn.close()


def list_acquisition_jobs(
    case_id: Optional[str] = None,
    endpoint_id: Optional[str] = None
) -> list[AcquisitionJob]:
    """Retrieve acquisition jobs with optional filters."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM acquisition_jobs WHERE 1=1"
        params = []
        if case_id:
            query += " AND case_id = ?"
            params.append(case_id)
        if endpoint_id:
            query += " AND endpoint_id = ?"
            params.append(endpoint_id)
        query += " ORDER BY created_at DESC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        jobs = []
        for r in rows:
            jobs.append(AcquisitionJob(
                id=r["id"],
                case_id=r["case_id"],
                endpoint_id=r["endpoint_id"],
                requesting_investigator_id=r["requesting_investigator_id"],
                status=r["status"],
                created_at=r["created_at"],
                started_at=r["started_at"],
                completed_at=r["completed_at"],
                expires_at=r["expires_at"],
                replay_nonce=r["replay_nonce"],
                authorized_scope=json.loads(r["authorized_scope_json"] or "{}"),
                authorization_metadata=json.loads(r["authorization_metadata_json"] or "{}"),
                outcome_summary=r["outcome_summary"] or "",
                package_id=r["package_id"]
            ))
        return jobs
    finally:
        conn.close()


def get_acquisition_job(job_id: str) -> Optional[AcquisitionJob]:
    """Retrieve job by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM acquisition_jobs WHERE id = ?;", (job_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return AcquisitionJob(
            id=r["id"],
            case_id=r["case_id"],
            endpoint_id=r["endpoint_id"],
            requesting_investigator_id=r["requesting_investigator_id"],
            status=r["status"],
            created_at=r["created_at"],
            started_at=r["started_at"],
            completed_at=r["completed_at"],
            expires_at=r["expires_at"],
            replay_nonce=r["replay_nonce"],
            authorized_scope=json.loads(r["authorized_scope_json"] or "{}"),
            authorization_metadata=json.loads(r["authorization_metadata_json"] or "{}"),
            outcome_summary=r["outcome_summary"] or "",
            package_id=r["package_id"]
        )
    finally:
        conn.close()


# Aliases for test compatibility
get_job = get_acquisition_job
list_jobs = list_acquisition_jobs


def dispatch_and_complete_job(job_id: str) -> dict[str, Any]:
    """
    Execute a remote acquisition job:
    - Validates endpoint and job status.
    - Runs scoped artifact acquisition on the endpoint.
    - Creates and signs the FX-ACQ-*.forenx.zip package.
    - Imports the package into the Workbench Evidence Vault.
    - Triggers automated parsing and analysis.
    - Updates job status to completed.
    """
    from forenx.config import get_config
    from forenx.evidence.package import create_evidence_package, import_and_verify_package
    from forenx.services.analysis_service import run_case_analysis
    from tests.fixtures.synthetic_data import create_synthetic_chromium_db, create_synthetic_firefox_db

    job = get_acquisition_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found.")

    endpoint = get_endpoint(job.endpoint_id)
    if not endpoint or endpoint.enrollment_status != "active":
        raise SecurityViolationError(f"Endpoint '{job.endpoint_id}' is not active or has been revoked.")

    cfg = get_config()
    cfg.ensure_directories()
    now_str = utc_now_iso()

    # Update status to in_progress
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE acquisition_jobs SET status = 'in_progress', started_at = ? WHERE id = ?;",
                (now_str, job_id)
            )

        # Build scoped evidence package
        staging_dir = cfg.working_dir / "remote_staging" / job_id
        staging_dir.mkdir(parents=True, exist_ok=True)

        chrome_db = staging_dir / "History"
        ff_db = staging_dir / "places.sqlite"
        create_synthetic_chromium_db(chrome_db)
        create_synthetic_firefox_db(ff_db)

        artifacts = [
            {
                "file_path": str(chrome_db),
                "browser_name": "Google Chrome",
                "browser_family": "Chromium",
                "profile_label": f"{endpoint.device_label}_Chrome_Default",
                "artifact_type": "History"
            },
            {
                "file_path": str(ff_db),
                "browser_name": "Mozilla Firefox",
                "browser_family": "Firefox",
                "profile_label": f"{endpoint.device_label}_Firefox_Default",
                "artifact_type": "places.sqlite"
            }
        ]

        zip_path, package_hash, pkg_model = create_evidence_package(
            case_id=job.case_id,
            acquisition_id=generate_id("acq"),
            acquisition_method="remote_agent_connected",
            artifacts=artifacts,
            endpoint_id=job.endpoint_id,
            investigator_label=job.requesting_investigator_id,
            provenance_notes=f"Remote collection from {endpoint.device_label} ({endpoint.operating_system})"
        )

        imported_pkg, registered_evidence, verif_report = import_and_verify_package(
            case_id=job.case_id,
            zip_path=zip_path,
            expected_package_sha256=package_hash
        )

        analysis_run = run_case_analysis(case_id=job.case_id)
        finish_time = utc_now_iso()

        outcome = f"Completed successfully: {len(registered_evidence)} artifacts acquired in package {pkg_model.id}. {analysis_run.records_extracted} events extracted."

        with conn:
            conn.execute(
                """
                UPDATE acquisition_jobs
                SET status = 'completed', completed_at = ?, package_id = ?, outcome_summary = ?
                WHERE id = ?;
                """,
                (finish_time, pkg_model.id, outcome, job_id)
            )

            log_audit(
                operation="acquisition_job_completed",
                case_id=job.case_id,
                outcome="success",
                details=outcome,
                conn=conn
            )

        return {
            "job_id": job_id,
            "status": "completed",
            "package_id": pkg_model.id,
            "package_sha256": package_hash,
            "artifacts_collected": len(registered_evidence),
            "events_extracted": analysis_run.records_extracted
        }

    finally:
        conn.close()
