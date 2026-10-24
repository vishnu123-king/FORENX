"""
Unit tests for cryptographically chained tamper-evident audit logging.
"""

import tempfile
from pathlib import Path

import pytest

from forenx.audit import get_audit_entries, log_audit, verify_audit_chain
from forenx.config import ForenXConfig, set_config
from forenx.database import get_db_connection, init_db


@pytest.fixture(autouse=True)
def setup_test_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ForenXConfig(data_dir=Path(tmpdir))
        set_config(cfg)
        init_db()
        yield

def test_audit_log_chain_integrity():
    log_audit("case_created", case_id="case_1", details="Created case 1")
    log_audit("evidence_imported", case_id="case_1", details="Imported evidence 1")
    log_audit("analysis_completed", case_id="case_1", details="Finished analysis")

    entries = get_audit_entries("case_1")
    assert len(entries) == 3

    # Verify cryptographic chain
    is_intact, errors = verify_audit_chain()
    assert is_intact is True
    assert len(errors) == 0

def test_audit_tampering_detected():
    log_audit("op_1", details="Record 1")
    log_audit("op_2", details="Record 2")
    log_audit("op_3", details="Record 3")

    # Manually tamper with an entry in the database directly
    conn = get_db_connection()
    with conn:
        conn.execute("UPDATE audit_entries SET details = 'TAMPERED_DETAILS' WHERE operation = 'op_2';")
    conn.close()

    is_intact, errors = verify_audit_chain()
    assert is_intact is False
    assert len(errors) > 0
    assert any("Hash mismatch" in err or "Chain break" in err for err in errors)
