"""
Unit tests for ForenX Browser Discovery and Online Backup.
Covers inspect_chromium_profile, inspect_firefox_profile, and discover_local_browsers.
"""

import sqlite3
import pytest
from pathlib import Path
from forenx.discovery.browser_discovery import (
    inspect_chromium_profile,
    inspect_firefox_profile,
    discover_local_browsers,
    perform_sqlite_online_backup
)


def test_inspect_chromium_profile(tmp_path: Path):
    profile_dir = tmp_path / "Default"
    profile_dir.mkdir()

    # Create dummy History sqlite db and WAL
    conn = sqlite3.connect(profile_dir / "History")
    conn.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT);")
    conn.execute("INSERT INTO urls VALUES (1, 'https://forenx.io', 'ForenX Forensics');")
    conn.commit()
    conn.close()

    wal_file = profile_dir / "History-wal"
    wal_file.write_bytes(b"wal-header-dummy")

    bookmarks_file = profile_dir / "Bookmarks"
    bookmarks_file.write_text('{"roots": {"bookmark_bar": {"children": []}}}')

    disc = inspect_chromium_profile(profile_dir, "Google Chrome")
    assert disc is not None
    assert disc.browser_name == "Google Chrome"
    assert disc.browser_family == "Chromium"
    assert disc.profile_label == "Google Chrome (Default)"
    assert len(disc.available_artifacts) == 2

    history_art = next(a for a in disc.available_artifacts if a["artifact_type"] == "History")
    assert history_art["has_wal"] is True
    assert history_art["byte_size"] > 0


def test_inspect_firefox_profile(tmp_path: Path):
    profile_dir = tmp_path / "abc1234.default-release"
    profile_dir.mkdir()

    conn = sqlite3.connect(profile_dir / "places.sqlite")
    conn.execute("CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT, title TEXT);")
    conn.commit()
    conn.close()

    disc = inspect_firefox_profile(profile_dir, "default-release", "Mozilla Firefox")
    assert disc is not None
    assert disc.browser_name == "Mozilla Firefox"
    assert disc.browser_family == "Firefox"
    assert disc.profile_label == "Mozilla Firefox (default-release)"
    assert len(disc.available_artifacts) == 1
    assert disc.available_artifacts[0]["artifact_type"] == "places.sqlite"


def test_perform_sqlite_online_backup(tmp_path: Path):
    src_db = tmp_path / "src_history.db"
    dest_db = tmp_path / "backup_history.db"

    conn = sqlite3.connect(src_db)
    conn.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, visit_time INTEGER);")
    conn.execute("INSERT INTO visits VALUES (1, 1334567890);")
    conn.commit()
    conn.close()

    # Perform online backup
    perform_sqlite_online_backup(src_db, dest_db)

    assert dest_db.exists()
    dest_conn = sqlite3.connect(dest_db)
    cur = dest_conn.cursor()
    cur.execute("SELECT count(*) FROM visits;")
    count = cur.fetchone()[0]
    dest_conn.close()

    assert count == 1


def test_discover_local_browsers_returns_list():
    # Calling on the current machine should return a list without crashing
    res = discover_local_browsers()
    assert isinstance(res, list)
