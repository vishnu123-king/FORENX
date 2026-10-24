"""
Unit tests for Chromium History artifact parser.
"""


import pytest

from forenx.exceptions import CorruptDatabaseError, UnsupportedSchemaError
from forenx.parsers.chromium import ChromiumHistoryParser
from tests.fixtures.synthetic_data import create_synthetic_chromium_db


def test_parse_valid_chromium_db(tmp_path):
    db_path = tmp_path / "History"
    create_synthetic_chromium_db(db_path)

    parser = ChromiumHistoryParser()
    result = parser.parse(db_path, case_id="test_case", evidence_id="test_evi", analysis_run_id="test_run")

    assert result.parser_name == "ChromiumHistoryParser"
    assert result.records_seen == 5  # 4 visits + 1 download
    assert result.records_extracted == 5
    assert len(result.events) == 5

    # Check visit fields
    visits = [e for e in result.events if e.event_type == "url_visit"]
    assert len(visits) == 4
    urls = [v.url for v in visits]
    assert "https://en.wikipedia.org/wiki/Digital_forensics" in urls

    # Check download
    downloads = [e for e in result.events if e.event_type == "download"]
    assert len(downloads) == 1
    assert downloads[0].title == "nist_test_image.dd"
    assert downloads[0].extra_metadata["state"] == "COMPLETE"

def test_parse_missing_table_raises_unsupported_schema(tmp_path):
    db_path = tmp_path / "History_NoVisits"
    create_synthetic_chromium_db(db_path, anomaly="missing_table")

    parser = ChromiumHistoryParser()
    with pytest.raises(UnsupportedSchemaError):
        parser.parse(db_path, case_id="c", evidence_id="e", analysis_run_id="r")

def test_parse_corrupt_file_raises_error(tmp_path):
    db_path = tmp_path / "History_Corrupt"
    create_synthetic_chromium_db(db_path, anomaly="corrupt_file")

    parser = ChromiumHistoryParser()
    with pytest.raises(CorruptDatabaseError):
        parser.parse(db_path, case_id="c", evidence_id="e", analysis_run_id="r")

def test_parse_invalid_timestamp_warning(tmp_path):
    db_path = tmp_path / "History_InvalidTS"
    create_synthetic_chromium_db(db_path, anomaly="invalid_timestamp")

    parser = ChromiumHistoryParser()
    result = parser.parse(db_path, case_id="c", evidence_id="e", analysis_run_id="r")
    assert result.records_extracted >= 1
    assert len(result.warnings) > 0
