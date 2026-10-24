"""
Database management, schema initialization, and migrations for ForenX.
Uses standard-library sqlite3 with WAL mode, foreign keys, and versioned migrations.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from forenx.config import get_config

SCHEMA_VERSION = 2

CREATE_SCHEMA_SQL_V1 = """
-- Cases table
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    investigator_label TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    notes TEXT
);

-- Evidence items
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    acquisition_method TEXT NOT NULL,
    provenance_notes TEXT,
    storage_relative_path TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'verified',
    parser_compatibility TEXT NOT NULL DEFAULT 'compatible',
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- Analysis runs
CREATE TABLE IF NOT EXISTS analysis_runs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    parser_versions TEXT NOT NULL,
    records_seen INTEGER DEFAULT 0,
    records_extracted INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    error_summary TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- Normalized browser events
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    analysis_run_id TEXT NOT NULL,
    browser_family TEXT NOT NULL,
    event_type TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    raw_timestamp INTEGER,
    timestamp_format TEXT NOT NULL,
    normalized_utc TEXT,
    conversion_status TEXT NOT NULL,
    source_database TEXT,
    source_table TEXT,
    source_record_id TEXT,
    parser_version TEXT NOT NULL,
    warning TEXT,
    extra_json TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE,
    FOREIGN KEY(evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
    FOREIGN KEY(analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);

-- Cryptographically chained audit log
CREATE TABLE IF NOT EXISTS audit_entries (
    id TEXT PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    operation TEXT NOT NULL,
    case_id TEXT,
    evidence_id TEXT,
    outcome TEXT NOT NULL,
    details TEXT,
    previous_entry_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL
);

-- Known-answer validation runs
CREATE TABLE IF NOT EXISTS validation_runs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    expected_count INTEGER DEFAULT 0,
    extracted_count INTEGER DEFAULT 0,
    matched_count INTEGER DEFAULT 0,
    missing_count INTEGER DEFAULT 0,
    unexpected_count INTEGER DEFAULT 0,
    precision REAL,
    recall REAL,
    result_summary TEXT,
    details_json TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_id);
CREATE INDEX IF NOT EXISTS idx_events_case ON events(case_id);
CREATE INDEX IF NOT EXISTS idx_events_evidence ON events(evidence_id);
CREATE INDEX IF NOT EXISTS idx_events_utc ON events(normalized_utc);
CREATE INDEX IF NOT EXISTS idx_events_browser ON events(browser_family);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_entries(case_id);
CREATE INDEX IF NOT EXISTS idx_validation_case ON validation_runs(case_id);
"""

CREATE_SCHEMA_SQL_V2 = """
-- Endpoints table
CREATE TABLE IF NOT EXISTS endpoints (
    id TEXT PRIMARY KEY,
    device_label TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    agent_version TEXT NOT NULL,
    enrollment_status TEXT NOT NULL DEFAULT 'active',
    certificate_identity TEXT,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revocation_timestamp TEXT,
    ip_address TEXT
);

-- Enrollment tokens
CREATE TABLE IF NOT EXISTS enrollment_tokens (
    token TEXT PRIMARY KEY,
    device_label TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER DEFAULT 0,
    used_at TEXT,
    created_by TEXT NOT NULL
);

-- Scoped acquisition jobs
CREATE TABLE IF NOT EXISTS acquisition_jobs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    endpoint_id TEXT NOT NULL,
    requesting_investigator_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    expires_at TEXT,
    replay_nonce TEXT NOT NULL,
    authorized_scope_json TEXT NOT NULL,
    authorization_metadata_json TEXT,
    outcome_summary TEXT,
    package_id TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- Shared Evidence Packages (FX-ACQ-*.forenx.zip)
CREATE TABLE IF NOT EXISTS evidence_packages (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    acquisition_id TEXT NOT NULL,
    endpoint_id TEXT,
    acquisition_method TEXT NOT NULL,
    package_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    package_sha256 TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    manifest_version TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'verified',
    created_at TEXT NOT NULL,
    artifact_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    manifest_json TEXT,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_case ON acquisition_jobs(case_id);
CREATE INDEX IF NOT EXISTS idx_jobs_endpoint ON acquisition_jobs(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_packages_case ON evidence_packages(case_id);
"""

def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a connection to the application SQLite database with foreign keys enabled."""
    if db_path is None:
        cfg = get_config()
        cfg.ensure_directories()
        db_path = cfg.db_path
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize database tables and handle schema migrations."""
    conn = get_db_connection(db_path)
    with conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version;")
        current_version = cursor.fetchone()[0]

        if current_version < 1:
            cursor.executescript(CREATE_SCHEMA_SQL_V1)
            current_version = 1

        if current_version < 2:
            cursor.executescript(CREATE_SCHEMA_SQL_V2)
            cursor.execute("PRAGMA user_version = 2;")
    conn.close()
