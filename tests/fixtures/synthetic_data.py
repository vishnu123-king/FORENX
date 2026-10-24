"""
Synthetic browser artifact database fixtures for ForenX tests and validation lab.
Generates genuine SQLite databases with realistic Chromium and Firefox schemas,
realistic WebKit / PRTime timestamps, and optional controlled anomalies.
"""

import sqlite3
from datetime import UTC
from pathlib import Path
from typing import Any

# Constants for timestamp offsets
WEBKIT_OFFSET = 11644473600000000

# Controlled test timestamps (Unix epoch seconds)
TS_1 = 1792074600  # 2026-10-15 14:30:00 UTC
TS_2 = 1792077000  # 2026-10-15 15:10:00 UTC
TS_3 = 1792142400  # 2026-10-16 09:20:00 UTC
TS_4 = 1792151100  # 2026-10-16 11:45:00 UTC
TS_5 = 1792152000  # 2026-10-16 12:00:00 UTC

TS_FF_1 = 1792231200  # 2026-10-17 10:00:00 UTC
TS_FF_2 = 1792242900  # 2026-10-17 13:15:00 UTC
TS_FF_BM = 1792243500 # 2026-10-17 13:25:00 UTC

def to_webkit(unix_sec: int) -> int:
    return (unix_sec * 1_000_000) + WEBKIT_OFFSET

def to_prtime(unix_sec: int) -> int:
    return unix_sec * 1_000_000

def create_synthetic_chromium_db(db_path: Path, anomaly: str | None = None) -> Path:
    """
    Create a realistic synthetic Chromium History SQLite database.
    Supports controlled anomalies:
    - 'missing_table': omits the 'visits' table
    - 'missing_column': omits 'visit_time'
    - 'invalid_timestamp': inserts invalid / corrupt timestamp value
    - 'corrupt_file': writes non-SQLite garbage bytes
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if anomaly == "corrupt_file":
        with open(path, "wb") as f:
            f.write(b"NOT_A_SQLITE_DATABASE_CORRUPT_HEADER_0123456789")
        return path

    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()

    if anomaly == "missing_table":
        cursor.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT, visit_count INT);")
        conn.commit()
        conn.close()
        return path

    if anomaly == "missing_column":
        cursor.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT, visit_count INT);")
        cursor.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, url INTEGER, from_visit INTEGER);")
        conn.commit()
        conn.close()
        return path

    cursor.executescript("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url LONGVARCHAR NOT NULL,
            title LONGVARCHAR,
            visit_count INTEGER DEFAULT 0 NOT NULL,
            typed_count INTEGER DEFAULT 0 NOT NULL,
            last_visit_time INTEGER NOT NULL,
            hidden INTEGER DEFAULT 0 NOT NULL
        );

        CREATE TABLE visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url INTEGER NOT NULL,
            visit_time INTEGER NOT NULL,
            from_visit INTEGER,
            transition INTEGER DEFAULT 0 NOT NULL,
            segment_id INTEGER,
            visit_duration INTEGER DEFAULT 0 NOT NULL
        );

        CREATE TABLE downloads (
            id INTEGER PRIMARY KEY,
            guid VARCHAR(64) NOT NULL,
            current_path LONGVARCHAR NOT NULL,
            target_path LONGVARCHAR NOT NULL,
            start_time INTEGER NOT NULL,
            received_bytes INTEGER NOT NULL,
            total_bytes INTEGER NOT NULL,
            state INTEGER NOT NULL,
            danger_type INTEGER NOT NULL,
            interrupt_reason INTEGER NOT NULL,
            tab_url LONGVARCHAR NOT NULL
        );
    """)

    # Seed URLs
    urls_data = [
        (1, "https://en.wikipedia.org/wiki/Digital_forensics", "Digital Forensics - Wikipedia", 5, 1, to_webkit(TS_1), 0),
        (2, "https://csrc.nist.gov/projects/computer-forensic-tool-testing-cftt", "NIST CFTT Project", 2, 0, to_webkit(TS_2), 0),
        (3, "https://github.com/forenx-project/research", "ForenX Research Repository", 1, 1, to_webkit(TS_3), 0),
        (4, "https://academic.oup.com/dfr", "Digital Forensic Research - Academic Review", 3, 0, to_webkit(TS_4), 0)
    ]
    cursor.executemany("INSERT INTO urls VALUES (?, ?, ?, ?, ?, ?, ?);", urls_data)

    # Seed Visits
    t1 = -9999 if anomaly == "invalid_timestamp" else to_webkit(TS_1)
    visits_data = [
        (101, 1, t1, 0, 0, 1, 12000000),
        (102, 2, to_webkit(TS_2), 101, 0, 1, 45000000),
        (103, 3, to_webkit(TS_3), 0, 1, 2, 8000000),
        (104, 4, to_webkit(TS_4), 0, 0, 3, 30000000)
    ]
    cursor.executemany("INSERT INTO visits VALUES (?, ?, ?, ?, ?, ?, ?);", visits_data)

    # Seed Downloads
    downloads_data = [
        (201, "guid-cftt-test-01", "/downloads/nist_test_image.dd", "/downloads/nist_test_image.dd",
         to_webkit(TS_5), 104857600, 104857600, 1, 0, 0, "https://csrc.nist.gov/downloads/nist_test_image.dd")
    ]
    cursor.executemany("INSERT INTO downloads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", downloads_data)

    conn.commit()
    conn.close()
    return path

def create_synthetic_firefox_db(db_path: Path, anomaly: str | None = None) -> Path:
    """
    Create a realistic synthetic Firefox places.sqlite database.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if anomaly == "corrupt_file":
        with open(path, "wb") as f:
            f.write(b"CORRUPT_FIREFOX_PLACES_HEADER_XYZ")
        return path

    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()

    if anomaly == "missing_table":
        cursor.execute("CREATE TABLE moz_favicons (id INTEGER PRIMARY KEY);")
        conn.commit()
        conn.close()
        return path

    cursor.executescript("""
        CREATE TABLE moz_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url LONGVARCHAR,
            title LONGVARCHAR,
            rev_host LONGVARCHAR,
            visit_count INTEGER DEFAULT 0,
            hidden INTEGER DEFAULT 0,
            typed INTEGER DEFAULT 0,
            frecency INTEGER DEFAULT -1,
            last_visit_date INTEGER,
            guid TEXT,
            foreign_count INTEGER DEFAULT 0
        );

        CREATE TABLE moz_historyvisits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_visit INTEGER,
            place_id INTEGER,
            visit_date INTEGER,
            visit_type INTEGER,
            session INTEGER
        );

        CREATE TABLE moz_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type INTEGER,
            fk INTEGER,
            parent INTEGER,
            position INTEGER,
            title LONGVARCHAR,
            keyword_id INTEGER,
            folder_type TEXT,
            dateAdded INTEGER,
            lastModified INTEGER,
            guid TEXT,
            syncStatus INTEGER DEFAULT 0,
            syncChangeCounter INTEGER DEFAULT 1
        );
    """)

    # Seed places
    places_data = [
        (1, "https://www.wireshark.org/docs/", "Wireshark Documentation", "gro.krahseriw.www.", 3, 0, 1, 100, to_prtime(TS_FF_1), "guid_p1", 0),
        (2, "https://docs.python.org/3/library/sqlite3.html", "sqlite3 — DB-API 2.0 interface for SQLite databases", "gro.nohtyp.scod.", 6, 0, 1, 200, to_prtime(TS_FF_2), "guid_p2", 0)
    ]
    cursor.executemany("INSERT INTO moz_places VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", places_data)

    # Seed visits
    ff_visits_data = [
        (501, 0, 1, to_prtime(TS_FF_1), 1, 1),
        (502, 501, 2, to_prtime(TS_FF_2), 1, 1)
    ]
    cursor.executemany("INSERT INTO moz_historyvisits VALUES (?, ?, ?, ?, ?, ?);", ff_visits_data)

    # Seed bookmarks (type=1 indicates URL bookmark)
    bookmarks_data = [
        (801, 1, 2, 2, 0, "sqlite3 Python Documentation Bookmark", None, None, to_prtime(TS_FF_BM), to_prtime(TS_FF_BM), "guid_bm1", 0, 1)
    ]
    cursor.executemany("INSERT INTO moz_bookmarks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", bookmarks_data)

    conn.commit()
    conn.close()
    return path

def get_ground_truth_manifest() -> list[dict[str, Any]]:
    """
    Returns the exact known-answer ground truth events corresponding
    to the synthetic test databases for verification in Validation Lab.
    """
    from datetime import datetime
    return [
        {
            "browser_family": "Chromium",
            "event_type": "url_visit",
            "url": "https://en.wikipedia.org/wiki/Digital_forensics",
            "title": "Digital Forensics - Wikipedia",
            "expected_utc": datetime.fromtimestamp(TS_1, tz=UTC).isoformat(),
            "test_id": "TEST_CHROME_VISIT_01"
        },
        {
            "browser_family": "Chromium",
            "event_type": "url_visit",
            "url": "https://csrc.nist.gov/projects/computer-forensic-tool-testing-cftt",
            "title": "NIST CFTT Project",
            "expected_utc": datetime.fromtimestamp(TS_2, tz=UTC).isoformat(),
            "test_id": "TEST_CHROME_VISIT_02"
        },
        {
            "browser_family": "Chromium",
            "event_type": "url_visit",
            "url": "https://github.com/forenx-project/research",
            "title": "ForenX Research Repository",
            "expected_utc": datetime.fromtimestamp(TS_3, tz=UTC).isoformat(),
            "test_id": "TEST_CHROME_VISIT_03"
        },
        {
            "browser_family": "Chromium",
            "event_type": "url_visit",
            "url": "https://academic.oup.com/dfr",
            "title": "Digital Forensic Research - Academic Review",
            "expected_utc": datetime.fromtimestamp(TS_4, tz=UTC).isoformat(),
            "test_id": "TEST_CHROME_VISIT_04"
        },
        {
            "browser_family": "Chromium",
            "event_type": "download",
            "url": "https://csrc.nist.gov/downloads/nist_test_image.dd",
            "title": "nist_test_image.dd",
            "expected_utc": datetime.fromtimestamp(TS_5, tz=UTC).isoformat(),
            "test_id": "TEST_CHROME_DL_01"
        },
        {
            "browser_family": "Firefox",
            "event_type": "url_visit",
            "url": "https://www.wireshark.org/docs/",
            "title": "Wireshark Documentation",
            "expected_utc": datetime.fromtimestamp(TS_FF_1, tz=UTC).isoformat(),
            "test_id": "TEST_FF_VISIT_01"
        },
        {
            "browser_family": "Firefox",
            "event_type": "url_visit",
            "url": "https://docs.python.org/3/library/sqlite3.html",
            "title": "sqlite3 — DB-API 2.0 interface for SQLite databases",
            "expected_utc": datetime.fromtimestamp(TS_FF_2, tz=UTC).isoformat(),
            "test_id": "TEST_FF_VISIT_02"
        },
        {
            "browser_family": "Firefox",
            "event_type": "bookmark",
            "url": "https://docs.python.org/3/library/sqlite3.html",
            "title": "sqlite3 Python Documentation Bookmark",
            "expected_utc": datetime.fromtimestamp(TS_FF_BM, tz=UTC).isoformat(),
            "test_id": "TEST_FF_BM_01"
        }
    ]
