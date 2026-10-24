"""
Case management service for ForenX.
Handles case lifecycles, metadata preservation, and audit logging.
"""

from typing import Any

from forenx.audit import log_audit
from forenx.database import get_db_connection
from forenx.exceptions import CaseNotFoundError, DatabaseError
from forenx.models import Case, generate_id, utc_now_iso


def create_case(
    name: str,
    description: str = "",
    investigator_label: str = "",
    notes: str = ""
) -> Case:
    """Create and persist a new forensic investigation case."""
    if not name or not name.strip():
        raise ValueError("Case name cannot be empty.")

    case_id = generate_id("case")
    now = utc_now_iso()
    case = Case(
        id=case_id,
        name=name.strip(),
        description=description.strip(),
        investigator_label=investigator_label.strip(),
        status="active",
        created_at=now,
        updated_at=now,
        notes=notes.strip()
    )

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO cases (id, name, description, investigator_label, status, created_at, updated_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (case.id, case.name, case.description, case.investigator_label,
                 case.status, case.created_at, case.updated_at, case.notes)
            )
            log_audit(
                operation="case_created",
                case_id=case.id,
                outcome="success",
                details=f"Created case '{case.name}' by '{case.investigator_label or 'anonymous'}'",
                conn=conn
            )
        return case
    except Exception as e:
        raise DatabaseError(f"Failed to create case: {e!s}") from e
    finally:
        conn.close()

def get_case(case_id: str) -> Case:
    """Retrieve a single case by its unique identifier."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE id = ?;", (case_id,))
        row = cursor.fetchone()
        if not row:
            raise CaseNotFoundError(f"Case with ID '{case_id}' was not found.")
        return Case(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            investigator_label=row["investigator_label"] or "",
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            notes=row["notes"] or ""
        )
    finally:
        conn.close()

def list_cases(status_filter: str | None = None, search_query: str | None = None) -> list[Case]:
    """List cases with optional status filtering and name/description keyword search."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM cases WHERE 1=1"
        params: list[Any] = []

        if status_filter and status_filter.lower() != "all":
            sql += " AND status = ?"
            params.append(status_filter.lower())

        if search_query and search_query.strip():
            sql += " AND (name LIKE ? OR description LIKE ? OR investigator_label LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term, term])

        sql += " ORDER BY updated_at DESC;"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [
            Case(
                id=r["id"],
                name=r["name"],
                description=r["description"] or "",
                investigator_label=r["investigator_label"] or "",
                status=r["status"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                notes=r["notes"] or ""
            )
            for r in rows
        ]
    finally:
        conn.close()

def update_case(
    case_id: str,
    name: str | None = None,
    description: str | None = None,
    investigator_label: str | None = None,
    status: str | None = None,
    notes: str | None = None
) -> Case:
    """Update editable case metadata."""
    existing = get_case(case_id)
    new_name = name.strip() if name is not None else existing.name
    if not new_name:
        raise ValueError("Case name cannot be empty.")

    new_desc = description.strip() if description is not None else existing.description
    new_inv = investigator_label.strip() if investigator_label is not None else existing.investigator_label
    new_status = status.strip().lower() if status is not None else existing.status
    new_notes = notes.strip() if notes is not None else existing.notes
    now = utc_now_iso()

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                UPDATE cases
                SET name = ?, description = ?, investigator_label = ?, status = ?, notes = ?, updated_at = ?
                WHERE id = ?;
                """,
                (new_name, new_desc, new_inv, new_status, new_notes, now, case_id)
            )
            log_audit(
                operation="case_updated",
                case_id=case_id,
                outcome="success",
                details=f"Updated metadata for case '{new_name}' (status: {new_status})",
                conn=conn
            )
        return get_case(case_id)
    finally:
        conn.close()

def archive_case(case_id: str) -> Case:
    """Archive a case without destroying its evidence."""
    return update_case(case_id, status="archived")

def get_global_statistics() -> dict[str, Any]:
    """Compute real application-wide statistics from the SQLite database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cases;")
        total_cases = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM evidence;")
        total_evidence = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM analysis_runs;")
        total_analysis_runs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM events;")
        total_events = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM evidence WHERE verification_status = 'failed';")
        verification_failures = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT started_at, completed_at, status, records_extracted, warnings_count
            FROM analysis_runs
            ORDER BY started_at DESC LIMIT 1;
            """
        )
        recent_run = cursor.fetchone()
        recent_activity = dict(recent_run) if recent_run else None

        return {
            "total_cases": total_cases,
            "total_evidence": total_evidence,
            "total_analysis_runs": total_analysis_runs,
            "total_events": total_events,
            "verification_failures": verification_failures,
            "recent_activity": recent_activity
        }
    finally:
        conn.close()
