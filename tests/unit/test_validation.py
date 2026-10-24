"""
Unit tests for known-answer validation engine.
"""

import tempfile
from pathlib import Path

import pytest

from forenx.cases import create_case
from forenx.config import ForenXConfig, set_config
from forenx.database import init_db
from forenx.models import Event
from forenx.validation import evaluate_validation
from tests.fixtures.synthetic_data import get_ground_truth_manifest


@pytest.fixture(autouse=True)
def setup_test_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ForenXConfig(data_dir=Path(tmpdir))
        set_config(cfg)
        init_db()
        yield

def test_validation_all_match_100_percent():
    case = create_case("Validation Test Case")
    manifest = get_ground_truth_manifest()

    # Create matching events
    actual_events = [
        Event(
            id=f"evt_{i}",
            case_id=case.id,
            evidence_id="evi_1",
            analysis_run_id="run_1",
            browser_family=item["browser_family"],
            event_type=item["event_type"],
            url=item["url"],
            title=item.get("title") or "",
            raw_timestamp=0,
            timestamp_format="test",
            normalized_utc=item.get("expected_utc"),
            conversion_status="success",
            source_database="test.db",
            source_table="test_tbl",
            source_record_id=str(i),
            parser_version="1.0"
        )
        for i, item in enumerate(manifest)
    ]

    res = evaluate_validation(case.id, manifest, actual_events)
    assert res.matched_count == len(manifest)
    assert res.missing_count == 0
    assert res.unexpected_count == 0
    assert res.precision == 1.0
    assert res.recall == 1.0
    assert res.precision_display == "100.0%"
    assert res.recall_display == "100.0%"

def test_validation_missing_and_unexpected():
    case = create_case("Validation Incomplete Case")
    manifest = get_ground_truth_manifest()

    # Omit the first expected event (simulates missing record)
    # Add an extra unexpected event
    actual_events = [
        Event(
            id=f"evt_{i}",
            case_id=case.id,
            evidence_id="evi_1",
            analysis_run_id="run_1",
            browser_family=item["browser_family"],
            event_type=item["event_type"],
            url=item["url"],
            title=item.get("title") or "",
            raw_timestamp=0,
            timestamp_format="test",
            normalized_utc=item.get("expected_utc"),
            conversion_status="success",
            source_database="test.db",
            source_table="test_tbl",
            source_record_id=str(i),
            parser_version="1.0"
        )
        for i, item in enumerate(manifest[1:])  # drop index 0
    ]

    # Add unexpected event
    actual_events.append(Event(
        id="evt_unexpected",
        case_id=case.id,
        evidence_id="evi_1",
        analysis_run_id="run_1",
        browser_family="Chromium",
        event_type="url_visit",
        url="https://unexpected.example.org",
        title="Unexpected Page",
        raw_timestamp=0,
        timestamp_format="test",
        normalized_utc="2026-10-15T10:00:00+00:00",
        conversion_status="success",
        source_database="test.db",
        source_table="test_tbl",
        source_record_id="999",
        parser_version="1.0"
    ))

    res = evaluate_validation(case.id, manifest, actual_events)
    assert res.missing_count == 1
    assert res.unexpected_count == 1
    assert res.recall < 1.0
    assert res.precision < 1.0

def test_validation_zero_denominators_give_na():
    case = create_case("Zero Denominator Case")
    # Empty expected and empty actual
    res = evaluate_validation(case.id, [], [])
    assert res.precision is None
    assert res.recall is None
    assert res.precision_display == "N/A"
    assert res.recall_display == "N/A"
