"""
Domain models and dataclasses for ForenX.
Supports dual-mode local and remote forensic operations.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, List, Dict, Optional


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(UTC).isoformat()

def generate_id(prefix: str = "") -> str:
    """Generate a clean unique identifier."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid

@dataclass
class Case:
    id: str
    name: str
    description: str = ""
    investigator_label: str = ""
    status: str = "active"  # active, archived, closed
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class Endpoint:
    id: str
    device_label: str
    operating_system: str  # linux, windows, darwin
    agent_version: str = "1.0.0"
    enrollment_status: str = "active"  # active, revoked, offline
    certificate_identity: str = ""
    last_seen: str = field(default_factory=utc_now_iso)
    created_at: str = field(default_factory=utc_now_iso)
    revocation_timestamp: Optional[str] = None
    ip_address: str = "127.0.0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class EnrollmentToken:
    token: str
    device_label: str
    operating_system: str
    created_at: str = field(default_factory=utc_now_iso)
    expires_at: str = field(default_factory=utc_now_iso)
    used: bool = False
    used_at: Optional[str] = None
    created_by: str = "admin"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class AcquisitionJob:
    id: str
    case_id: str
    endpoint_id: str
    requesting_investigator_id: str
    status: str = "created"  # created, pending, approved, in_progress, completed, failed, rejected
    created_at: str = field(default_factory=utc_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    expires_at: Optional[str] = None
    replay_nonce: str = field(default_factory=lambda: uuid.uuid4().hex)
    authorized_scope: dict[str, Any] = field(default_factory=dict)
    authorization_metadata: dict[str, Any] = field(default_factory=dict)
    outcome_summary: str = ""
    package_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class EvidencePackage:
    id: str  # e.g. FX-ACQ-123456
    case_id: str
    acquisition_id: str
    endpoint_id: Optional[str]
    acquisition_method: str  # local_system_authorized, remote_agent_connected, offline_field_collector
    package_filename: str
    storage_path: str
    package_sha256: str
    byte_size: int
    manifest_version: str = "1.0.0"
    verification_status: str = "verified"  # verified, failed, unverified
    created_at: str = field(default_factory=utc_now_iso)
    artifact_count: int = 0
    warnings_count: int = 0
    manifest_json: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class DiscoveredProfile:
    browser_name: str  # Google Chrome, Microsoft Edge, Brave, Mozilla Firefox
    browser_family: str  # Chromium, Firefox
    profile_id: str  # Default, Profile 1, xxxx.default-release
    profile_label: str
    profile_path: str
    available_artifacts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class Evidence:
    id: str
    case_id: str
    filename: str
    evidence_type: str  # chromium_history, firefox_places, artifact_package, unknown
    byte_size: int
    sha256: str
    imported_at: str = field(default_factory=utc_now_iso)
    acquisition_method: str = "controlled_local_copy"
    provenance_notes: str = ""
    storage_relative_path: str = ""
    verification_status: str = "verified"  # verified, failed, unverified, missing
    parser_compatibility: str = "compatible"  # compatible, warning, unsupported, corrupt

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class AnalysisRun:
    id: str
    case_id: str
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None
    status: str = "running"  # running, completed, completed_with_warnings, failed
    parser_versions: str = "ChromiumHistoryParser 1.0.0, FirefoxPlacesParser 1.0.0"
    records_seen: int = 0
    records_extracted: int = 0
    records_skipped: int = 0
    warnings_count: int = 0
    error_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class Event:
    id: str
    case_id: str
    evidence_id: str
    analysis_run_id: str
    browser_family: str  # Chromium, Firefox
    event_type: str  # url_visit, download, bookmark
    url: str
    title: str = ""
    raw_timestamp: int = 0
    timestamp_format: str = "webkit_microseconds_1601"
    normalized_utc: str | None = None
    conversion_status: str = "success"  # success, out_of_range, invalid, unparseable
    source_database: str = ""
    source_table: str = ""
    source_record_id: str = ""
    parser_version: str = "1.0.0"
    warning: str = ""
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class AuditEntry:
    id: str
    timestamp_utc: str = field(default_factory=utc_now_iso)
    operation: str = ""
    case_id: str | None = None
    evidence_id: str | None = None
    outcome: str = "success"  # success, failure, warning
    details: str = ""
    previous_entry_hash: str = "0000000000000000000000000000000000000000000000000000000000000000"
    entry_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class ValidationRun:
    id: str
    case_id: str
    created_at: str = field(default_factory=utc_now_iso)
    dataset_version: str = "synthetic-1.0"
    expected_count: int = 0
    extracted_count: int = 0
    matched_count: int = 0
    missing_count: int = 0
    unexpected_count: int = 0
    precision: float | None = None
    recall: float | None = None
    result_summary: str = ""
    details_json: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
