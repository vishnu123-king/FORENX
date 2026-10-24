"""
Unit tests for Firefox places.sqlite artifact parser.
"""


import pytest

from forenx.exceptions import UnsupportedSchemaError
from forenx.parsers.firefox import FirefoxPlacesParser
from tests.fixtures.synthetic_data import create_synthetic_firefox_db


def test_parse_valid_firefox_db(tmp_path):
    db_path = tmp_path / "places.sqlite"
    create_synthetic_firefox_db(db_path)

    parser = FirefoxPlacesParser()
    result = parser.parse(db_path, case_id="c", evidence_id="e", analysis_run_id="r")

    assert result.parser_name == "FirefoxPlacesParser"
    assert result.records_extracted == 3  # 2 visits + 1 bookmark
    assert len(result.events) == 3

    visits = [ev for ev in result.events if ev.event_type == "url_visit"]
    assert len(visits) == 2
    assert any("wireshark" in v.url for v in visits)

    bookmarks = [ev for ev in result.events if ev.event_type == "bookmark"]
    assert len(bookmarks) == 1
    assert "sqlite3 Python Documentation Bookmark" == bookmarks[0].title

def test_parse_missing_moz_places_raises_unsupported(tmp_path):
    db_path = tmp_path / "places_invalid.sqlite"
    create_synthetic_firefox_db(db_path, anomaly="missing_table")

    parser = FirefoxPlacesParser()
    with pytest.raises(UnsupportedSchemaError):
        parser.parse(db_path, case_id="c", evidence_id="e", analysis_run_id="r")
