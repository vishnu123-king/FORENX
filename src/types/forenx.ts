export interface Case {
  id: string;
  name: string;
  description: string;
  investigator_label: string;
  status: "active" | "archived" | "closed";
  created_at: string;
  updated_at: string;
  notes: string;
}

export interface Endpoint {
  id: string;
  device_label: string;
  operating_system: string;
  agent_version: string;
  enrollment_status: "active" | "revoked" | "offline";
  certificate_identity: string;
  last_seen: string;
  created_at: string;
  revocation_timestamp: string | null;
  ip_address: string;
}

export interface EnrollmentToken {
  token: string;
  device_label: string;
  operating_system: string;
  created_at: string;
  expires_at: string;
  used: boolean;
  used_at: string | null;
  created_by: string;
}

export interface AcquisitionJob {
  id: string;
  case_id: string;
  endpoint_id: string;
  requesting_investigator_id: string;
  status: "created" | "pending" | "approved" | "in_progress" | "completed" | "failed" | "rejected";
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  expires_at: string | null;
  replay_nonce: string;
  authorized_scope: {
    approved_browsers?: string[];
    approved_artifact_types?: string[];
    allow_wal_sidecars?: boolean;
    max_package_size_mb?: number;
  };
  authorization_metadata: {
    warrant_or_incident_id?: string;
    investigator_signature_label?: string;
    scope_summary?: string;
  };
  outcome_summary: string;
  package_id: string | null;
}

export interface EvidencePackage {
  id: string;
  case_id: string;
  acquisition_id: string;
  endpoint_id: string | null;
  acquisition_method: string;
  package_filename: string;
  storage_path: string;
  package_sha256: string;
  byte_size: number;
  manifest_version: string;
  verification_status: "verified" | "failed" | "unverified";
  created_at: string;
  artifact_count: number;
  warnings_count: number;
  manifest_json: string;
}

export interface DiscoveredProfile {
  browser_name: string;
  browser_family: "Chromium" | "Firefox" | string;
  profile_id: string;
  profile_label: string;
  profile_path: string;
  available_artifacts: Array<{
    artifact_type: string;
    file_name: string;
    file_path: string;
    byte_size: number;
    has_wal: boolean;
    has_shm: boolean;
  }>;
}

export interface Evidence {
  id: string;
  case_id: string;
  filename: string;
  evidence_type: string;
  byte_size: number;
  sha256: string;
  imported_at: string;
  acquisition_method: string;
  provenance_notes: string;
  storage_relative_path: string;
  verification_status: "verified" | "failed" | "unverified" | "missing";
  parser_compatibility: string;
}

export interface AnalysisRun {
  id: string;
  case_id: string;
  started_at: string;
  completed_at: string | null;
  status: "running" | "completed" | "completed_with_warnings" | "failed";
  parser_versions: string;
  records_seen: number;
  records_extracted: number;
  records_skipped: number;
  warnings_count: number;
  error_summary: string;
}

export interface ForensicEvent {
  id: string;
  case_id: string;
  evidence_id: string;
  analysis_run_id: string;
  browser_family: "Chromium" | "Firefox" | string;
  event_type: "url_visit" | "download" | "bookmark" | string;
  url: string;
  title: string;
  raw_timestamp: number;
  timestamp_format: string;
  normalized_utc: string | null;
  conversion_status: "success" | "out_of_range" | "invalid" | "zero";
  source_database: string;
  source_table: string;
  source_record_id: string;
  parser_version: string;
  warning: string;
  extra_metadata?: Record<string, any>;
}

export interface ValidationRun {
  id: string;
  case_id: string;
  created_at: string;
  dataset_version: string;
  expected_count: number;
  extracted_count: number;
  matched_count: number;
  missing_count: number;
  unexpected_count: number;
  precision: number | null;
  recall: number | null;
  result_summary: string;
  details?: {
    field_mismatches?: Array<{
      event_id: string;
      url: string;
      field: string;
      expected: string;
      actual: string;
      difference_seconds?: number;
    }>;
    missing_records?: any[];
    unexpected_records?: any[];
  };
}

export interface AuditEntry {
  id: string;
  timestamp_utc: string;
  operation: string;
  case_id: string | null;
  evidence_id: string | null;
  outcome: "success" | "failure" | "warning";
  details: string;
  previous_entry_hash: string;
  entry_hash: string;
}

export interface GlobalStats {
  total_cases: number;
  total_evidence: number;
  total_analysis_runs: number;
  total_events: number;
  verification_failures: number;
  recent_activity: {
    started_at: string;
    completed_at: string;
    status: string;
    records_extracted: number;
    warnings_count: number;
  } | null;
}
