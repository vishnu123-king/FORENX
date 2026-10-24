"""
JSON IPC Bridge for ForenX Express backend.
Translates API requests directly to ForenX Python core functions and returns JSON.
"""

import sys
import json
from pathlib import Path

# Add project root and src to path
sys.path.insert(0, str(Path(__file__).parent))

from forenx.config import get_config
from forenx.database import init_db
from forenx.cases import (
    create_case, list_cases, get_case, get_global_statistics, archive_case
)
from forenx.acquisition import (
    import_evidence, list_case_evidence, verify_case_evidence_item, get_evidence
)
from forenx.services.analysis_service import run_case_analysis, list_case_analysis_runs
from forenx.events import list_events, get_timeline_breakdown
from forenx.validation import evaluate_validation, list_validation_runs
from forenx.reporting import export_case_html, export_timeline_csv, export_case_json, build_case_report_data
from forenx.audit import get_audit_entries, verify_audit_chain
from forenx.cli import seed_synthetic_case
from tests.fixtures.synthetic_data import get_ground_truth_manifest
from forenx.discovery.browser_discovery import discover_local_browsers, acquire_selected_profiles
from forenx.evidence.package import list_evidence_packages, import_and_verify_package
from forenx.remote.endpoints import generate_enrollment_token, enroll_endpoint, list_endpoints, revoke_endpoint
from forenx.remote.jobs import create_acquisition_job, list_acquisition_jobs, get_acquisition_job, dispatch_and_complete_job

def handle_request(payload: dict) -> dict:
    cmd = payload.get("cmd")
    args = payload.get("args", {})

    init_db()

    if cmd == "stats":
        return {"status": "ok", "data": get_global_statistics()}

    elif cmd == "list_cases":
        status_filter = args.get("status")
        search = args.get("search")
        cases = list_cases(status_filter=status_filter, search_query=search)
        return {"status": "ok", "data": [c.to_dict() for c in cases]}

    elif cmd == "get_case":
        case_id = args.get("case_id")
        case = get_case(case_id)
        return {"status": "ok", "data": case.to_dict()}

    elif cmd == "create_case":
        case = create_case(
            name=args.get("name", "Untitled Case"),
            description=args.get("description", ""),
            investigator_label=args.get("investigator", ""),
            notes=args.get("notes", "")
        )
        return {"status": "ok", "data": case.to_dict()}

    elif cmd == "archive_case":
        case_id = args.get("case_id")
        case = archive_case(case_id)
        return {"status": "ok", "data": case.to_dict()}

    elif cmd == "list_evidence":
        case_id = args.get("case_id")
        items = list_case_evidence(case_id)
        return {"status": "ok", "data": [e.to_dict() for e in items]}

    elif cmd == "verify_evidence":
        evidence_id = args.get("evidence_id")
        res = verify_case_evidence_item(evidence_id)
        return {"status": "ok", "data": res}

    elif cmd == "import_file":
        case_id = args.get("case_id")
        src_path = Path(args.get("file_path"))
        notes = args.get("notes", "")
        evi = import_evidence(case_id=case_id, source_file_path=src_path, provenance_notes=notes)
        return {"status": "ok", "data": evi.to_dict()}

    elif cmd == "run_analysis":
        case_id = args.get("case_id")
        evidence_id = args.get("evidence_id")
        run = run_case_analysis(case_id=case_id, evidence_id=evidence_id)
        return {"status": "ok", "data": run.to_dict()}

    elif cmd == "list_analysis_runs":
        case_id = args.get("case_id")
        runs = list_case_analysis_runs(case_id)
        return {"status": "ok", "data": [r.to_dict() for r in runs]}

    elif cmd == "list_events":
        case_id = args.get("case_id")
        events, total = list_events(
            case_id=case_id,
            browser_family=args.get("browser"),
            event_type=args.get("event_type"),
            search_term=args.get("search"),
            limit=args.get("limit", 200),
            offset=args.get("offset", 0)
        )
        breakdown = get_timeline_breakdown(case_id)
        return {
            "status": "ok",
            "data": {
                "events": [ev.to_dict() for ev in events],
                "total_count": total,
                "breakdown": breakdown
            }
        }

    elif cmd == "run_validation":
        case_id = args.get("case_id")
        events, _ = list_events(case_id, limit=2000)
        manifest = get_ground_truth_manifest()
        val_res = evaluate_validation(
            case_id=case_id,
            expected_manifest=manifest,
            actual_events=events,
            dataset_version="synthetic-groundtruth-v1.0"
        )
        return {
            "status": "ok",
            "data": {
                "validation_run_id": val_res.validation_run_id,
                "precision": val_res.precision,
                "recall": val_res.recall,
                "precision_display": val_res.precision_display,
                "recall_display": val_res.recall_display,
                "expected_count": val_res.expected_count,
                "matched_count": val_res.matched_count,
                "missing_count": val_res.missing_count,
                "unexpected_count": val_res.unexpected_count,
                "summary": val_res.summary_text,
                "details": {
                    "field_mismatches": val_res.details.field_mismatches,
                    "missing_records": val_res.details.missing_records,
                    "unexpected_records": val_res.details.unexpected_records
                }
            }
        }

    elif cmd == "list_validations":
        case_id = args.get("case_id")
        runs = list_validation_runs(case_id)
        return {"status": "ok", "data": runs}

    elif cmd == "get_report_data":
        case_id = args.get("case_id")
        data = build_case_report_data(case_id)
        return {
            "status": "ok",
            "data": data,
            "html": export_case_html(case_id),
            "csv": export_timeline_csv(case_id),
            "json": export_case_json(case_id)
        }

    elif cmd == "get_audit":
        case_id = args.get("case_id")
        entries = get_audit_entries(case_id=case_id, limit=args.get("limit", 100))
        is_intact, errors = verify_audit_chain()
        return {
            "status": "ok",
            "data": {
                "entries": [e.to_dict() for e in entries],
                "chain_intact": is_intact,
                "chain_errors": errors
            }
        }

    elif cmd == "seed_demo":
        res = seed_synthetic_case()
        return {"status": "ok", "data": res}

    elif cmd == "settings":
        cfg = get_config()
        return {
            "status": "ok",
            "data": {
                "data_dir": str(cfg.data_dir),
                "evidence_dir": str(cfg.evidence_dir),
                "working_dir": str(cfg.working_dir),
                "reports_dir": str(cfg.reports_dir),
                "max_import_size_bytes": cfg.max_import_size_bytes,
                "display_timezone": cfg.display_timezone,
                "app_version": cfg.app_version
            }
        }

    elif cmd == "list_samples":
        return {
            "status": "ok",
            "data": {
                "samples": get_samples_manifest(),
                "os_paths": OS_BROWSER_PATHS
            }
        }

    elif cmd == "generate_sample":
        sample_id = args.get("sample_id", "chromium_history_sample")
        cfg = get_config()
        staging_dir = cfg.data_dir / "generated_samples"
        file_path = generate_sample_file(sample_id, staging_dir)
        return {
            "status": "ok",
            "data": {
                "file_path": str(file_path),
                "filename": file_path.name
            }
        }

    elif cmd == "acquire_sample":
        case_id = args.get("case_id")
        sample_id = args.get("sample_id", "chromium_history_sample")
        cfg = get_config()
        staging_dir = cfg.data_dir / "sample_staging" / case_id
        sample_file = generate_sample_file(sample_id, staging_dir)
        evi = import_evidence(
            case_id=case_id,
            source_file_path=sample_file,
            acquisition_method="synthetic_sample_library",
            provenance_notes=f"Sample evidence artifact '{sample_id}' generated by ForenX testing library."
        )
        return {"status": "ok", "data": evi.to_dict()}

    elif cmd == "discover_local":
        discovered = discover_local_browsers()
        return {"status": "ok", "data": [d.to_dict() for d in discovered]}

    elif cmd == "acquire_local":
        case_id = args.get("case_id")
        selected_profiles = args.get("profiles", [])
        inv = args.get("investigator", "Examiner")
        notes = args.get("notes", "Authorized local browser acquisition")
        res = acquire_selected_profiles(
            case_id=case_id,
            selected_profiles=selected_profiles,
            investigator_label=inv,
            notes=notes
        )
        return {"status": "ok", "data": res}

    elif cmd == "list_packages":
        case_id = args.get("case_id")
        pkgs = list_evidence_packages(case_id)
        return {"status": "ok", "data": [p.to_dict() for p in pkgs]}

    elif cmd == "import_package":
        case_id = args.get("case_id")
        pkg_path = Path(args.get("package_path"))
        expected_hash = args.get("expected_sha256")
        pkg_model, evis, verif = import_and_verify_package(
            case_id=case_id,
            zip_path=pkg_path,
            expected_package_sha256=expected_hash
        )
        return {
            "status": "ok",
            "data": {
                "package": pkg_model.to_dict(),
                "evidence_count": len(evis),
                "verification": verif
            }
        }

    elif cmd == "list_endpoints":
        endpoints = list_endpoints()
        return {"status": "ok", "data": [ep.to_dict() for ep in endpoints]}

    elif cmd == "create_enrollment_token":
        dev_label = args.get("device_label", "Workstation")
        os_name = args.get("operating_system", "linux")
        created_by = args.get("created_by", "Admin")
        tok = generate_enrollment_token(device_label=dev_label, operating_system=os_name, created_by=created_by)
        return {"status": "ok", "data": tok.to_dict()}

    elif cmd == "enroll_endpoint":
        token = args.get("token")
        cert = args.get("certificate_identity", "")
        ip = args.get("ip_address", "127.0.0.1")
        ep = enroll_endpoint(token=token, certificate_identity=cert, ip_address=ip)
        return {"status": "ok", "data": ep.to_dict()}

    elif cmd == "revoke_endpoint":
        ep_id = args.get("endpoint_id")
        success = revoke_endpoint(ep_id)
        return {"status": "ok", "data": {"revoked": success}}

    elif cmd == "list_jobs":
        case_id = args.get("case_id")
        ep_id = args.get("endpoint_id")
        jobs = list_acquisition_jobs(case_id=case_id, endpoint_id=ep_id)
        return {"status": "ok", "data": [j.to_dict() for j in jobs]}

    elif cmd == "create_job":
        case_id = args.get("case_id")
        ep_id = args.get("endpoint_id")
        inv = args.get("investigator", "Examiner")
        scope = args.get("scope", {})
        meta = args.get("metadata", {})
        job = create_acquisition_job(
            case_id=case_id,
            endpoint_id=ep_id,
            requesting_investigator_id=inv,
            authorized_scope=scope,
            authorization_metadata=meta
        )
        return {"status": "ok", "data": job.to_dict()}

    elif cmd == "execute_job":
        job_id = args.get("job_id")
        res = dispatch_and_complete_job(job_id)
        return {"status": "ok", "data": res}

    else:
        return {"status": "error", "message": f"Unknown command: {cmd}"}

def main():
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
    else:
        raw_input = sys.stdin.read()

    try:
        payload = json.loads(raw_input)
        resp = handle_request(payload)
    except Exception as e:
        resp = {"status": "error", "message": str(e)}

    print(json.dumps(resp))

if __name__ == "__main__":
    main()
