"""
Command-line interface and IPC bridge for ForenX.
Allows running forensic workflows from the terminal or orchestration scripts.
"""

import argparse
import json
from typing import Any

from forenx.acquisition import (
    import_evidence,
    verify_case_evidence_item,
)
from forenx.audit import verify_audit_chain
from forenx.cases import create_case, get_global_statistics, list_cases
from forenx.config import get_config
from forenx.database import init_db
from forenx.events import list_events
from forenx.reporting import (
    generate_case_report_bundle,
)
from forenx.services.analysis_service import run_case_analysis
from forenx.validation import evaluate_validation
from tests.fixtures.synthetic_data import (
    create_synthetic_chromium_db,
    create_synthetic_firefox_db,
    get_ground_truth_manifest,
)


def seed_synthetic_case(name: str = "SYNTHETIC DEMO: Cross-Browser Intrusion Investigation") -> dict[str, Any]:
    """
    Generate a complete, realistic synthetic demo case with Chromium History
    and Firefox places.sqlite artifacts, run analysis, perform validation, and export reports.
    """
    cfg = get_config()
    cfg.ensure_directories()
    init_db()

    case = create_case(
        name=name,
        description="Controlled forensic test dataset containing known Chromium and Firefox artifacts for known-answer validation.",
        investigator_label="Prof. A. Vance (ForenX Academic Evaluation)",
        notes="Synthetic test dataset generated for cross-browser timeline reconstruction and precision/recall evaluation."
    )

    demo_dir = cfg.data_dir / "synthetic_staging" / case.id
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Generate synthetic Chromium and Firefox databases
    chrome_db = demo_dir / "History"
    ff_db = demo_dir / "places.sqlite"
    create_synthetic_chromium_db(chrome_db)
    create_synthetic_firefox_db(ff_db)

    # Import evidence
    chrome_evi = import_evidence(
        case_id=case.id,
        source_file_path=chrome_db,
        acquisition_method="synthetic_controlled_generation",
        provenance_notes="Synthetic Chromium browser History database with 4 visit events and 1 download."
    )

    ff_evi = import_evidence(
        case_id=case.id,
        source_file_path=ff_db,
        acquisition_method="synthetic_controlled_generation",
        provenance_notes="Synthetic Mozilla Firefox places.sqlite database with 2 visit events and 1 bookmark."
    )

    # Verify evidence
    v_chrome = verify_case_evidence_item(chrome_evi.id)
    v_ff = verify_case_evidence_item(ff_evi.id)

    # Run Analysis
    run = run_case_analysis(case_id=case.id)

    # Run Validation against ground truth manifest
    events, _ = list_events(case_id=case.id, limit=500)
    ground_truth = get_ground_truth_manifest()
    val_res = evaluate_validation(
        case_id=case.id,
        expected_manifest=ground_truth,
        actual_events=events,
        dataset_version="synthetic-groundtruth-v1.0"
    )

    # Generate Reports
    reports = generate_case_report_bundle(case_id=case.id)

    return {
        "case_id": case.id,
        "case_name": case.name,
        "evidence_count": 2,
        "events_extracted": run.records_extracted,
        "warnings_count": run.warnings_count,
        "validation_precision": val_res.precision_display,
        "validation_recall": val_res.recall_display,
        "reports": reports
    }

def main():
    parser = argparse.ArgumentParser(description="ForenX Browser Forensics & Evidence Validation CLI")
    subparsers = parser.add_subparsers(dest="command")

    # init-db
    subparsers.add_parser("init-db", help="Initialize the ForenX SQLite database schema")

    # seed-demo
    subparsers.add_parser("seed-demo", help="Seed complete synthetic test case and run analysis")

    # list-cases
    subparsers.add_parser("list-cases", help="List all investigation cases")

    # verify-chain
    subparsers.add_parser("verify-chain", help="Verify the cryptographic audit log chain")

    # stats
    subparsers.add_parser("stats", help="Get application-wide statistics")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
        print("Database schema successfully initialized.")
    elif args.command == "seed-demo":
        res = seed_synthetic_case()
        print(f"Synthetic demo case created: {res['case_id']}")
        print(f"Events extracted: {res['events_extracted']}")
        print(f"Validation Precision: {res['validation_precision']}, Recall: {res['validation_recall']}")
        print(f"HTML Report: {res['reports']['html_path']}")
    elif args.command == "list-cases":
        cases = list_cases()
        print(f"Found {len(cases)} cases:")
        for c in cases:
            print(f"- [{c.id}] {c.name} ({c.status}) - {c.created_at}")
    elif args.command == "verify-chain":
        valid, errors = verify_audit_chain()
        if valid:
            print("Audit log cryptographic chain is intact (VERIFIED).")
        else:
            print(f"Audit chain verification FAILED with {len(errors)} error(s):")
            for err in errors:
                print(f"  * {err}")
    elif args.command == "stats":
        stats = get_global_statistics()
        print(json.dumps(stats, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
