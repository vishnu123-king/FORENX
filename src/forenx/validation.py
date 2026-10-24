"""
Known-Answer Validation Engine for ForenX.
Implements the core academic research contribution: reproducible validation of
extracted browser artifacts against ground-truth expected test manifests.
Calculates Precision, Recall, Field Mismatches, Missing and Unexpected records.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from forenx.audit import log_audit
from forenx.database import get_db_connection
from forenx.models import Event, generate_id, utc_now_iso


@dataclass
class ExpectedEvent:
    browser_family: str
    event_type: str
    url: str
    title: str | None = None
    expected_utc: str | None = None
    test_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExpectedEvent:
        return cls(
            browser_family=data.get("browser_family", "Chromium"),
            event_type=data.get("event_type", "url_visit"),
            url=data.get("url", ""),
            title=data.get("title"),
            expected_utc=data.get("expected_utc") or data.get("normalized_utc"),
            test_id=data.get("test_id")
        )

@dataclass
class ValidationDetail:
    matched_records: list[dict[str, Any]] = field(default_factory=list)
    missing_records: list[dict[str, Any]] = field(default_factory=list)
    unexpected_records: list[dict[str, Any]] = field(default_factory=list)
    field_mismatches: list[dict[str, Any]] = field(default_factory=list)
    timestamp_errors_seconds: list[float] = field(default_factory=list)

@dataclass
class ValidationSummaryResult:
    validation_run_id: str
    case_id: str
    dataset_version: str
    expected_count: int
    extracted_count: int
    matched_count: int
    missing_count: int
    unexpected_count: int
    precision: float | None
    recall: float | None
    precision_display: str
    recall_display: str
    mean_timestamp_error_seconds: float | None
    summary_text: str
    details: ValidationDetail

def evaluate_validation(
    case_id: str,
    expected_manifest: list[dict[str, Any]],
    actual_events: list[Event],
    dataset_version: str = "synthetic-v1.0",
    timestamp_tolerance_seconds: float = 2.0
) -> ValidationSummaryResult:
    """
    Compare extracted events against expected ground-truth records.
    Uses composite key: (browser_family.lower(), event_type.lower(), url.strip().lower())
    Evaluates:
    - Correct matches
    - Missing expected events
    - Unexpected extracted events
    - Field mismatches (title, timestamp within tolerance)
    - Precision and Recall with safe zero-denominator handling.
    """
    expected_objs = [ExpectedEvent.from_dict(item) for item in expected_manifest]

    # Map actual events by composite key
    # Key: (browser_family, event_type, normalized_url)
    def make_key(browser: str, etype: str, url: str) -> str:
        return f"{browser.lower()}|{etype.lower()}|{url.strip().lower().rstrip('/')}"

    # Group actual events
    actual_by_key: dict[str, list[Event]] = {}
    for ev in actual_events:
        k = make_key(ev.browser_family, ev.event_type, ev.url)
        actual_by_key.setdefault(k, []).append(ev)

    # Track matches
    matched_actual_ids = set()
    matched_records = []
    missing_records = []
    field_mismatches = []
    ts_errors = []

    for exp in expected_objs:
        k = make_key(exp.browser_family, exp.event_type, exp.url)
        candidates = actual_by_key.get(k, [])

        # Find first unmatched candidate
        chosen_candidate = None
        for cand in candidates:
            if cand.id not in matched_actual_ids:
                chosen_candidate = cand
                break

        if chosen_candidate is not None:
            matched_actual_ids.add(chosen_candidate.id)
            matched_records.append({
                "expected": asdict(exp),
                "actual_id": chosen_candidate.id,
                "url": chosen_candidate.url
            })

            # Check title field match if expected title is given
            if exp.title is not None and chosen_candidate.title is not None:
                if exp.title.strip().lower() != chosen_candidate.title.strip().lower():
                    field_mismatches.append({
                        "event_id": chosen_candidate.id,
                        "url": chosen_candidate.url,
                        "field": "title",
                        "expected": exp.title,
                        "actual": chosen_candidate.title
                    })

            # Check timestamp tolerance if both ISO dates available
            if exp.expected_utc and chosen_candidate.normalized_utc:
                try:
                    exp_dt = datetime.fromisoformat(exp.expected_utc)
                    act_dt = datetime.fromisoformat(chosen_candidate.normalized_utc)
                    diff = abs((act_dt - exp_dt).total_seconds())
                    ts_errors.append(diff)
                    if diff > timestamp_tolerance_seconds:
                        field_mismatches.append({
                            "event_id": chosen_candidate.id,
                            "url": chosen_candidate.url,
                            "field": "normalized_utc",
                            "expected": exp.expected_utc,
                            "actual": chosen_candidate.normalized_utc,
                            "difference_seconds": round(diff, 3)
                        })
                except Exception:
                    pass
        else:
            missing_records.append(asdict(exp))

    # Unexpected events are extracted events that did not match any expected item
    unexpected_records = [
        {
            "id": ev.id,
            "browser_family": ev.browser_family,
            "event_type": ev.event_type,
            "url": ev.url,
            "title": ev.title,
            "normalized_utc": ev.normalized_utc
        }
        for ev in actual_events
        if ev.id not in matched_actual_ids
    ]

    expected_count = len(expected_objs)
    extracted_count = len(actual_events)
    matched_count = len(matched_records)
    missing_count = len(missing_records)
    unexpected_count = len(unexpected_records)

    # Precision = correctly matched extracted events / all extracted events
    if extracted_count > 0:
        precision = round(matched_count / extracted_count, 4)
        precision_display = f"{precision * 100:.1f}%"
    else:
        precision = None
        precision_display = "N/A"

    # Recall = correctly matched expected events / all expected events
    if expected_count > 0:
        recall = round(matched_count / expected_count, 4)
        recall_display = f"{recall * 100:.1f}%"
    else:
        recall = None
        recall_display = "N/A"

    mean_ts_err = round(sum(ts_errors) / len(ts_errors), 4) if ts_errors else None

    summary_text = (
        f"Validation Run ({dataset_version}): {matched_count}/{expected_count} expected events matched. "
        f"Precision: {precision_display}, Recall: {recall_display}. "
        f"Missing: {missing_count}, Unexpected: {unexpected_count}, Field mismatches: {len(field_mismatches)}."
    )

    detail_obj = ValidationDetail(
        matched_records=matched_records,
        missing_records=missing_records,
        unexpected_records=unexpected_records,
        field_mismatches=field_mismatches,
        timestamp_errors_seconds=ts_errors
    )

    run_id = generate_id("val")
    summary_result = ValidationSummaryResult(
        validation_run_id=run_id,
        case_id=case_id,
        dataset_version=dataset_version,
        expected_count=expected_count,
        extracted_count=extracted_count,
        matched_count=matched_count,
        missing_count=missing_count,
        unexpected_count=unexpected_count,
        precision=precision,
        recall=recall,
        precision_display=precision_display,
        recall_display=recall_display,
        mean_timestamp_error_seconds=mean_ts_err,
        summary_text=summary_text,
        details=detail_obj
    )

    # Persist in validation_runs table
    conn = get_db_connection()
    try:
        with conn:
            details_serialized = json.dumps(asdict(detail_obj))
            now = utc_now_iso()
            conn.execute(
                """
                INSERT INTO validation_runs (
                    id, case_id, created_at, dataset_version, expected_count,
                    extracted_count, matched_count, missing_count, unexpected_count,
                    precision, recall, result_summary, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (run_id, case_id, now, dataset_version, expected_count,
                 extracted_count, matched_count, missing_count, unexpected_count,
                 precision, recall, summary_text, details_serialized)
            )
            log_audit(
                operation="validation_executed",
                case_id=case_id,
                outcome="success" if missing_count == 0 and len(field_mismatches) == 0 else "warning",
                details=summary_text,
                conn=conn
            )
    finally:
        conn.close()

    return summary_result

def list_validation_runs(case_id: str) -> list[dict[str, Any]]:
    """Retrieve validation run history for a case."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM validation_runs WHERE case_id = ? ORDER BY created_at DESC;",
            (case_id,)
        )
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "case_id": r["case_id"],
                "created_at": r["created_at"],
                "dataset_version": r["dataset_version"],
                "expected_count": r["expected_count"],
                "extracted_count": r["extracted_count"],
                "matched_count": r["matched_count"],
                "missing_count": r["missing_count"],
                "unexpected_count": r["unexpected_count"],
                "precision": r["precision"],
                "recall": r["recall"],
                "result_summary": r["result_summary"],
                "details": json.loads(r["details_json"]) if r["details_json"] else {}
            })
        return results
    finally:
        conn.close()
