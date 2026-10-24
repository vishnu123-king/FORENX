"""
Unit tests for report generation and safe HTML escaping.
"""

import json
import tempfile
from pathlib import Path

import pytest

from forenx.cases import create_case
from forenx.config import ForenXConfig, set_config
from forenx.database import init_db
from forenx.reporting import export_case_html, export_case_json, export_timeline_csv


@pytest.fixture(autouse=True)
def setup_test_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ForenXConfig(data_dir=Path(tmpdir))
        set_config(cfg)
        init_db()
        yield

def test_html_report_escaping_xss_protection():
    # Attempt XSS payload in case name and investigator
    case = create_case(
        name="<script>alert('xss')</script> Investigation",
        description="<b>Bold Attempt</b> & <img src=x onerror=alert(1)>",
        investigator_label="Inv. <style>body{color:red}</style>"
    )

    html = export_case_html(case.id)
    # Ensure raw unescaped script tag is NOT in the HTML
    assert "<script>alert('xss')</script>" not in html
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html
    assert "<img src=x onerror=alert(1)>" not in html

def test_json_report_structure():
    case = create_case("JSON Test Case")
    json_str = export_case_json(case.id)
    data = json.loads(json_str)

    assert data["case"]["id"] == case.id
    assert "limitations_statement" in data
    assert "supported_scope" in data
    assert "forenx_version" in data

def test_csv_report_columns():
    case = create_case("CSV Test Case")
    csv_str = export_timeline_csv(case.id)
    lines = csv_str.strip().splitlines()
    header = lines[0]

    assert "Event ID" in header
    assert "Normalized UTC" in header
    assert "URL" in header
    assert "Source Record ID" in header
