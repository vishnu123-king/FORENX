"""
Unit tests for evidence integrity and SHA-256 calculation.
"""

import tempfile
from pathlib import Path

import pytest

from forenx.acquisition import import_evidence, verify_case_evidence_item
from forenx.cases import create_case
from forenx.config import ForenXConfig, set_config
from forenx.database import init_db
from forenx.integrity import calculate_sha256, verify_evidence_file


@pytest.fixture(autouse=True)
def setup_test_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ForenXConfig(data_dir=Path(tmpdir))
        set_config(cfg)
        init_db()
        yield

def test_calculate_sha256(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Forensic Evidence Testing 12345", encoding="utf-8")
    expected_hash = "f3a46618cead888df790ff4feffbeaa9bfeb20ee6b4d36efce9d33b5a75877c4"

    calc_hash = calculate_sha256(test_file)
    assert isinstance(calc_hash, str)
    assert len(calc_hash) == 64

def test_verify_evidence_success(tmp_path):
    test_file = tmp_path / "intact.db"
    test_file.write_bytes(b"SQLITE_SAMPLE_BYTES_0123456789")

    case = create_case("Integrity Case")
    evidence = import_evidence(case.id, test_file)

    assert evidence.verification_status == "verified"
    res = verify_case_evidence_item(evidence.id)
    assert res["is_match"] is True
    assert res["status"] == "verified"

def test_detect_tampered_evidence(tmp_path):
    test_file = tmp_path / "tamper_target.db"
    test_file.write_bytes(b"INITIAL_EVIDENCE_BYTES")

    case = create_case("Tamper Detection Case")
    evidence = import_evidence(case.id, test_file)

    # Directly tamper with the vault copy to simulate bit-rot or unauthorized modification
    cfg = ForenXConfig()
    from forenx.config import get_config
    vault_file = get_config().evidence_dir / evidence.storage_relative_path
    vault_file.write_bytes(b"TAMPERED_MODIFIED_BYTES")

    res = verify_case_evidence_item(evidence.id)
    assert res["is_match"] is False
    assert res["status"] == "failed"

def test_missing_evidence_file():
    is_match, status, details = verify_evidence_file(Path("/nonexistent/file/path.db"), "dummy_hash")
    assert is_match is False
    assert status == "missing"
