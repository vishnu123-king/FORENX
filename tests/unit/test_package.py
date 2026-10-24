"""
Unit tests for ForenX Evidence Package format (FX-ACQ-*.forenx.zip).
Covers package generation, manifest validation, path traversal defense, and integrity checks.
"""

import json
import pytest
import zipfile
from pathlib import Path
from forenx.evidence.package import (
    create_evidence_package,
    import_and_verify_package,
    inspect_package,
    validate_archive_member_path
)
from forenx.exceptions import SecurityViolationError, IntegrityVerificationError
from forenx.cases import create_case


def test_validate_archive_member_path_safe():
    validate_archive_member_path("manifest.json")
    validate_archive_member_path("artifacts/profile-1/History")
    validate_archive_member_path("artifacts/default/places.sqlite")


def test_validate_archive_member_path_traversal_rejected():
    with pytest.raises(SecurityViolationError):
        validate_archive_member_path("../etc/passwd")

    with pytest.raises(SecurityViolationError):
        validate_archive_member_path("artifacts/../../secrets.txt")


def test_validate_archive_member_path_absolute_rejected():
    with pytest.raises(SecurityViolationError):
        validate_archive_member_path("/root/.ssh/id_rsa")

    with pytest.raises(SecurityViolationError):
        validate_archive_member_path("~/.bashrc")


def test_create_and_import_evidence_package(tmp_path: Path):
    # Setup case
    test_case = create_case("Package Ingestion Test Case")

    # Create dummy artifact file
    artifact_file = tmp_path / "History"
    artifact_file.write_bytes(b"SQLite format 3\x00\x10\x00\x01\x01testdataforforenx")

    artifacts = [{
        "file_path": str(artifact_file),
        "artifact_type": "History",
        "browser_family": "Chromium",
        "profile_label": "Default"
    }]

    # Create package
    pkg_path, outer_sha256, pkg_model = create_evidence_package(
        case_id=test_case.id,
        acquisition_id="acq-test-001",
        acquisition_method="local_snapshot",
        artifacts=artifacts,
        output_directory=tmp_path / "out",
        investigator_label="Examiner A",
        provenance_notes="Test package creation"
    )

    assert pkg_path.exists()
    assert pkg_path.name.startswith("FX-ACQ-")
    assert pkg_path.name.endswith(".forenx.zip")
    assert len(outer_sha256) == 64

    # Inspect package manifest
    manifest = inspect_package(pkg_path)
    assert manifest["package_id"].startswith("FX-ACQ-")
    assert manifest["manifest_version"] == "1.0.0"
    assert len(manifest["artifacts"]) >= 1

    # Import package into case
    imported_model, evis, verif = import_and_verify_package(
        case_id=test_case.id,
        zip_path=pkg_path,
        expected_package_sha256=outer_sha256
    )

    assert imported_model.verification_status == "verified"
    assert len(evis) == 1
    assert evis[0].verification_status == "verified"
    assert verif["verification_status"] == "verified"
    assert verif["artifacts_verified_count"] == 1
    assert len(verif["failures"]) == 0


def test_tampered_package_detection(tmp_path: Path):
    test_case = create_case("Tamper Test Case")

    artifact_file = tmp_path / "places.sqlite"
    artifact_file.write_bytes(b"SQLite format 3\x00moz_places_dummy_data")

    artifacts = [{
        "file_path": str(artifact_file),
        "artifact_type": "places.sqlite",
        "browser_family": "Firefox",
        "profile_label": "default-release"
    }]

    pkg_path, outer_sha256, _ = create_evidence_package(
        case_id=test_case.id,
        acquisition_id="acq-test-002",
        acquisition_method="offline_field_collector",
        artifacts=artifacts,
        output_directory=tmp_path / "out2"
    )

    # Provide altered expected SHA256
    bogus_sha256 = "0" * 64
    with pytest.raises(IntegrityVerificationError):
        import_and_verify_package(
            case_id=test_case.id,
            zip_path=pkg_path,
            expected_package_sha256=bogus_sha256
        )
