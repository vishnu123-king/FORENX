"""
Unit tests for ForenX case management.
"""

import tempfile
from pathlib import Path

import pytest

from forenx.cases import archive_case, create_case, get_case, list_cases, update_case
from forenx.config import ForenXConfig, set_config
from forenx.database import init_db
from forenx.exceptions import CaseNotFoundError


@pytest.fixture(autouse=True)
def setup_test_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ForenXConfig(data_dir=Path(tmpdir))
        set_config(cfg)
        init_db()
        yield

def test_create_and_retrieve_case():
    case = create_case(
        name="Operation Nightfall",
        description="Forensic investigation into unauthorized data access",
        investigator_label="Inv. Smith",
        notes="High priority"
    )
    assert case.id.startswith("case_")
    assert case.name == "Operation Nightfall"
    assert case.status == "active"

    retrieved = get_case(case.id)
    assert retrieved.id == case.id
    assert retrieved.name == "Operation Nightfall"
    assert retrieved.investigator_label == "Inv. Smith"

def test_create_case_empty_name_fails():
    with pytest.raises(ValueError):
        create_case(name="   ")

def test_get_nonexistent_case():
    with pytest.raises(CaseNotFoundError):
        get_case("case_nonexistent_9999")

def test_update_case_metadata():
    case = create_case(name="Preliminary Case")
    updated = update_case(case.id, name="Confirmed Case", status="archived", notes="Completed")
    assert updated.name == "Confirmed Case"
    assert updated.status == "archived"
    assert updated.notes == "Completed"

def test_archive_case():
    case = create_case(name="To Be Archived")
    archived = archive_case(case.id)
    assert archived.status == "archived"

def test_list_and_search_cases():
    create_case(name="Investigation Alpha", description="Malware incident")
    create_case(name="Investigation Beta", description="Data leak")
    create_case(name="Investigation Gamma", description="Malware analysis")

    all_cases = list_cases()
    assert len(all_cases) >= 3

    search_malware = list_cases(search_query="Malware")
    assert len(search_malware) == 2
