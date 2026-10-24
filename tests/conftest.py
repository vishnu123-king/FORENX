"""
Pytest configuration and global fixtures for ForenX tests.
"""

import tempfile
from pathlib import Path
import pytest
from forenx.config import ForenXConfig, set_config
from forenx.database import init_db


@pytest.fixture(autouse=True)
def setup_test_env():
    """Ensure every test runs against a clean, isolated SQLite database in a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ForenXConfig(data_dir=Path(tmpdir))
        set_config(cfg)
        init_db()
        yield
