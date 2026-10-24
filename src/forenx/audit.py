"""
Cryptographically chained audit logging service for ForenX.
Maintains a tamper-evident chain of custody and forensic operations.
"""

import hashlib
import json
import sqlite3

from forenx.database import get_db_connection
from forenx.models import AuditEntry, generate_id, utc_now_iso

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def compute_entry_hash(
    timestamp_utc: str,
    operation: str,
    case_id: str | None,
    evidence_id: str | None,
    outcome: str,
    details: str,
    previous_hash: str
) -> str:
    """Compute canonical SHA-256 hash of an audit record to ensure tamper-evidence."""
    canonical_payload = json.dumps({
        "timestamp_utc": timestamp_utc,
        "operation": operation,
        "case_id": case_id or "",
        "evidence_id": evidence_id or "",
        "outcome": outcome,
        "details": details or "",
        "previous_hash": previous_hash
    }, sort_keys=True)
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

def log_audit(
    operation: str,
    case_id: str | None = None,
    evidence_id: str | None = None,
    outcome: str = "success",
    details: str = "",
    conn: sqlite3.Connection | None = None
) -> AuditEntry:
    """Record a new tamper-evident audit log entry."""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    try:
        cursor = conn.cursor()
        # Fetch the last entry hash
        cursor.execute("SELECT entry_hash FROM audit_entries ORDER BY rowid DESC LIMIT 1;")
        row = cursor.fetchone()
        previous_hash = row[0] if row else GENESIS_HASH

        entry_id = generate_id("aud")
        timestamp_utc = utc_now_iso()
        entry_hash = compute_entry_hash(
            timestamp_utc=timestamp_utc,
            operation=operation,
            case_id=case_id,
            evidence_id=evidence_id,
            outcome=outcome,
            details=details,
            previous_hash=previous_hash
        )

        cursor.execute(
            """
            INSERT INTO audit_entries (
                id, timestamp_utc, operation, case_id, evidence_id,
                outcome, details, previous_entry_hash, entry_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (entry_id, timestamp_utc, operation, case_id, evidence_id,
             outcome, details, previous_hash, entry_hash)
        )
        if should_close:
            conn.commit()

        return AuditEntry(
            id=entry_id,
            timestamp_utc=timestamp_utc,
            operation=operation,
            case_id=case_id,
            evidence_id=evidence_id,
            outcome=outcome,
            details=details,
            previous_entry_hash=previous_hash,
            entry_hash=entry_hash
        )
    finally:
        if should_close:
            conn.close()

def get_audit_entries(case_id: str | None = None, limit: int = 100) -> list[AuditEntry]:
    """Retrieve audit entries with optional case filter."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if case_id:
            cursor.execute(
                "SELECT * FROM audit_entries WHERE case_id = ? ORDER BY timestamp_utc DESC LIMIT ?;",
                (case_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM audit_entries ORDER BY timestamp_utc DESC LIMIT ?;",
                (limit,)
            )
        rows = cursor.fetchall()
        entries = []
        for r in rows:
            entries.append(AuditEntry(
                id=r["id"],
                timestamp_utc=r["timestamp_utc"],
                operation=r["operation"],
                case_id=r["case_id"],
                evidence_id=r["evidence_id"],
                outcome=r["outcome"],
                details=r["details"],
                previous_entry_hash=r["previous_entry_hash"],
                entry_hash=r["entry_hash"]
            ))
        return entries
    finally:
        conn.close()

def verify_audit_chain() -> tuple[bool, list[str]]:
    """
    Verify the cryptographic integrity of the entire audit log chain.
    Returns (is_valid, list_of_error_descriptions).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_entries ORDER BY rowid ASC;")
        rows = cursor.fetchall()
        if not rows:
            return True, []

        errors = []
        expected_prev_hash = GENESIS_HASH

        for idx, row in enumerate(rows):
            if row["previous_entry_hash"] != expected_prev_hash:
                errors.append(
                    f"Chain break at record {row['id']}: expected prev_hash {expected_prev_hash[:10]}... "
                    f"got {row['previous_entry_hash'][:10]}..."
                )

            recalculated = compute_entry_hash(
                timestamp_utc=row["timestamp_utc"],
                operation=row["operation"],
                case_id=row["case_id"],
                evidence_id=row["evidence_id"],
                outcome=row["outcome"],
                details=row["details"],
                previous_hash=row["previous_entry_hash"]
            )
            if recalculated != row["entry_hash"]:
                errors.append(
                    f"Hash mismatch at record {row['id']}: recorded {row['entry_hash'][:10]}... "
                    f"recalculated {recalculated[:10]}..."
                )

            expected_prev_hash = row["entry_hash"]

        return len(errors) == 0, errors
    finally:
        conn.close()
