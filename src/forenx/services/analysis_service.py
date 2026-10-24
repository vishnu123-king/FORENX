"""
Analysis orchestration service for ForenX.
Dispatches parsers to controlled working copies, normalizes results,
persists events, and tracks analysis runs with audit logging.
"""

import json
import sqlite3
from pathlib import Path

from forenx.acquisition import get_evidence, get_working_copy_path, list_case_evidence
from forenx.audit import log_audit
from forenx.config import get_config
from forenx.database import get_db_connection
from forenx.exceptions import (
    CorruptDatabaseError,
    EvidenceError,
    UnsupportedSchemaError,
)
from forenx.models import AnalysisRun, Event, generate_id, utc_now_iso
from forenx.parsers.chromium import ChromiumHistoryParser
from forenx.parsers.firefox import FirefoxPlacesParser


def select_parser_for_evidence(evidence_type: str, working_path: Path):
    """
    Select appropriate browser parser based on evidence type or schema probe.
    """
    if evidence_type == "chromium_history":
        return ChromiumHistoryParser()
    if evidence_type == "firefox_places":
        return FirefoxPlacesParser()

    # Dynamic fallback probing
    try:
        conn = sqlite3.connect(f"file:{working_path.as_posix()}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {r[0].lower() for r in cursor.fetchall()}
        conn.close()

        if "moz_places" in tables:
            return FirefoxPlacesParser()
        if "urls" in tables and "visits" in tables:
            return ChromiumHistoryParser()
    except Exception:
        pass

    # Default to Chromium if uncertain
    return ChromiumHistoryParser()

def run_case_analysis(case_id: str, evidence_id: str | None = None) -> AnalysisRun:
    """
    Execute browser artifact extraction on evidence working copies for a case.
    Prevents alteration of source evidence and maintains complete traceability.
    """
    cfg = get_config()
    cfg.ensure_directories()

    evidence_items = [get_evidence(evidence_id)] if evidence_id else list_case_evidence(case_id)
    if not evidence_items:
        raise EvidenceError(f"No evidence items available to analyze for case '{case_id}'.")

    run_id = generate_id("run")
    now = utc_now_iso()
    parser_names = []

    analysis_run = AnalysisRun(
        id=run_id,
        case_id=case_id,
        started_at=now,
        status="running",
        parser_versions="ChromiumHistoryParser 1.0.0, FirefoxPlacesParser 1.0.0"
    )

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO analysis_runs (
                    id, case_id, started_at, status, parser_versions,
                    records_seen, records_extracted, records_skipped, warnings_count, error_summary
                ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, '');
                """,
                (analysis_run.id, analysis_run.case_id, analysis_run.started_at,
                 analysis_run.status, analysis_run.parser_versions)
            )
            log_audit(
                operation="analysis_started",
                case_id=case_id,
                outcome="success",
                details=f"Started analysis run '{run_id}' for {len(evidence_items)} evidence item(s).",
                conn=conn
            )

        total_seen = 0
        total_extracted = 0
        total_skipped = 0
        total_warnings = 0
        all_warnings = []
        extracted_events: list[Event] = []

        for item in evidence_items:
            working_copy = get_working_copy_path(item)
            if not working_copy.exists():
                all_warnings.append(f"Working copy for evidence '{item.filename}' ({item.id}) does not exist.")
                total_warnings += 1
                continue

            parser = select_parser_for_evidence(item.evidence_type, working_copy)
            if parser.name not in parser_names:
                parser_names.append(f"{parser.name} {parser.version}")

            try:
                parse_result = parser.parse(
                    db_path=working_copy,
                    case_id=case_id,
                    evidence_id=item.id,
                    analysis_run_id=run_id
                )
                total_seen += parse_result.records_seen
                total_extracted += parse_result.records_extracted
                total_skipped += parse_result.records_skipped
                total_warnings += len(parse_result.warnings)
                all_warnings.extend(parse_result.warnings)
                extracted_events.extend(parse_result.events)
            except (UnsupportedSchemaError, CorruptDatabaseError) as err:
                total_warnings += 1
                all_warnings.append(f"Parser error on '{item.filename}': {err!s}")
            except Exception as e:
                total_warnings += 1
                all_warnings.append(f"Unexpected parsing error on '{item.filename}': {e!s}")

        # Persist extracted events in a single transaction
        with conn:
            for ev in extracted_events:
                extra_str = json.dumps(ev.extra_metadata) if ev.extra_metadata else "{}"
                conn.execute(
                    """
                    INSERT INTO events (
                        id, case_id, evidence_id, analysis_run_id, browser_family,
                        event_type, url, title, raw_timestamp, timestamp_format,
                        normalized_utc, conversion_status, source_database, source_table,
                        source_record_id, parser_version, warning, extra_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (ev.id, ev.case_id, ev.evidence_id, ev.analysis_run_id, ev.browser_family,
                     ev.event_type, ev.url, ev.title, ev.raw_timestamp, ev.timestamp_format,
                     ev.normalized_utc, ev.conversion_status, ev.source_database, ev.source_table,
                     ev.source_record_id, ev.parser_version, ev.warning, extra_str)
                )

            finish_time = utc_now_iso()
            final_status = "completed_with_warnings" if total_warnings > 0 else "completed"
            summary_err = "; ".join(all_warnings[:5]) if all_warnings else ""
            if len(all_warnings) > 5:
                summary_err += f" (and {len(all_warnings) - 5} more warnings)"

            conn.execute(
                """
                UPDATE analysis_runs
                SET completed_at = ?, status = ?, parser_versions = ?,
                    records_seen = ?, records_extracted = ?, records_skipped = ?,
                    warnings_count = ?, error_summary = ?
                WHERE id = ?;
                """,
                (finish_time, final_status, ", ".join(parser_names) or analysis_run.parser_versions,
                 total_seen, total_extracted, total_skipped, total_warnings, summary_err, run_id)
            )

            log_audit(
                operation="analysis_completed",
                case_id=case_id,
                outcome="success" if final_status == "completed" else "warning",
                details=f"Analysis run '{run_id}' finished: {total_extracted} records extracted, {total_warnings} warnings.",
                conn=conn
            )

        analysis_run.completed_at = finish_time
        analysis_run.status = final_status
        analysis_run.records_seen = total_seen
        analysis_run.records_extracted = total_extracted
        analysis_run.records_skipped = total_skipped
        analysis_run.warnings_count = total_warnings
        analysis_run.error_summary = summary_err
        return analysis_run
    finally:
        conn.close()

def list_case_analysis_runs(case_id: str) -> list[AnalysisRun]:
    """Retrieve all analysis runs for a case."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_runs WHERE case_id = ? ORDER BY started_at DESC;", (case_id,))
        rows = cursor.fetchall()
        return [
            AnalysisRun(
                id=r["id"],
                case_id=r["case_id"],
                started_at=r["started_at"],
                completed_at=r["completed_at"],
                status=r["status"],
                parser_versions=r["parser_versions"],
                records_seen=r["records_seen"],
                records_extracted=r["records_extracted"],
                records_skipped=r["records_skipped"],
                warnings_count=r["warnings_count"],
                error_summary=r["error_summary"] or ""
            )
            for r in rows
        ]
    finally:
        conn.close()
