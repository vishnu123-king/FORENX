"""
End-to-end integration test for ForenX forensic workflow.
Tests: Case Creation -> Evidence Import -> SHA-256 Verification ->
       Analysis Orchestration -> Event Extraction -> Known-Answer Validation ->
       Reporting -> Audit Verification.
"""

import tempfile
from pathlib import Path

import pytest

from forenx.acquisition import (
    import_evidence,
    verify_case_evidence_item,
)
from forenx.audit import verify_audit_chain
from forenx.cases import create_case
from forenx.config import ForenXConfig, set_config
from forenx.database import init_db
from forenx.events import list_events
from forenx.reporting import generate_case_report_bundle
from forenx.services.analysis_service import run_case_analysis
from forenx.validation import evaluate_validation
from tests.fixtures.synthetic_data import (
    create_synthetic_chromium_db,
    create_synthetic_firefox_db,
    get_ground_truth_manifest,
)


@pytest.fixture(autouse=True)
def setup_test_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ForenXConfig(data_dir=Path(tmpdir))
        set_config(cfg)
        init_db()
        yield

def test_full_cross_browser_forensic_workflow(tmp_path):
    # 1. Create Case
    case = create_case(
        name="Academic Benchmark Case",
        description="Full verification of cross-browser extraction and traceability",
        investigator_label="Lead Forensics Specialist"
    )

    # 2. Prepare synthetic Chromium & Firefox databases
    chrome_src = tmp_path / "History"
    ff_src = tmp_path / "places.sqlite"
    create_synthetic_chromium_db(chrome_src)
    create_synthetic_firefox_db(ff_src)

    # 3. Import Evidence into Vault (non-destructive copy, records SHA-256)
    evi_chrome = import_evidence(case.id, chrome_src, provenance_notes="Synthetic Chrome profile")
    evi_ff = import_evidence(case.id, ff_src, provenance_notes="Synthetic Firefox profile")

    assert evi_chrome.verification_status == "verified"
    assert evi_ff.verification_status == "verified"

    # 4. Verify Integrity against recorded SHA-256
    v1 = verify_case_evidence_item(evi_chrome.id)
    v2 = verify_case_evidence_item(evi_ff.id)
    assert v1["is_match"] is True
    assert v2["is_match"] is True

    # 5. Execute Analysis Orchestration
    run = run_case_analysis(case.id)
    assert run.status == "completed"
    assert run.records_extracted == 8  # 5 Chrome (4 visits+1 DL) + 3 Firefox (2 visits+1 BM)
    assert run.warnings_count == 0

    # 6. Query Timeline
    events, count = list_events(case.id, limit=100)
    assert count == 8
    assert len(events) == 8

    # Verify source traceability
    for ev in events:
        assert ev.source_database in ["History", "places.sqlite"]
        assert ev.source_table != ""
        assert ev.source_record_id != ""
        assert ev.conversion_status == "success"
        assert ev.normalized_utc is not None

    # 7. Execute Known-Answer Validation Lab
    manifest = get_ground_truth_manifest()
    val_res = evaluate_validation(
        case_id=case.id,
        expected_manifest=manifest,
        actual_events=events,
        dataset_version="bench-1.0"
    )
    assert val_res.matched_count == 8
    assert val_res.missing_count == 0
    assert val_res.unexpected_count == 0
    assert val_res.precision == 1.0
    assert val_res.recall == 1.0

    # 8. Generate Reports (HTML, JSON, CSV)
    report_bundle = generate_case_report_bundle(case.id)
    assert Path(report_bundle["html_path"]).exists()
    assert Path(report_bundle["json_path"]).exists()
    assert Path(report_bundle["csv_path"]).exists()

    # 9. Verify Cryptographic Audit Log
    is_audit_valid, errors = verify_audit_chain()
    assert is_audit_valid is True
    assert len(errors) == 0
