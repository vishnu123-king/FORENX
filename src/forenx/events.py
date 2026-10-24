"""
Normalized event queries and timeline filtering for ForenX.
"""

import json
from typing import Any

from forenx.database import get_db_connection
from forenx.models import Event


def row_to_event(row: Any) -> Event:
    """Convert SQLite row to Event model."""
    extra = {}
    if row["extra_json"]:
        try:
            extra = json.loads(row["extra_json"])
        except Exception:
            extra = {}

    return Event(
        id=row["id"],
        case_id=row["case_id"],
        evidence_id=row["evidence_id"],
        analysis_run_id=row["analysis_run_id"],
        browser_family=row["browser_family"],
        event_type=row["event_type"],
        url=row["url"],
        title=row["title"] or "",
        raw_timestamp=row["raw_timestamp"] or 0,
        timestamp_format=row["timestamp_format"],
        normalized_utc=row["normalized_utc"],
        conversion_status=row["conversion_status"],
        source_database=row["source_database"] or "",
        source_table=row["source_table"] or "",
        source_record_id=row["source_record_id"] or "",
        parser_version=row["parser_version"],
        warning=row["warning"] or "",
        extra_metadata=extra
    )

def get_event(event_id: str) -> Event | None:
    """Retrieve an event by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?;", (event_id,))
        row = cursor.fetchone()
        return row_to_event(row) if row else None
    finally:
        conn.close()

def list_events(
    case_id: str,
    evidence_id: str | None = None,
    browser_family: str | None = None,
    event_type: str | None = None,
    search_term: str | None = None,
    start_utc: str | None = None,
    end_utc: str | None = None,
    limit: int = 500,
    offset: int = 0
) -> tuple[list[Event], int]:
    """
    Search and filter timeline events for a given case.
    Returns: (list_of_events, total_matching_count)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        base_where = "WHERE case_id = ?"
        params: list[Any] = [case_id]

        if evidence_id and evidence_id != "all":
            base_where += " AND evidence_id = ?"
            params.append(evidence_id)

        if browser_family and browser_family != "all":
            base_where += " AND browser_family = ?"
            params.append(browser_family)

        if event_type and event_type != "all":
            base_where += " AND event_type = ?"
            params.append(event_type)

        if search_term and search_term.strip():
            base_where += " AND (url LIKE ? OR title LIKE ?)"
            term = f"%{search_term.strip()}%"
            params.extend([term, term])

        if start_utc:
            base_where += " AND normalized_utc >= ?"
            params.append(start_utc)

        if end_utc:
            base_where += " AND normalized_utc <= ?"
            params.append(end_utc)

        # Count total matching
        count_sql = f"SELECT COUNT(*) FROM events {base_where};"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        # Fetch page sorted chronologically
        query_sql = f"""
            SELECT * FROM events
            {base_where}
            ORDER BY
                CASE WHEN normalized_utc IS NULL THEN 1 ELSE 0 END,
                normalized_utc ASC,
                id ASC
            LIMIT ? OFFSET ?;
        """
        cursor.execute(query_sql, params + [limit, offset])
        rows = cursor.fetchall()
        events = [row_to_event(r) for r in rows]
        return events, total_count
    finally:
        conn.close()

def get_timeline_breakdown(case_id: str) -> dict[str, Any]:
    """Get event count breakdown by browser family and event type."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT browser_family, COUNT(*) FROM events WHERE case_id = ? GROUP BY browser_family;",
            (case_id,)
        )
        browser_counts = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute(
            "SELECT event_type, COUNT(*) FROM events WHERE case_id = ? GROUP BY event_type;",
            (case_id,)
        )
        type_counts = {r[0]: r[1] for r in cursor.fetchall()}

        return {
            "by_browser": browser_counts,
            "by_type": type_counts
        }
    finally:
        conn.close()
