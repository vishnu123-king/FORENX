"""
Abstract base parser for browser SQLite artifacts.
Enforces read-only database connections, schema validation, integrity checks,
and structured warning reporting.
"""

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forenx.models import Event


@dataclass
class ParserResult:
    parser_name: str
    parser_version: str
    records_seen: int = 0
    records_extracted: int = 0
    records_skipped: int = 0
    warnings: list[str] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    schema_info: dict[str, Any] = field(default_factory=dict)

class BaseBrowserParser(ABC):
    name: str = "BaseParser"
    version: str = "1.0.0"
    browser_family: str = "Generic"

    def open_readonly_db(self, db_path: Path) -> sqlite3.Connection:
        """
        Open the target SQLite database safely in read-only mode.
        """
        path = Path(db_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        # Open in read-only mode using SQLite URI or query_only pragma
        try:
            uri = f"file:{path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=10.0)
        except Exception:
            conn = sqlite3.connect(str(path), timeout=10.0)
            conn.execute("PRAGMA query_only = ON;")

        conn.row_factory = sqlite3.Row
        return conn

    def check_sqlite_integrity(self, conn: sqlite3.Connection) -> tuple[bool, str]:
        """Verify low-level SQLite database integrity via PRAGMA quick_check."""
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check;")
            row = cursor.fetchone()
            result = row[0] if row else "unknown"
            return (result == "ok"), result
        except sqlite3.DatabaseError as e:
            return False, str(e)

    def get_table_columns(self, conn: sqlite3.Connection, table_name: str) -> set[str]:
        """Inspect and return existing column names for a table."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        return {r["name"].lower() for r in cursor.fetchall()}

    def get_existing_tables(self, conn: sqlite3.Connection) -> set[str]:
        """Inspect and return existing user table names in the database."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return {r["name"].lower() for r in cursor.fetchall()}

    @abstractmethod
    def parse(
        self,
        db_path: Path,
        case_id: str,
        evidence_id: str,
        analysis_run_id: str
    ) -> ParserResult:
        """Extract normalized events from the browser database."""
