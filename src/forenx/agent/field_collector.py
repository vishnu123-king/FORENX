"""
ForenX Offline Field Collector.
Runs locally on client laptops (Windows / Linux) to discover browser profiles,
acquire allowlisted artifacts into a verifiable FX-ACQ-*.forenx.zip package,
and calculate custody SHA-256 hashes without requiring network access.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Add src to path if run as standalone script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from forenx.discovery.browser_discovery import discover_local_browsers, snapshot_sqlite_online
from forenx.evidence.package import create_evidence_package
from forenx.models import generate_id, utc_now_iso


def run_field_collection(
    output_dir: Path,
    case_id: str = "FIELD_ACQUISITION",
    investigator_label: str = "Field Examiner",
    notes: str = "Offline field collection"
) -> dict[str, Any]:
    """Execute offline collection and return summary with custody hashes."""
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    profiles = discover_local_browsers()
    if not profiles:
        print("[!] No supported browser profiles detected on this machine.")
        return {"status": "empty", "message": "No browser profiles detected."}

    print(f"[*] Discovered {len(profiles)} browser profile(s):")
    artifacts_for_package = []

    staging_dir = out_path / f"staging_{generate_id()}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        for p in profiles:
            print(f"  -> {p.profile_label}: {len(p.available_artifacts)} artifact(s)")
            for art in p.available_artifacts:
                src_p = Path(art["file_path"])
                dest_f = staging_dir / f"{p.profile_id}_{src_p.name}"

                try:
                    snapshot_sqlite_online(src_p, dest_f)
                except Exception:
                    shutil.copy2(src_p, dest_f)

                # Copy WAL sidecars if present
                for sfx in ["-wal", "-shm"]:
                    s_file = src_p.parent / f"{src_p.name}{sfx}"
                    if s_file.exists():
                        shutil.copy2(s_file, staging_dir / f"{dest_f.name}{sfx}")

                artifacts_for_package.append({
                    "file_path": str(dest_f),
                    "browser_name": p.browser_name,
                    "browser_family": p.browser_family,
                    "profile_label": p.profile_label,
                    "artifact_type": art["artifact_type"]
                })

        # Build portable package
        zip_path, package_hash, pkg_model = create_evidence_package(
            case_id=case_id,
            acquisition_id=generate_id("field"),
            acquisition_method="offline_field_collector",
            artifacts=artifacts_for_package,
            output_directory=out_path,
            investigator_label=investigator_label,
            provenance_notes=notes
        )

        print(f"[+] Evidence Package successfully generated:")
        print(f"    File:    {zip_path.name}")
        print(f"    Path:    {zip_path}")
        print(f"    SHA-256: {package_hash}")
        print(f"    Items:   {len(artifacts_for_package)} artifacts")

        return {
            "status": "success",
            "package_path": str(zip_path),
            "package_filename": zip_path.name,
            "package_sha256": package_hash,
            "artifacts_collected": len(artifacts_for_package)
        }

    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="ForenX Portable Offline Field Collector")
    parser.add_argument("--out", "-o", default="./forenx_output", help="Output directory for evidence package")
    parser.add_argument("--case", "-c", default="FIELD_CASE_01", help="Case identifier")
    parser.add_argument("--examiner", "-e", default="Field Analyst", help="Investigator name")
    parser.add_argument("--notes", "-n", default="Offline Field Collection", help="Acquisition notes")

    args = parser.parse_args()
    run_field_collection(
        output_dir=Path(args.out),
        case_id=args.case,
        investigator_label=args.examiner,
        notes=args.notes
    )


if __name__ == "__main__":
    main()
